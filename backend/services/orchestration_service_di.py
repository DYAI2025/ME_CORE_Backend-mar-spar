"""
OrchestrationService with Dependency Injection
Enhanced version using the modular architecture components.
"""
import time
from typing import Dict, Any, Optional, List
from ..models.analysis_context import AnalysisContext
from ..services.marker_service import MarkerService
from ..core.interfaces import ICacheProvider, IMetricsCollector
from ..core.logging import get_logger, MarkerEngineLogger
from ..core.container import get_service
from ..config import settings

logger = get_logger(__name__)


class OrchestrationServiceDI:
    """
    Orchestration service with dependency injection support.
    Manages the 3-phase analysis pipeline with caching and metrics.
    """
    
    def __init__(
        self,
        marker_service: Optional[MarkerService] = None,
        cache_provider: Optional[ICacheProvider] = None,
        metrics_collector: Optional[IMetricsCollector] = None
    ):
        """Initialize with injected dependencies."""
        # Use injected services or get from container
        self.marker_service = marker_service or MarkerService()
        self.cache = cache_provider or get_service(ICacheProvider)
        self.metrics = metrics_collector or get_service(IMetricsCollector)
        
        # Get NLP service
        from ..services.nlp_service import get_nlp_service
        self.nlp_service = get_nlp_service()
        
        self._phase_timings = {}
        self.logger_config = MarkerEngineLogger()
        
    async def analyze(
        self, 
        text: str, 
        schema_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete 3-phase analysis pipeline with caching.
        """
        start_time = time.time()
        request_id = AnalysisContext.generate_request_id()
        
        # Check cache first
        cache_key = self._generate_cache_key(text, schema_id)
        cached_result = await self._check_cache(cache_key)
        if cached_result:
            self.metrics.track_cache('analysis', hit=True)
            return cached_result
        
        self.metrics.track_cache('analysis', hit=False)
        self.metrics.increment_active_requests()
        
        # Initialize analysis context
        context = AnalysisContext(
            text=text,
            schema_id=schema_id,
            session_id=session_id,
            request_id=request_id
        )
        
        try:
            # Log request start
            self.logger_config.log_request(
                logger,
                request_id=request_id,
                message="Starting analysis",
                text_length=len(text)
            )
            
            # Track text length
            self.metrics.text_length.observe(len(text))
            
            # Phase 1: Initial marker scan
            await self._phase1_initial_scan(context)
            
            # Phase 2: NLP enrichment
            self._phase2_nlp_enrichment(context)
            
            # Phase 3: Contextual rescan
            await self._phase3_contextual_rescan(context)
            
            # Prepare final results
            results = self._prepare_results(context)
            
            # Cache results
            await self._cache_results(cache_key, results)
            
            # Track success metrics
            self._track_success_metrics(context, results)
            
        except Exception as e:
            logger.error(f"Orchestration error: {str(e)}", exc_info=True)
            self.metrics.track_error(type(e).__name__, 'orchestration')
            results = self._prepare_error_results(context, str(e))
        
        finally:
            # Record total timing
            total_time = time.time() - start_time
            self._phase_timings['total'] = total_time
            results['performance_metrics'] = self._phase_timings.copy()
            
            # Log performance
            self.logger_config.log_performance(
                logger,
                phase='total',
                duration_ms=total_time * 1000,
                request_id=request_id
            )
            
            self.metrics.decrement_active_requests()
            
        return results
    
    async def _phase1_initial_scan(self, context: AnalysisContext) -> None:
        """Phase 1: Initial marker detection with metrics."""
        phase_start = time.time()
        
        with self.metrics.measure_duration(
            self.metrics.analysis_duration,
            {'phase': 'initial_scan', 'schema_id': context.schema_id or 'default'}
        ):
            try:
                # Run initial scan
                initial_markers = await self.marker_service.initial_scan(
                    text=context.text,
                    schema_id=context.schema_id
                )
                
                # Store results in context
                context.detected_markers = initial_markers
                context.metadata['phase1_marker_count'] = len(initial_markers)
                
                logger.info(
                    f"Phase 1: Found {len(initial_markers)} initial markers",
                    extra={'request_id': context.request_id}
                )
                
            except Exception as e:
                logger.error(
                    f"Phase 1 error: {str(e)}",
                    extra={'request_id': context.request_id}
                )
                context.metadata['phase1_error'] = str(e)
                context.detected_markers = []
                self.metrics.track_error(type(e).__name__, 'phase1')
            
            finally:
                duration = time.time() - phase_start
                self._phase_timings['phase1_initial_scan'] = duration
                self.logger_config.log_performance(
                    logger,
                    phase='phase1_initial_scan',
                    duration_ms=duration * 1000,
                    request_id=context.request_id
                )
    
    def _phase2_nlp_enrichment(self, context: AnalysisContext) -> None:
        """Phase 2: NLP enrichment with metrics."""
        phase_start = time.time()
        
        with self.metrics.measure_duration(
            self.metrics.analysis_duration,
            {'phase': 'nlp_enrichment', 'schema_id': context.schema_id or 'default'}
        ):
            try:
                # Check if NLP service is available
                if not self.nlp_service.is_available():
                    logger.warning("NLP service not available, skipping enrichment")
                    context.metadata['nlp_skipped'] = True
                    self.metrics.track_nlp_operation('enrichment', success=False)
                    return
                
                # Enrich context with NLP data
                self.nlp_service.enrich(context)
                self.metrics.track_nlp_operation('enrichment', success=True)
                
                # Log enrichment details
                enrichment_summary = {
                    'tokens': len(context.tokens) if context.tokens else 0,
                    'sentences': len(context.sentences) if context.sentences else 0,
                    'entities': len(context.named_entities) if context.named_entities else 0,
                    'nlp_service': context.metadata.get('nlp_service', 'unknown')
                }
                
                context.metadata['phase2_enrichment'] = enrichment_summary
                logger.info(
                    f"Phase 2: Enrichment complete",
                    extra={
                        'request_id': context.request_id,
                        **enrichment_summary
                    }
                )
                
            except Exception as e:
                logger.error(
                    f"Phase 2 error: {str(e)}",
                    extra={'request_id': context.request_id}
                )
                context.metadata['phase2_error'] = str(e)
                self.metrics.track_error(type(e).__name__, 'phase2')
                self.metrics.track_nlp_operation('enrichment', success=False)
            
            finally:
                duration = time.time() - phase_start
                self._phase_timings['phase2_nlp_enrichment'] = duration
                self.logger_config.log_performance(
                    logger,
                    phase='phase2_nlp_enrichment',
                    duration_ms=duration * 1000,
                    request_id=context.request_id
                )
    
    async def _phase3_contextual_rescan(self, context: AnalysisContext) -> None:
        """Phase 3: Contextual rescan with metrics."""
        phase_start = time.time()
        
        with self.metrics.measure_duration(
            self.metrics.analysis_duration,
            {'phase': 'contextual_rescan', 'schema_id': context.schema_id or 'default'}
        ):
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
                logger.info(
                    f"Phase 3: Added {final_count - initial_count} contextual markers",
                    extra={'request_id': context.request_id}
                )
                
            except Exception as e:
                logger.error(
                    f"Phase 3 error: {str(e)}",
                    extra={'request_id': context.request_id}
                )
                context.metadata['phase3_error'] = str(e)
                self.metrics.track_error(type(e).__name__, 'phase3')
            
            finally:
                duration = time.time() - phase_start
                self._phase_timings['phase3_contextual_rescan'] = duration
                self.logger_config.log_performance(
                    logger,
                    phase='phase3_contextual_rescan',
                    duration_ms=duration * 1000,
                    request_id=context.request_id
                )
    
    def _merge_markers(self, context: AnalysisContext, new_markers: List[Dict[str, Any]]) -> None:
        """Merge newly detected markers with existing ones."""
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
        """Prepare the final analysis results from the context."""
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
        """Prepare error results when orchestration fails."""
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
    
    def _generate_cache_key(self, text: str, schema_id: Optional[str]) -> str:
        """Generate cache key for analysis results."""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        schema_part = schema_id or 'default'
        return f"analysis:{schema_part}:{text_hash}"
    
    async def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check cache for existing results."""
        try:
            cached = await self.cache.get(cache_key)
            if cached:
                # Add cache hit indicator
                cached['from_cache'] = True
                return cached
        except Exception as e:
            logger.warning(f"Cache check error: {e}")
        return None
    
    async def _cache_results(self, cache_key: str, results: Dict[str, Any]) -> None:
        """Cache analysis results."""
        try:
            # Don't cache errors
            if results.get('status') == 'error':
                return
            
            # Cache with TTL
            await self.cache.set(
                cache_key,
                results,
                ttl=settings.CACHE_DEFAULT_TTL
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def _track_success_metrics(self, context: AnalysisContext, results: Dict[str, Any]) -> None:
        """Track success metrics for the analysis."""
        # Track markers by type
        marker_counts = {}
        for marker in context.detected_markers:
            marker_type = marker.get('marker_id', 'unknown').split('_')[0]
            marker_counts[marker_type] = marker_counts.get(marker_type, 0) + 1
        
        for marker_type, count in marker_counts.items():
            self.metrics.track_analysis(
                phase='complete',
                schema_id=context.schema_id or 'default',
                duration=self._phase_timings.get('total', 0),
                text_length=len(context.text),
                markers_found={marker_type: count}
            )
    
    async def analyze_batch(
        self, 
        texts: List[str], 
        schema_id: Optional[str] = None,
        session_id: Optional[str] = None,
        parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple texts in batch with optional parallelization.
        """
        if parallel and len(texts) > 1:
            import asyncio
            tasks = [
                self.analyze(text, schema_id, session_id)
                for text in texts
            ]
            results = await asyncio.gather(*tasks)
        else:
            results = []
            for text in texts:
                result = await self.analyze(text, schema_id, session_id)
                results.append(result)
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get the current status of orchestration services."""
        cache_info = {}
        try:
            cache_info = {
                'type': type(self.cache).__name__,
                'available': True
            }
        except:
            cache_info = {'available': False}
        
        return {
            'orchestration_service': 'active',
            'marker_service': 'active' if self.marker_service else 'unavailable',
            'nlp_service': {
                'type': self.nlp_service.__class__.__name__,
                'available': self.nlp_service.is_available(),
                'spark_nlp_enabled': settings.SPARK_NLP_ENABLED
            },
            'cache_service': cache_info,
            'metrics_service': {
                'type': type(self.metrics).__name__,
                'available': True,
                'enabled': settings.ENABLE_METRICS
            },
            'phases_enabled': {
                'phase1_initial_scan': True,
                'phase2_nlp_enrichment': self.nlp_service.is_available(),
                'phase3_contextual_rescan': self.nlp_service.is_available()
            }
        }


# Factory function
def create_orchestration_service() -> OrchestrationServiceDI:
    """Create orchestration service with dependencies from container."""
    from ..core.container import get_container
    
    container = get_container()
    return OrchestrationServiceDI(
        cache_provider=container.get(ICacheProvider),
        metrics_collector=container.get(IMetricsCollector)
    )