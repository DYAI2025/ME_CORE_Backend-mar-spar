"""
Unit tests for markers API endpoint.
"""
import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import HTTPException
from backend.api.markers import router


class TestMarkersAPI:
    """Test cases for markers API endpoints."""
    
    @pytest.mark.unit
    async def test_get_markers_success(self, client, mock_marker_repository):
        """Test successful retrieval of markers."""
        # Mock repository response
        mock_markers = [
            {
                "_id": "marker1",
                "name": "TEST_MARKER",
                "pattern": r"\btest\b",
                "description": "Test marker",
                "marker_type": "action"
            },
            {
                "_id": "marker2", 
                "name": "ANOTHER_MARKER",
                "pattern": r"\banother\b",
                "description": "Another marker",
                "marker_type": "condition"
            }
        ]
        mock_marker_repository.get_all_markers.return_value = mock_markers
        
        response = client.get("/markers/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "TEST_MARKER"
        assert data[1]["name"] == "ANOTHER_MARKER"
    
    @pytest.mark.unit
    async def test_get_markers_empty(self, client, mock_marker_repository):
        """Test getting markers when none exist."""
        mock_marker_repository.get_all_markers.return_value = []
        
        response = client.get("/markers/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.unit
    async def test_get_marker_by_id_success(self, client, mock_marker_repository):
        """Test getting a specific marker by ID."""
        mock_marker = {
            "_id": "marker1",
            "name": "TEST_MARKER",
            "pattern": r"\btest\b",
            "description": "Test marker",
            "marker_type": "action"
        }
        mock_marker_repository.get_marker_by_id.return_value = mock_marker
        
        response = client.get("/markers/marker1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_MARKER"
        assert data["_id"] == "marker1"
    
    @pytest.mark.unit
    async def test_get_marker_by_id_not_found(self, client, mock_marker_repository):
        """Test getting a non-existent marker."""
        mock_marker_repository.get_marker_by_id.return_value = None
        
        response = client.get("/markers/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    async def test_get_markers_by_type_success(self, client, mock_marker_repository):
        """Test filtering markers by type."""
        mock_markers = [
            {
                "_id": "marker1",
                "name": "ACTION_MARKER",
                "pattern": r"\baction\b",
                "description": "Action marker",
                "marker_type": "action"
            }
        ]
        mock_marker_repository.get_markers_by_type.return_value = mock_markers
        
        response = client.get("/markers/type/action")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["marker_type"] == "action"
    
    @pytest.mark.unit
    async def test_search_markers_success(self, client, mock_marker_repository):
        """Test searching markers."""
        mock_markers = [
            {
                "_id": "marker1",
                "name": "TEST_MARKER",
                "pattern": r"\btest\b",
                "description": "Test marker for testing",
                "marker_type": "action"
            }
        ]
        mock_marker_repository.search_markers.return_value = mock_markers
        
        response = client.get("/markers/search?query=test")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "test" in data[0]["description"].lower()
    
    @pytest.mark.unit
    async def test_search_markers_no_query(self, client):
        """Test search without query parameter."""
        response = client.get("/markers/search")
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.unit
    async def test_get_markers_pagination(self, client, mock_marker_repository):
        """Test marker pagination."""
        # Create 20 mock markers
        mock_markers = [
            {
                "_id": f"marker{i}",
                "name": f"MARKER_{i}",
                "pattern": f"\\bmarker{i}\\b",
                "description": f"Marker {i}",
                "marker_type": "action"
            }
            for i in range(20)
        ]
        mock_marker_repository.get_all_markers.return_value = mock_markers
        
        # Test first page
        response = client.get("/markers/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        assert data[0]["name"] == "MARKER_0"
        assert data[9]["name"] == "MARKER_9"
        
        # Test second page
        response = client.get("/markers/?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        assert data[0]["name"] == "MARKER_10"
        assert data[9]["name"] == "MARKER_19"
    
    @pytest.mark.unit
    async def test_get_marker_statistics(self, client, mock_marker_repository):
        """Test getting marker statistics."""
        mock_stats = {
            "total_markers": 100,
            "markers_by_type": {
                "action": 40,
                "condition": 30,
                "object": 20,
                "property": 10
            },
            "most_used_markers": [
                {"name": "IF", "count": 150},
                {"name": "THEN", "count": 140},
                {"name": "WITH", "count": 120}
            ]
        }
        mock_marker_repository.get_marker_statistics.return_value = mock_stats
        
        response = client.get("/markers/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_markers"] == 100
        assert data["markers_by_type"]["action"] == 40
        assert len(data["most_used_markers"]) == 3
    
    @pytest.mark.unit
    async def test_markers_error_handling(self, client, mock_marker_repository):
        """Test error handling in markers endpoint."""
        # Simulate database error
        mock_marker_repository.get_all_markers.side_effect = Exception("Database connection failed")
        
        response = client.get("/markers/")
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()