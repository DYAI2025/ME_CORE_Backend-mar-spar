"""
Redis cache implementation.
Distributed cache for production deployments.
"""
import json
import pickle
from typing import Any, Optional
from redis import asyncio as aioredis
from redis.exceptions import RedisError
from app.core.interfaces import ICacheProvider
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class RedisCache(ICacheProvider):
    """Redis cache implementation for distributed caching."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL. Defaults to settings.REDIS_URL.
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self._client: Optional[aioredis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Establish Redis connection."""
        if self._connected:
            return
        
        try:
            self._client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle decoding ourselves
                max_connections=10,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self._client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.redis_url}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client and self._connected:
            await self._client.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    async def _ensure_connected(self) -> None:
        """Ensure Redis connection is established."""
        if not self._connected:
            await self.connect()
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for Redis storage."""
        try:
            # Try JSON first (for simple types)
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from Redis storage."""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        await self._ensure_connected()
        
        try:
            data = await self._client.get(key)
            if data is None:
                return None
            
            logger.debug(f"Redis cache hit for key: {key}")
            return self._deserialize(data)
        except RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Deserialization error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        await self._ensure_connected()
        
        try:
            data = self._serialize(value)
            if ttl:
                await self._client.setex(key, ttl, data)
            else:
                await self._client.set(key, data)
            
            logger.debug(f"Redis cache set for key: {key}, TTL: {ttl}")
        except RedisError as e:
            logger.error(f"Redis set error for key {key}: {e}")
        except Exception as e:
            logger.error(f"Serialization error for key {key}: {e}")
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        await self._ensure_connected()
        
        try:
            await self._client.delete(key)
            logger.debug(f"Redis cache delete for key: {key}")
        except RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
    
    async def clear(self) -> None:
        """Clear all cache entries (use with caution)."""
        await self._ensure_connected()
        
        try:
            await self._client.flushdb()
            logger.warning("Redis cache cleared (all keys deleted)")
        except RedisError as e:
            logger.error(f"Redis clear error: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        await self._ensure_connected()
        
        try:
            return await self._client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key in seconds."""
        await self._ensure_connected()
        
        try:
            ttl = await self._client.ttl(key)
            return ttl if ttl > 0 else None
        except RedisError as e:
            logger.error(f"Redis TTL error for key {key}: {e}")
            return None
    
    async def mget(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values at once."""
        await self._ensure_connected()
        
        try:
            values = await self._client.mget(keys)
            result = {}
            
            for key, data in zip(keys, values):
                if data is not None:
                    try:
                        result[key] = self._deserialize(data)
                    except Exception as e:
                        logger.error(f"Deserialization error for key {key}: {e}")
            
            return result
        except RedisError as e:
            logger.error(f"Redis mget error: {e}")
            return {}
    
    async def mset(self, mapping: dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set multiple values at once."""
        await self._ensure_connected()
        
        try:
            # Serialize all values
            serialized = {}
            for key, value in mapping.items():
                try:
                    serialized[key] = self._serialize(value)
                except Exception as e:
                    logger.error(f"Serialization error for key {key}: {e}")
                    continue
            
            if not serialized:
                return
            
            if ttl:
                # Use pipeline for setting with TTL
                async with self._client.pipeline() as pipe:
                    for key, data in serialized.items():
                        pipe.setex(key, ttl, data)
                    await pipe.execute()
            else:
                await self._client.mset(serialized)
            
            logger.debug(f"Redis cache mset for {len(serialized)} keys, TTL: {ttl}")
        except RedisError as e:
            logger.error(f"Redis mset error: {e}")