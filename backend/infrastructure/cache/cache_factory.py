"""
Cache factory for creating appropriate cache implementations.
"""
from typing import Optional
from app.core.interfaces import ICacheProvider
from app.core.config import settings
from app.core.logging import get_logger
from .memory_cache import MemoryCache
from .redis_cache import RedisCache

logger = get_logger(__name__)


class CacheFactory:
    """Factory for creating cache providers based on configuration."""
    
    @staticmethod
    def create_cache(cache_type: Optional[str] = None) -> ICacheProvider:
        """Create cache provider based on type or configuration.
        
        Args:
            cache_type: Type of cache ('memory', 'redis'). 
                       Defaults to settings.CACHE_TYPE.
        
        Returns:
            ICacheProvider implementation
        
        Raises:
            ValueError: If cache type is not supported
        """
        cache_type = cache_type or settings.CACHE_TYPE
        
        if cache_type == "memory":
            logger.info("Creating MemoryCache provider")
            return MemoryCache()
        
        elif cache_type == "redis":
            if not settings.REDIS_URL:
                logger.warning("Redis URL not configured, falling back to MemoryCache")
                return MemoryCache()
            
            logger.info("Creating RedisCache provider")
            return RedisCache(settings.REDIS_URL)
        
        else:
            raise ValueError(f"Unsupported cache type: {cache_type}")
    
    @staticmethod
    def create_layered_cache() -> ICacheProvider:
        """Create a two-layer cache with memory L1 and Redis L2.
        
        This provides fast in-memory access with Redis fallback
        for distributed caching.
        
        Returns:
            LayeredCache implementation
        """
        from .layered_cache import LayeredCache
        
        l1_cache = MemoryCache()
        l2_cache = None
        
        if settings.REDIS_URL:
            try:
                l2_cache = RedisCache(settings.REDIS_URL)
                logger.info("Creating LayeredCache with MemoryCache (L1) and RedisCache (L2)")
            except Exception as e:
                logger.warning(f"Failed to create Redis L2 cache: {e}")
        
        if l2_cache:
            return LayeredCache(l1_cache, l2_cache)
        else:
            logger.info("Creating single-layer MemoryCache (Redis not available)")
            return l1_cache