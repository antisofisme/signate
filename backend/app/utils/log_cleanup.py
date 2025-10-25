"""
Device Log Cleanup Utility
Automatically cleans up old device logs from database
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.device_log import DeviceLog
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


def cleanup_old_logs(retention_hours: int = 24):
    """
    Delete device logs older than specified hours

    Args:
        retention_hours: Keep logs from last N hours (default: 24 hours = 1 day)

    Returns:
        Number of logs deleted
    """
    db: Session = SessionLocal()

    try:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)

        # Delete old logs
        deleted_count = db.query(DeviceLog).filter(
            DeviceLog.timestamp < cutoff_time
        ).delete()

        db.commit()

        logger.info(f"✅ Cleaned up {deleted_count} device logs older than {retention_hours} hours")

        return deleted_count

    except Exception as e:
        logger.error(f"❌ Error cleaning up logs: {e}")
        db.rollback()
        return 0

    finally:
        db.close()


def cleanup_all_logs():
    """Delete ALL device logs (use with caution!)"""
    db: Session = SessionLocal()

    try:
        deleted_count = db.query(DeviceLog).delete()
        db.commit()

        logger.warning(f"⚠️ Deleted ALL {deleted_count} device logs")

        return deleted_count

    except Exception as e:
        logger.error(f"❌ Error deleting all logs: {e}")
        db.rollback()
        return 0

    finally:
        db.close()
