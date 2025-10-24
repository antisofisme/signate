"""
Redis Client for Pub/Sub
Real-time log streaming via Redis Pub/Sub
"""

import redis
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Get Redis client singleton
    
    Returns:
        Redis client instance
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,  # Decode bytes to strings
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            _redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    return _redis_client


def publish_log(device_id: int, log_data: dict) -> bool:
    """
    Publish log entry to Redis channel for real-time streaming
    
    Args:
        device_id: Device ID
        log_data: Log data dictionary
    
    Returns:
        True if published successfully
    """
    try:
        client = get_redis_client()
        channel = f"device_logs:{device_id}"
        
        # Publish as JSON string
        import json
        message = json.dumps(log_data)
        
        client.publish(channel, message)
        logger.debug(f"Published log to channel {channel}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to publish log: {e}")
        return False


def close_redis_client():
    """
    Close Redis client connection
    """
    global _redis_client
    
    if _redis_client:
        try:
            _redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis: {e}")
        finally:
            _redis_client = None
