"""
Redis Caching Layer with Connection Pooling
Provides cache decorators, key generation, TTL management, and cache warming
"""

import json
import logging
from app.core.logging import StructuredLogger
from typing import Optional, Callable, Any, TypeVar, Union
from functools import wraps
from datetime import datetime, timedelta
import hashlib
from inspect import iscoroutinefunction

import redis
from redis.connection import ConnectionPool
from app.core.config import settings

logger = StructuredLogger(__name__)

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Cache TTLs (in seconds)
CACHE_TTLS = {
    "playlist": settings.CACHE_PLAYLIST_TTL,  # 5 minutes (300s)
    "device": 60,  # 1 minute
    "content": settings.CACHE_CONTENT_METADATA_TTL,  # 15 minutes (900s)
    "dashboard": 30,  # 30 seconds
    "activity": 60,  # 1 minute
    "tags": 300,  # 5 minutes
    "settings": 600,  # 10 minutes
}

# Cache key prefixes
CACHE_KEY_PREFIXES = {
    "playlist_list": "cache:playlists:list",
    "playlist": "cache:playlist:",
    "device_list": "cache:devices:list",
    "device": "cache:device:",
    "content_list": "cache:content:list",
    "content": "cache:content:",
    "dashboard_stats": "cache:dashboard:stats",
    "activity_list": "cache:activities:list",
    "tags_list": "cache:tags:list",
    "tag": "cache:tag:",
    "settings": "cache:settings",
}


# =============================================================================
# REDIS CONNECTION POOL
# =============================================================================

class RedisConnectionPool:
    """
    Singleton Redis connection pool with health checks
    Provides async-safe connection management
    """

    _instance: Optional["RedisConnectionPool"] = None
    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls) -> redis.Redis:
        """
        Initialize Redis connection pool
        Called once during application startup

        Returns:
            Redis client instance
        """
        if cls._client is not None:
            return cls._client

        try:
            # Create connection pool with optimized settings
            cls._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=20,  # Connection pool size
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 1,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                },
                health_check_interval=30,
                retry_on_timeout=True,
                decode_responses=True,  # Return strings, not bytes
            )

            cls._client = redis.Redis(connection_pool=cls._pool)

            # Test connection
            cls._client.ping()
            logger.info("✓ Redis connection pool initialized successfully")

            return cls._client

        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis connection pool: {e}")
            raise

    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        Get Redis client instance
        Ensures connection is initialized

        Returns:
            Redis client instance
        """
        if cls._client is None:
            cls.initialize()
        return cls._client

    @classmethod
    def close(cls):
        """
        Close connection pool
        Called during application shutdown
        """
        if cls._pool:
            try:
                cls._pool.disconnect()
                logger.info("✓ Redis connection pool closed")
            except Exception as e:
                logger.error(f"❌ Error closing Redis pool: {e}")
            finally:
                cls._client = None
                cls._pool = None

    @classmethod
    def is_healthy(cls) -> bool:
        """
        Check Redis connection health

        Returns:
            True if Redis is healthy, False otherwise
        """
        try:
            client = cls.get_client()
            client.ping()
            return True
        except Exception as e:
            logger.warning(f"⚠ Redis health check failed: {e}")
            return False


# =============================================================================
# CACHE KEY GENERATION
# =============================================================================

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate consistent cache key from prefix and arguments

    Args:
        prefix: Cache key prefix
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key

    Returns:
        Formatted cache key string
    """
    key_parts = [prefix]

    # Add positional arguments
    for arg in args:
        if arg is not None:
            key_parts.append(str(arg))

    # Add keyword arguments (sorted for consistency)
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if v is not None:
            key_parts.append(f"{k}={v}")

    # Join all parts with colon separator
    full_key = ":".join(key_parts)

    # Hash very long keys to avoid Redis key size limits
    if len(full_key) > 200:
        hash_suffix = hashlib.md5(full_key.encode()).hexdigest()[:8]
        full_key = f"{prefix}:hash:{hash_suffix}"

    return full_key


# =============================================================================
# CACHE DECORATOR
# =============================================================================

T = TypeVar("T")


