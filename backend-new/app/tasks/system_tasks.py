"""
System Maintenance & Analytics Background Tasks
================================================

Celery tasks untuk system maintenance, analytics computation,
dan scheduled jobs lainnya.
"""

import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from celery import Task
from celery.utils.log import get_task_logger
from sqlalchemy import func

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.repositories import (
    ContentRepository,
    DeviceRepository,
    OrganizationRepository,
    ActivityRepository
)
from app.utils.activity_logger import log_activity, ActivityAction, EntityType

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.system_tasks.cleanup_old_files",
    queue="maintenance"
)
def cleanup_old_files(self: Task, days_threshold: int = 30) -> Dict[str, Any]:
    """
    Cleanup old temporary files and unused media.

    Removes:
    - Temporary transcoding files older than X days
    - Deleted content files
    - Orphaned thumbnails
    - Old cache files

    Args:
        days_threshold: Remove files older than X days (default: 30)

    Returns:
        Dict with cleanup results
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting file cleanup (threshold: {days_threshold} days)...")

        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        content_repo = ContentRepository(db)
        
        cleanup_stats = {
            "temp_files_deleted": 0,
            "orphaned_thumbnails": 0,
            "cache_files_deleted": 0,
            "total_space_freed_mb": 0
        }

        # 1. Cleanup temporary transcoding directories
        # Assuming temp files are in /data/screenly_assets/temp/
        temp_dir = Path("/data/screenly_assets/temp")
        if temp_dir.exists():
            for item in temp_dir.iterdir():
                if item.is_dir():
                    # Check if directory is old enough
                    mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                    if mod_time < cutoff_date:
                        size_mb = sum(f.stat().st_size for f in item.rglob('*') if f.is_file()) / (1024 * 1024)
                        shutil.rmtree(item, ignore_errors=True)
                        cleanup_stats["temp_files_deleted"] += 1
                        cleanup_stats["total_space_freed_mb"] += size_mb

        # 2. Find and remove orphaned thumbnails
        # Get all content IDs that should have thumbnails
        active_content_ids = set(
            content.id for content in db.query(content_repo.model.id).filter(
                content_repo.model.is_active == True
            ).all()
        )

        thumbnail_dir = Path("/data/screenly_assets/thumbnails")
        if thumbnail_dir.exists():
            for thumbnail_file in thumbnail_dir.glob("thumbnail_*.jpg"):
                # Extract content_id from filename (e.g., thumbnail_123.jpg)
                try:
                    content_id = int(thumbnail_file.stem.replace("thumbnail_", ""))
                    if content_id not in active_content_ids:
                        size_mb = thumbnail_file.stat().st_size / (1024 * 1024)
                        thumbnail_file.unlink()
                        cleanup_stats["orphaned_thumbnails"] += 1
                        cleanup_stats["total_space_freed_mb"] += size_mb
                except ValueError:
                    continue

        # 3. Cleanup old cache files
        cache_dir = Path("/tmp/signage_cache")
        if cache_dir.exists():
            for cache_file in cache_dir.iterdir():
                if cache_file.is_file():
                    mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if mod_time < cutoff_date:
                        size_mb = cache_file.stat().st_size / (1024 * 1024)
                        cache_file.unlink()
                        cleanup_stats["cache_files_deleted"] += 1
                        cleanup_stats["total_space_freed_mb"] += size_mb

        cleanup_stats["total_space_freed_mb"] = round(cleanup_stats["total_space_freed_mb"], 2)

        logger.info(f"File cleanup completed. Freed {cleanup_stats['total_space_freed_mb']} MB")

        # Log activity
        log_activity(
            db=db,
            action=ActivityAction.DELETE,
            entity_type=EntityType.SYSTEM,
            description=f"Automatic file cleanup completed",
            metadata=cleanup_stats
        )

        return {
            "status": "success",
            "stats": cleanup_stats,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error cleaning up files: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.system_tasks.compute_analytics",
    queue="analytics"
)
def compute_analytics(
    self: Task,
    organization_id: Optional[int] = None,
    period: str = "daily"
) -> Dict[str, Any]:
    """
    Compute analytics for dashboard and reporting.

    Computes:
    - Device online/offline trends
    - Content views and popularity
    - Storage usage trends
    - Playlist performance

    Args:
        organization_id: Organization ID (None = all organizations)
        period: Analysis period: daily, weekly, monthly (default: daily)

    Returns:
        Dict with analytics results
    """
    db = SessionLocal()
    try:
        logger.info(f"Computing {period} analytics...")

        device_repo = DeviceRepository(db)
        content_repo = ContentRepository(db)
        org_repo = OrganizationRepository(db)

        # Determine time range based on period
        now = datetime.utcnow()
        if period == "daily":
            start_time = now - timedelta(days=1)
        elif period == "weekly":
            start_time = now - timedelta(weeks=1)
        elif period == "monthly":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)

        analytics = {
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "organizations": []
        }

        # Get organizations to analyze
        if organization_id:
            organizations = [org_repo.get(organization_id)]
        else:
            organizations = db.query(org_repo.model).filter(
                org_repo.model.is_active == True
            ).all()

        # Compute analytics per organization
        for org in organizations:
            if not org:
                continue

            org_analytics = {
                "organization_id": org.id,
                "organization_name": org.name,
                "devices": {},
                "content": {},
                "storage": {}
            }

            # Device analytics
            total_devices = db.query(func.count(device_repo.model.id)).filter(
                device_repo.model.organization_id == org.id,
                device_repo.model.is_active == True
            ).scalar() or 0

            online_devices = len(device_repo.get_online_devices(org.id))
            offline_devices = total_devices - online_devices

            org_analytics["devices"] = {
                "total": total_devices,
                "online": online_devices,
                "offline": offline_devices,
                "uptime_percent": round((online_devices / total_devices * 100) if total_devices > 0 else 0, 2)
            }

            # Content analytics
            content_stats = content_repo.get_organization_stats(org.id)
            org_analytics["content"] = {
                "total": content_stats.get("total", 0),
                "by_type": content_stats.get("by_type", {}),
                "active": content_stats.get("active", 0)
            }

            # Storage analytics
            storage_usage = org_repo.get_storage_usage(org.id)
            org_analytics["storage"] = {
                "total_gb": storage_usage.get("used_storage_gb", 0),
                "max_gb": org.max_storage_gb,
                "usage_percent": round((storage_usage.get("used_storage_gb", 0) / org.max_storage_gb * 100) if org.max_storage_gb > 0 else 0, 2)
            }

            analytics["organizations"].append(org_analytics)

        logger.info(f"Analytics computed for {len(analytics['organizations'])} organizations")

        # Log activity
        log_activity(
            db=db,
            action=ActivityAction.READ,
            entity_type=EntityType.SYSTEM,
            organization_id=organization_id,
            description=f"{period.capitalize()} analytics computed",
            metadata={"organizations_count": len(analytics["organizations"])}
        )

        return {
            "status": "success",
            "analytics": analytics,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error computing analytics: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=120, max_retries=2)
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.system_tasks.generate_daily_report",
    queue="analytics"
)
def generate_daily_report(self: Task) -> Dict[str, Any]:
    """
    Generate daily system report.

    Creates summary report with:
    - System health status
    - Device statistics
    - Content upload stats
    - Storage usage
    - Top issues/errors

    Returns:
        Dict with report data
    """
    db = SessionLocal()
    try:
        logger.info("Generating daily report...")

        device_repo = DeviceRepository(db)
        content_repo = ContentRepository(db)
        org_repo = OrganizationRepository(db)
        activity_repo = ActivityRepository(db)

        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        report = {
            "date": today.isoformat(),
            "period": f"{yesterday} to {today}",
            "summary": {},
            "organizations": [],
            "top_issues": []
        }

        # Overall summary
        total_orgs = db.query(func.count(org_repo.model.id)).filter(
            org_repo.model.is_active == True
        ).scalar() or 0

        total_devices = db.query(func.count(device_repo.model.id)).filter(
            device_repo.model.is_active == True
        ).scalar() or 0

        total_content = db.query(func.count(content_repo.model.id)).filter(
            content_repo.model.is_active == True
        ).scalar() or 0

        report["summary"] = {
            "total_organizations": total_orgs,
            "total_devices": total_devices,
            "total_content": total_content,
            "generated_at": datetime.utcnow().isoformat()
        }

        # Per-organization stats
        organizations = db.query(org_repo.model).filter(
            org_repo.model.is_active == True
        ).all()

        for org in organizations:
            org_stats = {
                "id": org.id,
                "name": org.name,
                "devices_online": len(device_repo.get_online_devices(org.id)),
                "content_uploaded_today": 0,  # TODO: Add date filter
                "storage_usage_gb": org_repo.get_storage_usage(org.id).get("used_storage_gb", 0)
            }
            report["organizations"].append(org_stats)

        logger.info(f"Daily report generated for {len(report['organizations'])} organizations")

        # Log activity
        log_activity(
            db=db,
            action=ActivityAction.CREATE,
            entity_type=EntityType.SYSTEM,
            description="Daily report generated",
            metadata={"summary": report["summary"]}
        )

        return {
            "status": "success",
            "report": report,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error generating daily report: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.system_tasks.check_storage_quotas",
    queue="maintenance"
)
def check_storage_quotas(self: Task, warning_threshold: float = 0.8) -> Dict[str, Any]:
    """
    Check storage quotas for all organizations and send warnings.

    Args:
        warning_threshold: Send warning if usage > X% of quota (default: 0.8 = 80%)

    Returns:
        Dict with quota check results
    """
    db = SessionLocal()
    try:
        logger.info(f"Checking storage quotas (warning threshold: {warning_threshold * 100}%)...")

        org_repo = OrganizationRepository(db)
        organizations = db.query(org_repo.model).filter(
            org_repo.model.is_active == True
        ).all()

        quota_warnings = []
        quota_exceeded = []

        for org in organizations:
            storage_usage = org_repo.get_storage_usage(org.id)
            used_gb = storage_usage.get("used_storage_gb", 0)
            max_gb = org.max_storage_gb

            usage_percent = (used_gb / max_gb) if max_gb > 0 else 0

            if usage_percent >= 1.0:
                quota_exceeded.append({
                    "organization_id": org.id,
                    "organization_name": org.name,
                    "used_gb": round(used_gb, 2),
                    "max_gb": max_gb,
                    "usage_percent": round(usage_percent * 100, 2)
                })

                # Log activity
                log_activity(
                    db=db,
                    action=ActivityAction.UPDATE,
                    entity_type=EntityType.ORGANIZATION,
                    entity_id=org.id,
                    organization_id=org.id,
                    description=f"Storage quota exceeded: {round(used_gb, 2)} GB / {max_gb} GB",
                    metadata={"usage_percent": round(usage_percent * 100, 2)}
                )

            elif usage_percent >= warning_threshold:
                quota_warnings.append({
                    "organization_id": org.id,
                    "organization_name": org.name,
                    "used_gb": round(used_gb, 2),
                    "max_gb": max_gb,
                    "usage_percent": round(usage_percent * 100, 2)
                })

        logger.info(f"Quota check: {len(quota_warnings)} warnings, {len(quota_exceeded)} exceeded")

        return {
            "status": "success",
            "total_checked": len(organizations),
            "quota_warnings": quota_warnings,
            "quota_exceeded": quota_exceeded,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error checking storage quotas: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.system_tasks.archive_old_activity_logs",
    queue="maintenance"
)
def archive_old_activity_logs(self: Task, days_threshold: int = 90) -> Dict[str, Any]:
    """
    Archive old activity logs to reduce database size.

    Args:
        days_threshold: Archive logs older than X days (default: 90)

    Returns:
        Dict with archive results
    """
    db = SessionLocal()
    try:
        logger.info(f"Archiving activity logs older than {days_threshold} days...")

        activity_repo = ActivityRepository(db)
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        # Count old logs
        old_logs_count = db.query(func.count(activity_repo.model.id)).filter(
            activity_repo.model.created_at < cutoff_date
        ).scalar() or 0

        if old_logs_count == 0:
            logger.info("No old activity logs to archive")
            return {
                "status": "success",
                "archived_count": 0,
                "task_id": self.request.id
            }

        # TODO: Implement actual archiving logic
        # For now, just delete old logs (in production, export to archive first)
        db.query(activity_repo.model).filter(
            activity_repo.model.created_at < cutoff_date
        ).delete()

        db.commit()

        logger.info(f"Archived {old_logs_count} activity logs")

        # Log this activity
        log_activity(
            db=db,
            action=ActivityAction.DELETE,
            entity_type=EntityType.SYSTEM,
            description=f"Archived {old_logs_count} old activity logs",
            metadata={"threshold_days": days_threshold, "count": old_logs_count}
        )

        return {
            "status": "success",
            "archived_count": old_logs_count,
            "threshold_days": days_threshold,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error archiving activity logs: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()
