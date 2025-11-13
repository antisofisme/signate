"""
WebSocket Routes
Centralized WebSocket endpoints for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json
import logging

from shared.websocket_manager import websocket_manager
from shared.auth import get_current_user_ws, get_device_by_token_ws
from services.auth.dtos import UserResponse
from services.device.dtos import DeviceResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/admin")
async def admin_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Admin WebSocket endpoint for real-time updates

    Connect with: ws://host/ws/admin?token=JWT_TOKEN

    Receives events for:
    - Device status changes
    - Content updates
    - Playlist changes
    - System notifications
    """
    # Accept connection first, then authenticate
    await websocket.accept()

    # Debug: log full URL and query params
    logger.info(f"[WebSocket] Connection accepted from {websocket.client}")
    logger.info(f"[WebSocket] URL path: {websocket.url.path}")
    logger.info(f"[WebSocket] Query params: {dict(websocket.query_params)}")
    logger.info(f"[WebSocket] Token parameter: {token[:20] if token else 'None'}...")

    # Authenticate user
    current_user = await get_current_user_ws(token)

    if not current_user:
        logger.warning(f"[WebSocket] Authentication failed - token: {token[:20] if token else 'None'}...")
        await websocket.send_json({"error": "Unauthorized", "code": 1008})
        await websocket.close(code=1008, reason="Unauthorized")
        return

    logger.info(f"[WebSocket] User authenticated: {current_user.username} (ID: {current_user.id}, Org: {current_user.organization_id})")
    
    try:
        # Connect admin to WebSocket manager
        await websocket_manager.connect_admin(
            websocket=websocket,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            permissions=current_user.permissions if hasattr(current_user, 'permissions') else []
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle admin messages
                await websocket_manager.handle_admin_message(
                    user_id=current_user.id,
                    message=message
                )
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON format"
                })
                
    except WebSocketDisconnect:
        # Clean disconnect
        await websocket_manager.disconnect_admin(current_user.id)
        
    except Exception as e:
        logger.error(f"WebSocket error for admin {current_user.id}: {e}")
        await websocket_manager.disconnect_admin(current_user.id)
        await websocket.close(code=1011, reason="Internal error")


@router.websocket("/ws/device")
async def device_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    device: DeviceResponse = Depends(get_device_by_token_ws)
):
    """
    Device WebSocket endpoint for real-time commands and updates
    
    Connect with: ws://host/ws/device?token=DEVICE_JWT_TOKEN
    
    Receives:
    - Remote commands (reboot, screenshot, etc.)
    - Content update notifications
    - Schedule changes
    
    Sends:
    - Status updates
    - Command responses
    - Health metrics
    """
    if not device:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    try:
        # Connect device to WebSocket manager
        await websocket_manager.connect_device(
            websocket=websocket,
            device_id=device.id,
            organization_id=device.organization_id
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Receive message from device
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle device messages
                await websocket_manager.handle_device_message(
                    device_id=device.id,
                    message=message
                )
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON format"
                })
                
    except WebSocketDisconnect:
        # Clean disconnect
        await websocket_manager.disconnect_device(device.id)
        
    except Exception as e:
        logger.error(f"WebSocket error for device {device.id}: {e}")
        await websocket_manager.disconnect_device(device.id)
        await websocket.close(code=1011, reason="Internal error")


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket connection statistics
    
    Returns current connection counts and status
    """
    stats = websocket_manager.get_connection_stats()
    
    return {
        "status": "active",
        "connections": stats,
        "ping_interval": 30,
        "features": [
            "real-time-updates",
            "device-commands",
            "organization-isolation",
            "auto-reconnect"
        ]
    }
