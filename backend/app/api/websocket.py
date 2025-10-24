"""
WebSocket endpoints for real-time log streaming
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import logging
import json
import asyncio
import redis.asyncio as redis

from app.core.database import get_db
from app.core.config import settings
from app.models.device import Device

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/logs/{device_id}")
async def websocket_logs(
    websocket: WebSocket,
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for streaming device logs in real-time
    
    Args:
        websocket: WebSocket connection
        device_id: Device ID to stream logs for
        db: Database session
    
    Flow:
        1. Accept WebSocket connection
        2. Verify device exists
        3. Subscribe to Redis channel: device_logs:{device_id}
        4. Stream logs to client in real-time
        5. Handle disconnect gracefully
    
    Message Format:
        {
            "id": 123,
            "device_id": 1,
            "log_level": "log",
            "message": "Content loaded",
            "source": "browser-viewer",
            "timestamp": "2025-10-24T12:34:56.789Z"
        }
    """
    await websocket.accept()
    
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            await websocket.send_json({
                "error": f"Device {device_id} not found"
            })
            await websocket.close()
            return
        
        logger.info(f"📡 WebSocket connected for device {device_id} ({device.device_name})")
        
        # Send initial connection success message
        await websocket.send_json({
            "type": "connected",
            "device_id": device_id,
            "device_name": device.device_name,
            "message": "Connected to log stream"
        })
        
        # Create Redis async client for pub/sub
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        
        pubsub = redis_client.pubsub()
        channel = f"device_logs:{device_id}"
        
        # Subscribe to Redis channel
        await pubsub.subscribe(channel)
        logger.info(f"📻 Subscribed to Redis channel: {channel}")
        
        # Send subscription confirmation
        await websocket.send_json({
            "type": "subscribed",
            "channel": channel,
            "message": f"Listening for logs from device {device_id}"
        })
        
        # Listen for messages from Redis and forward to WebSocket
        async def redis_listener():
            """Listen to Redis pub/sub and forward to WebSocket"""
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        # Parse log data
                        log_data = json.loads(message["data"])
                        
                        # Forward to WebSocket client
                        await websocket.send_json({
                            "type": "log",
                            **log_data
                        })
                        
            except Exception as e:
                logger.error(f"Redis listener error: {e}")
        
        # Listen for client messages (e.g., ping/pong)
        async def websocket_receiver():
            """Receive messages from WebSocket client"""
            try:
                while True:
                    data = await websocket.receive_json()
                    
                    # Handle ping
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for device {device_id}")
            except Exception as e:
                logger.error(f"WebSocket receiver error: {e}")
        
        # Run both listeners concurrently
        await asyncio.gather(
            redis_listener(),
            websocket_receiver()
        )
        
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for device {device_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for device {device_id}: {e}")
        try:
            await websocket.send_json({
                "error": str(e)
            })
        except:
            pass
    finally:
        # Cleanup
        try:
            await pubsub.unsubscribe(channel)
            await redis_client.close()
            logger.info(f"🔌 Cleaned up Redis connection for device {device_id}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
