"""
WebSocket Service Helper Functions
Provides utilities for sending WebSocket messages from other parts of the application
"""

import json
import logging
from app.core.logging import StructuredLogger
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.api.websocket_v2 import manager, MessageType

logger = StructuredLogger(__name__)


class WebSocketService:
    """
    Service class for sending WebSocket messages from anywhere in the application
    """

    @staticmethod
    async def notify_playlist_update(
        device_ids: List[int],
        playlist_id: int,
        playlist_name: str,
        action: str = "assigned"
    ) -> bool:
        """
        Notify devices about playlist updates

        Args:
            device_ids: List of device IDs to notify
            playlist_id: ID of the playlist
            playlist_name: Name of the playlist
            action: Type of update (assigned, updated, removed)

        Returns:
            Success status
        """
        try:
            data = {
                "playlist_id": playlist_id,
                "playlist_name": playlist_name,
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }

            results = await manager.broadcast_to_devices(
                device_ids,
                MessageType.PLAYLIST_UPDATE,
                data
            )

            success_count = sum(1 for success in results.values() if success)
            logger.info(
                f"Playlist update sent to {success_count}/{len(device_ids)} devices"
            )

            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send playlist update: {e}")
            return False

    @staticmethod
    async def notify_content_ready(
        device_ids: List[int],
        content_id: int,
        content_title: str,
        content_url: str,
        content_type: str = "video"
    ) -> bool:
        """
        Notify devices that content is ready for playback

        Args:
            device_ids: List of device IDs to notify
            content_id: ID of the content
            content_title: Title of the content
            content_url: URL to access the content
            content_type: Type of content (video, image, etc.)

        Returns:
            Success status
        """
        try:
            data = {
                "content_id": content_id,
                "content_title": content_title,
                "content_url": content_url,
                "content_type": content_type,
                "timestamp": datetime.utcnow().isoformat()
            }

            results = await manager.broadcast_to_devices(
                device_ids,
                MessageType.CONTENT_READY,
                data
            )

            success_count = sum(1 for success in results.values() if success)
            logger.info(
                f"Content ready notification sent to {success_count}/{len(device_ids)} devices"
            )

            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send content ready notification: {e}")
            return False

    @staticmethod
    async def send_command_to_device(
        device_id: int,
        command: str,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send command to a specific device

        Args:
            device_id: Device ID
            command: Command to execute (reload, screenshot, restart, etc.)
            params: Optional command parameters

        Returns:
            Success status
        """
        try:
            data = {
                "command": command,
                "params": params or {},
                "timestamp": datetime.utcnow().isoformat()
            }

            success = await manager.send_to_device(
                device_id,
                MessageType.COMMAND,
                data
            )

            if success:
                logger.info(f"Command '{command}' sent to device {device_id}")
            else:
                logger.warning(f"Failed to send command '{command}' to device {device_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to send command to device {device_id}: {e}")
            return False

    @staticmethod
    async def broadcast_command(
        command: str,
        params: Optional[Dict[str, Any]] = None,
        device_ids: Optional[List[int]] = None
    ) -> Dict[int, bool]:
        """
        Broadcast command to multiple devices

        Args:
            command: Command to execute
            params: Optional command parameters
            device_ids: Optional list of device IDs (if None, sends to all)

        Returns:
            Dict of device_id -> success status
        """
        try:
            data = {
                "command": command,
                "params": params or {},
                "timestamp": datetime.utcnow().isoformat()
            }

            if device_ids:
                results = await manager.broadcast_to_devices(
                    device_ids,
                    MessageType.COMMAND,
                    data
                )
            else:
                results = await manager.broadcast_to_all_devices(
                    MessageType.COMMAND,
                    data
                )

            success_count = sum(1 for success in results.values() if success)
            logger.info(
                f"Command '{command}' broadcast to {success_count}/{len(results)} devices"
            )

            return results

        except Exception as e:
            logger.error(f"Failed to broadcast command: {e}")
            return {}

    @staticmethod
    async def notify_transcoding_progress(
        content_id: int,
        progress: int,
        stage: str,
        eta: Optional[str] = None
    ) -> bool:
        """
        Notify admin dashboard about transcoding progress

        Args:
            content_id: Content ID being transcoded
            progress: Progress percentage (0-100)
            stage: Current stage of transcoding
            eta: Estimated time of completion

        Returns:
            Success status
        """
        try:
            data = {
                "content_id": content_id,
                "progress": progress,
                "stage": stage,
                "eta": eta,
                "timestamp": datetime.utcnow().isoformat()
            }

            count = await manager.broadcast_to_admins(
                MessageType.TRANSCODING_PROGRESS,
                data
            )

            return count > 0

        except Exception as e:
            logger.error(f"Failed to send transcoding progress: {e}")
            return False

    @staticmethod
    async def notify_device_status_change(
        device_id: int,
        device_name: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Notify admin dashboard about device status change

        Args:
            device_id: Device ID
            device_name: Device name
            status: New status (online, offline, error, etc.)
            details: Optional status details

        Returns:
            Success status
        """
        try:
            data = {
                "device_id": device_id,
                "device_name": device_name,
                "status": status,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }

            count = await manager.broadcast_to_admins(
                MessageType.DEVICE_STATUS,
                data
            )

            return count > 0

        except Exception as e:
            logger.error(f"Failed to send device status update: {e}")
            return False

    @staticmethod
    async def get_connected_devices() -> List[int]:
        """
        Get list of currently connected device IDs

        Returns:
            List of device IDs
        """
        try:
            stats = await manager.get_connection_stats()
            return list(stats.get("devices", {}).keys())

        except Exception as e:
            logger.error(f"Failed to get connected devices: {e}")
            return []

    @staticmethod
    async def is_device_connected(device_id: int) -> bool:
        """
        Check if a specific device is connected via WebSocket

        Args:
            device_id: Device ID to check

        Returns:
            True if connected, False otherwise
        """
        try:
            stats = await manager.get_connection_stats()
            return device_id in stats.get("devices", {})

        except Exception as e:
            logger.error(f"Failed to check device connection: {e}")
            return False


# Global service instance
websocket_service = WebSocketService()


# Convenience functions for common operations
async def notify_all_devices(message_type: str, data: dict) -> int:
    """
    Send notification to all connected devices

    Args:
        message_type: Type of message
        data: Message data

    Returns:
        Number of devices notified
    """
    try:
        msg_type = MessageType(message_type)
        results = await manager.broadcast_to_all_devices(msg_type, data)
        return sum(1 for success in results.values() if success)

    except Exception as e:
        logger.error(f"Failed to notify all devices: {e}")
        return 0


async def notify_device_group(
    tag_id: int,
    message_type: str,
    data: dict,
    db_session
) -> int:
    """
    Send notification to all devices in a tag group

    Args:
        tag_id: Tag ID
        message_type: Type of message
        data: Message data
        db_session: Database session

    Returns:
        Number of devices notified
    """
    try:
        from app.models.device import Device, DeviceTag

        # Get all device IDs with this tag
        device_ids = db_session.query(Device.id).join(
            DeviceTag, Device.id == DeviceTag.device_id
        ).filter(
            DeviceTag.tag_id == tag_id,
            Device.is_approved == True
        ).all()

        device_ids = [d[0] for d in device_ids]

        if not device_ids:
            return 0

        msg_type = MessageType(message_type)
        results = await manager.broadcast_to_devices(device_ids, msg_type, data)
        return sum(1 for success in results.values() if success)

    except Exception as e:
        logger.error(f"Failed to notify device group: {e}")
        return 0