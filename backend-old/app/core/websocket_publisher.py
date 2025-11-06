"""
WebSocket Event Publisher
Helper utility to publish WebSocket events via Redis pub/sub

Usage:
    from app.core.websocket_publisher import ws_publisher

    # Notify specific device
    await ws_publisher.notify_device(device_id, 'playlist_update', {'playlist_id': 123})

    # Broadcast to all devices
    await ws_publisher.broadcast_devices('command', {'command': 'reload'})

    # Notify dashboard
    await ws_publisher.notify_dashboard('device_registered', {'device_id': 123})
"""

import json
import logging
from app.core.logging import StructuredLogger
from typing import Any, Dict, Optional
from datetime import datetime
import redis.asyncio as redis

from app.core.config import settings

logger = StructuredLogger(__name__)


class WebSocketPublisher:
    """
    WebSocket event publisher using Redis pub/sub
    Publishes events that WebSocket endpoints will forward to connected clients
    """

    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None

    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
        return self._redis_client

    async def close(self):
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None

    async def notify_device(
        self,
        device_id: int,
        event_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Notify specific device via WebSocket

        Args:
            device_id: Target device ID
            event_type: Event type (playlist_update, content_ready, command, etc.)
            data: Event data (will be merged with type and timestamp)

        Returns:
            True if published successfully, False otherwise
        """
        try:
            redis_client = await self._get_redis_client()

            # Build event message
            message = {
                "type": event_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                **data
            }

            # Publish to device-specific channel
            channel = f"device:{device_id}:updates"
            await redis_client.publish(channel, json.dumps(message))

            logger.debug(
                f"WebSocket event published to device {device_id}",
                extra={
                    "channel": channel,
                    "event_type": event_type,
                    "device_id": device_id
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to publish WebSocket event to device {device_id}",
                extra={
                    "error": str(e),
                    "event_type": event_type,
                    "device_id": device_id
                }
            )
            return False

    async def broadcast_devices(
        self,
        event_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Broadcast event to all connected devices

        Args:
            event_type: Event type (command, announcement, etc.)
            data: Event data

        Returns:
            True if published successfully, False otherwise
        """
        try:
            redis_client = await self._get_redis_client()

            # Build event message
            message = {
                "type": event_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                **data
            }

            # Publish to broadcast channel
            channel = "devices:broadcast"
            await redis_client.publish(channel, json.dumps(message))

            logger.info(
                "WebSocket event broadcasted to all devices",
                extra={
                    "channel": channel,
                    "event_type": event_type
                }
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to broadcast WebSocket event",
                extra={
                    "error": str(e),
                    "event_type": event_type
                }
            )
            return False

    async def notify_dashboard(
        self,
        event: str,
        data: Dict[str, Any],
        channel: str = "dashboard:devices"
    ) -> bool:
        """
        Notify dashboard via WebSocket

        Args:
            event: Event name (device_registered, content_uploaded, etc.)
            data: Event data
            channel: Dashboard channel (dashboard:devices, dashboard:content, etc.)

        Returns:
            True if published successfully, False otherwise
        """
        try:
            redis_client = await self._get_redis_client()

            # Build event message
            message = {
                "event": event,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": data
            }

            # Publish to dashboard channel
            await redis_client.publish(channel, json.dumps(message))

            logger.debug(
                f"Dashboard event published: {event}",
                extra={
                    "channel": channel,
                    "event": event
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to publish dashboard event: {event}",
                extra={
                    "error": str(e),
                    "event": event,
                    "channel": channel
                }
            )
            return False


# Global singleton instance
ws_publisher = WebSocketPublisher()
