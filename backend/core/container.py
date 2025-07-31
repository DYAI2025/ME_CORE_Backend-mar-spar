"""
Dependency injection container for MarkerEngine.
Manages service lifecycles and dependencies.
"""
from typing import Dict, Type, Any, Optional
from functools import lru_cache
from .interfaces import (
    IMarkerRepository,
    INlpProcessor,
    ICacheProvider,
    IMetricsCollector,
    INotificationService
)
from .logging import get_logger
from ..config import settings

logger = get_logger(__name__)


class ServiceContainer:
    """
    Dependency injection container for managing services.
    Implements singleton pattern for service instances.
    """
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
        self._initialized = False
    
    def register(self, interface: Type, factory: callable) -> None:
        """
        Register a factory function for an interface.
        
        Args:
            interface: Interface type
            factory: Factory function that creates the service
        """
        self._factories[interface] = factory
        logger.info(f"Registered factory for {interface.__name__}")
    
    def get(self, interface: Type) -> Any:
        """
        Get or create a service instance.
        
        Args:
            interface: Interface type
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If no factory is registered for the interface
        """
        if interface not in self._services:
            if interface not in self._factories:
                raise KeyError(f"No factory registered for {interface.__name__}")
            
            # Create service instance
            self._services[interface] = self._factories[interface]()
            logger.info(f"Created service instance for {interface.__name__}")
        
        return self._services[interface]
    
    def clear(self) -> None:
        """Clear all service instances."""
        self._services.clear()
        logger.info("Cleared all service instances")
    
    def initialize(self) -> None:
        """Initialize all required services."""
        if self._initialized:
            return
        
        logger.info("Initializing service container...")
        
        # Register default services
        self._register_default_services()
        
        self._initialized = True
        logger.info("Service container initialized")
    
    def _register_default_services(self) -> None:
        """Register default service implementations."""
        
        # Repository
        def create_marker_repository():
            from ..repositories.marker_repository import MongoMarkerRepository
            return MongoMarkerRepository()
        
        self.register(IMarkerRepository, create_marker_repository)
        
        # NLP Processor
        def create_nlp_processor():
            from ..services.nlp_service import get_nlp_service
            return get_nlp_service()
        
        self.register(INlpProcessor, create_nlp_processor)
        
        # Cache Provider
        def create_cache_provider():
            from ..infrastructure.cache.cache_factory import CacheFactory
            # Use layered cache for production, simple cache for development
            if settings.ENVIRONMENT == "production":
                return CacheFactory.create_layered_cache()
            else:
                return CacheFactory.create_cache()
        
        self.register(ICacheProvider, create_cache_provider)
        
        # Metrics Collector
        def create_metrics_collector():
            from ..infrastructure.metrics.prometheus_metrics import PrometheusMetrics
            return PrometheusMetrics()
        
        self.register(IMetricsCollector, create_metrics_collector)
        
        # Notification Service (optional)
        if settings.NOTIFICATION_WEBHOOK_URL:
            def create_notification_service():
                from ..infrastructure.notifications.webhook_notifier import WebhookNotifier
                return WebhookNotifier(settings.NOTIFICATION_WEBHOOK_URL)
            
            self.register(INotificationService, create_notification_service)


# Global container instance
_container = ServiceContainer()


@lru_cache()
def get_container() -> ServiceContainer:
    """Get the global service container."""
    if not _container._initialized:
        _container.initialize()
    return _container


def get_service(interface: Type) -> Any:
    """
    Get a service from the container.
    
    Args:
        interface: Interface type
        
    Returns:
        Service instance
    """
    return get_container().get(interface)