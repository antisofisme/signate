"""
Redis Cache Service for Digital Signage System
Provides caching functionality for improved performance
"""

import redis
import json
import logging
from typing import Any, Optional, Union, List
from datetime import timedelta
import os

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        """Initialize Redis connection"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            # Parse Redis URL
            if redis_url.startswith('redis://'):
                # Extract host, port, db from URL
                parts = redis_url.replace('redis://', '').split('/')
                host_port = parts[0].split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 6379
                db = int(parts[1]) if len(parts) > 1 else 0
            else:
                host, port, db = 'localhost', 6379, 0
            
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis cache connected: {host}:{port}/{db}")
            
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON string"""
        return json.dumps(value, default=str)
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize JSON string to value"""
        try:
            return json.loads(value)
        except:
            return value
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return self._deserialize(value)
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None,  # Uses env var if not specified
        nx: bool = False  # Only set if not exists
    ) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False

        # Use default TTL from env if not specified
        if ttl is None:
            ttl = int(os.getenv("CACHE_DEFAULT_TTL", "300"))

        try:
            serialized = self._serialize(value)
            if nx:
                return bool(self.redis_client.set(key, serialized, ex=ttl, nx=True))
            else:
                return bool(self.redis_client.setex(key, ttl, serialized))
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except:
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.incr(key, amount)
        except:
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on existing key"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.expire(key, ttl))
        except:
            return False
    
    # Cache invalidation helpers
    
    def invalidate_content(self, content_id: int, org_id: Optional[int] = None):
        """Invalidate content-related caches"""
        self.delete(f"content:{content_id}")
        self.clear_pattern(f"content:{content_id}:*")
        self.clear_pattern("contents:list:*")
        if org_id:
            self.clear_pattern(f"org:{org_id}:contents:*")
    
    def invalidate_playlist(self, playlist_id: int, org_id: Optional[int] = None):
        """Invalidate playlist-related caches"""
        self.delete(f"playlist:{playlist_id}")
        self.clear_pattern(f"playlist:{playlist_id}:*")
        self.clear_pattern("playlists:list:*")
        if org_id:
            self.clear_pattern(f"org:{org_id}:playlists:*")
    
    def invalidate_device(self, device_id: int, org_id: Optional[int] = None):
        """Invalidate device-related caches"""
        self.delete(f"device:{device_id}")
        self.clear_pattern(f"device:{device_id}:*")
        self.clear_pattern("devices:list:*")
        if org_id:
            self.clear_pattern(f"org:{org_id}:devices:*")
    
    def invalidate_organization(self, org_id: int):
        """Invalidate all organization caches"""
        self.clear_pattern(f"org:{org_id}:*")
    
    # Utility methods
    
    def get_many(self, keys: List[str]) -> dict:
        """Get multiple values at once"""
        if not self.redis_client:
            return {}
        
        try:
            values = self.redis_client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = self._deserialize(value)
            return result
        except:
            return {}
    
    def set_many(self, mapping: dict, ttl: int = None) -> bool:
        """Set multiple values at once"""
        if not self.redis_client:
            return False

        # Use default TTL from env if not specified
        if ttl is None:
            ttl = int(os.getenv("CACHE_DEFAULT_TTL", "300"))

        try:
            pipe = self.redis_client.pipeline()
            for key, value in mapping.items():
                pipe.setex(key, ttl, self._serialize(value))
            pipe.execute()
            return True
        except:
            return False
    
    def health_check(self) -> dict:
        """Check Redis health status"""
        if not self.redis_client:
            return {"status": "error", "message": "Redis client not initialized"}
        
        try:
            self.redis_client.ping()
            info = self.redis_client.info()
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Global cache instance
cache = CacheService()


# Cache key generators

def content_cache_key(content_id: int) -> str:
    """Generate cache key for content"""
    return f"content:{content_id}"


def playlist_cache_key(playlist_id: int) -> str:
    """Generate cache key for playlist"""
    return f"playlist:{playlist_id}"


def device_cache_key(device_id: int) -> str:
    """Generate cache key for device"""
    return f"device:{device_id}"


def list_cache_key(
    entity: str, 
    org_id: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
    **filters
) -> str:
    """Generate cache key for list queries"""
    if org_id:
        base = f"org:{org_id}:{entity}:list"
    else:
        base = f"{entity}:list"
    
    # Add pagination
    key_parts = [base, f"page:{page}", f"limit:{limit}"]
    
    # Add filters
    for k, v in sorted(filters.items()):
        if v is not None:
            key_parts.append(f"{k}:{v}")
    
    return ":".join(key_parts)