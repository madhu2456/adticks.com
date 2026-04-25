"""
AdTicks — Redis caching utilities.

Provides decorators and helper functions for caching expensive operations
with TTL-based invalidation and cache key generation.
"""

import functools
import json
import logging
from typing import Any, Callable, Optional, TypeVar
import uuid

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Global Redis client (lazy-loaded)
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client. Returns None if Redis is unavailable."""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        _redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        # Test connection
        await _redis_client.ping()
        logger.info("redis_connected")
        return _redis_client
    except Exception as e:
        logger.warning("redis_unavailable", extra={"error": str(e)})
        return None


async def close_redis_client() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def cache_key(*args: Any, **kwargs: Any) -> str:
    """Generate a cache key from function arguments."""
    # Filter out non-serializable objects (like request, db session, etc.)
    serializable_args = []
    for arg in args:
        if isinstance(arg, (str, int, float, bool, type(None), uuid.UUID)):
            serializable_args.append(arg)
        elif hasattr(arg, "id"):  # For objects with an id attribute
            serializable_args.append(f"{arg.__class__.__name__}:{arg.id}")
    
    serializable_kwargs = {
        k: v for k, v in kwargs.items()
        if isinstance(v, (str, int, float, bool, type(None), uuid.UUID))
    }
    
    try:
        key_parts = [str(arg) for arg in serializable_args]
        if serializable_kwargs:
            key_parts.append(json.dumps(serializable_kwargs, sort_keys=True))
        return ":".join(key_parts)
    except Exception:
        return str(uuid.uuid4())


def cached(ttl: int = 300, key_prefix: str = "") -> Callable:
    """
    Decorator to cache async function results in Redis.
    
    Args:
        ttl: Time to live in seconds (default 5 minutes)
        key_prefix: Optional prefix for the cache key (uses function name if not provided)
    
    Usage:
        @cached(ttl=600)
        async def get_user_projects(user_id: UUID) -> List[Project]:
            # expensive operation
            return projects
    """
    def decorator(func: Callable) -> Callable:
        prefix = key_prefix or func.__name__
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            redis_client = await get_redis_client()
            
            if not redis_client:
                # Redis unavailable, call function directly
                return await func(*args, **kwargs)
            
            # Generate cache key
            key_suffix = cache_key(*args, **kwargs)
            full_key = f"cache:{prefix}:{key_suffix}"
            
            try:
                # Try to get from cache
                cached_value = await redis_client.get(full_key)
                if cached_value is not None:
                    logger.debug(
                        "cache_hit",
                        extra={"key": full_key, "function": func.__name__}
                    )
                    try:
                        return json.loads(cached_value)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, just return the string value
                        return cached_value
            except Exception as e:
                logger.warning(
                    "cache_get_error",
                    extra={"key": full_key, "error": str(e)}
                )
            
            # Cache miss - call function
            result = await func(*args, **kwargs)
            
            # Store in cache (don't fail if caching fails)
            try:
                # Try to JSON serialize the result
                if result is None:
                    cached_data = json.dumps(None)
                elif isinstance(result, (dict, list, str, int, float, bool)):
                    cached_data = json.dumps(result, default=str)
                elif hasattr(result, "model_dump"):  # Pydantic models
                    cached_data = json.dumps(result.model_dump(), default=str)
                elif hasattr(result, "dict"):  # Legacy Pydantic v1
                    cached_data = json.dumps(result.dict(), default=str)
                elif hasattr(result, "__dict__"):
                    cached_data = json.dumps(result.__dict__, default=str)
                else:
                    # For other objects, convert to string and JSONify
                    cached_data = json.dumps(str(result))
                
                await redis_client.setex(full_key, ttl, cached_data)
                logger.debug(
                    "cache_set",
                    extra={"key": full_key, "ttl": ttl, "function": func.__name__}
                )
            except Exception as e:
                # Don't fail the request if caching fails
                logger.warning(
                    "cache_set_error",
                    extra={"key": full_key, "error": str(e)}
                )
            
            return result
        
        return wrapper
    
    return decorator


async def invalidate_cache(pattern: str = "*") -> None:
    """
    Invalidate cache entries matching a pattern.
    
    Args:
        pattern: Redis key pattern to match (e.g., "cache:get_user_projects:*")
    
    Usage:
        # Invalidate all caches for a function
        await invalidate_cache("cache:get_user_projects:*")
        
        # Invalidate specific user's project cache
        await invalidate_cache(f"cache:get_user_projects:*{user_id}*")
        
        # Invalidate all caches
        await invalidate_cache("cache:*")
    """
    redis_client = await get_redis_client()
    
    if not redis_client:
        logger.warning("cache_invalidate_skip_redis_unavailable")
        return
    
    try:
        # Find keys matching the pattern
        keys = []
        cursor = 0
        while True:
            cursor, batch_keys = await redis_client.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            keys.extend(batch_keys)
            if cursor == 0:
                break
        
        if keys:
            await redis_client.delete(*keys)
            logger.info(
                "cache_invalidated",
                extra={"pattern": pattern, "count": len(keys)}
            )
    except Exception as e:
        logger.error(
            "cache_invalidate_error",
            extra={"pattern": pattern, "error": str(e)}
        )


async def clear_cache(key: str) -> None:
    """
    Delete a specific cache key.
    
    Args:
        key: Full cache key to delete
    """
    redis_client = await get_redis_client()
    
    if not redis_client:
        logger.warning("cache_clear_skip_redis_unavailable")
        return
    
    try:
        await redis_client.delete(key)
        logger.debug("cache_cleared", extra={"key": key})
    except Exception as e:
        logger.error("cache_clear_error", extra={"key": key, "error": str(e)})


def get_cache_stats() -> dict[str, Any]:
    """Get Redis cache statistics."""
    return {
        "redis_url": settings.REDIS_URL.replace(settings.REDIS_URL.split("://")[1], "***"),
        "status": "configured",
    }
