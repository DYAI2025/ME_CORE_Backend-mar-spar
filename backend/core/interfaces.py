"""
Core interfaces for MarkerEngine services.
Defines contracts for modular components.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models.analysis_context import AnalysisContext
from ..models.marker import Marker


class IMarkerRepository(ABC):
    """Interface for marker data access."""
    
    @abstractmethod
    async def get_marker(self, marker_id: str) -> Optional[Marker]:
        """Get a single marker by ID."""
        pass
    
    @abstractmethod
    async def list_markers(self, 
                          skip: int = 0, 
                          limit: int = 100,
                          schema_id: Optional[str] = None) -> List[Marker]:
        """List markers with pagination and filtering."""
        pass
    
    @abstractmethod
    async def create_marker(self, marker: Marker) -> Marker:
        """Create a new marker."""
        pass
    
    @abstractmethod
    async def update_marker(self, marker_id: str, marker: Marker) -> Optional[Marker]:
        """Update an existing marker."""
        pass
    
    @abstractmethod
    async def delete_marker(self, marker_id: str) -> bool:
        """Delete a marker."""
        pass
    
    @abstractmethod
    async def get_markers_by_type(self, marker_type: str) -> List[Marker]:
        """Get all markers of a specific type (A_, S_, C_, MM_)."""
        pass


class IDetectionStrategy(ABC):
    """Interface for marker detection strategies."""
    
    @abstractmethod
    async def detect(self, text: str, marker: Marker) -> Optional[Dict[str, Any]]:
        """
        Detect if a marker is present in text.
        
        Returns:
            Detection result with confidence and details, or None
        """
        pass


class IActivationRule(ABC):
    """Interface for activation rules."""
    
    @abstractmethod
    def check_activation(self, 
                        marker: Marker,
                        context: AnalysisContext,
                        detected_markers: set) -> Dict[str, Any]:
        """
        Check if a marker should be activated.
        
        Returns:
            Dict with activated status, confidence, and details
        """
        pass


class INlpProcessor(ABC):
    """Interface for NLP processing."""
    
    @abstractmethod
    def enrich(self, context: AnalysisContext) -> None:
        """Enrich context with NLP annotations."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if NLP processor is available."""
        pass


class IAnalysisPhase(ABC):
    """Interface for analysis pipeline phases."""
    
    @abstractmethod
    async def execute(self, context: AnalysisContext) -> None:
        """
        Execute analysis phase.
        Modifies context in-place.
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get phase name for logging."""
        pass


class ICacheProvider(ABC):
    """Interface for caching providers."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass


class IMetricsCollector(ABC):
    """Interface for metrics collection."""
    
    @abstractmethod
    def record_request(self, 
                      endpoint: str,
                      method: str,
                      status_code: int,
                      duration_ms: float) -> None:
        """Record API request metrics."""
        pass
    
    @abstractmethod
    def record_phase_duration(self,
                            phase: str,
                            duration_ms: float) -> None:
        """Record analysis phase duration."""
        pass
    
    @abstractmethod
    def record_markers_detected(self,
                              count: int,
                              marker_type: str) -> None:
        """Record markers detected."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        pass


class INotificationService(ABC):
    """Interface for notification services."""
    
    @abstractmethod
    async def notify_analysis_complete(self,
                                     request_id: str,
                                     results: Dict[str, Any]) -> None:
        """Notify when analysis is complete."""
        pass
    
    @abstractmethod
    async def notify_error(self,
                          request_id: str,
                          error: Exception) -> None:
        """Notify when an error occurs."""
        pass