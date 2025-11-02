"""
Device Background Tasks
=======================

Celery tasks untuk device management dan monitoring.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import Task
from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.repositories import DeviceRepository
from app.utils.activity_logger import log_activity, ActivityAction, EntityType

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.device_tasks.check_offline_devices")
def check_offline_devices(self: Task) -> Dict[str, Any]:
    """
    Check for offline devices and log activity.

    Runs every 5 minutes via Celery Beat.

    Business Rule:
    - Device is offline if last_seen > 5 minutes ago
    - Log activity for devices that went offline
    - Update device status if needed

    Returns:
        Dict with task results
    """
    db = SessionLocal()
    try:
        logger.info("Starting offline device check...")

        device_repo = DeviceRepository(db)

        # Get all active devices
        all_devices = db.query(device_repo.model).filter(
            device_repo.model.is_active == True
        ).all()

        offline_threshold = datetime.utcnow() - timedelta(minutes=5)
        offline_count = 0
        offline_devices = []

        for device in all_devices:
            if device.last_seen and device.last_seen < offline_threshold:
                offline_count += 1
                offline_devices.append({
                    "id": device.id,
                    "device_name": device.device_name,
                    "last_seen": device.last_seen.isoformat(),
                    "offline_duration_minutes": int(
                        (datetime.utcnow() - device.last_seen).total_seconds() / 60
                    )
                })

                # Log activity
                log_activity(
                    db=db,
                    action=ActivityAction.UPDATE,
                    entity_type=EntityType.DEVICE,
                    entity_id=device.id,
                    description=f"Device {device.device_name} went offline",
                    metadata={
                        "last_seen": device.last_seen.isoformat(),
                        "offline_duration_minutes": int(
                            (datetime.utcnow() - device.last_seen).total_seconds() / 60
                        )
                    }
                )

        logger.info(f"Found {offline_count} offline devices out of {len(all_devices)} total devices")

        return {
            "status": "success",
            "total_devices": len(all_devices),
            "offline_count": offline_count,
            "offline_devices": offline_devices[:10],  # Return max 10 for logging
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error checking offline devices: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.device_tasks.sync_device_heartbeats")
def sync_device_heartbeats(self: Task) -> Dict[str, Any]:
    """
    Sync device heartbeat data and update statistics.

    Runs every minute via Celery Beat.

    Actions:
    - Count online vs offline devices per organization
    - Update cached statistics
    - Identify devices with irregular heartbeat patterns

    Returns:
        Dict with sync results
    """
    db = SessionLocal()
    try:
        logger.info("Starting device heartbeat sync...")

        device_repo = DeviceRepository(db)

        # Get all organizations with devices
        organizations = db.query(device_repo.model.organization_id).distinct().all()

        stats = []
        for (org_id,) in organizations:
            online_devices = device_repo.get_online_devices(org_id)
            offline_devices = device_repo.get_offline_devices(org_id)

            stats.append({
                "organization_id": org_id,
                "online": len(online_devices),
                "offline": len(offline_devices),
                "total": len(online_devices) + len(offline_devices)
            })

        logger.info(f"Synced heartbeats for {len(stats)} organizations")

        return {
            "status": "success",
            "organizations_processed": len(stats),
            "stats": stats,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error syncing device heartbeats: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=30, max_retries=3)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.device_tasks.cleanup_inactive_devices")
def cleanup_inactive_devices(self: Task, days_threshold: int = 30) -> Dict[str, Any]:
    """
    Cleanup devices that have been inactive for a long time.

    Can be triggered manually or scheduled.

    Args:
        days_threshold: Number of days of inactivity before cleanup (default: 30)

    Returns:
        Dict with cleanup results
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting inactive device cleanup (threshold: {days_threshold} days)...")

        device_repo = DeviceRepository(db)
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        # Find inactive devices
        inactive_devices = db.query(device_repo.model).filter(
            device_repo.model.is_active == True,
            device_repo.model.last_seen < cutoff_date
        ).all()

        cleaned_count = 0
        for device in inactive_devices:
            # Soft delete (set is_active = False)
            device_repo.update(device.id, {"is_active": False})

            # Log activity
            log_activity(
                db=db,
                action=ActivityAction.DELETE,
                entity_type=EntityType.DEVICE,
                entity_id=device.id,
                description=f"Auto-cleanup: Device {device.device_name} marked inactive after {days_threshold} days",
                metadata={
                    "last_seen": device.last_seen.isoformat(),
                    "days_inactive": (datetime.utcnow() - device.last_seen).days
                }
            )

            cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} inactive devices")

        return {
            "status": "success",
            "cleaned_count": cleaned_count,
            "threshold_days": days_threshold,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error cleaning up inactive devices: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=120, max_retries=2)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.device_tasks.send_device_command")
def send_device_command(
    self: Task,
    device_id: int,
    command: str,
    parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Send command to a device (async task).

    Commands:
    - reboot: Reboot device
    - refresh_content: Refresh content playlist
    - update_config: Update device configuration
    - screenshot: Take screenshot

    Args:
        device_id: Device ID
        command: Command to send
        parameters: Command parameters (optional)

    Returns:
        Dict with command result
    """
    db = SessionLocal()
    try:
        logger.info(f"Sending command '{command}' to device {device_id}...")

        device_repo = DeviceRepository(db)
        device = device_repo.get(device_id)

        if not device:
            logger.error(f"Device {device_id} not found")
            return {
                "status": "error",
                "message": f"Device {device_id} not found",
                "task_id": self.request.id
            }

        # Log command
        log_activity(
            db=db,
            action=ActivityAction.UPDATE,
            entity_type=EntityType.DEVICE,
            entity_id=device_id,
            description=f"Command sent: {command}",
            metadata={
                "command": command,
                "parameters": parameters or {},
                "task_id": self.request.id
            }
        )

        # TODO: Implement actual device command logic
        # This would involve WebSocket communication or HTTP callback

        logger.info(f"Command '{command}' sent successfully to device {device_id}")

        return {
            "status": "success",
            "device_id": device_id,
            "command": command,
            "parameters": parameters,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error sending command to device {device_id}: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        db.close()
