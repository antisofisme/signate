"""
WebSocket Manager
Centralized WebSocket connection management and broadcasting
"""

from typing import Dict, Set, Optional, Any, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
import json
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class WebSocketEventType(Enum):
    """WebSocket event types"""
    # Device events
    DEVICE_ACTIVATED = "device.activated"
    DEVICE_UPDATED = "device.updated"
    DEVICE_OFFLINE = "device.offline"
    DEVICE_ONLINE = "device.online"
    DEVICE_COMMAND = "device.command"
    
    # Content events
    CONTENT_UPLOADED = "content.uploaded"
    CONTENT_UPDATED = "content.updated"
    CONTENT_DELETED = "content.deleted"
    CONTENT_TRANSCODED = "content.transcoded"
    
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
    
    def __init__(self):
        # Device connections: {device_id: {websocket, org_id, last_ping}}
        self._device_connections: Dict[int, Dict[str, Any]] = {}
        
        # Admin connections: {user_id: {websocket, org_id, permissions}}
        self._admin_connections: Dict[int, Dict[str, Any]] = {}
        
        # Organization rooms: {org_id: {device_ids, admin_ids}}
        self._organization_rooms: Dict[int, Dict[str, Set[int]]] = {}
        
        # Channel subscriptions: {channel: {connection_ids}}
        self._channel_subscriptions: Dict[str, Set[str]] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Background tasks
        self._ping_task: Optional[asyncio.Task] = None
        
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
            "event": event_type.value,
            "data": data,
            "recorded_at": datetime.now(timezone.utc).isoformat()
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
            "event": event_type.value,
            "data": data,
            "recorded_at": datetime.now(timezone.utc).isoformat()
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
        
        Args:
            organization_id: Target organization
            event_type: Event type
            data: Event data
        """
        if organization_id not in self._organization_rooms:
            return
            
        room = self._organization_rooms[organization_id]
        
        # Send to all devices in organization
        failed_devices = []
        for device_id in room["device_ids"]:
            success = await self.send_to_device(device_id, event_type, data)
            if not success:
                failed_devices.append(device_id)
        
        # Send to all admins in organization
        failed_admins = []
        for user_id in room["admin_ids"]:
            success = await self.send_to_admin(user_id, event_type, data)
            if not success:
                failed_admins.append(user_id)
        
        # Clean up failed connections
        for device_id in failed_devices:
            room["device_ids"].discard(device_id)
        for user_id in failed_admins:
            room["admin_ids"].discard(user_id)
    
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
            "organizations": len(self._organization_rooms),
            "devices_by_org": {
                org_id: len(room["device_ids"])
                for org_id, room in self._organization_rooms.items()
            },
            "admins_by_org": {
                org_id: len(room["admin_ids"])
                for org_id, room in self._organization_rooms.items()
            }
        }


# Global WebSocket manager instance
websocket_manager = ConnectionManager()