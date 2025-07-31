from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class AnalysisContext(BaseModel):
    """
    Context object that holds the state of an analysis throughout the processing pipeline.
    NLP services and other components enrich this context in-place.
    """
    # Input data
    text: str
    schema_id: str
    session_id: Optional[str] = None
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    language: Optional[str] = None
    
    # NLP enrichments (populated by NLP services)
    tokens: Optional[List[str]] = None
    sentences: Optional[List[str]] = None
    pos_tags: Optional[List[Dict[str, str]]] = None
    named_entities: Optional[List[Dict[str, Any]]] = None
    dependency_parse: Optional[List[Dict[str, Any]]] = None
    embeddings: Optional[List[List[float]]] = None
    
    # Analysis results
    detected_markers: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Additional context that can be added by various services
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Ich vermisse dich, aber ich brauche Abstand.",
                "schema_id": "relationship_markers",
                "session_id": "session-123",
                "language": "de",
                "tokens": ["Ich", "vermisse", "dich", ",", "aber", "ich", "brauche", "Abstand", "."],
                "sentences": ["Ich vermisse dich, aber ich brauche Abstand."],
                "detected_markers": [
                    {
                        "marker_id": "C_RELATIONAL_DESTABILIZATION_LOOP",
                        "confidence": 0.85
                    }
                ]
            }
        }