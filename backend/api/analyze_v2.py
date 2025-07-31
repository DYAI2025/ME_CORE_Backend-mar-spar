"""
Analyze API v2 with OrchestrationService for 3-phase NLP-enhanced analysis.
"""
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from services.orchestration_service import get_orchestration_service
from services.llm_bridge import llm_bridge, MarkerInterpretation
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalysisRequestV2(BaseModel):
    """Enhanced analysis request with optional parameters"""
    text: str = Field(..., max_length=4000, description="Text to analyze (max 4000 characters)")
    schema_id: Optional[str] = Field(None, description="Schema ID for filtering markers")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    enable_nlp: bool = Field(True, description="Enable NLP enrichment (phase 2)")
    enable_contextual: bool = Field(True, description="Enable contextual rescan (phase 3)")


class PhaseMetrics(BaseModel):
    """Metrics for each analysis phase"""
    markers_found: Optional[int] = Field(None, description="Markers found in this phase")
    processing_time: Optional[float] = Field(None, description="Phase processing time")
    error: Optional[str] = Field(None, description="Error if phase failed")
    enrichment: Optional[Dict[str, Any]] = Field(None, description="Additional phase data")


class AnalysisResponseV2(BaseModel):
    """Enhanced analysis response with phase breakdown"""
    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Analysis status (success/error)")
    text: str = Field(..., description="Analyzed text")
    markers: List[Dict[str, Any]] = Field(..., description="All detected markers")
    marker_count: int = Field(..., description="Total number of markers detected")
    total_score: float = Field(0.0, description="Combined score of all markers")
    
    # Phase breakdown
    phases: Dict[str, PhaseMetrics] = Field(..., description="Metrics for each phase")
    nlp_enriched: bool = Field(..., description="Whether NLP enrichment was applied")
    
    # Performance metrics
    performance_metrics: Dict[str, float] = Field(..., description="Timing for each phase")
    total_processing_time: float = Field(..., description="Total processing time")
    
    # LLM interpretation
    interpretation: Optional[str] = Field(None, description="Narrative interpretation")
    model_used: Optional[str] = Field(None, description="LLM model used")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


@router.post("/", response_model=AnalysisResponseV2)
async def analyze_text_v2(request: AnalysisRequestV2 = Body(...)):
    """
    Analyze text using 3-phase NLP-enhanced pipeline.
    
    Phases:
    1. Initial scan for atomic and signal markers
    2. NLP enrichment (if enabled)
    3. Contextual rescan for complex markers (if enabled)
    """
    start_time = time.time()
    
    try:
        # Get orchestration service
        orchestration_service = get_orchestration_service()
        
        # Run analysis through orchestration pipeline
        analysis_result = await orchestration_service.analyze(
            text=request.text,
            schema_id=request.schema_id,
            session_id=request.session_id
        )
        
        # Extract markers and calculate scores
        markers = analysis_result.get('markers', [])
        marker_count = len(markers)
        total_score = _calculate_total_score(markers)
        
        # Generate LLM interpretation if markers were found
        interpretation = None
        model_used = None
        
        if marker_count > 0:
            try:
                interpretation_data = MarkerInterpretation(
                    markers=markers,
                    schema_name=request.schema_id or "general",
                    detected_count=marker_count,
                    total_score=total_score
                )
                
                llm_response = await llm_bridge.generate_interpretation(interpretation_data)
                interpretation = llm_response.interpretation
                model_used = llm_response.model_used
                
            except Exception as e:
                logger.warning(f"LLM interpretation failed: {str(e)}")
                interpretation = _generate_fallback_interpretation(marker_count, total_score)
                model_used = "fallback"
        else:
            interpretation = "Die Analyse hat keine signifikanten Marker in Ihrem Text gefunden. Dies kann bedeuten, dass der Text keine der spezifischen Muster enthält, nach denen das Analyseschema sucht."
            model_used = "none"
        
        # Build phase metrics
        phase_data = analysis_result.get('metadata', {}).get('phases', {})
        phases = {
            "phase1_initial_scan": PhaseMetrics(
                markers_found=phase_data.get('phase1', {}).get('markers_found'),
                processing_time=analysis_result.get('performance_metrics', {}).get('phase1_initial_scan'),
                error=phase_data.get('phase1', {}).get('error')
            ),
            "phase2_nlp_enrichment": PhaseMetrics(
                enrichment=phase_data.get('phase2', {}).get('enrichment'),
                processing_time=analysis_result.get('performance_metrics', {}).get('phase2_nlp_enrichment'),
                error=phase_data.get('phase2', {}).get('error')
            ),
            "phase3_contextual_rescan": PhaseMetrics(
                markers_found=phase_data.get('phase3', {}).get('markers_added'),
                processing_time=analysis_result.get('performance_metrics', {}).get('phase3_contextual_rescan'),
                error=phase_data.get('phase3', {}).get('error')
            )
        }
        
        # Total processing time
        total_time = time.time() - start_time
        
        return AnalysisResponseV2(
            request_id=analysis_result.get('request_id', ''),
            status=analysis_result.get('status', 'success'),
            text=request.text,
            markers=markers,
            marker_count=marker_count,
            total_score=total_score,
            phases=phases,
            nlp_enriched=analysis_result.get('nlp_enriched', False),
            performance_metrics=analysis_result.get('performance_metrics', {}),
            total_processing_time=total_time,
            interpretation=interpretation,
            model_used=model_used,
            metadata=analysis_result.get('metadata', {})
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/batch", response_model=List[AnalysisResponseV2])
async def analyze_batch_v2(
    texts: List[str] = Body(..., description="List of texts to analyze"),
    schema_id: Optional[str] = Body(None, description="Schema ID for all texts"),
    session_id: Optional[str] = Body(None, description="Session ID for tracking")
):
    """
    Analyze multiple texts in batch using the orchestration pipeline.
    """
    results = []
    
    for text in texts:
        request = AnalysisRequestV2(
            text=text,
            schema_id=schema_id,
            session_id=session_id
        )
        result = await analyze_text_v2(request)
        results.append(result)
    
    return results


@router.get("/status")
async def get_analysis_status():
    """
    Get the current status of the analysis services.
    """
    orchestration_service = get_orchestration_service()
    return orchestration_service.get_service_status()


def _calculate_total_score(markers: List[Dict[str, Any]]) -> float:
    """Calculate the combined score of all markers"""
    total_score = 0.0
    
    for marker in markers:
        if 'scoring' in marker:
            base = marker['scoring'].get('base', 1.0)
            weight = marker['scoring'].get('weight', 1.0)
            confidence = marker.get('confidence', 1.0)
            total_score += base * weight * confidence
    
    return total_score


def _generate_fallback_interpretation(marker_count: int, total_score: float) -> str:
    """Generate a basic interpretation when LLM is unavailable"""
    return (
        f"Die Analyse hat {marker_count} Marker in Ihrem Text identifiziert "
        f"mit einem Gesamtscore von {total_score:.2f}. "
        "Eine detaillierte Interpretation ist momentan nicht verfügbar."
    )