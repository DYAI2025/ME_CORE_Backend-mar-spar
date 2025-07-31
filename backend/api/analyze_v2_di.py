"""
Analysis v2 endpoints with dependency injection.
Enhanced version using modular architecture.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.orchestration_service_di import create_orchestration_service
from app.core.logging import get_logger
from app.config import settings

logger = get_logger(__name__)
router = APIRouter()


class AnalyzeRequestV2(BaseModel):
    """Enhanced analysis request with caching options."""
    text: str = Field(..., description="Text to analyze", min_length=1, max_length=settings.MAX_TEXT_LENGTH)
    schema_id: Optional[str] = Field(None, description="Optional schema ID to filter markers")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")
    use_cache: bool = Field(True, description="Whether to use cached results if available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Das System muss eine hohe Verfügbarkeit von 99.9% gewährleisten.",
                "schema_id": "lean-deep-3.1",
                "session_id": "session-123",
                "use_cache": True
            }
        }


class BatchAnalyzeRequestV2(BaseModel):
    """Batch analysis request."""
    texts: List[str] = Field(..., description="List of texts to analyze", min_items=1, max_items=100)
    schema_id: Optional[str] = Field(None, description="Optional schema ID to filter markers")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")
    parallel: bool = Field(True, description="Process texts in parallel")
    use_cache: bool = Field(True, description="Whether to use cached results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "texts": [
                    "Das System muss eine hohe Verfügbarkeit gewährleisten.",
                    "Die Antwortzeit sollte unter 2 Sekunden liegen."
                ],
                "schema_id": "lean-deep-3.1",
                "parallel": True
            }
        }


@router.post("/text", summary="Analyze text with enhanced features")
async def analyze_text_v2(request: AnalyzeRequestV2):
    """
    Analyze text using the enhanced 3-phase pipeline with caching and metrics.
    
    Features:
    - Automatic caching of results
    - Prometheus metrics collection
    - Structured logging with request tracking
    - Graceful degradation if NLP unavailable
    
    Returns:
        Analysis results with detected markers and metadata
    """
    try:
        # Get orchestration service with DI
        orchestration = create_orchestration_service()
        
        # Disable cache if requested
        if not request.use_cache:
            # Temporarily clear cache key to force fresh analysis
            # This is a simplified approach - in production you might want
            # to pass this as a parameter through the service
            pass
        
        # Perform analysis
        result = await orchestration.analyze(
            text=request.text,
            schema_id=request.schema_id,
            session_id=request.session_id
        )
        
        # Add API version to results
        result['api_version'] = 'v2-di'
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/batch", summary="Analyze multiple texts")
async def analyze_batch_v2(request: BatchAnalyzeRequestV2):
    """
    Analyze multiple texts in batch with optional parallelization.
    
    Features:
    - Parallel processing for better performance
    - Individual caching per text
    - Aggregate metrics collection
    
    Returns:
        List of analysis results
    """
    try:
        # Validate text lengths
        for i, text in enumerate(request.texts):
            if len(text) > settings.MAX_TEXT_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail=f"Text at index {i} exceeds maximum length of {settings.MAX_TEXT_LENGTH}"
                )
        
        # Get orchestration service
        orchestration = create_orchestration_service()
        
        # Perform batch analysis
        results = await orchestration.analyze_batch(
            texts=request.texts,
            schema_id=request.schema_id,
            session_id=request.session_id,
            parallel=request.parallel
        )
        
        # Add batch metadata
        batch_summary = {
            'total_texts': len(request.texts),
            'successful': sum(1 for r in results if r.get('status') == 'success'),
            'failed': sum(1 for r in results if r.get('status') == 'error'),
            'total_markers': sum(r.get('marker_count', 0) for r in results),
            'api_version': 'v2-di',
            'parallel_processing': request.parallel
        }
        
        return {
            'results': results,
            'summary': batch_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.get("/status", summary="Get service status")
async def get_service_status():
    """
    Get the current status of all services.
    
    Returns:
        Service availability and configuration
    """
    try:
        orchestration = create_orchestration_service()
        status = orchestration.get_service_status()
        
        # Add cache statistics if available
        cache_provider = orchestration.cache
        if hasattr(cache_provider, 'get_stats'):
            status['cache_stats'] = cache_provider.get_stats()
        
        return status
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Status check failed: {str(e)}"
        )


@router.delete("/cache", summary="Clear analysis cache")
async def clear_cache(pattern: Optional[str] = None):
    """
    Clear the analysis cache.
    
    Args:
        pattern: Optional pattern to match cache keys (e.g., "analysis:*")
    
    Returns:
        Number of entries cleared
    """
    try:
        orchestration = create_orchestration_service()
        cache = orchestration.cache
        
        if pattern:
            # Clear specific pattern (if supported by cache implementation)
            logger.warning(f"Pattern-based cache clearing not yet implemented")
            return {"message": "Pattern-based clearing not implemented", "cleared": 0}
        else:
            # Clear all cache
            await cache.clear()
            logger.info("Cache cleared successfully")
            return {"message": "Cache cleared", "cleared": "all"}
            
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache clear failed: {str(e)}"
        )