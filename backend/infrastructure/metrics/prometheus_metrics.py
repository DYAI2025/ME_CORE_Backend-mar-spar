"""
Prometheus metrics collection for MarkerEngine.
Provides comprehensive performance and business metrics.
"""
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from contextlib import contextmanager
import time
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry
)
from ...core.logging import get_logger

logger = get_logger(__name__)


class PrometheusMetrics:
    """Centralized Prometheus metrics collector."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics with optional custom registry."""
        self.registry = registry or CollectorRegistry()
        
        # Request metrics
        self.requests_total = Counter(
            'markerengine_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'markerengine_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        # Analysis metrics
        self.analysis_duration = Histogram(
            'markerengine_analysis_duration_seconds',
            'Text analysis duration by phase',
            ['phase', 'schema_id'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        
        self.markers_detected = Counter(
            'markerengine_markers_detected_total',
            'Total markers detected',
            ['marker_type', 'schema_id'],
            registry=self.registry
        )
        
        self.text_length = Histogram(
            'markerengine_text_length_chars',
            'Length of analyzed text in characters',
            buckets=(100, 500, 1000, 5000, 10000, 50000),
            registry=self.registry
        )
        
        # NLP metrics
        self.nlp_operations = Counter(
            'markerengine_nlp_operations_total',
            'NLP operations performed',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.nlp_model_load_time = Gauge(
            'markerengine_nlp_model_load_seconds',
            'Time taken to load NLP models',
            ['model_type'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'markerengine_cache_hits_total',
            'Cache hit count',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'markerengine_cache_misses_total',
            'Cache miss count',
            ['cache_type'],
            registry=self.registry
        )
        
        # Database metrics
        self.db_operations = Counter(
            'markerengine_db_operations_total',
            'Database operations',
            ['operation', 'collection', 'status'],
            registry=self.registry
        )
        
        self.db_operation_duration = Histogram(
            'markerengine_db_operation_duration_seconds',
            'Database operation duration',
            ['operation', 'collection'],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
            registry=self.registry
        )
        
        # System metrics
        self.active_requests = Gauge(
            'markerengine_active_requests',
            'Number of requests currently being processed',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'markerengine_memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'markerengine_errors_total',
            'Total number of errors',
            ['error_type', 'component'],
            registry=self.registry
        )
        
        # Business metrics
        self.unique_users = Gauge(
            'markerengine_unique_users_daily',
            'Unique users in the last 24 hours',
            registry=self.registry
        )
        
        self.api_usage = Summary(
            'markerengine_api_usage',
            'API usage statistics',
            ['api_key', 'endpoint'],
            registry=self.registry
        )
        
        # Application info
        self.app_info = Info(
            'markerengine_app',
            'Application information',
            registry=self.registry
        )
        
        # Set initial app info
        self.app_info.info({
            'version': '1.0.0',
            'spark_enabled': 'true',
            'start_time': datetime.utcnow().isoformat()
        })
        
        logger.info("Prometheus metrics initialized")
    
    @contextmanager
    def measure_duration(self, metric: Histogram, labels: Dict[str, str]):
        """Context manager to measure operation duration."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            metric.labels(**labels).observe(duration)
    
    def track_request(self, method: str, endpoint: str, status: int, duration: float):
        """Track HTTP request metrics."""
        self.requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def track_analysis(self, phase: str, schema_id: str, duration: float, 
                      text_length: int, markers_found: Dict[str, int]):
        """Track text analysis metrics."""
        self.analysis_duration.labels(
            phase=phase,
            schema_id=schema_id or 'default'
        ).observe(duration)
        
        self.text_length.observe(text_length)
        
        for marker_type, count in markers_found.items():
            self.markers_detected.labels(
                marker_type=marker_type,
                schema_id=schema_id or 'default'
            ).inc(count)
    
    def track_nlp_operation(self, operation: str, success: bool = True):
        """Track NLP operation metrics."""
        status = 'success' if success else 'failure'
        self.nlp_operations.labels(
            operation=operation,
            status=status
        ).inc()
    
    def track_cache(self, cache_type: str, hit: bool):
        """Track cache hit/miss metrics."""
        if hit:
            self.cache_hits.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses.labels(cache_type=cache_type).inc()
    
    def track_db_operation(self, operation: str, collection: str, 
                          duration: float, success: bool = True):
        """Track database operation metrics."""
        status = 'success' if success else 'failure'
        self.db_operations.labels(
            operation=operation,
            collection=collection,
            status=status
        ).inc()
        
        if success:
            self.db_operation_duration.labels(
                operation=operation,
                collection=collection
            ).observe(duration)
    
    def track_error(self, error_type: str, component: str):
        """Track error occurrence."""
        self.errors_total.labels(
            error_type=error_type,
            component=component
        ).inc()
    
    def set_memory_usage(self, memory_type: str, bytes_used: int):
        """Update memory usage gauge."""
        self.memory_usage.labels(type=memory_type).set(bytes_used)
    
    def increment_active_requests(self):
        """Increment active requests counter."""
        self.active_requests.inc()
    
    def decrement_active_requests(self):
        """Decrement active requests counter."""
        self.active_requests.dec()
    
    def get_metrics(self) -> bytes:
        """Generate metrics in Prometheus format."""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get Prometheus content type."""
        return CONTENT_TYPE_LATEST


# Global metrics instance
metrics = PrometheusMetrics()


# Convenience decorators
def track_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to track function execution time."""
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            labels_dict = labels or {}
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metric_name == 'analysis':
                    metrics.analysis_duration.labels(**labels_dict).observe(duration)
                elif metric_name == 'db_operation':
                    metrics.db_operation_duration.labels(**labels_dict).observe(duration)
        
        def sync_wrapper(*args, **kwargs):
            labels_dict = labels or {}
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metric_name == 'analysis':
                    metrics.analysis_duration.labels(**labels_dict).observe(duration)
                elif metric_name == 'db_operation':
                    metrics.db_operation_duration.labels(**labels_dict).observe(duration)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator