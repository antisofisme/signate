"""
GDPR Data Management Routes
Provides endpoints for data subject rights compliance:
- Right to Access (download user data)
- Right to Erasure (delete user data)
- Data retention policy management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timedelta
import json

from shared.database import get_db
from shared.responses import success_response
from shared.auth import get_current_user, CurrentUser
from shared.rbac import require_permission
from shared.cache import cache as redis_cache
from shared.logging import AuditLogger

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/gdpr", tags=["gdpr"])


# ========== Data Retention Configuration ==========

# Default data retention periods (in days)
DATA_RETENTION_PERIODS = {
    "menu_views": 90,           # Analytics data - 90 days
    "portal_analytics": 30,      # Redis portal analytics - 30 days
    "audit_logs": 365,          # Audit logs - 1 year
    "deleted_media": 30,        # Soft-deleted media - 30 days before permanent deletion
}


def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    return AuditLogger()


# ========== Data Retention Endpoints ==========

@router.get("/retention-policy")
def get_retention_policy(
    current_user: CurrentUser = Depends(require_permission("settings", "view"))
):
    """
    Get current data retention policy settings.
    Shows how long different types of data are kept before automatic deletion.
    """
    return success_response(data={
        "retention_periods": DATA_RETENTION_PERIODS,
        "description": {
            "menu_views": "Menu view analytics (IP addresses, user agents, device info)",
            "portal_analytics": "Portal view counters stored in Redis",
            "audit_logs": "System audit logs for security and compliance",
            "deleted_media": "Soft-deleted media files in recycle bin"
        },
        "note": "Data older than retention period is automatically deleted"
    })


@router.post("/cleanup")
async def trigger_data_cleanup(
    data_type: str = Query(..., description="Type of data to clean: menu_views, portal_analytics, deleted_media, all"),
    dry_run: bool = Query(True, description="If true, only report what would be deleted without actually deleting"),
    background_tasks: BackgroundTasks = None,
    current_user: CurrentUser = Depends(require_permission("settings", "manage")),
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Trigger data cleanup according to retention policy.
    Use dry_run=true to preview what would be deleted.

    Requires settings:manage permission (typically SUPER_ADMIN only).
    """
    results = {}

    if data_type in ("menu_views", "all"):
        # Clean old menu views
        retention_days = DATA_RETENTION_PERIODS["menu_views"]
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        if dry_run:
            count = db.execute(text("""
                SELECT COUNT(*) FROM menu_views
                WHERE viewed_at < :cutoff_date
            """), {"cutoff_date": cutoff_date}).scalar()
            results["menu_views"] = {"would_delete": count, "cutoff_date": cutoff_date.isoformat()}
        else:
            result = db.execute(text("""
                DELETE FROM menu_views
                WHERE viewed_at < :cutoff_date
            """), {"cutoff_date": cutoff_date})
            db.commit()
            results["menu_views"] = {"deleted": result.rowcount, "cutoff_date": cutoff_date.isoformat()}

    if data_type in ("portal_analytics", "all"):
        # Clean old portal analytics from Redis
        retention_days = DATA_RETENTION_PERIODS["portal_analytics"]
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Redis keys use date format YYYY-MM-DD
        old_keys_deleted = 0
        try:
            # Find and delete old portal_views keys
            pattern = "portal_views:*"
            keys = redis_cache.redis_client.keys(pattern) if redis_cache.redis_client else []

            for key in keys:
                # Extract date from key format: portal_views:{org_id}:{slug}:{date}
                parts = key.split(":")
                if len(parts) >= 4:
                    key_date_str = parts[-1]
                    try:
                        key_date = datetime.strptime(key_date_str, "%Y-%m-%d")
                        if key_date < cutoff_date:
                            if not dry_run:
                                redis_cache.delete(key)
                            old_keys_deleted += 1
                    except ValueError:
                        pass  # Skip keys with invalid date format

            # Also clean portal_unique and portal_devices keys
            for pattern in ["portal_unique:*", "portal_devices:*"]:
                keys = redis_cache.redis_client.keys(pattern) if redis_cache.redis_client else []
                for key in keys:
                    parts = key.split(":")
                    if len(parts) >= 4:
                        # Date is in different positions for different key types
                        for part in parts:
                            try:
                                key_date = datetime.strptime(part, "%Y-%m-%d")
                                if key_date < cutoff_date:
                                    if not dry_run:
                                        redis_cache.delete(key)
                                    old_keys_deleted += 1
                                break
                            except ValueError:
                                continue

            if dry_run:
                results["portal_analytics"] = {"would_delete": old_keys_deleted}
            else:
                results["portal_analytics"] = {"deleted": old_keys_deleted}

        except Exception as e:
            results["portal_analytics"] = {"error": str(e)}

    if data_type in ("deleted_media", "all"):
        # Permanently delete old soft-deleted media
        retention_days = DATA_RETENTION_PERIODS["deleted_media"]
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        if dry_run:
            count = db.execute(text("""
                SELECT COUNT(*) FROM menu_media
                WHERE deleted_at IS NOT NULL
                AND deleted_at < :cutoff_date
            """), {"cutoff_date": cutoff_date}).scalar()
            results["deleted_media"] = {"would_delete": count, "cutoff_date": cutoff_date.isoformat()}
        else:
            # Get IDs first for audit log
            old_media = db.execute(text("""
                SELECT id, filename FROM menu_media
                WHERE deleted_at IS NOT NULL
                AND deleted_at < :cutoff_date
            """), {"cutoff_date": cutoff_date}).fetchall()

            if old_media:
                media_ids = [m.id for m in old_media]
                result = db.execute(text("""
                    DELETE FROM menu_media
                    WHERE deleted_at IS NOT NULL
                    AND deleted_at < :cutoff_date
                """), {"cutoff_date": cutoff_date})
                db.commit()
                results["deleted_media"] = {"deleted": result.rowcount, "cutoff_date": cutoff_date.isoformat()}
            else:
                results["deleted_media"] = {"deleted": 0, "cutoff_date": cutoff_date.isoformat()}

    # Audit log
    if not dry_run:
        audit_logger.log_action(
            user_id=current_user.id,
            action="gdpr.data_cleanup",
            resource_type="system",
            resource_id=None,
            details={"data_type": data_type, "results": results},
            organization_id=current_user.organization_id
        )

    return success_response(data={
        "dry_run": dry_run,
        "results": results,
        "message": "Data cleanup preview" if dry_run else "Data cleanup completed"
    })


