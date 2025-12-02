"""
WebSocket Manager
Centralized WebSocket connection management and broadcasting with Redis pub/sub support
"""

from typing import Dict, Set, Optional, Any, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
import json
import asyncio
import logging
from enum import Enum
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class WebSocketEventType(Enum):
    """WebSocket event types"""
    # Device events
    DEVICE_ACTIVATED = "device.activated"
    DEVICE_UPDATED = "device.updated"
    DEVICE_OFFLINE = "device.offline"
    DEVICE_ONLINE = "device.online"
    DEVICE_COMMAND = "device.command"
    DEVICE_CONSOLE_LOG = "device.console_log"

    # Content events
    CONTENT_UPLOADED = "content.uploaded"
    CONTENT_UPDATED = "content.updated"
    CONTENT_DELETED = "content.deleted"
    CONTENT_TRANSCODED = "content.transcoded"
    CONTENT_TRANSCODING_PROGRESS = "content.transcoding_progress"  # Real-time progress
    CONTENT_TRANSCODING_FAILED = "content.transcoding_failed"
    CONTENT_THUMBNAIL_READY = "content.thumbnail_ready"  # Thumbnail generated

    # Playlist events
    PLAYLIST_CREATED = "playlist.created"
    PLAYLIST_UPDATED = "playlist.updated"
    PLAYLIST_ASSIGNED = "playlist.assigned"
    PLAYLIST_UNASSIGNED = "playlist.unassigned"

    # Schedule events
    SCHEDULE_ACTIVATED = "schedule.activated"
    SCHEDULE_DEACTIVATED = "schedule.deactivated"

    # PMS events
    PMS_GUEST_UPDATE = "pms.guest_update"
    PMS_ROOM_UPDATE = "pms.room_update"

    # System events
    SYSTEM_NOTIFICATION = "system.notification"
    SYSTEM_MAINTENANCE = "system.maintenance"


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting
    
    Supports:
    - Multiple connection types (devices, admin users)
    - Organization-based isolation
    - Room/channel-based messaging
    - Connection health monitoring
    """
    
    def __init__(self, redis_url: Optional[str] = None, use_redis: bool = True):
        # Device connections: {device_id: {websocket, org_id, last_ping}}
        self._device_connections: Dict[int, Dict[str, Any]] = {}

        # Admin connections: {user_id: {websocket, org_id, permissions}}
        self._admin_connections: Dict[int, Dict[str, Any]] = {}

        # Organization rooms: {org_id: {device_ids, admin_ids}}
        self._organization_rooms: Dict[int, Dict[str, Set[int]]] = {}

        # Channel subscriptions: {channel: {connection_ids}}
        self._channel_subscriptions: Dict[str, Set[str]] = {}

        # Console log subscriptions: {device_id: {admin_user_ids}} - ALWAYS in-memory
        self._console_subscriptions: Dict[int, Set[int]] = {}

        # Player control WebSocket connections: {device_id: websocket} - For sending commands
        self._player_control_connections: Dict[int, WebSocket] = {}

        # Console subscriber count tracking: {device_id: {org_id: count}}
        self._console_subscriber_counts: Dict[int, Dict[int, int]] = {}

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Background tasks
        self._ping_task: Optional[asyncio.Task] = None
        self._redis_listener_task: Optional[asyncio.Task] = None
        self._command_listener_task: Optional[asyncio.Task] = None

        # Redis pub/sub for multi-instance support
        self._use_redis = use_redis and redis_url is not None
        self._redis_client: Optional[redis.Redis] = None
        self._redis_pubsub: Optional[redis.client.PubSub] = None
        self._command_pubsub: Optional[redis.client.PubSub] = None  # Separate pubsub for commands

        if self._use_redis and redis_url:
            try:
                self._redis_client = redis.from_url(redis_url, decode_responses=True)
                self._redis_pubsub = self._redis_client.pubsub()
                self._command_pubsub = self._redis_client.pubsub()  # Separate pubsub connection
                logger.info(f"Redis pub/sub enabled for WebSocket broadcasting")
            except Exception as e:
                logger.error(f"Failed to initialize Redis pub/sub: {e}")
                self._use_redis = False
        else:
            logger.info("Using in-memory WebSocket broadcasting (single instance mode)")
        
    async def connect_device(
        self, 
        websocket: WebSocket, 
        device_id: int, 
        organization_id: int
    ):
        """
        Connect a device WebSocket
        
        Args:
            websocket: WebSocket connection
            device_id: Device ID
            organization_id: Organization ID
        """
        await websocket.accept()
        
        async with self._lock:
            # Store device connection
            self._device_connections[device_id] = {
                "websocket": websocket,
                "org_id": organization_id,
                "last_ping": datetime.now(timezone.utc),
                "connected_at": datetime.now(timezone.utc)
            }
            
            # Add to organization room
            if organization_id not in self._organization_rooms:
                self._organization_rooms[organization_id] = {
                    "device_ids": set(),
                    "admin_ids": set()
                }
            self._organization_rooms[organization_id]["device_ids"].add(device_id)
            
        logger.info(f"Device {device_id} connected (org: {organization_id})")
        
        # Notify admins of device online
        await self.broadcast_to_organization(
            organization_id,
            WebSocketEventType.DEVICE_ONLINE,
            {"device_id": device_id, "recorded_at": datetime.now(timezone.utc).isoformat()}
        )
    
    async def connect_admin(
        self,
        websocket: WebSocket,
        user_id: int,
        organization_id: int,
        permissions: List[str] = None
    ):
        """
        Connect an admin user WebSocket

        Args:
            websocket: WebSocket connection (already accepted by route)
            user_id: User ID
            organization_id: Organization ID
            permissions: User permissions list
        """
        # Note: websocket.accept() already called in route for authentication

        async with self._lock:
            # Store admin connection
            self._admin_connections[user_id] = {
                "websocket": websocket,
                "org_id": organization_id,
                "permissions": permissions or [],
                "last_ping": datetime.now(timezone.utc),
                "connected_at": datetime.now(timezone.utc)
            }
            
            # Add to organization room
            if organization_id not in self._organization_rooms:
                self._organization_rooms[organization_id] = {
                    "device_ids": set(),
                    "admin_ids": set()
                }
            self._organization_rooms[organization_id]["admin_ids"].add(user_id)
            
        logger.info(f"Admin user {user_id} connected (org: {organization_id})")
    
    async def disconnect_device(self, device_id: int):
        """Disconnect a device WebSocket"""
        async with self._lock:
            if device_id in self._device_connections:
                conn_info = self._device_connections[device_id]
                org_id = conn_info["org_id"]
                
                # Remove from connections
                del self._device_connections[device_id]
                
                # Remove from organization room
                if org_id in self._organization_rooms:
                    self._organization_rooms[org_id]["device_ids"].discard(device_id)
                
        logger.info(f"Device {device_id} disconnected")
        
        # Notify admins of device offline
        if 'org_id' in locals():
            await self.broadcast_to_organization(
                org_id,
                WebSocketEventType.DEVICE_OFFLINE,
                {"device_id": device_id, "recorded_at": datetime.now(timezone.utc).isoformat()}
            )
    
    async def disconnect_admin(self, user_id: int):
        """Disconnect an admin user WebSocket"""
        async with self._lock:
            if user_id in self._admin_connections:
                conn_info = self._admin_connections[user_id]
                org_id = conn_info["org_id"]
                
                # Remove from connections
                del self._admin_connections[user_id]
                
                # Remove from organization room
                if org_id in self._organization_rooms:
                    self._organization_rooms[org_id]["admin_ids"].discard(user_id)
                
        logger.info(f"Admin user {user_id} disconnected")
    
    def _convert_event_type_to_frontend(self, event_type: WebSocketEventType) -> str:
        """
        Convert backend event type (dot notation) to frontend format (colon notation)
        e.g., 'content.thumbnail_ready' -> 'content:thumbnail_ready'
        """
        return event_type.value.replace('.', ':')

    async def send_to_device(
        self,
        device_id: int,
        event_type: WebSocketEventType,
        data: Any
    ) -> bool:
        """
        Send message to specific device

        Args:
            device_id: Target device ID
            event_type: Event type
            data: Event data

        Returns:
            True if sent successfully
        """
        if device_id not in self._device_connections:
            return False

        conn_info = self._device_connections[device_id]
        websocket = conn_info["websocket"]

        message = {
            "type": self._convert_event_type_to_frontend(event_type),
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send to device {device_id}: {e}")
            # Remove failed connection
            await self.disconnect_device(device_id)
            return False
    
    async def send_to_admin(
        self,
        user_id: int,
        event_type: WebSocketEventType,
        data: Any
    ) -> bool:
        """Send message to specific admin user"""
        if user_id not in self._admin_connections:
            return False

        conn_info = self._admin_connections[user_id]
        websocket = conn_info["websocket"]

        message = {
            "type": self._convert_event_type_to_frontend(event_type),
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send to admin {user_id}: {e}")
            # Remove failed connection
            await self.disconnect_admin(user_id)
            return False
    
    async def broadcast_to_organization(
        self,
        organization_id: int,
        event_type: WebSocketEventType,
        data: Any
    ):
        """
        Broadcast message to all connections in an organization
        Uses Redis pub/sub if enabled for multi-instance support

        Args:
            organization_id: Target organization
            event_type: Event type
            data: Event data
        """
        # If Redis is enabled, publish to Redis (all instances will receive)
        if self._use_redis:
            await self._publish_to_redis(organization_id, event_type, data)
            # Also broadcast locally for immediate delivery
            await self._broadcast_local(organization_id, event_type, data)
        else:
            # In-memory only - broadcast to local connections
            await self._broadcast_local(organization_id, event_type, data)
    
    async def broadcast_to_devices(
        self,
        device_ids: List[int],
        event_type: WebSocketEventType,
        data: Any
    ):
        """Broadcast message to specific devices"""
        tasks = []
        for device_id in device_ids:
            tasks.append(self.send_to_device(device_id, event_type, data))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def handle_device_message(self, device_id: int, message: dict):
        """Handle incoming message from device"""
        # Update last ping time
        if device_id in self._device_connections:
            self._device_connections[device_id]["last_ping"] = datetime.now(timezone.utc)
        
        # Handle different message types
        message_type = message.get("type")
        
        if message_type == "ping":
            # Respond with pong
            await self.send_to_device(device_id, WebSocketEventType.SYSTEM_NOTIFICATION, {"type": "pong"})
        
        elif message_type == "status_update":
            # Broadcast device status to admins
            org_id = self._device_connections[device_id]["org_id"]
            await self.broadcast_to_organization(
                org_id,
                WebSocketEventType.DEVICE_UPDATED,
                {
                    "device_id": device_id,
                    "status": message.get("status"),
                    "data": message.get("data")
                }
            )
    
    async def handle_admin_message(self, user_id: int, message: dict):
        """Handle incoming message from admin"""
        # Update last ping time
        if user_id in self._admin_connections:
            self._admin_connections[user_id]["last_ping"] = datetime.now(timezone.utc)
        
        # Handle different message types
        message_type = message.get("type")
        
        if message_type == "ping":
            # Respond with pong
            await self.send_to_admin(user_id, WebSocketEventType.SYSTEM_NOTIFICATION, {"type": "pong"})
    
    async def start_ping_task(self):
        """Start background task to ping connections"""
        if self._ping_task is None:
            self._ping_task = asyncio.create_task(self._ping_connections())
    
    async def stop_ping_task(self):
        """Stop ping background task"""
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
            self._ping_task = None
    
    async def _ping_connections(self):
        """Background task to ping all connections periodically"""
        while True:
            try:
                # Ping every 30 seconds
                await asyncio.sleep(30)
                
                # Ping all device connections
                for device_id in list(self._device_connections.keys()):
                    await self.send_to_device(
                        device_id, 
                        WebSocketEventType.SYSTEM_NOTIFICATION, 
                        {"type": "ping"}
                    )
                
                # Ping all admin connections
                for user_id in list(self._admin_connections.keys()):
                    await self.send_to_admin(
                        user_id,
                        WebSocketEventType.SYSTEM_NOTIFICATION,
                        {"type": "ping"}
                    )
                    
            except Exception as e:
                logger.error(f"Error in ping task: {e}")
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_devices": len(self._device_connections),
            "total_admins": len(self._admin_connections),
            "total_player_controls": len(self._player_control_connections),
            "organizations": len(self._organization_rooms),
            "devices_by_org": {
                org_id: len(room["device_ids"])
                for org_id, room in self._organization_rooms.items()
            },
            "admins_by_org": {
                org_id: len(room["admin_ids"])
                for org_id, room in self._organization_rooms.items()
            },
            "console_subscriptions": {
                device_id: len(admins)
                for device_id, admins in self._console_subscriptions.items()
            }
        }

    # ========== PLAYER CONTROL WEBSOCKET METHODS ==========

    async def register_player_control(self, device_id: int, websocket: WebSocket):
        """
        Register a player's control WebSocket connection
        This is used for bidirectional communication with the player

        Args:
            device_id: Device ID
            websocket: WebSocket connection from player
        """
        async with self._lock:
            self._player_control_connections[device_id] = websocket
            logger.info(f"Player control WebSocket registered for device {device_id}")

    async def unregister_player_control(self, device_id: int):
        """
        Unregister a player's control WebSocket connection

        Args:
            device_id: Device ID
        """
        async with self._lock:
            if device_id in self._player_control_connections:
                del self._player_control_connections[device_id]
                logger.info(f"Player control WebSocket unregistered for device {device_id}")

    async def send_command_to_player(self, device_id: int, command: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a control command to the player via WebSocket
        Used for console streaming control (start_streaming, stop_streaming)

        Args:
            device_id: Target device ID
            command: Command name (e.g., "start_streaming", "stop_streaming")
            data: Optional additional command data

        Returns:
            True if command was sent successfully, False otherwise
        """
        # Try direct WebSocket first (if player is connected)
        if device_id in self._player_control_connections:
            websocket = self._player_control_connections[device_id]
            message = {
                "command": command,
                "data": data or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            try:
                await websocket.send_json(message)
                logger.info(f"Sent command '{command}' to player {device_id} via WebSocket")
                return True
            except Exception as e:
                logger.error(f"Failed to send command to player {device_id} via WebSocket: {e}")
                # Remove failed connection
                await self.unregister_player_control(device_id)

        # Fallback to Redis pub/sub (for multi-instance support or reconnection)
        if self._use_redis:
            channel = f"command:{device_id}"
            message = {
                "command": command,
                "data": data or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            try:
                await self._redis_client.publish(channel, json.dumps(message))
                logger.info(f"Published command '{command}' to Redis channel {channel}")
                return True
            except Exception as e:
                logger.error(f"Failed to publish command to Redis: {e}")
                return False

        logger.warning(f"Unable to send command to player {device_id} - no WebSocket or Redis")
        return False

    async def get_console_subscriber_count(self, device_id: int, organization_id: int) -> int:
        """
        Get the number of admins currently subscribed to a device's console logs
        Used to determine when to start/stop player streaming

        Args:
            device_id: Device ID
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            Number of subscribed admins from the specified organization
        """
        async with self._lock:
            if device_id not in self._console_subscriber_counts:
                return 0
            return self._console_subscriber_counts[device_id].get(organization_id, 0)

    # ========== CONSOLE LOG STREAMING ==========

    async def subscribe_to_console(
        self,
        device_id: int,
        admin_user_id: int,
        organization_id: int,
        websocket: WebSocket
    ) -> bool:
        """
        Subscribe admin to device console logs (in-memory tracking)
        Sends start_streaming command to player if this is the first subscriber

        Args:
            device_id: Device ID to subscribe to
            admin_user_id: Admin user ID
            organization_id: Organization ID for multi-tenant isolation
            websocket: WebSocket connection for console streaming

        Returns:
            True if subscribed successfully
        """
        is_first_subscriber = False

        async with self._lock:
            # Track console subscriptions
            if device_id not in self._console_subscriptions:
                self._console_subscriptions[device_id] = {}

            # Store WebSocket connection with user_id
            self._console_subscriptions[device_id][admin_user_id] = websocket

            # Track subscriber counts per organization
            if device_id not in self._console_subscriber_counts:
                self._console_subscriber_counts[device_id] = {}

            if organization_id not in self._console_subscriber_counts[device_id]:
                self._console_subscriber_counts[device_id][organization_id] = 0

            # Check if this is the first subscriber for this organization
            if self._console_subscriber_counts[device_id][organization_id] == 0:
                is_first_subscriber = True

            # Increment subscriber count
            self._console_subscriber_counts[device_id][organization_id] += 1

            total_subs = len(self._console_subscriptions[device_id])
            org_subs = self._console_subscriber_counts[device_id][organization_id]

            logger.info(
                f"Admin {admin_user_id} subscribed to device {device_id} console "
                f"(org: {organization_id}, total: {total_subs}, org_total: {org_subs})"
            )

        # Send start_streaming command if this is the first subscriber
        if is_first_subscriber:
            logger.info(f"First subscriber for device {device_id} - sending start_streaming command")
            await self.send_command_to_player(device_id, "start_streaming", {"organization_id": organization_id})

        return True

    async def unsubscribe_from_console(self, device_id: int, admin_user_id: int, organization_id: int):
        """
        Unsubscribe admin from device console logs
        Sends stop_streaming command to player if this is the last subscriber

        Args:
            device_id: Device ID to unsubscribe from
            admin_user_id: Admin user ID
            organization_id: Organization ID for multi-tenant isolation
        """
        is_last_subscriber = False

        async with self._lock:
            if device_id in self._console_subscriptions:
                if admin_user_id in self._console_subscriptions[device_id]:
                    del self._console_subscriptions[device_id][admin_user_id]

                # Clean up empty subscriptions
                if not self._console_subscriptions[device_id]:
                    del self._console_subscriptions[device_id]

            # Decrement subscriber count
            if device_id in self._console_subscriber_counts:
                if organization_id in self._console_subscriber_counts[device_id]:
                    self._console_subscriber_counts[device_id][organization_id] -= 1

                    # Check if this was the last subscriber for this organization
                    if self._console_subscriber_counts[device_id][organization_id] <= 0:
                        is_last_subscriber = True
                        del self._console_subscriber_counts[device_id][organization_id]

                    # Clean up empty counts
                    if not self._console_subscriber_counts[device_id]:
                        del self._console_subscriber_counts[device_id]

            logger.info(f"Admin {admin_user_id} unsubscribed from device {device_id} console logs (org: {organization_id})")

        # Send stop_streaming command if this was the last subscriber
        if is_last_subscriber:
            logger.info(f"Last subscriber for device {device_id} - sending stop_streaming command")
            await self.send_command_to_player(device_id, "stop_streaming", {"organization_id": organization_id})

    async def broadcast_console_log(self, device_id: int, organization_id: int, logs: List[Dict[str, Any]]):
        """
        Broadcast console logs from device to subscribed admins via Redis pub/sub

        Args:
            device_id: Source device ID
            organization_id: Organization ID for multi-tenant routing
            logs: List of console log entries
        """
        # Prepare message
        message = {
            "event": WebSocketEventType.DEVICE_CONSOLE_LOG.value,
            "data": {
                "device_id": device_id,
                "logs": logs
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if self._use_redis:
            # Use Redis pub/sub for multi-worker support
            # Channel format: console:{device_id}:{org_id}
            channel = f"console:{device_id}:{organization_id}"
            try:
                print(f"[WSManager] Publishing {len(logs)} console logs to Redis channel: {channel}")
                await self._redis_client.publish(channel, json.dumps(message))
                logger.info(f"Published {len(logs)} console logs to Redis channel {channel}")
            except Exception as e:
                print(f"[WSManager] ❌ Failed to publish to Redis: {e}")
                logger.error(f"Failed to publish console logs to Redis: {e}")
        else:
            # Fallback to in-memory (single worker only)
            subscribed_admins = self._console_subscriptions.get(device_id, {})

            print(f"[WSManager] Broadcasting {len(logs)} console logs from device {device_id} to {len(subscribed_admins)} in-memory subscribers")

            if not subscribed_admins:
                print(f"[WSManager] ⚠️ No admins subscribed to device {device_id} console logs - logs discarded")
                logger.info(f"No admins subscribed to device {device_id} console logs - logs discarded")
                return

            # Send to subscribed admins via their console WebSocket connections
            failed_admins = []
            sent_count = 0
            for user_id, websocket in subscribed_admins.items():
                try:
                    print(f"[WSManager] Sending {len(logs)} logs to admin {user_id}...")
                    await websocket.send_json(message)
                    sent_count += 1
                    print(f"[WSManager] ✅ Sent to admin {user_id}")
                except Exception as e:
                    print(f"[WSManager] ❌ Failed to send to admin {user_id}: {e}")
                    logger.error(f"Failed to send console logs to admin {user_id}: {e}")
                    failed_admins.append(user_id)

            # Clean up failed subscriptions
            if failed_admins:
                async with self._lock:
                    for user_id in failed_admins:
                        if user_id in self._console_subscriptions[device_id]:
                            del self._console_subscriptions[device_id][user_id]

            logger.info(f"Broadcasted {len(logs)} console logs from device {device_id} to {sent_count}/{len(subscribed_admins)} admins (org: {organization_id})")

    # ========== REDIS PUB/SUB METHODS ==========

    async def start_redis_listener(self):
        """Start Redis pub/sub listener tasks"""
        if self._use_redis and not self._redis_listener_task:
            self._redis_listener_task = asyncio.create_task(self._redis_listener())
            logger.info("Redis pub/sub listener started")

        if self._use_redis and not self._command_listener_task:
            self._command_listener_task = asyncio.create_task(self._command_listener())
            logger.info("Redis command listener started")

    async def stop_redis_listener(self):
        """Stop Redis pub/sub listener tasks"""
        if self._redis_listener_task:
            self._redis_listener_task.cancel()
            try:
                await self._redis_listener_task
            except asyncio.CancelledError:
                pass
            self._redis_listener_task = None
            logger.info("Redis pub/sub listener stopped")

        if self._command_listener_task:
            self._command_listener_task.cancel()
            try:
                await self._command_listener_task
            except asyncio.CancelledError:
                pass
            self._command_listener_task = None
            logger.info("Redis command listener stopped")

    def _convert_string_event_to_frontend(self, event_type_str: str) -> str:
        """
        Convert event type string to frontend format (colon notation)
        Handles both dot notation from enums and direct strings from Celery
        e.g., 'content.thumbnail_ready' -> 'content:thumbnail_ready'
        """
        return event_type_str.replace('.', ':')

    async def _redis_listener(self):
        """Background task to listen for Redis pub/sub messages"""
        if not self._redis_pubsub:
            return

        try:
            # Subscribe to organization channels AND console channels
            await self._redis_pubsub.psubscribe("org:*")
            await self._redis_pubsub.psubscribe("console:*")
            print("[WSManager] Subscribed to Redis channels: org:* and console:*")

            async for message in self._redis_pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        # Parse channel and data
                        channel = message["channel"]
                        data = json.loads(message["data"])

                        # Check if this is a console log message
                        if channel.startswith("console:"):
                            # Console channel format: console:{device_id}:{org_id}
                            parts = channel.split(":")
                            if len(parts) == 3:
                                device_id = int(parts[1])
                                org_id = int(parts[2])

                                # Broadcast to local console subscribers only
                                print(f"[WSManager] Received console logs from Redis for device {device_id}")
                                await self._broadcast_console_local(device_id, data)
                        else:
                            # Regular organization message
                            # Handle both 'event' (from _publish_to_redis) and 'type' (from Celery)
                            event_type_str = data.get("event") or data.get("type")
                            if not event_type_str:
                                logger.warning(f"Redis message missing event/type key: {data}")
                                continue

                            event_data = data.get("data", {})

                            # Extract org_id from channel (format: org:123)
                            org_id = int(channel.split(":")[1])

                            # Convert to frontend format and broadcast directly
                            frontend_event_type = self._convert_string_event_to_frontend(event_type_str)
                            await self._broadcast_local_raw(org_id, frontend_event_type, event_data)

                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")

        except asyncio.CancelledError:
            await self._redis_pubsub.punsubscribe("org:*")
            await self._redis_pubsub.punsubscribe("console:*")
            raise
        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    async def _command_listener(self):
        """
        Background task to listen for Redis command channel messages
        Forwards commands from Redis to player control WebSocket connections
        """
        if not self._command_pubsub:
            return

        try:
            # Subscribe to all command channels: command:*
            await self._command_pubsub.psubscribe("command:*")
            logger.info("Subscribed to Redis command channels: command:*")

            async for message in self._command_pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        # Parse channel and data
                        channel = message["channel"]
                        data = json.loads(message["data"])

                        # Extract device_id from channel (format: command:{device_id})
                        parts = channel.split(":")
                        if len(parts) == 2:
                            device_id = int(parts[1])
                            command = data.get("command")
                            command_data = data.get("data", {})

                            logger.info(f"Received command '{command}' from Redis for device {device_id}")

                            # Forward command to player if connected locally
                            if device_id in self._player_control_connections:
                                websocket = self._player_control_connections[device_id]
                                try:
                                    await websocket.send_json({
                                        "command": command,
                                        "data": command_data,
                                        "timestamp": data.get("timestamp")
                                    })
                                    logger.info(f"Forwarded command '{command}' to player {device_id}")
                                except Exception as e:
                                    logger.error(f"Failed to forward command to player {device_id}: {e}")
                                    # Remove failed connection
                                    await self.unregister_player_control(device_id)
                            else:
                                logger.debug(f"Player {device_id} not connected to this instance - command handled by other instance")

                    except Exception as e:
                        logger.error(f"Error processing command message: {e}")

        except asyncio.CancelledError:
            await self._command_pubsub.punsubscribe("command:*")
            raise
        except Exception as e:
            logger.error(f"Command listener error: {e}")

    async def _broadcast_local(self, organization_id: int, event_type: WebSocketEventType, data: Any):
        """Broadcast to local WebSocket connections only (called by Redis listener)"""
        if organization_id not in self._organization_rooms:
            return

        room = self._organization_rooms[organization_id]

        # Send to local devices
        for device_id in room["device_ids"]:
            if device_id in self._device_connections:
                await self.send_to_device(device_id, event_type, data)

        # Send to local admins
        for user_id in room["admin_ids"]:
            if user_id in self._admin_connections:
                await self.send_to_admin(user_id, event_type, data)

    async def _broadcast_local_raw(self, organization_id: int, event_type_str: str, data: Any):
        """
        Broadcast to local WebSocket connections with raw string event type.
        Used for messages from Redis/Celery that are already in frontend format.
        """
        if organization_id not in self._organization_rooms:
            return

        room = self._organization_rooms[organization_id]

        message = {
            "type": event_type_str,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Send to local devices
        for device_id in list(room["device_ids"]):
            if device_id in self._device_connections:
                try:
                    websocket = self._device_connections[device_id]["websocket"]
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to device {device_id}: {e}")
                    await self.disconnect_device(device_id)

        # Send to local admins
        for user_id in list(room["admin_ids"]):
            if user_id in self._admin_connections:
                try:
                    websocket = self._admin_connections[user_id]["websocket"]
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to admin {user_id}: {e}")
                    await self.disconnect_admin(user_id)

    async def _broadcast_console_local(self, device_id: int, message: dict):
        """
        Broadcast console logs to local WebSocket subscribers only (called by Redis listener)

        Args:
            device_id: Device ID
            message: Complete message dict with event, data, timestamp
        """
        subscribed_admins = self._console_subscriptions.get(device_id, {})

        if not subscribed_admins:
            print(f"[WSManager] No local subscribers for device {device_id} console")
            return

        print(f"[WSManager] Broadcasting console logs to {len(subscribed_admins)} local subscribers")
        print(f"[WSManager] Message to send: {message}")  # DEBUG

        failed_admins = []
        sent_count = 0
        for user_id, websocket in subscribed_admins.items():
            try:
                print(f"[WSManager] Sending to admin {user_id}...")  # DEBUG
                await websocket.send_json(message)
                sent_count += 1
                print(f"[WSManager] ✅ Sent console logs to admin {user_id}")
            except Exception as e:
                print(f"[WSManager] ❌ Failed to send to admin {user_id}: {e}")
                logger.error(f"Failed to send console logs to admin {user_id}: {e}")
                failed_admins.append(user_id)

        # Clean up failed subscriptions
        if failed_admins:
            async with self._lock:
                for user_id in failed_admins:
                    if user_id in self._console_subscriptions[device_id]:
                        del self._console_subscriptions[device_id][user_id]

        logger.info(f"Sent console logs to {sent_count}/{len(subscribed_admins)} local subscribers for device {device_id}")

    async def _publish_to_redis(self, organization_id: int, event_type: WebSocketEventType, data: Any):
        """Publish message to Redis for multi-instance broadcasting"""
        if not self._use_redis or not self._redis_client:
            return

        try:
            channel = f"org:{organization_id}"
            message = {
                "event": event_type.value,
                "data": data,
                "recorded_at": datetime.now(timezone.utc).isoformat()
            }

            await self._redis_client.publish(channel, json.dumps(message))
            logger.debug(f"Published to Redis channel {channel}: {event_type.value}")

        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")


# Global WebSocket manager instance (will be initialized in main.py with settings)
websocket_manager: Optional[ConnectionManager] = None


def init_websocket_manager(redis_url: Optional[str] = None, use_redis: bool = True):
    """Initialize global WebSocket manager with Redis support"""
    global websocket_manager
    websocket_manager = ConnectionManager(redis_url=redis_url, use_redis=use_redis)
    return websocket_manager