from fastapi import APIRouter, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from ..services import analyze_service
from ..services.llm_bridge import llm_bridge, MarkerInterpretation

router = APIRouter()

class AnalysisRequest(BaseModel):
    text: str = Field(..., max_length=4000, description="Text to analyze (max 4000 characters)")
    schema_id: str = Field(..., description="Schema ID for analysis")

class DetectionEntry(BaseModel):
    marker: str
    count: int
    score: float


class AnalysisResponse(BaseModel):
    markers: List[Dict[str, Any]] = Field(..., description="Detected markers")
    detection: List[DetectionEntry] = Field(default_factory=list, description="Aggregated detection summary")
    interpretation: str = Field(..., description="Narrative interpretation of results")
    model_used: Optional[str] = Field(None, description="LLM model used for interpretation")
    processing_time: Optional[float] = Field(None, description="Total processing time")
    marker_count: int = Field(..., description="Number of markers detected")
    total_score: float = Field(0.0, description="Combined score of all markers")

@router.post("/", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest = Body(...)):
    """
    Analyze text for markers and provide narrative interpretation
    """
    # Run marker detection
    analysis_result = await analyze_service.run_analysis(request.text, request.schema_id)
    recognized_markers = analysis_result.get("recognized_markers", [])
    detection_summary = analysis_result.get("detection", [])
    
    # Calculate summary statistics
    marker_count = len(recognized_markers)
    total_score = 0.0
    
    for marker in recognized_markers:
        if 'scoring' in marker:
            base = marker['scoring'].get('base', 1.0)
            weight = marker['scoring'].get('weight', 1.0)
            total_score += base * weight
    
    # Generate LLM interpretation if markers were found
    if marker_count > 0:
        interpretation_data = MarkerInterpretation(
            markers=recognized_markers,
            schema_name=request.schema_id,
            detected_count=marker_count,
            total_score=total_score
        )
        
        llm_response = await llm_bridge.generate_interpretation(interpretation_data)
        
        return AnalysisResponse(
            markers=recognized_markers,
            detection=detection_summary,
            interpretation=llm_response.interpretation,
            model_used=llm_response.model_used,
            processing_time=llm_response.processing_time,
            marker_count=marker_count,
            total_score=total_score
        )
    else:
        # No markers found
        return AnalysisResponse(
            markers=[],
            detection=[],
            interpretation="Die Analyse hat keine signifikanten Marker in Ihrem Text gefunden. Dies kann bedeuten, dass der Text keine der spezifischen Muster enthält, nach denen das gewählte Analyseschema sucht.",
            model_used="none",
            marker_count=0,
            total_score=0.0
        )