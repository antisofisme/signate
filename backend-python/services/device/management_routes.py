"""
Device Management API Routes
Consolidated from: assignment_routes.py + group_routes.py

Handles device management operations:
- Tag assignments (device <-> tags)
- Content assignments (device <-> content with priority)
- Playlist assignments (device <-> playlists)
- Schedule assignments (device <-> schedules)
- Device groups (hierarchical grouping)
- Group device management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.database import get_db
from shared.auth import get_current_user, CurrentUser
from shared.middleware import get_current_active_user, require_permission
from shared.logging import AuditLogger
from shared.websocket_manager import websocket_manager, WebSocketEventType
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio

# Initialize audit logger
audit_logger = AuditLogger()

from .dtos import (
    CreateDeviceGroupRequest,
    UpdateDeviceGroupRequest,
    AddDeviceToGroupRequest,
    RemoveDeviceFromGroupRequest,
    DeviceGroupResponse,
    DeviceGroupListResponse,
    DeviceGroupStatsResponse,
    GroupDevicesResponse,
)

from .use_cases.create_device_group import CreateDeviceGroupUseCase
from .use_cases.update_device_group import UpdateDeviceGroupUseCase
from .use_cases.delete_device_group import DeleteDeviceGroupUseCase
from .use_cases.get_device_groups import GetDeviceGroupsUseCase
from .use_cases.add_device_to_group import AddDeviceToGroupUseCase
from .use_cases.remove_device_from_group import RemoveDeviceFromGroupUseCase

# Router with management prefix
management_router = APIRouter()


# =============================================================================
# TAG ASSIGNMENTS
# =============================================================================

class AssignTagRequest(BaseModel):
    """Request to assign tag to device"""
    tag_id: int

class TagAssignmentResponse(BaseModel):
    """Response for tag assignment"""
    id: int
    device_id: int
    tag_id: int
    tag_name: str
    tag_color: str
    assigned_at: datetime


@management_router.get("/{device_id}/tags")
def get_device_tags(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all tags assigned to a device"""
    # Verify device belongs to user's organization
    device_query = text("SELECT organization_id FROM devices WHERE id = :device_id")
    device = db.execute(device_query, {"device_id": device_id}).fetchone()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    if device.organization_id != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Device belongs to different organization"
        )

    query = text("""
        SELECT
            dt.id,
            dt.device_id,
            dt.tag_id,
            t.tag_name as tag_name,
            t.color as tag_color,
            dt.assigned_at
        FROM device_tags dt
        JOIN tags t ON t.id = dt.tag_id
        WHERE dt.device_id = :device_id
        ORDER BY dt.assigned_at DESC
    """)

    result = db.execute(query, {"device_id": device_id})
    rows = result.fetchall()

    return {
        "items": [
            {
                "id": row.id,
                "device_id": row.device_id,
                "tag_id": row.tag_id,
                "tag_name": row.tag_name,
                "tag_color": row.tag_color,
                "assigned_at": row.assigned_at
            }
            for row in rows
        ],
        "total": len(rows)
    }


@management_router.post("/{device_id}/tags", status_code=status.HTTP_201_CREATED)
def assign_tag_to_device(
    device_id: int,
    request: AssignTagRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Assign a tag to a device"""
    try:
        # Verify device belongs to user's organization
        device_query = text("SELECT organization_id FROM devices WHERE id = :device_id")
        device = db.execute(device_query, {"device_id": device_id}).fetchone()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

        if device.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Device belongs to different organization"
            )

        # Verify tag belongs to user's organization
        tag_query = text("SELECT organization_id FROM tags WHERE id = :tag_id")
        tag = db.execute(tag_query, {"tag_id": request.tag_id}).fetchone()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )

        if tag.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Tag belongs to different organization"
            )

        # Check if already assigned
        check_query = text("""
            SELECT id FROM device_tags
            WHERE device_id = :device_id AND tag_id = :tag_id
        """)
        existing = db.execute(check_query, {
            "device_id": device_id,
            "tag_id": request.tag_id
        }).fetchone()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag already assigned to this device"
            )

        # Insert assignment
        insert_query = text("""
            INSERT INTO device_tags (device_id, tag_id, assigned_at)
            VALUES (:device_id, :tag_id, NOW())
            RETURNING id, assigned_at
        """)

        result = db.execute(insert_query, {
            "device_id": device_id,
            "tag_id": request.tag_id
        })
        db.commit()

        row = result.fetchone()

        # Get tag details
        tag_query = text("SELECT tag_name, color FROM tags WHERE id = :tag_id")
        tag = db.execute(tag_query, {"tag_id": request.tag_id}).fetchone()

        return {
            "id": row.id,
            "device_id": device_id,
            "tag_id": request.tag_id,
            "tag_name": tag.tag_name,
            "tag_color": tag.color,
            "assigned_at": row.assigned_at,
            "message": "Tag assigned successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@management_router.delete("/{device_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_tag_from_device(
    device_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Remove a tag from a device"""
    try:
        # Verify device belongs to user's organization
        device_query = text("SELECT organization_id FROM devices WHERE id = :device_id")
        device = db.execute(device_query, {"device_id": device_id}).fetchone()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

        if device.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Device belongs to different organization"
            )

        delete_query = text("""
            DELETE FROM device_tags
            WHERE device_id = :device_id AND tag_id = :tag_id
            RETURNING id
        """)

        result = db.execute(delete_query, {
            "device_id": device_id,
            "tag_id": tag_id
        })
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag assignment not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# CONTENT ASSIGNMENTS
# =============================================================================

class AssignContentRequest(BaseModel):
    """Request to assign content to device"""
    content_id: int
    priority: Optional[int] = 1
    schedule: Optional[dict] = None
    expires_at: Optional[datetime] = None

class ContentAssignmentResponse(BaseModel):
    """Response for content assignment"""
    id: int
    device_id: int
    content_id: int
    content_name: str
    content_type: str
    priority: int
    assigned_at: datetime
    expires_at: Optional[datetime] = None


