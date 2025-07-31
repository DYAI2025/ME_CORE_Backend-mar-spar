"""
Layered cache implementation with L1 and L2 caching.
Provides fast local cache with distributed cache fallback.
"""
from typing import Any, Optional
from app.core.interfaces import ICacheProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class LayeredCache(ICacheProvider):
    """Two-layer cache implementation with L1 and L2 providers."""
    
    def __init__(self, l1_cache: ICacheProvider, l2_cache: Optional[ICacheProvider] = None):
        """Initialize layered cache.
        
        Args:
            l1_cache: Primary (fast) cache provider
            l2_cache: Secondary (distributed) cache provider
        """
        self.l1_cache = l1_cache
        self.l2_cache = l2_cache
        logger.info(f"Initialized LayeredCache with L1: {type(l1_cache).__name__}, "
                   f"L2: {type(l2_cache).__name__ if l2_cache else 'None'}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache, checking L1 first, then L2."""
        # Try L1 cache first
        value = await self.l1_cache.get(key)
        if value is not None:
            logger.debug(f"L1 cache hit for key: {key}")
            return value
        
        # Try L2 cache if available
        if self.l2_cache:
            value = await self.l2_cache.get(key)
            if value is not None:
                logger.debug(f"L2 cache hit for key: {key}")
                # Promote to L1 cache with shorter TTL
                await self.l1_cache.set(key, value, ttl=300)  # 5 minutes in L1
                return value
        
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in both cache layers."""
        # Set in L1 with potentially shorter TTL
        l1_ttl = min(ttl or 3600, 3600)  # Max 1 hour in L1
        await self.l1_cache.set(key, value, ttl=l1_ttl)
        
        # Set in L2 if available
        if self.l2_cache:
            try:
                await self.l2_cache.set(key, value, ttl=ttl)
            except Exception as e:
                logger.warning(f"Failed to set key {key} in L2 cache: {e}")
    
    async def delete(self, key: str) -> None:
        """Delete value from both cache layers."""
        await self.l1_cache.delete(key)
        
        if self.l2_cache:
            try:
                await self.l2_cache.delete(key)
            except Exception as e:
                logger.warning(f"Failed to delete key {key} from L2 cache: {e}")
    
    async def clear(self) -> None:
        """Clear both cache layers."""
        await self.l1_cache.clear()
        
        if self.l2_cache:
            try:
                await self.l2_cache.clear()
            except Exception as e:
                logger.warning(f"Failed to clear L2 cache: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in either cache layer."""
        if await self.l1_cache.get(key) is not None:
            return True
        
        if self.l2_cache:
            return await self.l2_cache.exists(key) if hasattr(self.l2_cache, 'exists') else False
        
        return False
    
    async def warm_l1_from_l2(self, keys: list[str]) -> int:
        """Warm L1 cache with values from L2.
        
        Args:
            keys: List of keys to warm
        
        Returns:
            Number of keys successfully warmed
        """
        if not self.l2_cache:
            return 0
        
        warmed = 0
        for key in keys:
            value = await self.l2_cache.get(key)
            if value is not None:
                await self.l1_cache.set(key, value, ttl=300)  # 5 minutes
                warmed += 1
        
        logger.info(f"Warmed {warmed} keys in L1 cache from L2")
        return warmed