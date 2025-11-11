"""
PMS WebSocket Routes
Real-time sync via WebSocket for Firebird Bridge Agent
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Optional
import json
import logging
from datetime import datetime

from shared.database import get_db
from services.pms.repositories.pms_repo import PMSRepository
from services.pms.use_cases.sync_guests import SyncGuestsUseCase
from services.pms.use_cases.sync_rooms import SyncRoomsUseCase

router = APIRouter(tags=["PMS WebSocket"])

# WebSocket connection manager
class PMSConnectionManager:
    """Manage WebSocket connections for PMS sync"""

    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}  # organization_id -> websocket
        self.logger = logging.getLogger('PMSWebSocket')

    async def connect(self, websocket: WebSocket, organization_id: int):
        """Accept new connection"""
        await websocket.accept()
        self.active_connections[organization_id] = websocket
        self.logger.info(f"Organization {organization_id} connected via WebSocket")

    def disconnect(self, organization_id: int):
        """Remove connection"""
        if organization_id in self.active_connections:
            del self.active_connections[organization_id]
            self.logger.info(f"Organization {organization_id} disconnected")

    async def send_message(self, organization_id: int, message: dict):
        """Send message to specific organization"""
        if organization_id in self.active_connections:
            websocket = self.active_connections[organization_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        for websocket in self.active_connections.values():
            await websocket.send_json(message)


manager = PMSConnectionManager()


def verify_websocket_auth(api_key: str, organization_id: int, db: Session) -> bool:
    """Verify API key for WebSocket connection"""
    try:
        repo = PMSRepository(db)
        config = repo.get_config_by_api_key(api_key)

        if not config:
            return False

        if config.organization_id != organization_id:
            return False

        if not config.is_active:
            return False

        return True
    except Exception:
        return False


@router.websocket("/ws/pms/sync")
async def websocket_pms_sync(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time PMS data sync

    Headers required:
    - X-API-Key: API key from PMS configuration
    - X-Organization-ID: Organization ID

    Message format:
    {
        "type": "sync_guests" | "sync_rooms",
        "data": {
            "guests": [...] | "rooms": [...]
        }
    }
    """
    # Get headers
    headers = dict(websocket.headers)
    api_key = headers.get('x-api-key')
    org_id_str = headers.get('x-organization-id')

    if not api_key or not org_id_str:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing auth headers")
        return

    try:
        organization_id = int(org_id_str)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid organization ID")
        return

    # Verify authentication
    if not verify_websocket_auth(api_key, organization_id, db):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid credentials")
        return

    # Accept connection
    await manager.connect(websocket, organization_id)

    # Send welcome message
    await websocket.send_json({
        'type': 'connected',
        'message': 'WebSocket connection established',
        'organization_id': organization_id,
        'timestamp': datetime.now().isoformat()
    })

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get('type')
            msg_data = message.get('data', {})

            # Handle message based on type
            if msg_type == 'sync_guests':
                await handle_sync_guests(websocket, msg_data, organization_id, db)

            elif msg_type == 'sync_rooms':
                await handle_sync_rooms(websocket, msg_data, organization_id, db)

            elif msg_type == 'ping':
                # Respond to ping
                await websocket.send_json({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                })

            else:
                # Unknown message type
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Unknown message type: {msg_type}'
                })

    except WebSocketDisconnect:
        manager.disconnect(organization_id)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(organization_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


async def handle_sync_guests(
    websocket: WebSocket,
    data: dict,
    organization_id: int,
    db: Session
):
    """Handle guest sync message"""
    try:
        guests_data = data.get('guests', [])

        if not guests_data:
            await websocket.send_json({
                'type': 'error',
                'message': 'No guest data provided'
            })
            return

        # Sync guests
        use_case = SyncGuestsUseCase(db)
        result = use_case.execute(guests_data, organization_id)

        # Send acknowledgment
        await websocket.send_json({
            'type': 'ack',
            'message': f'Synced {result["synced"]} guests successfully',
            'data': result,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'message': f'Failed to sync guests: {str(e)}'
        })


async def handle_sync_rooms(
    websocket: WebSocket,
    data: dict,
    organization_id: int,
    db: Session
):
    """Handle room sync message"""
    try:
        rooms_data = data.get('rooms', [])

        if not rooms_data:
            await websocket.send_json({
                'type': 'error',
                'message': 'No room data provided'
            })
            return

        # Sync rooms
        use_case = SyncRoomsUseCase(db)
        result = use_case.execute(rooms_data, organization_id)

        # Send acknowledgment
        await websocket.send_json({
            'type': 'ack',
            'message': f'Synced {result["created"] + result["updated"]} rooms successfully',
            'data': result,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'message': f'Failed to sync rooms: {str(e)}'
        })


@router.post("/pms/trigger-sync/{organization_id}")
async def trigger_sync(organization_id: int):
    """
    Trigger sync request to connected Bridge Agent

    Use this endpoint to request immediate sync from Bridge Agent
    """
    if organization_id not in manager.active_connections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bridge Agent not connected"
        )

    await manager.send_message(organization_id, {
        'type': 'sync_request',
        'message': 'Please sync data now',
        'timestamp': datetime.now().isoformat()
    })

    return {
        'success': True,
        'message': 'Sync request sent to Bridge Agent'
    }