@management_router.get("/{device_id}/contents")
def get_device_contents(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all content directly assigned to a device"""
    # Verify device belongs to user's organization
    device_query = text("SELECT organization_id FROM devices WHERE id = :device_id")
    device = db.execute(device_query, {"device_id": device_id}).fetchone()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    if device.organization_id != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Device belongs to different organization"
        )

    query = text("""
        SELECT
            ca.id,
            ca.device_id,
            ca.content_id,
            c.title as content_name,
            c.content_type as content_type,
            ca.priority,
            ca.assigned_at,
            ca.expires_at
        FROM content_assignments ca
        JOIN contents c ON c.id = ca.content_id
        WHERE ca.device_id = :device_id
          AND (ca.expires_at IS NULL OR ca.expires_at > NOW())
        ORDER BY ca.priority DESC, ca.assigned_at DESC
    """)

    result = db.execute(query, {"device_id": device_id})
    rows = result.fetchall()

    return {
        "items": [
            {
                "id": row.id,
                "device_id": row.device_id,
                "content_id": row.content_id,
                "content_name": row.content_name,
                "content_type": row.content_type,
                "priority": row.priority,
                "assigned_at": row.assigned_at,
                "expires_at": row.expires_at
            }
            for row in rows
        ],
        "total": len(rows)
    }


@management_router.post("/{device_id}/contents", status_code=status.HTTP_201_CREATED)
def assign_content_to_device(
    device_id: int,
    request: AssignContentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Assign content directly to a device or update priority if already assigned"""
    try:
        # Verify device belongs to user's organization
        device_query = text("SELECT organization_id FROM devices WHERE id = :device_id")
        device = db.execute(device_query, {"device_id": device_id}).fetchone()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

        if device.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Device belongs to different organization"
            )

        # Verify content belongs to user's organization
        content_query = text("SELECT organization_id FROM contents WHERE id = :content_id")
        content = db.execute(content_query, {"content_id": request.content_id}).fetchone()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )

        if content.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Content belongs to different organization"
            )

        # Check if already assigned
        check_query = text("""
            SELECT id, priority FROM content_assignments
            WHERE device_id = :device_id AND content_id = :content_id
        """)
        existing = db.execute(check_query, {
            "device_id": device_id,
            "content_id": request.content_id
        }).fetchone()

        if existing:
            # UPDATE: If already assigned, just update the priority
            update_query = text("""
                UPDATE content_assignments
                SET priority = :priority,
                    schedule = :schedule,
                    expires_at = :expires_at
                WHERE id = :assignment_id
                RETURNING id, assigned_at
            """)
            result = db.execute(update_query, {
                "assignment_id": existing.id,
                "priority": request.priority,
                "schedule": request.schedule,
                "expires_at": request.expires_at
            })
            db.commit()

            row = result.fetchone()

            # Get content details
            content_query = text("SELECT title, content_type FROM contents WHERE id = :content_id")
            content = db.execute(content_query, {"content_id": request.content_id}).fetchone()

            return {
                "id": row.id,
                "device_id": device_id,
                "content_id": request.content_id,
                "content_name": content.title,
                "content_type": content.content_type,
                "priority": request.priority,
                "assigned_at": row.assigned_at,
                "expires_at": request.expires_at,
                "message": "Content priority updated successfully"
            }

        # Insert assignment (device already verified at start of function)
        insert_query = text("""
            INSERT INTO content_assignments
            (device_id, content_id, priority, schedule, expires_at, assigned_at, organization_id)
            VALUES (:device_id, :content_id, :priority, :schedule, :expires_at, NOW(), :organization_id)
            RETURNING id, assigned_at
        """)

        result = db.execute(insert_query, {
            "device_id": device_id,
            "content_id": request.content_id,
            "priority": request.priority,
            "schedule": request.schedule,
            "expires_at": request.expires_at,
            "organization_id": device.organization_id
        })
        db.commit()

        row = result.fetchone()

        # Get content details
        content_query = text("SELECT title, content_type FROM contents WHERE id = :content_id")
        content = db.execute(content_query, {"content_id": request.content_id}).fetchone()

        # Send WebSocket notification to device for immediate content update
        if websocket_manager is not None:
            try:
                # Use asyncio.run() for sync routes (creates new event loop)
                asyncio.run(
                    websocket_manager.send_to_device(
                        device_id=device_id,
                        event_type=WebSocketEventType.CONTENT_UPDATED,
                        data={
                            "device_id": device_id,
                            "content_id": request.content_id,
                            "content_name": content.title,
                            "action": "assigned",
                            "message": "New content assigned - refresh playlist"
                        }
                    )
                )
                print(f"[Content Assign] WebSocket notification sent to device {device_id}")
            except Exception as ws_err:
                # Don't fail assignment if WebSocket notification fails
                print(f"[Content Assign] WebSocket notification failed: {ws_err}")

        return {
            "id": row.id,
            "device_id": device_id,
            "content_id": request.content_id,
            "content_name": content.title,
            "content_type": content.content_type,
            "priority": request.priority,
            "assigned_at": row.assigned_at,
            "expires_at": request.expires_at,
            "message": "Content assigned successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@management_router.delete("/{device_id}/contents/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_content_from_device(
    device_id: int,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Remove content from a device"""
    try:
        # Verify device belongs to user's organization
        device_query = text("SELECT organization_id FROM devices WHERE id = :device_id")
        device = db.execute(device_query, {"device_id": device_id}).fetchone()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

        if device.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Device belongs to different organization"
            )

        delete_query = text("""
            DELETE FROM content_assignments
            WHERE device_id = :device_id AND content_id = :content_id
            RETURNING id
        """)

        result = db.execute(delete_query, {
            "device_id": device_id,
            "content_id": content_id
        })
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content assignment not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# PLAYLIST ASSIGNMENTS
# =============================================================================

class AssignPlaylistRequest(BaseModel):
    """Request to assign playlist to device"""
    playlist_id: int

class PlaylistAssignmentResponse(BaseModel):
    """Response for playlist assignment"""
    id: int
    device_id: int
    playlist_id: int
    playlist_name: str
    assigned_at: datetime


@management_router.get("/{device_id}/playlists")
def get_device_playlists(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all playlists assigned to a device"""
    # Verify device belongs to user's organization
    device_query = text("SELECT organization_id FROM devices WHERE id = :device_id")
    device = db.execute(device_query, {"device_id": device_id}).fetchone()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    if device.organization_id != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Device belongs to different organization"
        )

    query = text("""
        SELECT
            pa.id,
            pa.device_id,
            pa.playlist_id,
            p.name as playlist_name,
            pa.created_at as assigned_at
        FROM playlist_assignments pa
        JOIN playlists p ON p.id = pa.playlist_id
        WHERE pa.device_id = :device_id
          AND p.is_active = TRUE
          AND p.deleted_at IS NULL
        ORDER BY pa.created_at DESC
    """)

    result = db.execute(query, {"device_id": device_id})
    rows = result.fetchall()

    return {
        "items": [
            {
                "id": row.id,
                "device_id": row.device_id,
                "playlist_id": row.playlist_id,
                "playlist_name": row.playlist_name,
                "assigned_at": row.assigned_at
            }
            for row in rows
        ],
        "total": len(rows)
    }


@management_router.post("/{device_id}/playlists", status_code=status.HTTP_201_CREATED)
def assign_playlist_to_device(
    device_id: int,
    request: AssignPlaylistRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Assign a playlist to a device"""
    try:
        # Verify device belongs to user's organization
        device_query = text("SELECT organization_id FROM devices WHERE id = :device_id")
        device = db.execute(device_query, {"device_id": device_id}).fetchone()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

        if device.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Device belongs to different organization"
            )

        # Verify playlist belongs to user's organization
        playlist_query = text("SELECT organization_id FROM playlists WHERE id = :playlist_id")
        playlist = db.execute(playlist_query, {"playlist_id": request.playlist_id}).fetchone()

        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found"
            )

        if playlist.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Playlist belongs to different organization"
            )

        # Check if already assigned
        check_query = text("""
            SELECT id FROM playlist_assignments
            WHERE device_id = :device_id AND playlist_id = :playlist_id
        """)
        existing = db.execute(check_query, {
            "device_id": device_id,
            "playlist_id": request.playlist_id
        }).fetchone()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Playlist already assigned to this device"
            )

        # Insert assignment
        insert_query = text("""
            INSERT INTO playlist_assignments (device_id, playlist_id, created_at)
            VALUES (:device_id, :playlist_id, NOW())
            RETURNING id, created_at
        """)

        result = db.execute(insert_query, {
            "device_id": device_id,
            "playlist_id": request.playlist_id
        })
        db.commit()

        row = result.fetchone()

        # Get playlist details
        playlist_query = text("SELECT name FROM playlists WHERE id = :playlist_id")
        playlist = db.execute(playlist_query, {"playlist_id": request.playlist_id}).fetchone()

        # Send WebSocket notification to device for immediate content update
        if websocket_manager is not None:
            try:
                # Use asyncio.run() for sync routes (creates new event loop)
                asyncio.run(
                    websocket_manager.send_to_device(
                        device_id=device_id,
                        event_type=WebSocketEventType.PLAYLIST_ASSIGNED,
                        data={
                            "device_id": device_id,
                            "playlist_id": request.playlist_id,
                            "playlist_name": playlist.name,
                            "action": "assigned",
                            "message": "New playlist assigned - refresh content"
                        }
                    )
                )
                print(f"[Playlist Assign] WebSocket notification sent to device {device_id}")
            except Exception as ws_err:
                # Don't fail assignment if WebSocket notification fails
                print(f"[Playlist Assign] WebSocket notification failed: {ws_err}")

        return {
            "id": row.id,
            "device_id": device_id,
            "playlist_id": request.playlist_id,
            "playlist_name": playlist.name,
            "assigned_at": row.created_at,
            "message": "Playlist assigned successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@management_router.delete("/{device_id}/playlists/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_playlist_from_device(
    device_id: int,
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Remove a playlist from a device"""
    try:
        # Verify device belongs to user's organization
        device_query = text("SELECT organization_id FROM devices WHERE id = :device_id")
        device = db.execute(device_query, {"device_id": device_id}).fetchone()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

        if device.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Device belongs to different organization"
            )

        delete_query = text("""
            DELETE FROM playlist_assignments
            WHERE device_id = :device_id AND playlist_id = :playlist_id
            RETURNING id
        """)

        result = db.execute(delete_query, {
            "device_id": device_id,
            "playlist_id": playlist_id
        })
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist assignment not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# DEVICE GROUPS - CRUD OPERATIONS
# =============================================================================

@management_router.post("/groups", response_model=DeviceGroupResponse, status_code=status.HTTP_201_CREATED)
def create_device_group(
    request: CreateDeviceGroupRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "create")),
):
    """
    Create a new device group

    - **name**: Group name (required)
    - **description**: Optional description
    - **parent_group_id**: Optional parent group for hierarchy
    - **group_type**: Type (chain, hotel, floor, location, custom)
    - **sort_order**: Display order
    - **default_playlist_id**: Default playlist for devices in this group

    Requires: device_groups.create permission
    """
    try:
        use_case = CreateDeviceGroupUseCase(db)
        group = use_case.execute(
            name=request.name,
            organization_id=current_user["organization_id"],
            description=request.description,
            parent_group_id=request.parent_group_id,
            group_type=request.group_type,
            sort_order=request.sort_order,
            default_playlist_id=request.default_playlist_id,
            created_by=current_user["user_id"],
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="device_group.create",
            resource_type="device_group",
            resource_id=group.id,
            details={
                "name": group.name,
                "parent_group_id": request.parent_group_id,
                "group_type": request.group_type,
            },
            ip_address=http_request.client.host if http_request.client else None,
            organization_id=current_user["organization_id"],
        )

        return DeviceGroupResponse(**group.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create group: {str(e)}",
        )