def cached(
    ttl: Union[int, str] = 300,
    key_prefix: Optional[str] = None,
    invalidate_on_methods: Optional[list] = None,
):
    """
    Decorator to cache function results in Redis

    Usage:
        @cached(ttl=300, key_prefix="playlist_list")
        async def get_playlists(db: Session):
            ...

        @cached(ttl="playlist", key_prefix="playlist")
        async def get_playlist(playlist_id: int, db: Session):
            ...

    Args:
        ttl: Time-to-live in seconds or cache category key
        key_prefix: Redis key prefix for cache
        invalidate_on_methods: HTTP methods that should invalidate cache

    Returns:
        Decorated function with caching
    """

    def decorator(func: Callable) -> Callable:
        # Determine TTL
        effective_ttl = ttl
        if isinstance(ttl, str):
            effective_ttl = CACHE_TTLS.get(ttl, 300)

        # Determine if function is async
        is_async = iscoroutinefunction(func)

        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                # Extract cache key arguments (skip self, db, request, etc.)
                cache_args = []
                for arg in args:
                    if hasattr(arg, "__tablename__"):  # SQLAlchemy model
                        continue
                    if hasattr(arg, "url"):  # Request object
                        continue
                    if hasattr(arg, "execute"):  # DB session
                        continue
                    cache_args.append(arg)

                # Generate cache key
                cache_key = generate_cache_key(key_prefix or func.__name__, *cache_args, **kwargs)

                try:
                    # Try to get from cache
                    client = RedisConnectionPool.get_client()
                    cached_data = client.get(cache_key)

                    if cached_data:
                        logger.debug(f"✓ Cache hit for {cache_key}")
                        return json.loads(cached_data)

                except Exception as e:
                    logger.warning(f"⚠ Cache retrieval error for {cache_key}: {e}")

                # Cache miss or error - call function
                result = await func(*args, **kwargs)

                # Store in cache
                try:
                    client = RedisConnectionPool.get_client()
                    client.setex(
                        cache_key,
                        int(effective_ttl),
                        json.dumps(result, default=str)
                    )
                    logger.debug(f"✓ Cached {cache_key} for {effective_ttl}s")
                except Exception as e:
                    logger.warning(f"⚠ Cache storage error for {cache_key}: {e}")

                return result

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                # Extract cache key arguments
                cache_args = []
                for arg in args:
                    if hasattr(arg, "__tablename__"):
                        continue
                    if hasattr(arg, "url"):
                        continue
                    if hasattr(arg, "execute"):
                        continue
                    cache_args.append(arg)

                cache_key = generate_cache_key(key_prefix or func.__name__, *cache_args, **kwargs)

                try:
                    client = RedisConnectionPool.get_client()
                    cached_data = client.get(cache_key)

                    if cached_data:
                        logger.debug(f"✓ Cache hit for {cache_key}")
                        return json.loads(cached_data)

                except Exception as e:
                    logger.warning(f"⚠ Cache retrieval error for {cache_key}: {e}")

                result = func(*args, **kwargs)

                try:
                    client = RedisConnectionPool.get_client()
                    client.setex(
                        cache_key,
                        int(effective_ttl),
                        json.dumps(result, default=str)
                    )
                    logger.debug(f"✓ Cached {cache_key} for {effective_ttl}s")
                except Exception as e:
                    logger.warning(f"⚠ Cache storage error for {cache_key}: {e}")

                return result

            return sync_wrapper

        return decorator

    # Handle decorator without parentheses: @cached
    if callable(ttl):
        func = ttl
        ttl = 300
        return decorator(func)

    return decorator


# =============================================================================
# CACHE INVALIDATION
# =============================================================================

