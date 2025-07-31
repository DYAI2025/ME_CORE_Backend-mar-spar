"""
Shared type definitions for ME_CORE Backend
These types are synchronized with frontend TypeScript interfaces
"""
from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MarkerType(str, Enum):
    """Marker type enumeration"""
    ATOMIC = "A"
    SIGNAL = "S"
    COMPOSED = "C"
    META = "MM"


class ActivationType(str, Enum):
    """Activation rule types"""
    ALL = "ALL"
    ANY = "ANY"
    ANY_N = "ANY_N"
    TEMPORAL = "TEMPORAL"
    SENTIMENT = "SENTIMENT"
    PROXIMITY = "PROXIMITY"
    NEGATION = "NEGATION"
    PATTERN = "PATTERN"
    COMPOSITE = "COMPOSITE"


class DetectionPhase(str, Enum):
    """Detection phase enumeration"""
    INITIAL = "initial"
    CONTEXTUAL = "contextual"


class RequestStatus(str, Enum):
    """Request status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class BaseRequest(BaseModel):
    """Base request model with common fields"""
    session_id: Optional[str] = None
    request_id: Optional[str] = Field(default_factory=lambda: None)
    
    class Config:
        use_enum_values = True


class BaseResponse(BaseModel):
    """Base response model with common fields"""
    request_id: str
    status: RequestStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class AnalyzeRequest(BaseRequest):
    """Text analysis request"""
    text: str = Field(..., min_length=1, max_length=100000)
    schema_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class SchemaRequest(BaseRequest):
    """Schema management request"""
    schema_id: Optional[str] = None
    name: Optional[str] = None
    version: Optional[str] = None
    content: Optional[Dict[str, Any]] = None


class MarkerDefinition(BaseModel):
    """Shared marker definition"""
    id: str = Field(..., alias="_id")
    type: MarkerType
    frame: Dict[str, str]
    pattern: Optional[str] = None
    composed_of: Optional[List[str]] = None
    detect_class: Optional[str] = None
    activation: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class DetectedMarker(BaseModel):
    """Detected marker result"""
    marker_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    detection_phase: DetectionPhase
    position: Optional[Dict[str, int]] = None
    components: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class AnalysisResult(BaseResponse):
    """Complete analysis result"""
    text: str
    markers: List[DetectedMarker]
    marker_count: int
    nlp_enriched: bool
    processing_time_ms: Optional[float] = None
    metadata: Dict[str, Any]


class SchemaInfo(BaseModel):
    """Schema information"""
    id: str
    name: str
    version: str
    created_at: datetime
    updated_at: datetime
    marker_count: int
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None


class HealthCheck(BaseModel):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    version: str
    checks: Dict[str, Dict[str, Any]]
    metrics: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseResponse):
    """Error response model"""
    status: Literal["error"] = "error"
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# Marker score calculation types
class ScoringProfile(BaseModel):
    """Scoring profile configuration"""
    name: str
    weights: Dict[MarkerType, float]
    thresholds: Dict[str, float]
    normalization: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class MarkerScore(BaseModel):
    """Individual marker score"""
    marker_id: str
    raw_score: float
    weighted_score: float
    weight: float
    confidence: float


class AggregateScore(BaseModel):
    """Aggregate scoring result"""
    total_score: float = Field(..., ge=0.0, le=1.0)
    marker_scores: List[MarkerScore]
    profile_used: str
    marker_count: int
    calculation_time_ms: float


# Batch processing types
class BatchAnalyzeRequest(BaseRequest):
    """Batch analysis request"""
    texts: List[str] = Field(..., min_items=1, max_items=100)
    schema_id: Optional[str] = None
    parallel: bool = True
    options: Optional[Dict[str, Any]] = None


class BatchAnalyzeResponse(BaseResponse):
    """Batch analysis response"""
    results: List[AnalysisResult]
    total_count: int
    successful_count: int
    failed_count: int
    processing_time_ms: float
    errors: Optional[List[Dict[str, Any]]] = None