@management_router.get("/groups", response_model=DeviceGroupListResponse)
def get_device_groups(
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "read")),
):
    """
    Get all device groups for the organization

    - **include_deleted**: Include soft-deleted groups (default: false)

    Requires: device_groups.view permission
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        groups = use_case.get_all_by_organization(current_user["organization_id"], include_deleted)

        group_responses = [DeviceGroupResponse(**g.to_dict()) for g in groups]

        return DeviceGroupListResponse(items=group_responses, total=len(group_responses))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get groups: {str(e)}",
        )


@management_router.get("/groups/roots", response_model=DeviceGroupListResponse)
def get_root_groups(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "read")),
):
    """
    Get root device groups (no parent) for the organization

    Requires: device_groups.view permission
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        groups = use_case.get_root_groups(current_user["organization_id"])

        group_responses = [DeviceGroupResponse(**g.to_dict()) for g in groups]

        return DeviceGroupListResponse(items=group_responses, total=len(group_responses))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get root groups: {str(e)}",
        )


@management_router.get("/groups/{group_id}", response_model=DeviceGroupResponse)
def get_device_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "read")),
):
    """
    Get a single device group by ID

    Requires: device_groups.view permission
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        group = use_case.get_by_id(group_id, current_user["organization_id"])

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found",
            )

        return DeviceGroupResponse(**group.to_dict())
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get group: {str(e)}",
        )


@management_router.get("/groups/{group_id}/children", response_model=DeviceGroupListResponse)
def get_group_children(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "read")),
):
    """
    Get child groups of a parent group

    Requires: device_groups.view permission
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        children = use_case.get_children(group_id, current_user["organization_id"])

        group_responses = [DeviceGroupResponse(**g.to_dict()) for g in children]

        return DeviceGroupListResponse(items=group_responses, total=len(group_responses))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get children: {str(e)}",
        )


