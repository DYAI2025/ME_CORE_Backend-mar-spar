"""
NLP Service abstraction for MarkerEngine.
Provides pluggable NLP capabilities with dummy and Spark NLP implementations.
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional
from ..models.analysis_context import AnalysisContext
from ..config import settings


logger = logging.getLogger(__name__)


class NlpService(ABC):
    """
    Abstract base class for NLP services.
    All NLP services must implement the enrich method which modifies
    the AnalysisContext in-place with NLP annotations.
    """
    
    @abstractmethod
    def enrich(self, context: AnalysisContext) -> None:
        """
        Enrich the analysis context with NLP annotations.
        This method modifies the context in-place and does not return anything.
        
        Args:
            context: The AnalysisContext to enrich with NLP data
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the NLP service is available and ready to use.
        
        Returns:
            bool: True if the service is available, False otherwise
        """
        pass


class DummyNlpService(NlpService):
    """
    No-op implementation of NLP service for initial deployment.
    This allows the system to work without any NLP dependencies.
    """
    
    def enrich(self, context: AnalysisContext) -> None:
        """
        Dummy implementation that performs basic tokenization only.
        """
        # Simple whitespace tokenization as a placeholder
        if context.text:
            context.tokens = context.text.split()
            context.sentences = [context.text]  # Treat entire text as one sentence
            
            # Add metadata to indicate dummy processing
            context.metadata["nlp_service"] = "dummy"
            context.metadata["nlp_version"] = "1.0.0"
            
        logger.debug(f"DummyNlpService processed text with {len(context.tokens or [])} tokens")
    
    def is_available(self) -> bool:
        """
        Dummy service is always available.
        """
        return True


class SparkNlpService(NlpService):
    """
    Spark NLP implementation stub that delegates to the full implementation.
    This provides a bridge to the complete Spark NLP service.
    """
    
    def __init__(self):
        """
        Initialize Spark NLP service by trying to load the full implementation.
        """
        self._available = False
        self._impl = None
        
        # Try to load the full implementation
        try:
            from .spark_nlp_service import SparkNlpServiceImpl
            self._impl = SparkNlpServiceImpl()
            self._available = self._impl.is_available()
            logger.info("Full Spark NLP implementation loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load full Spark NLP implementation: {e}")
            # Check if basic dependencies are available
            try:
                import sparknlp
                from pyspark.sql import SparkSession
                logger.info("Spark NLP dependencies found but full implementation not available")
            except ImportError:
                logger.warning("Spark NLP dependencies not available. Install pyspark and spark-nlp to enable.")
    
    def enrich(self, context: AnalysisContext) -> None:
        """
        Enrich context with Spark NLP annotations using the full implementation.
        """
        if self._impl and self._available:
            # Delegate to full implementation
            self._impl.enrich(context)
        else:
            logger.warning("SparkNlpService called but not available, falling back to basic processing")
            # Fallback to basic processing
            if context.text:
                context.tokens = context.text.split()
                context.sentences = [context.text]
                context.metadata["nlp_service"] = "spark_nlp_fallback"
                context.metadata["nlp_version"] = "unavailable"
    
    def is_available(self) -> bool:
        """
        Check if Spark NLP service is available.
        """
        return self._available
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about loaded models.
        """
        if self._impl and hasattr(self._impl, 'get_model_info'):
            return self._impl.get_model_info()
        return {
            "available": False,
            "reason": "Full implementation not loaded"
        }


class NlpServiceFactory:
    """
    Factory for creating NLP service instances based on configuration.
    """
    
    @staticmethod
    def create_nlp_service() -> NlpService:
        """
        Create an NLP service instance based on environment configuration.
        
        Uses SPARK_NLP_ENABLED setting to determine which
        implementation to use.
        
        Returns:
            NlpService: An instance of the appropriate NLP service
        """
        spark_nlp_enabled = settings.SPARK_NLP_ENABLED
        
        if spark_nlp_enabled:
            logger.info("Creating SparkNlpService (SPARK_NLP_ENABLED=true)")
            service = SparkNlpService()
            
            # Fall back to dummy if Spark NLP is not actually available
            if not service.is_available():
                logger.warning("Spark NLP requested but not available, falling back to DummyNlpService")
                return DummyNlpService()
            
            return service
        else:
            logger.info("Creating DummyNlpService (SPARK_NLP_ENABLED=false or not set)")
            return DummyNlpService()


# Singleton instance for easy access
_nlp_service_instance: Optional[NlpService] = None


def get_nlp_service() -> NlpService:
    """
    Get the singleton NLP service instance.
    Creates it on first access using the factory.
    
    Returns:
        NlpService: The NLP service instance
    """
    global _nlp_service_instance
    
    if _nlp_service_instance is None:
        _nlp_service_instance = NlpServiceFactory.create_nlp_service()
    
    return _nlp_service_instance