def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cache entries matching pattern

    Args:
        pattern: Cache key pattern (e.g., "cache:playlist:*")

    Returns:
        Number of keys deleted
    """
    try:
        client = RedisConnectionPool.get_client()
        keys = client.keys(pattern)
        if keys:
            deleted = client.delete(*keys)
            logger.info(f"✓ Invalidated {deleted} cache entries matching {pattern}")
            return deleted
        return 0
    except Exception as e:
        logger.warning(f"⚠ Cache invalidation error for pattern {pattern}: {e}")
        return 0


def invalidate_by_prefix(prefix_key: str) -> int:
    """
    Invalidate all cache entries with given prefix

    Args:
        prefix_key: Prefix key from CACHE_KEY_PREFIXES

    Returns:
        Number of keys deleted
    """
    prefix = CACHE_KEY_PREFIXES.get(prefix_key, prefix_key)
    return invalidate_cache(f"{prefix}*")


def clear_all_cache() -> int:
    """
    Clear all application cache (use with caution)

    Returns:
        Number of keys deleted
    """
    try:
        client = RedisConnectionPool.get_client()
        pattern = "cache:*"
        keys = client.keys(pattern)
        if keys:
            deleted = client.delete(*keys)
            logger.warning(f"⚠ Cleared all cache: {deleted} entries deleted")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")
        return 0


# =============================================================================
# CACHE WARMING
# =============================================================================

def warm_cache_playlist_list(db_session) -> int:
    """
    Pre-cache active playlists on startup

    Args:
        db_session: Database session

    Returns:
        Number of playlists cached
    """
    try:
        from app.models.playlist import Playlist
        from sqlalchemy import func
        from app.models.playlist import PlaylistContent
        from app.models.content import Content

        client = RedisConnectionPool.get_client()

        # Get all playlists
        playlists = db_session.query(Playlist).order_by(Playlist.created_at.desc()).all()

        cache_key = CACHE_KEY_PREFIXES["playlist_list"]
        playlist_responses = []

        for playlist in playlists:
            content_count = db_session.query(func.count(PlaylistContent.id)).filter(
                PlaylistContent.playlist_id == playlist.id
            ).scalar()

            # Calculate total duration
            content_items = db_session.query(PlaylistContent).filter(
                PlaylistContent.playlist_id == playlist.id
            ).all()

            total_duration = 0
            for item in content_items:
                if item.duration:
                    total_duration += item.duration
                else:
                    content = db_session.query(Content).filter(Content.id == item.content_id).first()
                    if content and content.duration:
                        total_duration += content.duration

            playlist_dict = playlist.to_dict()
            playlist_dict['content_count'] = content_count or 0
            playlist_dict['total_duration'] = total_duration
            playlist_responses.append(playlist_dict)

        # Store in cache
        client.setex(
            cache_key,
            CACHE_TTLS["playlist"],
            json.dumps(playlist_responses, default=str)
        )

        logger.info(f"✓ Warmed cache with {len(playlists)} playlists")
        return len(playlists)

    except Exception as e:
        logger.warning(f"⚠ Cache warming failed: {e}")
        return 0


def warm_cache_device_list(db_session) -> int:
    """
    Pre-cache device list on startup

    Args:
        db_session: Database session

    Returns:
        Number of devices cached
    """
    try:
        from app.models.device import Device

        client = RedisConnectionPool.get_client()

        # Get active devices
        devices = db_session.query(Device).filter(
            Device.is_active == True
        ).order_by(Device.created_at.desc()).all()

        cache_key = CACHE_KEY_PREFIXES["device_list"]
        device_responses = [device.to_dict() for device in devices]

        # Store in cache
        client.setex(
            cache_key,
            CACHE_TTLS["device"],
            json.dumps(device_responses, default=str)
        )

        logger.info(f"✓ Warmed cache with {len(devices)} devices")
        return len(devices)

    except Exception as e:
        logger.warning(f"⚠ Device cache warming failed: {e}")
        return 0


def warm_cache_content_list(db_session) -> int:
    """
    Pre-cache content list on startup

    Args:
        db_session: Database session

    Returns:
        Number of content items cached
    """
    try:
        from app.models.content import Content

        client = RedisConnectionPool.get_client()

        # Get all active content
        content_items = db_session.query(Content).filter(
            Content.is_active == True
        ).order_by(Content.created_at.desc()).all()

        cache_key = CACHE_KEY_PREFIXES["content_list"]
        content_responses = [content.to_dict() for content in content_items]

        # Store in cache
        client.setex(
            cache_key,
            CACHE_TTLS["content"],
            json.dumps(content_responses, default=str)
        )

        logger.info(f"✓ Warmed cache with {len(content_items)} content items")
        return len(content_items)

    except Exception as e:
        logger.warning(f"⚠ Content cache warming failed: {e}")
        return 0


# =============================================================================
# CACHE STATISTICS
# =============================================================================

def get_cache_stats() -> dict:
    """
    Get Redis cache statistics

    Returns:
        Dictionary with cache stats
    """
    try:
        client = RedisConnectionPool.get_client()

        # Get Redis info
        info = client.info()

        # Count cache keys
        cache_keys = client.keys("cache:*")
        key_count = len(cache_keys) if cache_keys else 0

        return {
            "connected": True,
            "used_memory": info.get("used_memory_human", "N/A"),
            "cache_keys": key_count,
            "evicted_keys": info.get("evicted_keys", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) /
                (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) * 100
            ) if (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) > 0 else 0,
        }
    except Exception as e:
        logger.error(f"❌ Error getting cache stats: {e}")
        return {"connected": False, "error": str(e)}