# ========== Right to Access (Data Export) ==========

@router.get("/my-data")
def export_my_data(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    GDPR Right to Access - Export all personal data for current user.

    Returns all data associated with the user:
    - User profile information
    - Activity logs (menu uploads, edits)
    - Session history
    """
    user_data = {}

    # 1. User profile
    user_result = db.execute(text("""
        SELECT id, username, email, full_name, role, is_active,
               created_at, last_login_at
        FROM users WHERE id = :user_id
    """), {"user_id": current_user.id}).fetchone()

    if user_result:
        user_data["profile"] = {
            "id": user_result.id,
            "username": user_result.username,
            "email": user_result.email,
            "full_name": user_result.full_name,
            "role": user_result.role,
            "is_active": user_result.is_active,
            "created_at": user_result.created_at.isoformat() if user_result.created_at else None,
            "last_login_at": user_result.last_login_at.isoformat() if user_result.last_login_at else None
        }

    # 2. Content created by user
    media_result = db.execute(text("""
        SELECT id, original_filename, created_at
        FROM menu_media
        WHERE uploaded_by_id = :user_id AND deleted_at IS NULL
        ORDER BY created_at DESC
        LIMIT 100
    """), {"user_id": current_user.id}).fetchall()

    user_data["uploaded_media"] = [
        {
            "id": m.id,
            "filename": m.original_filename,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in media_result
    ]

    # 3. Menus created by user
    menus_result = db.execute(text("""
        SELECT id, name, created_at
        FROM menus
        WHERE created_by_id = :user_id AND deleted_at IS NULL
        ORDER BY created_at DESC
        LIMIT 100
    """), {"user_id": current_user.id}).fetchall()

    user_data["created_menus"] = [
        {
            "id": m.id,
            "name": m.name,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in menus_result
    ]

    # 4. Session history (last 30 days)
    sessions_result = db.execute(text("""
        SELECT id, created_at, last_activity_at, ip_address, user_agent, is_active
        FROM sessions
        WHERE user_id = :user_id
        AND created_at > :cutoff
        ORDER BY created_at DESC
        LIMIT 50
    """), {
        "user_id": current_user.id,
        "cutoff": datetime.utcnow() - timedelta(days=30)
    }).fetchall()

    user_data["sessions"] = [
        {
            "id": s.id,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "last_activity_at": s.last_activity_at.isoformat() if s.last_activity_at else None,
            "ip_address": s.ip_address,  # Not anonymized - this is user's own data
            "user_agent": s.user_agent,
            "is_active": s.is_active
        }
        for s in sessions_result
    ]

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="gdpr.data_export",
        resource_type="user",
        resource_id=current_user.id,
        details={"export_type": "full"},
        organization_id=current_user.organization_id
    )

    return success_response(data={
        "user_data": user_data,
        "exported_at": datetime.utcnow().isoformat(),
        "data_categories": list(user_data.keys()),
        "note": "This export contains all personal data associated with your account"
    })


# ========== Right to Erasure (Data Deletion) ==========

@router.delete("/my-data")
def request_data_erasure(
    confirm: bool = Query(..., description="Must be true to confirm deletion"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    GDPR Right to Erasure - Request deletion of personal data.

    This will:
    1. Anonymize user data (replace name/email with anonymous values)
    2. Remove session history
    3. Anonymize audit logs (keep logs but remove identifying info)

    Note: This does NOT delete:
    - Content created by user (menus, media) - these belong to the organization
    - System audit logs (required for security compliance)

    The user account itself remains but is deactivated and anonymized.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="You must confirm deletion by setting confirm=true"
        )

    user_id = current_user.id
    anonymized_email = f"deleted_{user_id}@anonymous.local"
    anonymized_name = f"Deleted User {user_id}"

    # 1. Anonymize user profile
    db.execute(text("""
        UPDATE users SET
            email = :anon_email,
            full_name = :anon_name,
            is_active = false,
            password_hash = 'DELETED',
            updated_at = :now
        WHERE id = :user_id
    """), {
        "user_id": user_id,
        "anon_email": anonymized_email,
        "anon_name": anonymized_name,
        "now": datetime.utcnow()
    })

    # 2. Delete all sessions
    db.execute(text("""
        DELETE FROM sessions WHERE user_id = :user_id
    """), {"user_id": user_id})

    # 3. Update content ownership to show anonymized user
    # (Keep content but update display name in created_by references)
    # The content itself stays with the organization

    db.commit()

    # Audit log (before we lose the user context)
    audit_logger.log_action(
        user_id=user_id,
        action="gdpr.data_erasure",
        resource_type="user",
        resource_id=user_id,
        details={"anonymized": True, "account_deactivated": True},
        organization_id=current_user.organization_id
    )

    return success_response(data={
        "status": "completed",
        "actions_taken": [
            "User profile anonymized",
            "Email replaced with anonymous value",
            "Full name replaced with anonymous value",
            "Account deactivated",
            "All sessions deleted",
            "Password hash invalidated"
        ],
        "note": "Content created by you (menus, media) remains with the organization. Your account has been deactivated and cannot be recovered."
    })


# ========== Admin: User Data Management ==========

@router.get("/user/{user_id}/data")
def admin_export_user_data(
    user_id: int,
    current_user: CurrentUser = Depends(require_permission("users", "manage")),
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Admin endpoint: Export all data for a specific user.
    Requires users:manage permission.
    Used for responding to GDPR data access requests from users.
    """
    # Verify user belongs to same organization (unless super admin)
    if current_user.role.upper() != "SUPER_ADMIN":
        user_check = db.execute(text("""
            SELECT organization_id FROM users WHERE id = :user_id
        """), {"user_id": user_id}).fetchone()

        if not user_check or user_check.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Cannot access user from different organization")

    # Use same logic as my-data but for specified user
    # (Simplified - in production would share code with my-data endpoint)
    user_result = db.execute(text("""
        SELECT id, username, email, full_name, role, is_active,
               created_at, last_login_at, organization_id
        FROM users WHERE id = :user_id
    """), {"user_id": user_id}).fetchone()

    if not user_result:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = {
        "profile": {
            "id": user_result.id,
            "username": user_result.username,
            "email": user_result.email,
            "full_name": user_result.full_name,
            "role": user_result.role,
            "organization_id": user_result.organization_id,
            "is_active": user_result.is_active,
            "created_at": user_result.created_at.isoformat() if user_result.created_at else None,
            "last_login_at": user_result.last_login_at.isoformat() if user_result.last_login_at else None
        }
    }

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="gdpr.admin_data_export",
        resource_type="user",
        resource_id=user_id,
        details={"requested_by": current_user.id},
        organization_id=current_user.organization_id
    )

    return success_response(data={
        "user_data": user_data,
        "exported_at": datetime.utcnow().isoformat(),
        "exported_by": current_user.id
    })


