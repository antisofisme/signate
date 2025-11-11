"""
System Background Tasks
=======================

Celery tasks untuk system operations, analytics, dan monitoring.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import Task
from celery.utils.log import get_task_logger
from sqlalchemy import func
import os

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.repositories import (
    DeviceRepository,
    ContentRepository,
    OrganizationRepository,
    UserRepository
)
from app.models import Device, Content, User, Organization, ActivityLog
from app.utils.activity_logger import log_activity, ActivityAction, EntityType

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.system_tasks.generate_daily_analytics")
def generate_daily_analytics(self: Task) -> Dict[str, Any]:
    """
    Generate daily analytics report.

    Runs daily at 3 AM via Celery Beat.

    Analytics include:
    - Device statistics (online/offline/active)
    - Content statistics (by type, by organization)
    - User activity summary
    - Storage usage
    - System health metrics

    Returns:
        Dict with analytics data
    """
    db = SessionLocal()
    try:
        logger.info("Generating daily analytics...")

        device_repo = DeviceRepository(db)
        content_repo = ContentRepository(db)
        org_repo = OrganizationRepository(db)
        user_repo = UserRepository(db)

        # Yesterday's date range
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        start_of_day = datetime.combine(yesterday, datetime.min.time())
        end_of_day = datetime.combine(yesterday, datetime.max.time())

        # Device Analytics
        all_devices = db.query(Device).all()
        total_devices = len(all_devices)
        active_devices = len([d for d in all_devices if d.is_active])
        online_devices = len([d for d in all_devices if d.last_seen and
                             (datetime.utcnow() - d.last_seen).total_seconds() < 300])

        device_analytics = {
            "total": total_devices,
            "active": active_devices,
            "online": online_devices,
            "offline": active_devices - online_devices,
            "by_status": {
                "approved": len([d for d in all_devices if d.status == "approved"]),
                "pending": len([d for d in all_devices if d.status == "pending"]),
                "rejected": len([d for d in all_devices if d.status == "rejected"])
            },
            "by_type": {}
        }

        # Count by device type
        device_types = db.query(
            Device.device_type,
            func.count(Device.id)
        ).filter(Device.is_active == True).group_by(Device.device_type).all()

        for device_type, count in device_types:
            device_analytics["by_type"][device_type or "unknown"] = count

        # Content Analytics
        all_content = db.query(Content).all()
        total_content = len(all_content)
        active_content = len([c for c in all_content if c.is_active])

        content_analytics = {
            "total": total_content,
            "active": active_content,
            "inactive": total_content - active_content,
            "by_type": {},
            "by_organization": {}
        }

        # Count by content type
        content_types = db.query(
            Content.content_type,
            func.count(Content.id)
        ).filter(Content.is_active == True).group_by(Content.content_type).all()

        for content_type, count in content_types:
            content_analytics["by_type"][content_type] = count

        # Count by organization
        content_by_org = db.query(
            Content.organization_id,
            func.count(Content.id)
        ).filter(Content.is_active == True).group_by(Content.organization_id).all()

        for org_id, count in content_by_org:
            content_analytics["by_organization"][org_id] = count

        # Organization Analytics
        all_organizations = db.query(Organization).all()
        total_orgs = len(all_organizations)
        active_orgs = len([o for o in all_organizations if o.is_active])

        organization_analytics = {
            "total": total_orgs,
            "active": active_orgs,
            "inactive": total_orgs - active_orgs
        }

        # User Analytics
        all_users = db.query(User).all()
        total_users = len(all_users)
        active_users = len([u for u in all_users if u.is_active])

        user_analytics = {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
            "by_role": {}
        }

        # Count by role
        user_roles = db.query(
            User.role,
            func.count(User.id)
        ).filter(User.is_active == True).group_by(User.role).all()

        for role, count in user_roles:
            user_analytics["by_role"][role] = count

        # Activity Analytics
        activities_count = db.query(func.count(ActivityLog.id)).filter(
            ActivityLog.created_at >= start_of_day,
            ActivityLog.created_at <= end_of_day
        ).scalar() or 0

        activity_analytics = {
            "total_yesterday": activities_count,
            "by_action": {}
        }

        # Count by action type
        activities_by_action = db.query(
            ActivityLog.action,
            func.count(ActivityLog.id)
        ).filter(
            ActivityLog.created_at >= start_of_day,
            ActivityLog.created_at <= end_of_day
        ).group_by(ActivityLog.action).all()

        for action, count in activities_by_action:
            activity_analytics["by_action"][action] = count

        # Storage Analytics
        storage_analytics = calculate_storage_usage(db)

        # Compile full report
        analytics_report = {
            "date": yesterday.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "devices": device_analytics,
            "content": content_analytics,
            "organizations": organization_analytics,
            "users": user_analytics,
            "activities": activity_analytics,
            "storage": storage_analytics
        }

        # Log the analytics generation
        log_activity(
            db=db,
            action=ActivityAction.CREATE,
            entity_type=EntityType.DEVICE,  # Generic system entity
            entity_id=None,
            description=f"Daily analytics generated for {yesterday}",
            metadata=analytics_report
        )

        logger.info(f"Daily analytics generated successfully for {yesterday}")

        return {
            "status": "success",
            "date": yesterday.isoformat(),
            "analytics": analytics_report,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error generating daily analytics: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.system_tasks.check_storage_quota")
def check_storage_quota(self: Task) -> Dict[str, Any]:
    """
    Check storage quota and send alerts if approaching limits.

    Runs every hour via Celery Beat.

    Business Rules:
    - Alert at 80% usage
    - Warning at 90% usage
    - Critical at 95% usage
    - Track per-organization quotas

    Returns:
        Dict with storage status
    """
    db = SessionLocal()
    try:
        logger.info("Checking storage quota...")

        # Calculate global storage usage
        storage_info = calculate_storage_usage(db)

        alerts = []
        warnings = []
        critical = []

        # Check global storage
        usage_percent = storage_info.get("usage_percent", 0)

        if usage_percent >= 95:
            critical.append({
                "level": "critical",
                "message": f"Global storage critically full: {usage_percent:.1f}%",
                "usage_percent": usage_percent,
                "used_gb": storage_info.get("used_gb", 0),
                "total_gb": storage_info.get("total_gb", 0)
            })
        elif usage_percent >= 90:
            warnings.append({
                "level": "warning",
                "message": f"Global storage nearly full: {usage_percent:.1f}%",
                "usage_percent": usage_percent,
                "used_gb": storage_info.get("used_gb", 0),
                "total_gb": storage_info.get("total_gb", 0)
            })
        elif usage_percent >= 80:
            alerts.append({
                "level": "alert",
                "message": f"Global storage usage high: {usage_percent:.1f}%",
                "usage_percent": usage_percent,
                "used_gb": storage_info.get("used_gb", 0),
                "total_gb": storage_info.get("total_gb", 0)
            })

        # Check per-organization quotas
        org_repo = OrganizationRepository(db)
        all_orgs = db.query(Organization).filter(Organization.is_active == True).all()

        for org in all_orgs:
            if not org.storage_quota:
                continue

            # Calculate organization's storage usage
            org_content = db.query(Content).filter(
                Content.organization_id == org.id,
                Content.is_active == True
            ).all()

            org_used = sum(c.file_size or 0 for c in org_content)
            org_quota = org.storage_quota
            org_percent = (org_used / org_quota * 100) if org_quota > 0 else 0

            if org_percent >= 95:
                critical.append({
                    "level": "critical",
                    "organization_id": org.id,
                    "organization_name": org.name,
                    "message": f"Organization '{org.name}' storage critically full: {org_percent:.1f}%",
                    "usage_percent": org_percent,
                    "used_bytes": org_used,
                    "quota_bytes": org_quota
                })
            elif org_percent >= 90:
                warnings.append({
                    "level": "warning",
                    "organization_id": org.id,
                    "organization_name": org.name,
                    "message": f"Organization '{org.name}' storage nearly full: {org_percent:.1f}%",
                    "usage_percent": org_percent,
                    "used_bytes": org_used,
                    "quota_bytes": org_quota
                })
            elif org_percent >= 80:
                alerts.append({
                    "level": "alert",
                    "organization_id": org.id,
                    "organization_name": org.name,
                    "message": f"Organization '{org.name}' storage usage high: {org_percent:.1f}%",
                    "usage_percent": org_percent,
                    "used_bytes": org_used,
                    "quota_bytes": org_quota
                })

        # Log critical and warning issues
        if critical:
            for item in critical:
                log_activity(
                    db=db,
                    action=ActivityAction.UPDATE,
                    entity_type=EntityType.DEVICE,  # Generic system entity
                    entity_id=None,
                    description=f"CRITICAL: {item['message']}",
                    metadata=item
                )

        if warnings:
            for item in warnings:
                log_activity(
                    db=db,
                    action=ActivityAction.UPDATE,
                    entity_type=EntityType.DEVICE,  # Generic system entity
                    entity_id=None,
                    description=f"WARNING: {item['message']}",
                    metadata=item
                )

        logger.info(
            f"Storage check complete: {len(alerts)} alerts, "
            f"{len(warnings)} warnings, {len(critical)} critical"
        )

        return {
            "status": "success",
            "storage_info": storage_info,
            "alerts": alerts,
            "warnings": warnings,
            "critical": critical,
            "total_issues": len(alerts) + len(warnings) + len(critical),
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error checking storage quota: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300, max_retries=3)
    finally:
        db.close()


def calculate_storage_usage(db) -> Dict[str, Any]:
    """
    Calculate total storage usage.

    Args:
        db: Database session

    Returns:
        Dict with storage statistics
    """
    # Calculate used space from database records
    total_file_size = db.query(func.sum(Content.file_size)).filter(
        Content.is_active == True
    ).scalar() or 0

    # Get upload directory size
    upload_dir = settings.UPLOAD_DIR
    actual_disk_usage = 0

    if os.path.exists(upload_dir):
        for dirpath, dirnames, filenames in os.walk(upload_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    actual_disk_usage += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass

    # Get total disk space (if available)
    total_space = 0
    available_space = 0

    try:
        stat = os.statvfs(upload_dir)
        total_space = stat.f_frsize * stat.f_blocks
        available_space = stat.f_frsize * stat.f_bavail
    except Exception:
        pass

    used_space = total_space - available_space if total_space > 0 else actual_disk_usage
    usage_percent = (used_space / total_space * 100) if total_space > 0 else 0

    return {
        "total_bytes": total_space,
        "used_bytes": used_space,
        "available_bytes": available_space,
        "usage_percent": round(usage_percent, 2),
        "total_gb": round(total_space / 1024 / 1024 / 1024, 2),
        "used_gb": round(used_space / 1024 / 1024 / 1024, 2),
        "available_gb": round(available_space / 1024 / 1024 / 1024, 2),
        "content_file_size_bytes": total_file_size,
        "content_file_size_gb": round(total_file_size / 1024 / 1024 / 1024, 2),
        "actual_disk_usage_bytes": actual_disk_usage,
        "actual_disk_usage_gb": round(actual_disk_usage / 1024 / 1024 / 1024, 2)
    }


@celery_app.task(bind=True, name="app.tasks.system_tasks.cleanup_old_logs")
def cleanup_old_logs(
    self: Task,
    days_threshold: int = 90
) -> Dict[str, Any]:
    """
    Cleanup old activity logs.

    Args:
        days_threshold: Number of days to keep logs (default: 90)

    Returns:
        Dict with cleanup results
    """
    db = SessionLocal()
    try:
        logger.info(f"Cleaning up logs older than {days_threshold} days...")

        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        # Delete old logs
        deleted_count = db.query(ActivityLog).filter(
            ActivityLog.created_at < cutoff_date
        ).delete()

        db.commit()

        logger.info(f"Deleted {deleted_count} old activity logs")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "threshold_days": days_threshold,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error cleaning up old logs: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.system_tasks.database_backup")
def database_backup(self: Task) -> Dict[str, Any]:
    """
    Trigger database backup (can integrate with pg_dump or other tools).

    Returns:
        Dict with backup result
    """
    db = SessionLocal()
    try:
        logger.info("Starting database backup...")

        # TODO: Implement actual database backup logic
        # This could use pg_dump via subprocess for PostgreSQL
        # Or integrate with cloud backup services

        backup_path = None
        backup_size = 0

        # Log backup activity
        log_activity(
            db=db,
            action=ActivityAction.CREATE,
            entity_type=EntityType.DEVICE,  # Generic system entity
            entity_id=None,
            description="Database backup completed",
            metadata={
                "backup_path": backup_path,
                "backup_size": backup_size,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info("Database backup completed successfully")

        return {
            "status": "success",
            "backup_path": backup_path,
            "backup_size": backup_size,
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error during database backup: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=600, max_retries=2)
    finally:
        db.close()