@management_router.get("/groups/{group_id}/devices", response_model=GroupDevicesResponse)
def get_group_devices(
    group_id: int,
    recursive: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "read")),
):
    """
    Get device IDs in a group

    - **recursive**: Include devices in child groups (default: false)

    Requires: device_groups.view permission
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        device_ids = use_case.get_devices_in_group(group_id, current_user["organization_id"], recursive)

        return GroupDevicesResponse(
            group_id=group_id,
            devices=device_ids,
            count=len(device_ids),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get devices: {str(e)}",
        )


@management_router.get("/groups/{group_id}/stats", response_model=DeviceGroupStatsResponse)
def get_group_stats(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "read")),
):
    """
    Get group statistics (device count, online/offline)

    Requires: device_groups.view permission
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        stats = use_case.get_group_stats(group_id, current_user["organization_id"])

        return DeviceGroupStatsResponse(
            group_id=group_id,
            total_devices=stats["total_devices"],
            online_devices=stats["online_devices"],
            offline_devices=stats["offline_devices"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )


@management_router.put("/groups/{group_id}", response_model=DeviceGroupResponse)
@management_router.patch("/groups/{group_id}", response_model=DeviceGroupResponse)
def update_device_group(
    group_id: int,
    request: UpdateDeviceGroupRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "edit")),
):
    """
    Update a device group (supports both PUT and PATCH methods)

    **PUT**: Replace entire resource (all fields required)
    **PATCH**: Partial update (only provided fields updated)

    Requires: device_groups.edit permission
    """
    try:
        use_case = UpdateDeviceGroupUseCase(db)
        group = use_case.execute(
            group_id=group_id,
            organization_id=current_user["organization_id"],
            name=request.name,
            description=request.description,
            parent_group_id=request.parent_group_id,
            group_type=request.group_type,
            sort_order=request.sort_order,
            default_playlist_id=request.default_playlist_id,
            updated_by_id=current_user["user_id"],
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="device_group.update",
            resource_type="device_group",
            resource_id=group_id,
            details={
                "name": request.name,
                "description": request.description,
                "parent_group_id": request.parent_group_id,
                "group_type": request.group_type,
            },
            ip_address=http_request.client.host if http_request.client else None,
            organization_id=current_user["organization_id"],
        )

        return DeviceGroupResponse(**group.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update group: {str(e)}",
        )


