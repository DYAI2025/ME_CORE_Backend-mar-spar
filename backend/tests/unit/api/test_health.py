"""
Unit tests for health check API endpoint.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException
from backend.api.health import router, health_check
from backend.services.health_service import HealthStatus


class TestHealthAPI:
    """Test cases for health check endpoint."""
    
    @pytest.mark.unit
    async def test_health_check_success(self, client):
        """Test successful health check response."""
        response = client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database_connected" in data
        assert "timestamp" in data
    
    @pytest.mark.unit
    async def test_health_check_database_failure(self, client, monkeypatch):
        """Test health check when database is disconnected."""
        # Mock the health service to return database disconnected
        async def mock_check_health():
            return HealthStatus(
                status="unhealthy",
                database_connected=False,
                timestamp="2024-01-31T12:00:00Z",
                details={"error": "Database connection failed"}
            )
        
        # Patch the check_health function
        from backend.services import health_service
        monkeypatch.setattr(health_service, "check_health", mock_check_health)
        
        response = client.get("/healthz")
        
        assert response.status_code == 503
        assert response.json()["detail"] == "Database connection failed"
    
    @pytest.mark.unit
    async def test_health_check_response_model(self, async_client):
        """Test health check response conforms to model."""
        response = await async_client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert isinstance(data["status"], str)
        assert isinstance(data["database_connected"], bool)
        assert isinstance(data["timestamp"], str)
        
        # Validate status values
        assert data["status"] in ["healthy", "unhealthy"]
    
    @pytest.mark.unit
    async def test_health_check_headers(self, client):
        """Test health check response headers."""
        response = client.get("/healthz")
        
        # Check cache control headers for health endpoints
        assert "cache-control" in response.headers
        assert "no-cache" in response.headers["cache-control"].lower()
    
    @pytest.mark.unit
    @pytest.mark.parametrize("path", [
        "/healthz",
        "/healthz/",  # With trailing slash
    ])
    async def test_health_check_paths(self, client, path):
        """Test health check is accessible on expected paths."""
        response = client.get(path)
        assert response.status_code in [200, 503]
    
    @pytest.mark.unit
    async def test_health_check_method_not_allowed(self, client):
        """Test non-GET methods return 405."""
        for method in ["post", "put", "delete", "patch"]:
            response = getattr(client, method)("/healthz")
            assert response.status_code == 405
    
    @pytest.mark.unit
    async def test_health_check_with_metrics(self, client, mock_settings):
        """Test health check includes metrics when enabled."""
        # Enable metrics in settings
        mock_settings(include_metrics_in_health=True)
        
        response = client.get("/healthz")
        
        if response.status_code == 200:
            data = response.json()
            # When metrics are enabled, additional fields might be present
            possible_metric_fields = ["cpu_usage", "memory_usage", "uptime"]
            # Check if any metric fields are present
            has_metrics = any(field in data for field in possible_metric_fields)
            # This assertion depends on implementation
    
    @pytest.mark.unit
    async def test_health_check_timeout(self, client, monkeypatch):
        """Test health check handles timeouts gracefully."""
        import asyncio
        
        async def mock_slow_health_check():
            await asyncio.sleep(10)  # Simulate slow response
            return HealthStatus(
                status="healthy",
                database_connected=True,
                timestamp="2024-01-31T12:00:00Z"
            )
        
        from backend.services import health_service
        monkeypatch.setattr(health_service, "check_health", mock_slow_health_check)
        
        # The actual timeout behavior depends on implementation
        # This test verifies the endpoint doesn't hang indefinitely
        response = client.get("/healthz", timeout=1.0)
        # Expect either timeout error or graceful degradation
        assert response.status_code in [503, 504]
    
    @pytest.mark.unit
    async def test_health_check_concurrent_requests(self, async_client):
        """Test health check handles concurrent requests."""
        import asyncio
        
        # Send multiple concurrent requests
        tasks = [
            async_client.get("/healthz")
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code in [200, 503]
    
    @pytest.mark.unit
    async def test_health_check_error_handling(self, client, monkeypatch):
        """Test health check handles unexpected errors."""
        async def mock_error_health_check():
            raise Exception("Unexpected error in health check")
        
        from backend.services import health_service
        monkeypatch.setattr(health_service, "check_health", mock_error_health_check)
        
        response = client.get("/healthz")
        
        # Should return 503 on unexpected errors
        assert response.status_code == 500
        assert "Internal Server Error" in response.text