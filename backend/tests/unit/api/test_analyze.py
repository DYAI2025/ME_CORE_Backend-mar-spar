"""
Unit tests for analyze API endpoints.
"""
import pytest
from unittest.mock import AsyncMock, Mock
import json
from backend.api.analyze import router


class TestAnalyzeAPI:
    """Test cases for text analysis endpoints."""
    
    @pytest.mark.unit
    async def test_analyze_text_success(self, client, mock_analysis_service):
        """Test successful text analysis."""
        # Mock analysis response
        mock_result = {
            "markers": [
                {
                    "marker": "IF",
                    "type": "condition",
                    "start": 0,
                    "end": 2,
                    "context": "IF condition THEN action"
                },
                {
                    "marker": "THEN",
                    "type": "action",
                    "start": 13,
                    "end": 17,
                    "context": "IF condition THEN action"
                }
            ],
            "summary": {
                "total_markers": 2,
                "markers_by_type": {
                    "condition": 1,
                    "action": 1
                }
            },
            "metadata": {
                "text_length": 24,
                "processing_time": 0.123
            }
        }
        mock_analysis_service.analyze_text.return_value = mock_result
        
        request_data = {
            "text": "IF condition THEN action",
            "options": {
                "include_context": True,
                "context_window": 50
            }
        }
        
        response = client.post("/analyze/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["markers"]) == 2
        assert data["summary"]["total_markers"] == 2
        assert data["markers"][0]["marker"] == "IF"
        assert data["markers"][1]["marker"] == "THEN"
    
    @pytest.mark.unit
    async def test_analyze_text_empty(self, client):
        """Test analyzing empty text."""
        request_data = {
            "text": "",
            "options": {}
        }
        
        response = client.post("/analyze/", json=request_data)
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    async def test_analyze_text_too_long(self, client, mock_settings):
        """Test analyzing text that exceeds max length."""
        # Set max length to 100
        mock_settings(MAX_TEXT_LENGTH=100)
        
        request_data = {
            "text": "x" * 101,  # Exceed max length
            "options": {}
        }
        
        response = client.post("/analyze/", json=request_data)
        
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    async def test_analyze_with_custom_options(self, client, mock_analysis_service):
        """Test analysis with custom options."""
        mock_result = {
            "markers": [],
            "summary": {"total_markers": 0, "markers_by_type": {}},
            "metadata": {"custom_option_applied": True}
        }
        mock_analysis_service.analyze_text.return_value = mock_result
        
        request_data = {
            "text": "Sample text",
            "options": {
                "include_context": False,
                "marker_types": ["action", "condition"],
                "min_confidence": 0.8
            }
        }
        
        response = client.post("/analyze/", json=request_data)
        
        assert response.status_code == 200
        # Verify options were passed to service
        mock_analysis_service.analyze_text.assert_called_once()
        call_args = mock_analysis_service.analyze_text.call_args
        assert call_args[1]["options"]["marker_types"] == ["action", "condition"]
        assert call_args[1]["options"]["min_confidence"] == 0.8
    
    @pytest.mark.unit
    async def test_analyze_batch_success(self, client, mock_analysis_service):
        """Test batch text analysis."""
        # Mock batch results
        mock_results = [
            {
                "text_id": "text1",
                "markers": [{"marker": "IF", "type": "condition"}],
                "summary": {"total_markers": 1}
            },
            {
                "text_id": "text2",
                "markers": [{"marker": "THEN", "type": "action"}],
                "summary": {"total_markers": 1}
            }
        ]
        mock_analysis_service.analyze_batch.return_value = mock_results
        
        request_data = {
            "texts": [
                {"id": "text1", "content": "IF condition"},
                {"id": "text2", "content": "THEN action"}
            ],
            "options": {
                "parallel": True,
                "batch_size": 10
            }
        }
        
        response = client.post("/analyze/batch", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"][0]["text_id"] == "text1"
        assert data["results"][1]["text_id"] == "text2"
    
    @pytest.mark.unit
    async def test_analyze_batch_empty(self, client):
        """Test batch analysis with no texts."""
        request_data = {
            "texts": [],
            "options": {}
        }
        
        response = client.post("/analyze/batch", json=request_data)
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    async def test_analyze_batch_too_many(self, client, mock_settings):
        """Test batch analysis with too many texts."""
        # Set max batch size
        mock_settings(MAX_BATCH_SIZE=10)
        
        request_data = {
            "texts": [
                {"id": f"text{i}", "content": f"Text {i}"}
                for i in range(11)  # Exceed max
            ],
            "options": {}
        }
        
        response = client.post("/analyze/batch", json=request_data)
        
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    async def test_analyze_with_interpretation(self, client, mock_analysis_service):
        """Test analysis with LLM interpretation."""
        mock_result = {
            "markers": [
                {"marker": "IF", "type": "condition"},
                {"marker": "THEN", "type": "action"}
            ],
            "summary": {"total_markers": 2},
            "interpretation": {
                "summary": "This appears to be a conditional statement.",
                "suggestions": ["Consider adding ELSE clause"],
                "confidence": 0.85
            }
        }
        mock_analysis_service.analyze_text.return_value = mock_result
        
        request_data = {
            "text": "IF condition THEN action",
            "options": {
                "include_interpretation": True,
                "interpretation_model": "kimi-k2"
            }
        }
        
        response = client.post("/analyze/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "interpretation" in data
        assert data["interpretation"]["confidence"] == 0.85
        assert len(data["interpretation"]["suggestions"]) == 1
    
    @pytest.mark.unit
    async def test_analyze_async_job(self, client, mock_analysis_service):
        """Test async analysis job creation."""
        mock_job_id = "job_123456"
        mock_analysis_service.create_async_job.return_value = {
            "job_id": mock_job_id,
            "status": "pending",
            "created_at": "2024-01-31T12:00:00Z"
        }
        
        request_data = {
            "text": "Very long text that needs async processing...",
            "options": {
                "async": True,
                "callback_url": "https://example.com/callback"
            }
        }
        
        response = client.post("/analyze/async", json=request_data)
        
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert data["job_id"] == mock_job_id
        assert data["status"] == "pending"
    
    @pytest.mark.unit
    async def test_analyze_error_handling(self, client, mock_analysis_service):
        """Test error handling in analysis endpoint."""
        # Simulate service error
        mock_analysis_service.analyze_text.side_effect = Exception("Analysis engine failed")
        
        request_data = {
            "text": "Sample text",
            "options": {}
        }
        
        response = client.post("/analyze/", json=request_data)
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_data,expected_message", [
        ({"options": {}}, "field required"),  # Missing text
        ({"text": 123}, "str type expected"),  # Wrong type
        ({"text": "test", "options": "invalid"}, "dict type expected"),  # Invalid options
    ])
    async def test_analyze_validation_errors(self, client, invalid_data, expected_message):
        """Test request validation errors."""
        response = client.post("/analyze/", json=invalid_data)
        
        assert response.status_code == 422
        error_detail = response.json()["detail"][0]["msg"]
        assert expected_message in error_detail.lower()