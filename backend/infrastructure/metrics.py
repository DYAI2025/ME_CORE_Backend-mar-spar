"""
Metrics collection infrastructure for MarkerEngine.
Provides Prometheus-compatible metrics using prometheus_client.
"""
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, 
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry
)
from prometheus_client.core import CollectorRegistry
import time
import psutil
from backend.core.logging import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Centralized metrics collector for MarkerEngine."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics collector."""
        self.registry = registry or CollectorRegistry()
        
        # Request metrics
        self.request_count = Counter(
            'markerengine_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'markerengine_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.active_requests = Gauge(
            'markerengine_active_requests',
            'Number of active requests',
            registry=self.registry
        )
        
        # Analysis metrics
        self.analysis_count = Counter(
            'markerengine_analysis_total',
            'Total number of text analyses',
            ['status'],
            registry=self.registry
        )
        
        self.analysis_duration = Histogram(
            'markerengine_analysis_duration_seconds',
            'Analysis duration in seconds',
            registry=self.registry
        )
        
        self.marker_count = Counter(
            'markerengine_markers_detected_total',
            'Total number of markers detected',
            ['marker_type'],
            registry=self.registry
        )
        
        # Service metrics
        self.service_status = Gauge(
            'markerengine_service_status',
            'Service status (1 = healthy, 0 = unhealthy)',
            ['service'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'markerengine_cache_hits_total',
            'Total number of cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'markerengine_cache_misses_total',
            'Total number of cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # System metrics
        self.memory_usage = Gauge(
            'markerengine_memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],
            registry=self.registry
        )
        
        self.cpu_usage = Gauge(
            'markerengine_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        # Error metrics
        self.error_count = Counter(
            'markerengine_errors_total',
            'Total number of errors',
            ['error_type', 'service'],
            registry=self.registry
        )
        
        # Database metrics
        self.db_operations = Counter(
            'markerengine_db_operations_total',
            'Total number of database operations',
            ['operation', 'collection'],
            registry=self.registry
        )
        
        self.db_operation_duration = Histogram(
            'markerengine_db_operation_duration_seconds',
            'Database operation duration',
            ['operation', 'collection'],
            registry=self.registry
        )
        
        # Initialize system metrics
        self._update_system_metrics()
    
    def track_request(self, method: str, endpoint: str, status: int, duration: float):
        """Track HTTP request metrics."""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def increment_active_requests(self):
        """Increment active requests counter."""
        self.active_requests.inc()
    
    def decrement_active_requests(self):
        """Decrement active requests counter."""
        self.active_requests.dec()
    
    def track_analysis(self, status: str, duration: float, marker_count_by_type: Dict[str, int]):
        """Track text analysis metrics."""
        self.analysis_count.labels(status=status).inc()
        self.analysis_duration.observe(duration)
        
        # Track markers by type
        for marker_type, count in marker_count_by_type.items():
            self.marker_count.labels(marker_type=marker_type).inc(count)
    
    def track_cache_hit(self, cache_type: str = "memory"):
        """Track cache hit."""
        self.cache_hits.labels(cache_type=cache_type).inc()
    
    def track_cache_miss(self, cache_type: str = "memory"):
        """Track cache miss."""
        self.cache_misses.labels(cache_type=cache_type).inc()
    
    def track_error(self, error_type: str, service: str):
        """Track error occurrence."""
        self.error_count.labels(
            error_type=error_type,
            service=service
        ).inc()
    
    def track_db_operation(self, operation: str, collection: str, duration: float):
        """Track database operation."""
        self.db_operations.labels(
            operation=operation,
            collection=collection
        ).inc()
        
        self.db_operation_duration.labels(
            operation=operation,
            collection=collection
        ).observe(duration)
    
    def set_service_status(self, service: str, is_healthy: bool):
        """Set service health status."""
        self.service_status.labels(service=service).set(1 if is_healthy else 0)
    
    def set_memory_usage(self, type_: str, bytes_: int):
        """Set memory usage metric."""
        self.memory_usage.labels(type=type_).set(bytes_)
    
    def _update_system_metrics(self):
        """Update system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.set_memory_usage('total', memory.total)
            self.set_memory_usage('available', memory.available)
            self.set_memory_usage('used', memory.used)
            
            # Process-specific memory
            process = psutil.Process()
            process_memory = process.memory_info()
            self.set_memory_usage('process_rss', process_memory.rss)
            self.set_memory_usage('process_vms', process_memory.vms)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def get_metrics(self) -> bytes:
        """Generate Prometheus metrics."""
        # Update system metrics before generating
        self._update_system_metrics()
        
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get Prometheus content type."""
        return CONTENT_TYPE_LATEST
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics statistics."""
        return {
            "active_requests": self.active_requests._value.get(),
            "total_requests": sum(
                sample.value 
                for sample in self.request_count.collect()[0].samples
            ),
            "total_analyses": sum(
                sample.value 
                for sample in self.analysis_count.collect()[0].samples
            ),
            "total_errors": sum(
                sample.value 
                for sample in self.error_count.collect()[0].samples
            ),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "system": {
                "cpu_percent": self.cpu_usage._value.get(),
                "memory_percent": psutil.virtual_memory().percent
            }
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        hits = sum(
            sample.value 
            for sample in self.cache_hits.collect()[0].samples
        )
        misses = sum(
            sample.value 
            for sample in self.cache_misses.collect()[0].samples
        )
        
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0


# Global metrics instance
metrics = MetricsCollector()

# Export commonly used functions
def track_request(method: str, endpoint: str, status: int, duration: float):
    """Track HTTP request metrics."""
    metrics.track_request(method, endpoint, status, duration)

def track_analysis(status: str, duration: float, marker_count_by_type: Dict[str, int]):
    """Track text analysis metrics."""
    metrics.track_analysis(status, duration, marker_count_by_type)

def track_error(error_type: str, service: str):
    """Track error occurrence."""
    metrics.track_error(error_type, service)