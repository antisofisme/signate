"""
Console Log Streaming Routes
Live WebSocket streaming for device console logs (NO DATABASE)
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import logging
import asyncio
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
# ADMIN ENDPOINTS - Subscribe to console logs
# =============================================================================

@router.websocket("/devices/{device_id}/console/stream")
async def stream_console_logs(
    websocket: WebSocket,
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Admin WebSocket endpoint to subscribe to device console logs

    Flow:
    1. Admin opens modal → establishes WebSocket connection
    2. Subscribe to device console logs (with organization_id)
    3. Backend signals player to start streaming (if first subscriber)
    4. Receive real-time console logs from device
    5. Unsubscribe when modal closed
    6. Backend signals player to stop streaming (if last subscriber)

    No authentication needed here - handled by main WebSocket connection
    This is a secondary WebSocket for console streaming only
    """
    await websocket.accept()

    # Extract user info from query params (passed from frontend)
    organization_id = None
    try:
        # Get user_id from WebSocket query params
        user_id = int(websocket.query_params.get("user_id", 0))
        if not user_id:
            print(f"[Console] ❌ No user_id in query params")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get device to retrieve organization_id (required for multi-tenant isolation)
        device_repo = DeviceRepository(db)
        device = device_repo.find_by_id(device_id, organization_id=None)

        if not device:
            print(f"[Console] ❌ Device {device_id} not found")
            logger.error(f"Device {device_id} not found for console subscription")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if not device.organization_id:
            print(f"[Console] ❌ Device {device_id} has no organization_id")
            logger.error(f"Device {device_id} has no organization_id")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        organization_id = device.organization_id

        # Subscribe to console logs with WebSocket connection (BREAKING CHANGE: now requires organization_id)
        print(f"[Console] Subscribing admin {user_id} to device {device_id} console stream (org: {organization_id})")
        success = await get_ws_manager().subscribe_to_console(
            device_id=device_id,
            admin_user_id=user_id,
            organization_id=organization_id,
            websocket=websocket
        )
        if not success:
            print(f"[Console] ❌ Failed to subscribe admin {user_id}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        print(f"[Console] ✅ Admin {user_id} subscribed to device {device_id} console stream (org: {organization_id})")
        logger.info(f"Admin {user_id} subscribed to device {device_id} console stream (org: {organization_id})")

        # Send initial confirmation
        await websocket.send_json({
            "event": "console.subscribed",
            "data": {
                "device_id": device_id,
                "organization_id": organization_id,
                "message": "Successfully subscribed to console logs"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Keep connection alive - just wait for disconnect
        # Don't block on receive_text() - this WebSocket is one-way (server -> client)
        # Messages are sent via broadcast_console_log() from Redis pub/sub listener
        try:
            # Wait forever without blocking - allows broadcasts to flow through
            # This is a one-way connection: server sends, client receives only
            while True:
                await asyncio.sleep(1)  # Keep connection alive, check every second
        except WebSocketDisconnect:
            logger.info(f"Admin {user_id} disconnected from device {device_id} console stream (org: {organization_id})")

    except Exception as e:
        logger.error(f"Error in console stream: {e}")
    finally:
        # Unsubscribe on disconnect (BREAKING CHANGE: now requires organization_id)
        try:
            if organization_id:
                await get_ws_manager().unsubscribe_from_console(
                    device_id=device_id,
                    admin_user_id=user_id,
                    organization_id=organization_id
                )
                logger.info(f"Admin {user_id} unsubscribed from device {device_id} console (org: {organization_id})")
        except:
            pass

        try:
            await websocket.close()
        except:
            pass


# =============================================================================
# REMOVED: Old HTTP POST endpoint - Replaced by WebSocket control architecture
# =============================================================================
# The /devices/{device_id}/console/upload endpoint has been removed.
# Players now use bidirectional WebSocket (/devices/{device_id}/console/control)
# for console log streaming controlled by admin subscriptions.
# See: /tmp/CONSOLE_STREAMING_HYBRID_ARCHITECTURE.md