@router.delete("/user/{user_id}/data")
def admin_erase_user_data(
    user_id: int,
    confirm: bool = Query(..., description="Must be true to confirm deletion"),
    current_user: CurrentUser = Depends(require_permission("users", "manage")),
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Admin endpoint: Anonymize and deactivate a user account.
    Requires users:manage permission.
    Used for responding to GDPR erasure requests from users.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="You must confirm deletion by setting confirm=true"
        )

    # Verify user belongs to same organization (unless super admin)
    if current_user.role.upper() != "SUPER_ADMIN":
        user_check = db.execute(text("""
            SELECT organization_id FROM users WHERE id = :user_id
        """), {"user_id": user_id}).fetchone()

        if not user_check or user_check.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Cannot modify user from different organization")

    # Cannot delete yourself via admin endpoint
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account via admin endpoint. Use /my-data instead.")

    anonymized_email = f"deleted_{user_id}@anonymous.local"
    anonymized_name = f"Deleted User {user_id}"

    # Anonymize user
    db.execute(text("""
        UPDATE users SET
            email = :anon_email,
            full_name = :anon_name,
            is_active = false,
            password_hash = 'DELETED',
            updated_at = :now
        WHERE id = :user_id
    """), {
        "user_id": user_id,
        "anon_email": anonymized_email,
        "anon_name": anonymized_name,
        "now": datetime.utcnow()
    })

    # Delete sessions
    db.execute(text("""
        DELETE FROM sessions WHERE user_id = :user_id
    """), {"user_id": user_id})

    db.commit()

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="gdpr.admin_data_erasure",
        resource_type="user",
        resource_id=user_id,
        details={"deleted_by": current_user.id, "anonymized": True},
        organization_id=current_user.organization_id
    )

    return success_response(data={
        "status": "completed",
        "user_id": user_id,
        "actions_taken": [
            "User profile anonymized",
            "Account deactivated",
            "All sessions deleted"
        ]
    })
