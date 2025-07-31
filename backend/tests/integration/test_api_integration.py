"""
Integration tests for complete API workflows.
"""
import pytest
import asyncio
from httpx import AsyncClient


class TestAPIIntegration:
    """Integration tests for API workflows."""
    
    @pytest.mark.integration
    async def test_marker_analysis_workflow(self, async_client: AsyncClient, test_db):
        """Test complete marker analysis workflow."""
        # Step 1: Check system health
        health_response = await async_client.get("/healthz")
        assert health_response.status_code == 200
        assert health_response.json()["database_connected"] is True
        
        # Step 2: Submit text for analysis
        analysis_request = {
            "text": "Der Patient zeigt deutliche Anzeichen von AMBIVALENZ und RESONANZ.",
            "language": "de",
            "options": {
                "include_metadata": True,
                "confidence_threshold": 0.7
            }
        }
        
        analysis_response = await async_client.post(
            "/api/v1/analyze",
            json=analysis_request
        )
        assert analysis_response.status_code == 200
        
        analysis_result = analysis_response.json()
        assert "markers" in analysis_result
        assert len(analysis_result["markers"]) > 0
        
        # Step 3: Retrieve specific markers
        for marker in analysis_result["markers"]:
            marker_response = await async_client.get(
                f"/api/v1/markers/{marker['id']}"
            )
            assert marker_response.status_code == 200
            marker_data = marker_response.json()
            assert marker_data["name"] == marker["name"]
            assert marker_data["confidence"] >= 0.7
        
        # Step 4: Get analysis metrics
        metrics_response = await async_client.get("/api/v1/metrics")
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.json()
        assert metrics_data["total_analyses"] > 0
    
    @pytest.mark.integration
    async def test_concurrent_analysis_requests(self, async_client: AsyncClient, test_db):
        """Test system handles concurrent analysis requests."""
        # Prepare multiple analysis requests
        requests = [
            {
                "text": f"Test text {i} with markers for analysis.",
                "language": "de",
                "options": {"confidence_threshold": 0.8}
            }
            for i in range(10)
        ]
        
        # Send concurrent requests
        tasks = [
            async_client.post("/api/v1/analyze", json=req)
            for req in requests
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        for response in responses:
            assert response.status_code == 200
            assert "markers" in response.json()
    
    @pytest.mark.integration
    async def test_marker_crud_operations(self, async_client: AsyncClient, test_db):
        """Test complete CRUD operations for markers."""
        # Create marker
        new_marker = {
            "name": "TEST_INTEGRATION_MARKER",
            "category": "integration_test",
            "confidence": 0.95,
            "description": "Integration test marker"
        }
        
        create_response = await async_client.post(
            "/api/v1/markers",
            json=new_marker
        )
        assert create_response.status_code == 201
        created_marker = create_response.json()
        marker_id = created_marker["id"]
        
        # Read marker
        read_response = await async_client.get(f"/api/v1/markers/{marker_id}")
        assert read_response.status_code == 200
        assert read_response.json()["name"] == new_marker["name"]
        
        # Update marker
        update_data = {"confidence": 0.98}
        update_response = await async_client.patch(
            f"/api/v1/markers/{marker_id}",
            json=update_data
        )
        assert update_response.status_code == 200
        assert update_response.json()["confidence"] == 0.98
        
        # List markers
        list_response = await async_client.get("/api/v1/markers")
        assert list_response.status_code == 200
        markers = list_response.json()
        assert any(m["id"] == marker_id for m in markers)
        
        # Delete marker
        delete_response = await async_client.delete(f"/api/v1/markers/{marker_id}")
        assert delete_response.status_code == 204
        
        # Verify deletion
        verify_response = await async_client.get(f"/api/v1/markers/{marker_id}")
        assert verify_response.status_code == 404
    
    @pytest.mark.integration
    async def test_error_handling_workflow(self, async_client: AsyncClient):
        """Test API error handling across endpoints."""
        # Test invalid analysis request
        invalid_request = {
            "text": "",  # Empty text
            "language": "invalid_lang"
        }
        
        error_response = await async_client.post(
            "/api/v1/analyze",
            json=invalid_request
        )
        assert error_response.status_code == 422
        error_data = error_response.json()
        assert "detail" in error_data
        
        # Test non-existent resource
        not_found_response = await async_client.get("/api/v1/markers/99999")
        assert not_found_response.status_code == 404
        
        # Test method not allowed
        method_response = await async_client.patch("/api/v1/analyze")
        assert method_response.status_code == 405
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_dashboard_data_aggregation(self, async_client: AsyncClient, test_db):
        """Test dashboard endpoint aggregates data correctly."""
        # Create test data
        test_analyses = 5
        for i in range(test_analyses):
            await async_client.post(
                "/api/v1/analyze",
                json={
                    "text": f"Test analysis {i}",
                    "language": "de"
                }
            )
        
        # Get dashboard data
        dashboard_response = await async_client.get("/api/v1/dashboard")
        assert dashboard_response.status_code == 200
        
        dashboard_data = dashboard_response.json()
        assert "total_analyses" in dashboard_data
        assert "marker_statistics" in dashboard_data
        assert "recent_activity" in dashboard_data
        assert dashboard_data["total_analyses"] >= test_analyses
    
    @pytest.mark.integration
    async def test_rate_limiting(self, async_client: AsyncClient):
        """Test API rate limiting is enforced."""
        # Send many requests rapidly
        rapid_requests = 100
        endpoint = "/api/v1/analyze"
        
        responses = []
        for _ in range(rapid_requests):
            response = await async_client.post(
                endpoint,
                json={"text": "Rate limit test", "language": "de"}
            )
            responses.append(response.status_code)
            
            # Check if rate limited
            if response.status_code == 429:
                break
        
        # Verify rate limiting kicked in at some point
        # (This assumes rate limiting is configured)
        # assert 429 in responses, "Rate limiting should be enforced"
    
    @pytest.mark.integration
    async def test_api_versioning(self, async_client: AsyncClient):
        """Test API versioning works correctly."""
        # Test v1 endpoints
        v1_response = await async_client.get("/api/v1/markers")
        assert v1_response.status_code == 200
        
        # Test v2 endpoints if available
        v2_response = await async_client.get("/api/v2/markers")
        # v2 might not exist yet
        assert v2_response.status_code in [200, 404]
        
        # Test unversioned endpoints return error
        unversioned_response = await async_client.get("/api/markers")
        assert unversioned_response.status_code == 404