@management_router.post("/groups/{group_id}/devices", status_code=status.HTTP_204_NO_CONTENT)
def add_device_to_group(
    group_id: int,
    request: AddDeviceToGroupRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "edit")),
):
    """
    Add a device to a group

    Requires: device_groups.edit permission
    """
    try:
        use_case = AddDeviceToGroupUseCase(db)
        use_case.execute(
            device_id=request.device_id,
            group_id=group_id,
            organization_id=current_user["organization_id"],
            added_by=current_user["user_id"],
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="device_group.add_device",
            resource_type="device_group",
            resource_id=group_id,
            details={"device_id": request.device_id},
            ip_address=http_request.client.host if http_request.client else None,
            organization_id=current_user["organization_id"],
        )

        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add device to group: {str(e)}",
        )


@management_router.delete("/groups/{group_id}/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_device_from_group(
    group_id: int,
    device_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "edit")),
):
    """
    Remove a device from a group

    Requires: device_groups.edit permission
    """
    try:
        use_case = RemoveDeviceFromGroupUseCase(db)
        use_case.execute(
            device_id=device_id,
            group_id=group_id,
            organization_id=current_user["organization_id"],
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="device_group.remove_device",
            resource_type="device_group",
            resource_id=group_id,
            details={"device_id": device_id},
            ip_address=http_request.client.host if http_request.client else None,
            organization_id=current_user["organization_id"],
        )

        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove device from group: {str(e)}",
        )


@management_router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device_group(
    group_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("device_groups", "delete")),
):
    """
    Soft delete a device group

    Note: Cannot delete groups with child groups. Delete or reassign children first.

    Requires: device_groups.delete permission
    """
    try:
        use_case = DeleteDeviceGroupUseCase(db)
        use_case.execute(
            group_id=group_id,
            organization_id=current_user["organization_id"],
            deleted_by_id=current_user["user_id"],
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="device_group.delete",
            resource_type="device_group",
            resource_id=group_id,
            details={"soft_delete": True},
            ip_address=http_request.client.host if http_request.client else None,
            organization_id=current_user["organization_id"],
        )

        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete group: {str(e)}",
        )
