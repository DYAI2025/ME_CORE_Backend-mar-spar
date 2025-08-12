"""
In-memory cache implementation.
Simple cache for development and small deployments.
"""
import asyncio
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from ...core.interfaces import ICacheProvider
from ...core.logging import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """Represents a cache entry with TTL support."""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        self.value = value
        self.expires_at = None
        if ttl:
            self.expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class MemoryCache(ICacheProvider):
    """In-memory cache implementation."""
    
    def __init__(self):
        """Initialize memory cache."""
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        logger.info("Initialized MemoryCache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            entry = self._cache.get(key)
            
            if not entry:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                return None
            
            logger.debug(f"Cache hit for key: {key}")
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        async with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
            logger.debug(f"Cache set for key: {key}, TTL: {ttl}")
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache delete for key: {key}")
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)