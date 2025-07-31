"""
Mock Marker Service for testing without MongoDB.
Provides in-memory marker storage and basic functionality.
"""
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from backend.core.logging import get_logger

logger = get_logger(__name__)


class MockMarkerService:
    """Mock implementation of marker service for testing."""
    
    def __init__(self):
        """Initialize with sample markers."""
        self.markers = self._load_default_markers()
        logger.info("MockMarkerService initialized with sample markers")
    
    def _load_default_markers(self) -> Dict[str, Any]:
        """Load default sample markers."""
        return {
            "marker_1": {
                "_id": "marker_1",
                "name": "IF",
                "pattern": r"\bIF\b",
                "description": "Conditional statement marker",
                "marker_type": "condition",
                "examples": ["IF condition THEN action"],
                "created_at": datetime.utcnow().isoformat()
            },
            "marker_2": {
                "_id": "marker_2",
                "name": "THEN",
                "pattern": r"\bTHEN\b",
                "description": "Action marker following condition",
                "marker_type": "action",
                "examples": ["IF condition THEN action"],
                "created_at": datetime.utcnow().isoformat()
            },
            "marker_3": {
                "_id": "marker_3",
                "name": "WITH",
                "pattern": r"\bWITH\b",
                "description": "Context or parameter marker",
                "marker_type": "context",
                "examples": ["EXECUTE action WITH parameters"],
                "created_at": datetime.utcnow().isoformat()
            },
            "marker_4": {
                "_id": "marker_4",
                "name": "FOR",
                "pattern": r"\bFOR\b",
                "description": "Loop or iteration marker",
                "marker_type": "control",
                "examples": ["FOR each item IN list"],
                "created_at": datetime.utcnow().isoformat()
            },
            "marker_5": {
                "_id": "marker_5",
                "name": "AND",
                "pattern": r"\bAND\b",
                "description": "Logical conjunction marker",
                "marker_type": "logical",
                "examples": ["condition1 AND condition2"],
                "created_at": datetime.utcnow().isoformat()
            }
        }
    
    async def get_all_markers(self) -> List[Dict[str, Any]]:
        """Get all markers."""
        return list(self.markers.values())
    
    async def get_marker_by_id(self, marker_id: str) -> Optional[Dict[str, Any]]:
        """Get marker by ID."""
        return self.markers.get(marker_id)
    
    async def get_markers_by_type(self, marker_type: str) -> List[Dict[str, Any]]:
        """Get markers by type."""
        return [
            marker for marker in self.markers.values()
            if marker.get("marker_type") == marker_type
        ]
    
    async def search_markers(self, query: str) -> List[Dict[str, Any]]:
        """Search markers by name or description."""
        query_lower = query.lower()
        return [
            marker for marker in self.markers.values()
            if query_lower in marker.get("name", "").lower() or
               query_lower in marker.get("description", "").lower()
        ]
    
    async def analyze_text(self, text: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock text analysis."""
        import re
        
        found_markers = []
        text_upper = text.upper()
        
        # Simple pattern matching for demo
        for marker in self.markers.values():
            pattern = marker.get("pattern", "")
            if pattern:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    found_markers.append({
                        "marker": marker["name"],
                        "type": marker["marker_type"],
                        "start": match.start(),
                        "end": match.end(),
                        "context": text[max(0, match.start()-20):min(len(text), match.end()+20)]
                    })
        
        # Sort by position
        found_markers.sort(key=lambda x: x["start"])
        
        # Create summary
        marker_types = {}
        for fm in found_markers:
            mt = fm["type"]
            marker_types[mt] = marker_types.get(mt, 0) + 1
        
        return {
            "markers": found_markers,
            "summary": {
                "total_markers": len(found_markers),
                "markers_by_type": marker_types,
                "text_length": len(text)
            },
            "metadata": {
                "processing_time": 0.05,  # Mock processing time
                "engine": "mock",
                "options": options or {}
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "status": "healthy",
            "mode": "mock",
            "markers_loaded": len(self.markers),
            "message": "Running in mock mode - no MongoDB connection"
        }


# Global instance
mock_marker_service = MockMarkerService()