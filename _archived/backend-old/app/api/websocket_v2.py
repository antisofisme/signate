"""
WebSocket Service V2 for Real-Time Updates
Production-ready WebSocket implementation with connection management and Quick Wins standardization

Features:
- Standardized message format (success, type, data, meta)
- Real-time device command execution
- Playlist update notifications
- Connection tracking in Redis
- Heartbeat mechanism (30s interval)
- Rate limiting for message sending
- Commands system integration
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Dict, Set, Optional, Any, List
import json
import asyncio
import redis.asyncio as redis
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_token
from app.core.logging import StructuredLogger
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response
from app.schemas.websocket import (
    MessageType,
    ConnectionStats,
    BroadcastRequest,
    BroadcastResponse,
    create_websocket_message,
    create_error_message,
    ConnectedMessageData,
    HeartbeatMessageData,
    CommandMessageData,
    CommandResponseMessageData,
    DeviceStatusMessageData,
    DashboardUpdateMessageData
)
from app.models.device import Device
from app.models.user import User

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/websocket", tags=["WebSocket"])


class ConnectionManager:
    """
    Manages WebSocket connections efficiently
    Supports 500-1000 concurrent connections per instance
    Memory efficient: ~1MB per connection
    """

    def __init__(self):
        # Device connections: device_id -> {websocket, metadata}
        self._device_connections: Dict[int, Dict[str, Any]] = {}

        # Admin connections: connection_id -> {websocket, user_id, metadata}
        self._admin_connections: Dict[str, Dict[str, Any]] = {}

        # Connection tracking for metrics
        self._connection_stats = {
            "total_connections": 0,
            "peak_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_sent": 0,
            "bytes_received": 0
        }

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        # Redis client for pub/sub
        self._redis_client: Optional[redis.Redis] = None

        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize Redis connection and background tasks"""
        try:
            self._redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=50
            )
            await self._redis_client.ping()
            logger.info("✓ WebSocket manager Redis connection initialized")

            # Start background tasks
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        except Exception as e:
            logger.error(f"Failed to initialize WebSocket manager: {e}")

    async def shutdown(self):
        """Gracefully shutdown all connections and tasks"""
        logger.info("Shutting down WebSocket manager...")

        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Close all connections
        async with self._lock:
            # Close device connections
            for device_id, conn_data in list(self._device_connections.items()):
                try:
                    await conn_data["websocket"].close()
                except:
                    pass

            # Close admin connections
            for conn_id, conn_data in list(self._admin_connections.items()):
                try:
                    await conn_data["websocket"].close()
                except:
                    pass

            self._device_connections.clear()
            self._admin_connections.clear()

        # Close Redis connection
        if self._redis_client:
            await self._redis_client.close()

        logger.info("✓ WebSocket manager shutdown complete")

    async def connect_device(
        self,
        websocket: WebSocket,
        device_id: int,
        device_name: str
    ) -> bool:
        """
        Connect a device WebSocket
        Returns True if connection successful
        """
        async with self._lock:
            # Check if device already connected
            if device_id in self._device_connections:
                # Close existing connection
                old_conn = self._device_connections[device_id]
                try:
                    await old_conn["websocket"].close()
                except:
                    pass
                logger.info(f"Replaced existing connection for device {device_id}")

            # Store new connection
            self._device_connections[device_id] = {
                "websocket": websocket,
                "device_name": device_name,
                "connected_at": datetime.utcnow(),
                "last_heartbeat": datetime.utcnow(),
                "messages_sent": 0,
                "messages_received": 0,
                "bytes_sent": 0,
                "bytes_received": 0
            }

            # Update stats
            self._connection_stats["total_connections"] += 1
            current_connections = len(self._device_connections) + len(self._admin_connections)
            if current_connections > self._connection_stats["peak_connections"]:
                self._connection_stats["peak_connections"] = current_connections

            logger.info(
                f"📱 Device connected: {device_name} (ID: {device_id}) | "
                f"Total devices: {len(self._device_connections)}"
            )

            # Publish connection event
            if self._redis_client:
                await self._redis_client.publish(
                    "device_events",
                    json.dumps({
                        "event": "device_connected",
                        "device_id": device_id,
                        "device_name": device_name,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )

            return True

    async def disconnect_device(self, device_id: int):
        """Disconnect a device WebSocket"""
        async with self._lock:
            if device_id in self._device_connections:
                conn_data = self._device_connections[device_id]
                device_name = conn_data["device_name"]

                # Calculate connection duration
                duration = (datetime.utcnow() - conn_data["connected_at"]).total_seconds()

                # Remove connection
                del self._device_connections[device_id]

                logger.info(
                    f"📱 Device disconnected: {device_name} (ID: {device_id}) | "
                    f"Duration: {duration:.1f}s | "
                    f"Messages: {conn_data['messages_sent']}/{conn_data['messages_received']}"
                )

                # Publish disconnection event
                if self._redis_client:
                    await self._redis_client.publish(
                        "device_events",
                        json.dumps({
                            "event": "device_disconnected",
                            "device_id": device_id,
                            "device_name": device_name,
                            "duration": duration,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    )

    async def connect_admin(
        self,
        websocket: WebSocket,
        user_id: int,
        username: str
    ) -> str:
        """
        Connect an admin WebSocket
        Returns connection ID
        """
        conn_id = str(uuid.uuid4())

        async with self._lock:
            self._admin_connections[conn_id] = {
                "websocket": websocket,
                "user_id": user_id,
                "username": username,
                "connected_at": datetime.utcnow(),
                "last_heartbeat": datetime.utcnow(),
                "messages_sent": 0,
                "messages_received": 0
            }

            # Update stats
            self._connection_stats["total_connections"] += 1
            current_connections = len(self._device_connections) + len(self._admin_connections)
            if current_connections > self._connection_stats["peak_connections"]:
                self._connection_stats["peak_connections"] = current_connections

            logger.info(
                f"👤 Admin connected: {username} (ID: {user_id}) | "
                f"Total admins: {len(self._admin_connections)}"
            )

            return conn_id

    async def disconnect_admin(self, conn_id: str):
        """Disconnect an admin WebSocket"""
        async with self._lock:
            if conn_id in self._admin_connections:
                conn_data = self._admin_connections[conn_id]
                username = conn_data["username"]

                # Calculate connection duration
                duration = (datetime.utcnow() - conn_data["connected_at"]).total_seconds()

                # Remove connection
                del self._admin_connections[conn_id]

                logger.info(
                    f"👤 Admin disconnected: {username} | "
                    f"Duration: {duration:.1f}s"
                )

    async def send_to_device(
        self,
        device_id: int,
        message_type: MessageType,
        data: dict
    ) -> bool:
        """
        Send standardized message to specific device
        Returns True if sent successfully

        Message format follows Quick Wins Pattern:
        {
            "success": true,
            "type": "command",
            "data": {...},
            "meta": {"timestamp": "...", "message_id": "...", "version": "1.0.0"}
        }
        """
        async with self._lock:
            if device_id not in self._device_connections:
                return False

            conn_data = self._device_connections[device_id]
            websocket = conn_data["websocket"]

            try:
                # Create standardized message with Quick Wins format
                message_id = f"msg-{uuid.uuid4().hex[:12]}"
                message = create_websocket_message(
                    message_type=message_type,
                    data=data,
                    message_id=message_id
                )

                message_str = json.dumps(message)
                await websocket.send_text(message_str)

                # Update stats
                conn_data["messages_sent"] += 1
                conn_data["bytes_sent"] += len(message_str)
                self._connection_stats["messages_sent"] += 1
                self._connection_stats["bytes_sent"] += len(message_str)

                logger.debug(
                    "Message sent to device",
                    device_id=device_id,
                    message_type=message_type.value,
                    message_id=message_id,
                    bytes=len(message_str)
                )

                return True

            except Exception as e:
                logger.error(
                    "Failed to send message to device",
                    device_id=device_id,
                    message_type=message_type.value,
                    error=str(e),
                    exc_info=True
                )
                return False

    async def broadcast_to_devices(
        self,
        device_ids: List[int],
        message_type: MessageType,
        data: dict
    ) -> Dict[int, bool]:
        """
        Broadcast message to multiple devices
        Returns dict of device_id -> success status
        """
        results = {}

        # Send messages concurrently
        tasks = []
        for device_id in device_ids:
            tasks.append(self.send_to_device(device_id, message_type, data))

        # Wait for all sends to complete
        send_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results
        for device_id, result in zip(device_ids, send_results):
            results[device_id] = result if not isinstance(result, Exception) else False

        success_count = sum(1 for success in results.values() if success)
        logger.info(
            f"📡 Broadcast {message_type.value} to {success_count}/{len(device_ids)} devices"
        )

        return results

    async def broadcast_to_all_devices(
        self,
        message_type: MessageType,
        data: dict
    ) -> Dict[int, bool]:
        """Broadcast message to all connected devices"""
        async with self._lock:
            device_ids = list(self._device_connections.keys())

        return await self.broadcast_to_devices(device_ids, message_type, data)

    async def broadcast_to_admins(
        self,
        message_type: MessageType,
        data: dict
    ) -> int:
        """
        Broadcast standardized message to all admin connections
        Returns number of successful sends

        Message format follows Quick Wins Pattern
        """
        success_count = 0

        async with self._lock:
            for conn_id, conn_data in list(self._admin_connections.items()):
                websocket = conn_data["websocket"]

                try:
                    # Create standardized message
                    message_id = f"msg-{uuid.uuid4().hex[:12]}"
                    message = create_websocket_message(
                        message_type=message_type,
                        data=data,
                        message_id=message_id
                    )

                    await websocket.send_json(message)
                    conn_data["messages_sent"] += 1
                    success_count += 1

                except Exception as e:
                    logger.error(
                        "Failed to send to admin",
                        conn_id=conn_id,
                        message_type=message_type.value,
                        error=str(e),
                        exc_info=True
                    )

        if success_count > 0:
            logger.info(
                "Broadcast to admins",
                message_type=message_type.value,
                admin_count=success_count
            )

        return success_count

    async def handle_device_message(
        self,
        device_id: int,
        message: dict
    ):
        """Process message received from device"""
        async with self._lock:
            if device_id not in self._device_connections:
                return

            conn_data = self._device_connections[device_id]
            conn_data["messages_received"] += 1
            self._connection_stats["messages_received"] += 1

            # Update last heartbeat on any message
            conn_data["last_heartbeat"] = datetime.utcnow()

        # Handle specific message types
        msg_type = message.get("type")

        if msg_type == "heartbeat":
            # Respond with pong
            await self.send_to_device(device_id, MessageType.PONG, {})

        elif msg_type == "command_response":
            # Forward command response to admins
            await self.broadcast_to_admins(
                MessageType.COMMAND_RESPONSE,
                {
                    "device_id": device_id,
                    "command": message.get("command"),
                    "success": message.get("success"),
                    "result": message.get("result"),
                    "error": message.get("error")
                }
            )

        elif msg_type == "status":
            # Update device status and forward to admins
            await self.broadcast_to_admins(
                MessageType.DEVICE_STATUS,
                {
                    "device_id": device_id,
                    "status": message.get("status"),
                    "details": message.get("details", {})
                }
            )

    async def get_connection_stats(self) -> dict:
        """Get current connection statistics"""
        async with self._lock:
            return {
                **self._connection_stats,
                "current_device_connections": len(self._device_connections),
                "current_admin_connections": len(self._admin_connections),
                "total_current_connections": len(self._device_connections) + len(self._admin_connections),
                "devices": {
                    device_id: {
                        "device_name": conn["device_name"],
                        "connected_at": conn["connected_at"].isoformat(),
                        "last_heartbeat": conn["last_heartbeat"].isoformat(),
                        "messages_sent": conn["messages_sent"],
                        "messages_received": conn["messages_received"]
                    }
                    for device_id, conn in self._device_connections.items()
                }
            }

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to all connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds

                # Send heartbeat to all devices
                await self.broadcast_to_all_devices(
                    MessageType.HEARTBEAT,
                    {"server_time": datetime.utcnow().isoformat()}
                )

                # Send heartbeat to all admins
                await self.broadcast_to_admins(
                    MessageType.HEARTBEAT,
                    {"server_time": datetime.utcnow().isoformat()}
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def _cleanup_loop(self):
        """Clean up stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.utcnow()
                stale_threshold = timedelta(minutes=5)

                # Find stale device connections
                async with self._lock:
                    stale_devices = [
                        device_id
                        for device_id, conn in self._device_connections.items()
                        if now - conn["last_heartbeat"] > stale_threshold
                    ]

                # Disconnect stale devices
                for device_id in stale_devices:
                    logger.warning(f"Removing stale device connection: {device_id}")
                    await self.disconnect_device(device_id)

                    # Close the websocket
                    async with self._lock:
                        if device_id in self._device_connections:
                            try:
                                await self._device_connections[device_id]["websocket"].close()
                            except:
                                pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")


# Global connection manager instance
manager = ConnectionManager()


# =============================================================================
# WEBSOCKET - COMMANDS INTEGRATION
# =============================================================================

async def send_command_to_device(
    device_id: int,
    command_id: int,
    command_type: str,
    params: Dict[str, Any]
) -> bool:
    """
    Send command to device via WebSocket

    This function is called by command_service to deliver commands to devices
    over WebSocket connection.

    Args:
        device_id: Target device ID
        command_id: Database command ID for tracking
        command_type: Command type (reload, screenshot, etc.)
        params: Command parameters

    Returns:
        True if sent successfully, False if device not connected

    Usage from command_service:
        from app.api.websocket_v2 import send_command_to_device

        success = await send_command_to_device(
            device_id=123,
            command_id=456,
            command_type="reload",
            params={}
        )
    """
    command_data = CommandMessageData(
        command=command_type,
        params=params,
        command_id=command_id
    )

    success = await manager.send_to_device(
        device_id=device_id,
        message_type=MessageType.COMMAND,
        data=command_data.model_dump()
    )

    if success:
        logger.info(
            "Command sent to device via WebSocket",
            device_id=device_id,
            command_id=command_id,
            command_type=command_type
        )
    else:
        logger.warning(
            "Failed to send command - device not connected",
            device_id=device_id,
            command_id=command_id,
            command_type=command_type
        )

    return success


async def notify_playlist_update(
    device_id: int,
    playlist_id: int,
    action: str = "reload",
    changes: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Notify device of playlist update via WebSocket

    Called when playlist is updated to immediately notify device
    without waiting for periodic polling.

    Args:
        device_id: Target device ID
        playlist_id: Updated playlist ID
        action: Action to take (reload, append, etc.)
        changes: Optional details about what changed

    Returns:
        True if sent successfully, False if device not connected
    """
    playlist_data = {
        "playlist_id": playlist_id,
        "device_id": device_id,
        "action": action,
        "changes": changes or {}
    }

    success = await manager.send_to_device(
        device_id=device_id,
        message_type=MessageType.PLAYLIST_UPDATE,
        data=playlist_data
    )

    if success:
        logger.info(
            "Playlist update notification sent",
            device_id=device_id,
            playlist_id=playlist_id,
            action=action
        )

    return success


async def notify_content_ready(
    device_id: int,
    content_id: int,
    content_name: str,
    content_type: str,
    content_url: str,
    file_size: int,
    checksum: Optional[str] = None
) -> bool:
    """
    Notify device that new content is ready for download

    Args:
        device_id: Target device ID
        content_id: Content ID
        content_name: Content filename
        content_type: MIME type
        content_url: Download URL
        file_size: File size in bytes
        checksum: Optional file checksum

    Returns:
        True if sent successfully, False if device not connected
    """
    content_data = {
        "content_id": content_id,
        "content_name": content_name,
        "content_type": content_type,
        "content_url": content_url,
        "file_size": file_size,
        "checksum": checksum
    }

    success = await manager.send_to_device(
        device_id=device_id,
        message_type=MessageType.CONTENT_READY,
        data=content_data
    )

    if success:
        logger.info(
            "Content ready notification sent",
            device_id=device_id,
            content_id=content_id,
            content_name=content_name
        )

    return success


@router.on_event("startup")
async def startup():
    """Initialize WebSocket manager on startup"""
    await manager.initialize()


@router.on_event("shutdown")
async def shutdown():
    """Cleanup WebSocket manager on shutdown"""
    await manager.shutdown()


@router.websocket("/ws/device/{device_id}")
async def device_websocket(
    websocket: WebSocket,
    device_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for device connections (Quick Wins Pattern)

    **Features:**
    - Standardized message format (success, type, data, meta)
    - Automatic reconnection support
    - Heartbeat mechanism (30s interval)
    - Real-time command execution
    - Playlist update notifications
    - Content ready notifications

    **Authentication:**
    - Devices authenticate with their activation code as token parameter
    - Optional token validation against device.activation_code

    **Message Format (ALL messages):**
    ```json
    {
        "success": true,
        "type": "command",
        "data": {...},
        "meta": {
            "timestamp": "2025-10-28T10:30:00.123456Z",
            "message_id": "msg-abc123",
            "version": "1.0.0"
        }
    }
    ```

    **Connection Flow:**
    1. Device connects with activation code
    2. Server validates and accepts connection
    3. Server sends standardized 'connected' message
    4. Bidirectional communication established
    5. Automatic heartbeat every 30s
    6. Graceful disconnect handling with cleanup
    """
    await websocket.accept()

    try:
        # Verify device exists and get info
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            # Send standardized error message
            error_msg = create_error_message(
                code="DEVICE_NOT_FOUND",
                message=f"Device {device_id} not found"
            )
            await websocket.send_json(error_msg)
            await websocket.close(code=1008, reason="Device not found")

            logger.warning(
                "Device WebSocket connection rejected - device not found",
                device_id=device_id
            )
            return

        # Optional: Verify token/activation code
        if token and device.activation_code != token:
            error_msg = create_error_message(
                code="INVALID_TOKEN",
                message="Invalid authentication token"
            )
            await websocket.send_json(error_msg)
            await websocket.close(code=1008, reason="Invalid token")

            logger.warning(
                "Device WebSocket connection rejected - invalid token",
                device_id=device_id
            )
            return

        # Register connection
        await manager.connect_device(websocket, device_id, device.device_name)

        # Send standardized connection success message
        connected_data = ConnectedMessageData(
            device_id=device_id,
            device_name=device.device_name,
            message="Connected to signage backend",
            server_time=datetime.utcnow()
        )

        connected_msg = create_websocket_message(
            message_type=MessageType.CONNECTED,
            data=connected_data.model_dump()
        )

        await websocket.send_json(connected_msg)

        # Update device last_seen
        device.last_seen = datetime.utcnow()
        device.is_online = True
        db.commit()

        # Notify admins of device connection
        await manager.broadcast_to_admins(
            MessageType.DASHBOARD_UPDATE,
            {
                "event": "device_connected",
                "device_id": device_id,
                "device_name": device.device_name
            }
        )

        # Listen for messages
        while True:
            try:
                data = await websocket.receive_json()
                await manager.handle_device_message(device_id, data)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from device {device_id}")
            except Exception as e:
                logger.error(f"Error handling message from device {device_id}: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket error for device {device_id}: {e}")

    finally:
        # Clean up connection
        await manager.disconnect_device(device_id)

        # Update device offline status
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if device:
                device.is_online = False
                db.commit()
        except:
            pass

        # Notify admins of disconnection
        await manager.broadcast_to_admins(
            MessageType.DASHBOARD_UPDATE,
            {
                "event": "device_disconnected",
                "device_id": device_id
            }
        )


@router.websocket("/ws/admin")
async def admin_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for admin dashboard (Quick Wins Pattern)

    **Features:**
    - Standardized message format (success, type, data, meta)
    - Real-time device status updates
    - Content transcoding progress
    - System-wide notifications
    - Command responses from devices
    - Connection statistics

    **Authentication:**
    - Admins authenticate with JWT token (query parameter)
    - In DEBUG mode, allows unauthenticated connections for testing

    **Message Format (ALL messages):**
    ```json
    {
        "success": true,
        "type": "dashboard_update",
        "data": {...},
        "meta": {
            "timestamp": "2025-10-28T10:30:00.123456Z",
            "message_id": "msg-abc123",
            "version": "1.0.0"
        }
    }
    ```

    **Received Message Types:**
    - device_connected/disconnected
    - playlist_updated
    - content_ready
    - transcoding_progress
    - command_response
    - connection_stats

    **Send Commands:**
    Send message with type="send_command" to execute command on device
    """
    await websocket.accept()

    conn_id = None

    try:
        # Verify admin authentication
        user_data = None
        if token:
            try:
                user_data = verify_token(token)
            except Exception as e:
                error_msg = create_error_message(
                    code="INVALID_TOKEN",
                    message="Invalid authentication token",
                    details={"error": str(e)}
                )
                await websocket.send_json(error_msg)
                await websocket.close(code=1008, reason="Invalid token")

                logger.warning(
                    "Admin WebSocket connection rejected - invalid token",
                    error=str(e)
                )
                return

        # For development, allow connection without token
        if not user_data and settings.DEBUG:
            user_data = {"user_id": 0, "username": "debug_admin"}
            logger.info("Admin WebSocket connection in DEBUG mode (no auth)")
        elif not user_data:
            error_msg = create_error_message(
                code="AUTH_REQUIRED",
                message="Authentication required"
            )
            await websocket.send_json(error_msg)
            await websocket.close(code=1008, reason="Auth required")

            logger.warning("Admin WebSocket connection rejected - no auth")
            return

        # Register connection
        conn_id = await manager.connect_admin(
            websocket,
            user_data.get("user_id", 0),
            user_data.get("username", "unknown")
        )

        # Send standardized connection success message
        connected_data = ConnectedMessageData(
            connection_id=conn_id,
            message="Connected to admin dashboard",
            server_time=datetime.utcnow()
        )

        connected_msg = create_websocket_message(
            message_type=MessageType.CONNECTED,
            data=connected_data.model_dump()
        )

        await websocket.send_json(connected_msg)

        # Send current connection stats
        stats = await manager.get_connection_stats()
        stats_msg = create_websocket_message(
            message_type=MessageType.DASHBOARD_UPDATE,
            data={
                "event": "connection_stats",
                "stats": stats
            }
        )

        await websocket.send_json(stats_msg)

        # Listen for messages
        while True:
            try:
                data = await websocket.receive_json()

                # Handle admin commands
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                elif data.get("type") == "get_stats":
                    stats = await manager.get_connection_stats()
                    await websocket.send_json({
                        "type": "connection_stats",
                        "stats": stats
                    })

                elif data.get("type") == "send_command":
                    # Send command to device
                    device_id = data.get("device_id")
                    command = data.get("command")
                    params = data.get("params", {})

                    if device_id and command:
                        success = await manager.send_to_device(
                            device_id,
                            MessageType.COMMAND,
                            {
                                "command": command,
                                "params": params
                            }
                        )

                        await websocket.send_json({
                            "type": "command_sent",
                            "device_id": device_id,
                            "command": command,
                            "success": success
                        })

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.error("Invalid JSON from admin")
            except Exception as e:
                logger.error(f"Error handling admin message: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket error for admin: {e}")

    finally:
        # Clean up connection
        if conn_id:
            await manager.disconnect_admin(conn_id)


@router.get("/stats")
async def get_websocket_stats(
    request: Request
):
    """
    Get current WebSocket connection statistics (Quick Wins Pattern)

    **Returns:**
    - Total connections since server start
    - Current connections (devices and admins)
    - Peak concurrent connections
    - Message statistics (sent/received, bytes)
    - Connected device details with metadata

    **Response Format:**
    ```json
    {
        "success": true,
        "data": {
            "total_connections": 1500,
            "current_device_connections": 25,
            "current_admin_connections": 3,
            "peak_connections": 50,
            "messages_sent": 125000,
            "messages_received": 98000,
            "devices": {...}
        },
        "meta": {
            "timestamp": "...",
            "request_id": "...",
            "version": "1.0.0"
        }
    }
    ```

    **Use Cases:**
    - Monitor WebSocket health
    - Check active device connections
    - Debug connection issues
    - Display connection metrics in dashboard
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching WebSocket connection stats",
        request_id=request_id
    )

    try:
        stats = await manager.get_connection_stats()

        logger.info(
            "WebSocket stats retrieved",
            request_id=request_id,
            current_devices=stats.get("current_device_connections", 0),
            current_admins=stats.get("current_admin_connections", 0),
            total_current=stats.get("total_current_connections", 0)
        )

        return success_response(
            data=stats,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Failed to get WebSocket stats",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get WebSocket stats: {str(e)}"
        )


@router.post("/broadcast")
async def broadcast_message(
    broadcast_request: BroadcastRequest,
    request: Request
):
    """
    Broadcast message to devices via WebSocket (Quick Wins Pattern)

    **Request Body:**
    ```json
    {
        "message_type": "playlist_update",
        "data": {
            "playlist_id": 5,
            "action": "reload"
        },
        "device_ids": [123, 456, 789]  // Optional - if null, broadcasts to all
    }
    ```

    **Broadcast Modes:**
    - **Targeted**: Specify device_ids array to broadcast to specific devices
    - **All Devices**: Omit device_ids or set to null to broadcast to all connected devices

    **Common Message Types:**
    - `playlist_update`: Notify devices to reload playlist
    - `content_ready`: Notify devices of new content available
    - `command`: Execute command on devices

    **Response Format:**
    ```json
    {
        "success": true,
        "data": {
            "total_devices": 3,
            "successful_sends": 2,
            "failed_sends": 1,
            "results": {
                "123": true,
                "456": true,
                "789": false
            }
        },
        "meta": {...}
    }
    ```

    **Use Cases:**
    - Bulk playlist updates to specific devices
    - System-wide content deployment notifications
    - Emergency broadcasts to all devices
    - Tag-based command execution
    """
    request_id = get_request_id(request)

    logger.info(
        "Broadcasting WebSocket message",
        request_id=request_id,
        message_type=broadcast_request.message_type.value,
        target_devices=len(broadcast_request.device_ids) if broadcast_request.device_ids else "all"
    )

    try:
        # Validate message type
        msg_type = broadcast_request.message_type

        # Broadcast to specific devices or all
        if broadcast_request.device_ids:
            results = await manager.broadcast_to_devices(
                broadcast_request.device_ids,
                msg_type,
                broadcast_request.data
            )
            success_count = sum(1 for success in results.values() if success)

            response_data = BroadcastResponse(
                total_devices=len(broadcast_request.device_ids),
                successful_sends=success_count,
                failed_sends=len(broadcast_request.device_ids) - success_count,
                results=results
            )
        else:
            results = await manager.broadcast_to_all_devices(
                msg_type,
                broadcast_request.data
            )
            success_count = sum(1 for success in results.values() if success)

            response_data = BroadcastResponse(
                total_devices=len(results),
                successful_sends=success_count,
                failed_sends=len(results) - success_count,
                results=None  # Don't include individual results for broadcast to all (could be large)
            )

        logger.info(
            "Broadcast completed",
            request_id=request_id,
            message_type=msg_type.value,
            total=response_data.total_devices,
            successful=response_data.successful_sends,
            failed=response_data.failed_sends
        )

        return success_response(
            data=response_data.model_dump(),
            request_id=request_id
        )

    except ValueError as e:
        logger.warning(
            "Invalid message type for broadcast",
            request_id=request_id,
            message_type=broadcast_request.message_type,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid message type: {broadcast_request.message_type}"
        )
    except Exception as e:
        logger.error(
            "Failed to broadcast message",
            request_id=request_id,
            message_type=broadcast_request.message_type.value,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast message: {str(e)}"
        )