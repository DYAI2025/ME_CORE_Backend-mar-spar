"""
OrchestrationService for MarkerEngine v1.0
Manages the 3-phase analysis process with NLP enrichment.

Phase 1: Initial marker scan (basic pattern matching)
Phase 2: NLP enrichment (tokenization, POS, NER, etc.)
Phase 3: Contextual rescan (using NLP data for complex rules)
"""
import logging
import time
from typing import Dict, Any, Optional, List
from ..models.analysis_context import AnalysisContext
from ..services.marker_service import MarkerService
from ..services.nlp_service import get_nlp_service
from ..config import settings

logger = logging.getLogger(__name__)


class OrchestrationService:
    """
    Orchestrates the multi-phase analysis pipeline for marker detection.
    Coordinates between MarkerService and NlpService to enable
    sophisticated semantic reasoning.
    """
    
    def __init__(self):
        """Initialize the orchestration service with required dependencies."""
        self.marker_service = MarkerService()
        self.nlp_service = get_nlp_service()
        self._phase_timings = {}
        
    async def analyze(
        self, 
        text: str, 
        schema_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete 3-phase analysis pipeline.
        
        Args:
            text: The text to analyze
            schema_id: Optional schema filter for markers
            session_id: Optional session ID for tracking
            
        Returns:
            Dict containing analysis results and metadata
        """
        start_time = time.time()
        
        # Initialize analysis context
        context = AnalysisContext(
            text=text,
            schema_id=schema_id,
            session_id=session_id
        )
        
        try:
            # Phase 1: Initial marker scan
            await self._phase1_initial_scan(context)
            
            # Phase 2: NLP enrichment
            self._phase2_nlp_enrichment(context)
            
            # Phase 3: Contextual rescan
            await self._phase3_contextual_rescan(context)
            
            # Prepare final results
            results = self._prepare_results(context)
            
        except Exception as e:
            logger.error(f"Orchestration error: {str(e)}", exc_info=True)
            results = self._prepare_error_results(context, str(e))
        
        finally:
            # Record total timing
            self._phase_timings['total'] = time.time() - start_time
            results['performance_metrics'] = self._phase_timings.copy()
            
        return results
    
    async def _phase1_initial_scan(self, context: AnalysisContext) -> None:
        """
        Phase 1: Run initial marker detection using basic patterns.
        This phase finds candidates using simple pattern matching.
        """
        phase_start = time.time()
        logger.info(f"Phase 1: Initial scan starting for request {context.request_id}")
        
        try:
            # Run initial scan
            initial_markers = await self.marker_service.initial_scan(
                text=context.text,
                schema_id=context.schema_id
            )
            
            # Store results in context
            context.detected_markers = initial_markers
            context.metadata['phase1_marker_count'] = len(initial_markers)
            
            logger.info(f"Phase 1: Found {len(initial_markers)} initial markers")
            
        except Exception as e:
            logger.error(f"Phase 1 error: {str(e)}")
            context.metadata['phase1_error'] = str(e)
            # Continue with empty markers list
            context.detected_markers = []
        
        finally:
            self._phase_timings['phase1_initial_scan'] = time.time() - phase_start
    
    def _phase2_nlp_enrichment(self, context: AnalysisContext) -> None:
        """
        Phase 2: Enrich context with NLP annotations.
        This phase adds linguistic features for sophisticated detection.
        """
        phase_start = time.time()
        logger.info(f"Phase 2: NLP enrichment starting for request {context.request_id}")
        
        try:
            # Check if NLP service is available
            if not self.nlp_service.is_available():
                logger.warning("NLP service not available, skipping enrichment")
                context.metadata['nlp_skipped'] = True
                return
            
            # Enrich context with NLP data
            self.nlp_service.enrich(context)
            
            # Log enrichment details
            enrichment_summary = {
                'tokens': len(context.tokens) if context.tokens else 0,
                'sentences': len(context.sentences) if context.sentences else 0,
                'nlp_service': context.metadata.get('nlp_service', 'unknown')
            }
            
            context.metadata['phase2_enrichment'] = enrichment_summary
            logger.info(f"Phase 2: Enrichment complete - {enrichment_summary}")
            
        except Exception as e:
            logger.error(f"Phase 2 error: {str(e)}")
            context.metadata['phase2_error'] = str(e)
            # Continue without NLP enrichment
        
        finally:
            self._phase_timings['phase2_nlp_enrichment'] = time.time() - phase_start
    
    async def _phase3_contextual_rescan(self, context: AnalysisContext) -> None:
        """
        Phase 3: Re-scan with NLP context for complex patterns.
        This phase can find new markers and adjust confidence scores.
        """
        phase_start = time.time()
        logger.info(f"Phase 3: Contextual rescan starting for request {context.request_id}")
        
        try:
            # Skip if no NLP enrichment was done
            if context.metadata.get('nlp_skipped'):
                logger.info("Phase 3: Skipping contextual rescan (no NLP data)")
                return
            
            # Run contextual rescan
            contextual_markers = await self.marker_service.contextual_rescan(context)
            
            # Merge results
            initial_count = len(context.detected_markers)
            self._merge_markers(context, contextual_markers)
            final_count = len(context.detected_markers)
            
            context.metadata['phase3_markers_added'] = final_count - initial_count
            logger.info(f"Phase 3: Added {final_count - initial_count} contextual markers")
            
        except Exception as e:
            logger.error(f"Phase 3 error: {str(e)}")
            context.metadata['phase3_error'] = str(e)
            # Keep existing markers
        
        finally:
            self._phase_timings['phase3_contextual_rescan'] = time.time() - phase_start
    
    def _merge_markers(self, context: AnalysisContext, new_markers: List[Dict[str, Any]]) -> None:
        """
        Merge newly detected markers with existing ones.
        Handles duplicates and updates confidence scores.
        """
        existing_ids = {m.get('marker_id') for m in context.detected_markers}
        
        for marker in new_markers:
            marker_id = marker.get('marker_id')
            
            if marker_id not in existing_ids:
                # New marker found
                marker['detection_phase'] = 'contextual'
                context.detected_markers.append(marker)
            else:
                # Update existing marker with higher confidence if applicable
                for existing in context.detected_markers:
                    if existing.get('marker_id') == marker_id:
                        old_confidence = existing.get('confidence', 0.5)
                        new_confidence = marker.get('confidence', 0.5)
                        
                        if new_confidence > old_confidence:
                            existing['confidence'] = new_confidence
                            existing['confidence_updated'] = True
                            existing['contextual_boost'] = new_confidence - old_confidence
    
    def _prepare_results(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Prepare the final analysis results from the context.
        """
        return {
            'request_id': context.request_id,
            'status': 'success',
            'text': context.text,
            'markers': context.detected_markers,
            'marker_count': len(context.detected_markers),
            'nlp_enriched': not context.metadata.get('nlp_skipped', False),
            'metadata': {
                'session_id': context.session_id,
                'schema_id': context.schema_id,
                'phases': {
                    'phase1': {
                        'markers_found': context.metadata.get('phase1_marker_count', 0),
                        'error': context.metadata.get('phase1_error')
                    },
                    'phase2': {
                        'enrichment': context.metadata.get('phase2_enrichment', {}),
                        'error': context.metadata.get('phase2_error')
                    },
                    'phase3': {
                        'markers_added': context.metadata.get('phase3_markers_added', 0),
                        'error': context.metadata.get('phase3_error')
                    }
                },
                'nlp_service': context.metadata.get('nlp_service', 'none')
            }
        }
    
    def _prepare_error_results(self, context: AnalysisContext, error: str) -> Dict[str, Any]:
        """
        Prepare error results when orchestration fails.
        """
        return {
            'request_id': context.request_id,
            'status': 'error',
            'error': error,
            'text': context.text,
            'markers': [],
            'marker_count': 0,
            'metadata': {
                'session_id': context.session_id,
                'schema_id': context.schema_id,
                'partial_results': len(context.detected_markers) if context.detected_markers else 0
            }
        }
    
    async def analyze_batch(
        self, 
        texts: List[str], 
        schema_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple texts in batch.
        
        Args:
            texts: List of texts to analyze
            schema_id: Optional schema filter
            session_id: Optional session ID
            
        Returns:
            List of analysis results
        """
        results = []
        
        for text in texts:
            result = await self.analyze(text, schema_id, session_id)
            results.append(result)
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the current status of orchestration services.
        
        Returns:
            Dict with service availability and configuration
        """
        return {
            'orchestration_service': 'active',
            'marker_service': 'active' if self.marker_service else 'unavailable',
            'nlp_service': {
                'type': self.nlp_service.__class__.__name__,
                'available': self.nlp_service.is_available(),
                'spark_nlp_enabled': settings.SPARK_NLP_ENABLED
            },
            'phases_enabled': {
                'phase1_initial_scan': True,
                'phase2_nlp_enrichment': self.nlp_service.is_available(),
                'phase3_contextual_rescan': self.nlp_service.is_available()
            }
        }


# Singleton instance
_orchestration_service: Optional[OrchestrationService] = None


def get_orchestration_service() -> OrchestrationService:
    """
    Get the singleton orchestration service instance.
    
    Returns:
        OrchestrationService: The service instance
    """
    global _orchestration_service
    
    if _orchestration_service is None:
        _orchestration_service = OrchestrationService()
        logger.info("OrchestrationService initialized")
    
    return _orchestration_service