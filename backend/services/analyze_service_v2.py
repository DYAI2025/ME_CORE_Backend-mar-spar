"""
Updated analyze service that uses the NLP service abstraction.
This is an example of how to integrate NLP processing into the analysis pipeline.
"""
import os
import importlib.util
import logging
from typing import List, Dict, Any
from ..database import db
from ..config import settings
from ..models.analysis_context import AnalysisContext
from .nlp_service import get_nlp_service

logger = logging.getLogger(__name__)
detector_collection = db["detectors"]


async def run_analysis_with_nlp(text: str, schema_id: str, session_id: str = None) -> Dict[str, Any]:
    """
    Run analysis with NLP enrichment.
    
    Args:
        text: The text to analyze
        schema_id: The schema ID for filtering detectors
        session_id: Optional session ID for tracking
        
    Returns:
        Dict containing the analysis results and enriched context
    """
    # Create analysis context
    context = AnalysisContext(
        text=text,
        schema_id=schema_id,
        session_id=session_id
    )
    
    # Get NLP service and enrich context
    nlp_service = get_nlp_service()
    nlp_service.enrich(context)
    
    logger.info(f"Enriched context with {len(context.tokens or [])} tokens using {context.metadata.get('nlp_service', 'unknown')} service")
    
    # Run detector analysis
    recognized_markers = []
    detectors = await detector_collection.find().to_list(length=None)
    
    for detector in detectors:
        file_path = os.path.join(settings.DETECTOR_PATH, detector.get("file_path", ""))
        module_name = detector.get("id")
        
        if not os.path.exists(file_path):
            logger.warning(f"Detector file not found: {file_path}")
            continue
        
        try:
            # Dynamically load the detector module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            detector_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(detector_module)
            
            # Check if detector has enhanced NLP-aware detect function
            if hasattr(detector_module, "detect_with_context"):
                # Use NLP-enriched detection if available
                result = detector_module.detect_with_context(context)
                if result:
                    recognized_markers.append({
                        "detector_id": detector["_id"],
                        "fired_marker": detector.get("fires_marker"),
                        "confidence": result.get("confidence", 1.0),
                        "details": result.get("details", {})
                    })
            elif hasattr(detector_module, "detect"):
                # Fall back to simple text-based detection
                result = detector_module.detect(text)
                if result:
                    recognized_markers.append({
                        "detector_id": detector["_id"],
                        "fired_marker": detector.get("fires_marker")
                    })
                    
        except Exception as e:
            logger.error(f"Error executing detector {module_name}: {e}")
    
    # Update context with results
    context.detected_markers = recognized_markers
    
    # Return comprehensive results
    return {
        "recognized_markers": recognized_markers,
        "nlp_metadata": {
            "service": context.metadata.get("nlp_service"),
            "version": context.metadata.get("nlp_version"),
            "token_count": len(context.tokens) if context.tokens else 0,
            "sentence_count": len(context.sentences) if context.sentences else 0
        },
        "context": context.dict(exclude_none=True)
    }


async def analyze_batch_with_nlp(texts: List[str], schema_id: str) -> List[Dict[str, Any]]:
    """
    Analyze multiple texts in batch with NLP enrichment.
    
    Args:
        texts: List of texts to analyze
        schema_id: The schema ID for filtering detectors
        
    Returns:
        List of analysis results
    """
    results = []
    
    # Get NLP service once for batch processing
    nlp_service = get_nlp_service()
    
    for text in texts:
        context = AnalysisContext(text=text, schema_id=schema_id)
        nlp_service.enrich(context)
        
        # Run detection on enriched context
        result = await run_analysis_with_nlp(text, schema_id)
        results.append(result)
    
    return results