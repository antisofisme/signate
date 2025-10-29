"""
WebSocket Message Schemas
Standardized message formats for WebSocket communication between server and devices/admins
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# MESSAGE TYPES
# =============================================================================

class MessageType(str, Enum):
    """WebSocket message types"""
    # Connection management
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    HEARTBEAT = "heartbeat"
    PONG = "pong"

    # Content & playlist updates
    PLAYLIST_UPDATE = "playlist_update"
    CONTENT_READY = "content_ready"
    CONTENT_UPDATE = "content_update"

    # Commands
    COMMAND = "command"
    COMMAND_RESPONSE = "command_response"

    # Status updates
    DEVICE_STATUS = "device_status"
    TRANSCODING_PROGRESS = "transcoding_progress"

    # Dashboard events
    DASHBOARD_UPDATE = "dashboard_update"

    # Logs
    LOG = "log"

    # Errors
    ERROR = "error"


# =============================================================================
# BASE MESSAGE SCHEMAS
# =============================================================================

class WebSocketMessageMeta(BaseModel):
    """
    Metadata for WebSocket messages

    Provides standardized metadata for all WebSocket messages
    """
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="ISO timestamp when message was created"
    )
    message_id: Optional[str] = Field(
        None,
        description="Unique message ID for tracking and deduplication"
    )
    version: str = Field(
        default="1.0.0",
        description="Message protocol version"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-28T10:30:00.123456Z",
                "message_id": "msg-abc123",
                "version": "1.0.0"
            }
        }


class WebSocketMessage(BaseModel):
    """
    Base WebSocket message format

    All WebSocket messages follow this standardized structure:
    - success: Boolean indicating if operation succeeded
    - type: Message type from MessageType enum
    - data: Message payload (any structure)
    - meta: Message metadata (timestamp, message_id, version)
    """
    success: bool = Field(
        default=True,
        description="Indicates if the operation was successful"
    )
    type: MessageType = Field(
        description="Type of WebSocket message"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Message payload (structure varies by type)"
    )
    meta: WebSocketMessageMeta = Field(
        default_factory=WebSocketMessageMeta,
        description="Message metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "type": "command",
                "data": {
                    "command": "reload",
                    "params": {}
                },
                "meta": {
                    "timestamp": "2025-10-28T10:30:00.123456Z",
                    "message_id": "msg-abc123",
                    "version": "1.0.0"
                }
            }
        }


class WebSocketErrorMessage(BaseModel):
    """
    WebSocket error message format

    Sent when an error occurs in WebSocket communication
    """
    success: bool = Field(
        default=False,
        description="Always false for errors"
    )
    type: MessageType = Field(
        default=MessageType.ERROR,
        description="Always 'error' for error messages"
    )
    error: Dict[str, Any] = Field(
        description="Error details"
    )
    meta: WebSocketMessageMeta = Field(
        default_factory=WebSocketMessageMeta,
        description="Message metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "type": "error",
                "error": {
                    "code": "INVALID_MESSAGE",
                    "message": "Message format invalid",
                    "details": {}
                },
                "meta": {
                    "timestamp": "2025-10-28T10:30:00.123456Z",
                    "message_id": "msg-abc123",
                    "version": "1.0.0"
                }
            }
        }


# =============================================================================
# CONNECTION MESSAGES
# =============================================================================

class ConnectedMessageData(BaseModel):
    """Data for 'connected' message"""
    device_id: Optional[int] = Field(None, description="Device ID (for device connections)")
    device_name: Optional[str] = Field(None, description="Device name")
    connection_id: Optional[str] = Field(None, description="Connection ID (for admin connections)")
    message: str = Field(default="Connected to signage backend")
    server_time: datetime = Field(default_factory=datetime.utcnow)


class HeartbeatMessageData(BaseModel):
    """Data for 'heartbeat' message"""
    server_time: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# COMMAND MESSAGES
# =============================================================================

class CommandMessageData(BaseModel):
    """
    Data for 'command' message

    Sent from server to device to execute a command
    """
    command: str = Field(description="Command type (reload, screenshot, reboot, etc.)")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Command parameters"
    )
    command_id: Optional[int] = Field(
        None,
        description="Database command ID for tracking"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "command": "reload",
                "params": {},
                "command_id": 123
            }
        }


class CommandResponseMessageData(BaseModel):
    """
    Data for 'command_response' message

    Sent from device to server after command execution
    """
    command: str = Field(description="Command that was executed")
    command_id: Optional[int] = Field(None, description="Database command ID")
    success: bool = Field(description="Whether command succeeded")
    result: Optional[Any] = Field(None, description="Command execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: Optional[int] = Field(
        None,
        description="Command execution time in milliseconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "command": "reload",
                "command_id": 123,
                "success": True,
                "result": "Page reloaded successfully",
                "error": None,
                "execution_time_ms": 150
            }
        }


# =============================================================================
# CONTENT MESSAGES
# =============================================================================

class PlaylistUpdateMessageData(BaseModel):
    """
    Data for 'playlist_update' message

    Notifies device that playlist has been updated
    """
    playlist_id: int = Field(description="Playlist ID that was updated")
    device_id: int = Field(description="Device ID that should reload")
    action: str = Field(
        default="reload",
        description="Action to take (reload, append, etc.)"
    )
    changes: Optional[Dict[str, Any]] = Field(
        None,
        description="Details about what changed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "playlist_id": 5,
                "device_id": 123,
                "action": "reload",
                "changes": {
                    "added": 2,
                    "removed": 1,
                    "reordered": True
                }
            }
        }


class ContentReadyMessageData(BaseModel):
    """
    Data for 'content_ready' message

    Notifies device that new content is ready for download
    """
    content_id: int = Field(description="Content ID that is ready")
    content_name: str = Field(description="Content filename")
    content_type: str = Field(description="Content MIME type")
    content_url: str = Field(description="URL to download content")
    file_size: int = Field(description="File size in bytes")
    checksum: Optional[str] = Field(None, description="File checksum for verification")

    class Config:
        json_schema_extra = {
            "example": {
                "content_id": 42,
                "content_name": "promo-video.mp4",
                "content_type": "video/mp4",
                "content_url": "http://192.168.5.12:8001/api/content/42/download",
                "file_size": 15728640,
                "checksum": "sha256:abc123..."
            }
        }


# =============================================================================
# STATUS MESSAGES
# =============================================================================

class DeviceStatusMessageData(BaseModel):
    """
    Data for 'device_status' message

    Sent from device to server with status updates
    """
    device_id: int = Field(description="Device ID")
    status: str = Field(description="Device status (playing, idle, error, etc.)")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional status details"
    )
    current_content: Optional[str] = Field(None, description="Currently playing content")
    memory_usage_mb: Optional[int] = Field(None, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 123,
                "status": "playing",
                "details": {
                    "playlist_position": 3,
                    "total_items": 10
                },
                "current_content": "promo-video.mp4",
                "memory_usage_mb": 256,
                "cpu_usage_percent": 45.2
            }
        }


class TranscodingProgressMessageData(BaseModel):
    """
    Data for 'transcoding_progress' message

    Notifies about content transcoding progress
    """
    content_id: int = Field(description="Content being transcoded")
    content_name: str = Field(description="Content filename")
    progress_percent: float = Field(description="Progress percentage (0-100)")
    status: str = Field(description="Status (queued, processing, completed, failed)")
    eta_seconds: Optional[int] = Field(None, description="Estimated time remaining")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "content_id": 42,
                "content_name": "promo-video.mp4",
                "progress_percent": 65.5,
                "status": "processing",
                "eta_seconds": 120,
                "error": None
            }
        }


# =============================================================================
# DASHBOARD MESSAGES
# =============================================================================

class DashboardUpdateMessageData(BaseModel):
    """
    Data for 'dashboard_update' message

    Sent to admin dashboard for real-time updates
    """
    event: str = Field(description="Event type (device_connected, device_disconnected, etc.)")
    device_id: Optional[int] = Field(None, description="Related device ID")
    device_name: Optional[str] = Field(None, description="Related device name")
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional event data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event": "device_connected",
                "device_id": 123,
                "device_name": "Lobby TV",
                "data": {
                    "ip_address": "192.168.1.100",
                    "location": "Main Lobby"
                }
            }
        }


# =============================================================================
# CONNECTION STATISTICS
# =============================================================================

class ConnectionStats(BaseModel):
    """
    WebSocket connection statistics

    Returned by GET /api/websocket/stats endpoint
    """
    total_connections: int = Field(description="Total connections since server start")
    current_device_connections: int = Field(description="Current device connections")
    current_admin_connections: int = Field(description="Current admin connections")
    total_current_connections: int = Field(description="Total current connections")
    peak_connections: int = Field(description="Peak concurrent connections")
    messages_sent: int = Field(description="Total messages sent")
    messages_received: int = Field(description="Total messages received")
    bytes_sent: int = Field(description="Total bytes sent")
    bytes_received: int = Field(description="Total bytes received")
    devices: Dict[int, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Connected device details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_connections": 1500,
                "current_device_connections": 25,
                "current_admin_connections": 3,
                "total_current_connections": 28,
                "peak_connections": 50,
                "messages_sent": 125000,
                "messages_received": 98000,
                "bytes_sent": 15728640,
                "bytes_received": 5242880,
                "devices": {
                    "123": {
                        "device_name": "Lobby TV",
                        "connected_at": "2025-10-28T10:00:00Z",
                        "last_heartbeat": "2025-10-28T10:29:00Z",
                        "messages_sent": 150,
                        "messages_received": 120
                    }
                }
            }
        }


# =============================================================================
# BROADCAST REQUEST
# =============================================================================

class BroadcastRequest(BaseModel):
    """
    Request to broadcast message to devices

    Used by POST /api/websocket/broadcast endpoint
    """
    message_type: MessageType = Field(description="Type of message to broadcast")
    data: Dict[str, Any] = Field(description="Message payload")
    device_ids: Optional[List[int]] = Field(
        None,
        description="Specific device IDs (if None, broadcasts to all)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "playlist_update",
                "data": {
                    "playlist_id": 5,
                    "action": "reload"
                },
                "device_ids": [123, 456, 789]
            }
        }


class BroadcastResponse(BaseModel):
    """
    Response from broadcast endpoint
    """
    total_devices: int = Field(description="Total devices targeted")
    successful_sends: int = Field(description="Number of successful deliveries")
    failed_sends: int = Field(description="Number of failed deliveries")
    results: Optional[Dict[int, bool]] = Field(
        None,
        description="Delivery results per device (device_id -> success)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_devices": 3,
                "successful_sends": 2,
                "failed_sends": 1,
                "results": {
                    "123": True,
                    "456": True,
                    "789": False
                }
            }
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_websocket_message(
    message_type: MessageType,
    data: Dict[str, Any],
    success: bool = True,
    message_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Helper function to create standardized WebSocket message

    Args:
        message_type: Type of message
        data: Message payload
        success: Whether operation succeeded (default: True)
        message_id: Optional message ID for tracking

    Returns:
        Dictionary ready to be sent via WebSocket
    """
    message = WebSocketMessage(
        success=success,
        type=message_type,
        data=data,
        meta=WebSocketMessageMeta(message_id=message_id)
    )
    return message.model_dump(mode='json')


def create_error_message(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    message_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Helper function to create standardized WebSocket error message

    Args:
        code: Error code (e.g., "INVALID_MESSAGE")
        message: Error message
        details: Optional additional error details
        message_id: Optional message ID for tracking

    Returns:
        Dictionary ready to be sent via WebSocket
    """
    error_msg = WebSocketErrorMessage(
        error={
            "code": code,
            "message": message,
            "details": details or {}
        },
        meta=WebSocketMessageMeta(message_id=message_id)
    )
    return error_msg.model_dump(mode='json')
