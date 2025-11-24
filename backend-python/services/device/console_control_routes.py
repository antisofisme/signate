"""
Console Control Routes - Player WebSocket Communication
Bidirectional WebSocket for player console streaming control (Hybrid Architecture)

This endpoint implements the player-side of the Hybrid Console Streaming architecture:
- Receives console logs from player (Player → Backend)
- Sends control commands to player (Backend → Player via Redis)
- Manages streaming lifecycle (start_streaming, stop_streaming)
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import logging
import asyncio
import json
from datetime import datetime, timezone

from shared import websocket_manager as ws_manager_module
from shared.database import get_db
from services.device.repositories.device_repo import DeviceRepository

def get_ws_manager():
    """Get WebSocket manager instance (access at runtime, not import time)"""
    manager = ws_manager_module.websocket_manager
    if manager is None:
        raise RuntimeError("WebSocket manager not initialized. This should not happen in production.")
    return manager

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# PLAYER CONTROL WEBSOCKET - Bidirectional Communication
# =============================================================================

@router.websocket("/devices/{device_id}/console/control")
async def console_control_websocket(
    websocket: WebSocket,
    device_id: int
):
    """
    Player control WebSocket endpoint - Bidirectional communication

    Architecture: Hybrid Console Streaming

    Responsibilities:
    1. Accept WebSocket connection from player
    2. Validate device_id exists in database
    3. Register player with WebSocket Manager
    4. Listen for incoming logs from player (Player → Backend)
    5. Listen for commands from Redis (Backend → Player)
    6. Broadcast logs to subscribed admins
    7. Handle graceful disconnect

    Message Protocol:

    INCOMING (Player → Backend):
    {
        "type": "console_logs",
        "logs": [
            {
                "level": "log" | "info" | "warn" | "error",
                "message": "Console message",
                "timestamp": "2025-01-13T10:30:00.000Z",
                "stack": "Error stack trace (optional)"
            }
        ],
        "logType": "historical" | "realtime"
    }

    OUTGOING (Backend → Player via Redis):
    {
        "command": "start_streaming" | "stop_streaming",
        "data": {},
        "timestamp": "2025-01-13T10:30:00.000Z"
    }

    Flow:
    1. Player connects → WebSocket accepted
    2. Validate device_id → Get organization_id from database
    3. Register player control WebSocket → WebSocket Manager
    4. Start concurrent listeners:
       a. Player message listener → Process incoming logs
       b. Redis command listener → Forward commands to player
    5. On disconnect → Unregister player control WebSocket
    """
    db_session = None
    organization_id = None
    ws_manager = get_ws_manager()

    try:
        # 1. Accept WebSocket connection
        await websocket.accept()
        logger.info(f"[PlayerControl] Device {device_id} attempting to connect control WebSocket")

        # 2. Validate device_id and get organization_id (multi-tenant security)
        # Use dependency injection manually since WebSocket doesn't support Depends()
        db_session = next(get_db())
        device_repo = DeviceRepository(db_session)

        # Don't filter by org - player self-identifies by device_id
        device = device_repo.find_by_id(device_id, organization_id=None)

        if not device or not device.organization_id:
            logger.warning(f"[PlayerControl] ❌ Device {device_id} not found or not activated")
            await websocket.send_json({
                "error": "Device not found or not activated",
                "code": "DEVICE_NOT_FOUND"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        organization_id = device.organization_id
        logger.info(f"[PlayerControl] ✅ Device {device_id} validated (org: {organization_id})")

        # 3. Register player control WebSocket
        await ws_manager.register_player_control(device_id, websocket)
        logger.info(f"[PlayerControl] Player {device_id} registered for control commands")

        # Send connection confirmation
        await websocket.send_json({
            "event": "control.connected",
            "data": {
                "device_id": device_id,
                "organization_id": organization_id,
                "message": "Control WebSocket connected successfully"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # 4. Start concurrent listeners (run both simultaneously)
        # This allows bidirectional communication
        await asyncio.gather(
            # Listen for incoming logs from player
            _listen_player_messages(websocket, device_id, organization_id, ws_manager),
            # Listen for commands from Redis
            _listen_redis_commands(websocket, device_id, ws_manager),
            return_exceptions=True
        )

    except WebSocketDisconnect:
        logger.info(f"[PlayerControl] Device {device_id} disconnected control WebSocket")
    except Exception as e:
        logger.error(f"[PlayerControl] Error in control WebSocket for device {device_id}: {e}")
    finally:
        # 5. Cleanup: Unregister player control WebSocket
        if organization_id:
            await ws_manager.unregister_player_control(device_id)
            logger.info(f"[PlayerControl] Device {device_id} unregistered from control WebSocket")

        # Close database session
        if db_session:
            db_session.close()

        # Close WebSocket connection
        try:
            await websocket.close()
        except:
            pass


# =============================================================================
# HELPER FUNCTIONS - Message Listeners
# =============================================================================

async def _listen_player_messages(
    websocket: WebSocket,
    device_id: int,
    organization_id: int,
    ws_manager
):
    """
    Listen for incoming messages from player

    Handles:
    - console_logs: Batch of console logs from player
    - ping: Heartbeat messages

    Args:
        websocket: Player WebSocket connection
        device_id: Device ID
        organization_id: Organization ID for multi-tenant routing
        ws_manager: WebSocket Manager instance
    """
    try:
        while True:
            # Receive message from player
            message = await websocket.receive_json()
            message_type = message.get("type")

            logger.debug(f"[PlayerControl] Received message from device {device_id}: {message_type}")

            if message_type == "console_logs":
                # Extract logs and logType
                logs = message.get("logs", [])
                log_type = message.get("logType", "realtime")  # historical | realtime

                if not logs:
                    logger.warning(f"[PlayerControl] Device {device_id} sent empty logs array")
                    continue

                logger.info(
                    f"[PlayerControl] Device {device_id} sent {len(logs)} {log_type} console logs "
                    f"(org: {organization_id})"
                )

                # Validate log structure (basic validation)
                valid_logs = []
                for log in logs:
                    if _validate_log_entry(log):
                        valid_logs.append(log)
                    else:
                        logger.warning(f"[PlayerControl] Invalid log entry from device {device_id}: {log}")

                if not valid_logs:
                    logger.warning(f"[PlayerControl] No valid logs from device {device_id}")
                    continue

                # Add logType metadata for CMS to differentiate historical vs realtime
                # This allows CMS to handle them differently (e.g., scroll to bottom for realtime)
                enriched_logs = []
                for log in valid_logs:
                    enriched_log = log.copy()
                    enriched_log["logType"] = log_type
                    enriched_logs.append(enriched_log)

                # Broadcast to subscribed admins via WebSocket Manager
                # WebSocket Manager handles Redis pub/sub and multi-tenant routing
                logger.info(
                    f"[PlayerControl] Broadcasting {len(enriched_logs)} {log_type} logs "
                    f"from device {device_id} to subscribed admins"
                )

                await ws_manager.broadcast_console_log(
                    device_id=device_id,
                    organization_id=organization_id,
                    logs=enriched_logs
                )

                logger.info(f"[PlayerControl] ✅ Broadcast complete for device {device_id}")

            elif message_type == "ping":
                # Respond to heartbeat
                await websocket.send_json({
                    "event": "control.pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            else:
                logger.warning(f"[PlayerControl] Unknown message type from device {device_id}: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"[PlayerControl] Player {device_id} disconnected during message listening")
        raise
    except Exception as e:
        logger.error(f"[PlayerControl] Error listening to player {device_id} messages: {e}")
        raise


async def _listen_redis_commands(
    websocket: WebSocket,
    device_id: int,
    ws_manager
):
    """
    Listen for commands from Redis and forward to player

    Commands:
    - start_streaming: Send buffered + real-time logs
    - stop_streaming: Stop sending logs, keep buffering

    Note: This is a redundant listener - commands are also handled by
    WebSocket Manager's _command_listener. However, we keep this for:
    1. Direct WebSocket forwarding (lower latency)
    2. Local command handling if Redis pub/sub fails
    3. Explicit control flow visibility

    Args:
        websocket: Player WebSocket connection
        device_id: Device ID
        ws_manager: WebSocket Manager instance
    """
    try:
        # Check if Redis is enabled
        if not ws_manager._use_redis or not ws_manager._command_pubsub:
            logger.info(f"[PlayerControl] Redis disabled - relying on WebSocket Manager command listener")
            # Keep connection alive without blocking
            while True:
                await asyncio.sleep(30)
            return

        # Subscribe to device-specific command channel
        channel = f"command:{device_id}"
        pubsub = ws_manager._redis_client.pubsub()
        await pubsub.subscribe(channel)

        logger.info(f"[PlayerControl] Listening for commands on Redis channel: {channel}")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    # Parse command message
                    data = json.loads(message["data"])
                    command = data.get("command")
                    command_data = data.get("data", {})
                    timestamp = data.get("timestamp")

                    logger.info(f"[PlayerControl] Received command '{command}' from Redis for device {device_id}")

                    # Forward command to player via WebSocket
                    await websocket.send_json({
                        "command": command,
                        "data": command_data,
                        "timestamp": timestamp
                    })

                    logger.info(f"[PlayerControl] ✅ Forwarded command '{command}' to player {device_id}")

                except json.JSONDecodeError as e:
                    logger.error(f"[PlayerControl] Failed to parse command message: {e}")
                except Exception as e:
                    logger.error(f"[PlayerControl] Error forwarding command to player {device_id}: {e}")

    except WebSocketDisconnect:
        logger.info(f"[PlayerControl] Player {device_id} disconnected during command listening")
        raise
    except Exception as e:
        logger.error(f"[PlayerControl] Error listening to Redis commands for device {device_id}: {e}")
        raise


def _validate_log_entry(log: Dict[str, Any]) -> bool:
    """
    Validate console log entry structure

    Required fields:
    - level: string (log, info, warn, error, debug)
    - message: string
    - timestamp: string (ISO 8601)

    Optional fields:
    - stack: string (for errors)

    Args:
        log: Log entry to validate

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["level", "message", "timestamp"]

    # Check required fields exist
    for field in required_fields:
        if field not in log:
            logger.warning(f"Log entry missing required field: {field}")
            return False

    # Validate level
    valid_levels = ["log", "info", "warn", "error", "debug"]
    if log["level"] not in valid_levels:
        logger.warning(f"Invalid log level: {log['level']}")
        return False

    # Validate message is string
    if not isinstance(log["message"], str):
        logger.warning(f"Log message is not a string: {type(log['message'])}")
        return False

    # Validate timestamp is string (basic check)
    if not isinstance(log["timestamp"], str):
        logger.warning(f"Log timestamp is not a string: {type(log['timestamp'])}")
        return False

    return True
