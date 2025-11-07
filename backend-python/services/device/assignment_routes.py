"""
Device Assignment API Routes
Endpoints for managing device assignments (tags, content, playlists)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.database import get_db
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# =============================================================================
# DTOs / Schemas
# =============================================================================

class AssignTagRequest(BaseModel):
    """Request to assign tag to device"""
    tag_id: int

class AssignContentRequest(BaseModel):
    """Request to assign content to device"""
    content_id: int
    priority: Optional[int] = 1
    schedule: Optional[dict] = None
    expires_at: Optional[datetime] = None

class AssignPlaylistRequest(BaseModel):
    """Request to assign playlist to device"""
    playlist_id: int

class TagAssignmentResponse(BaseModel):
    """Response for tag assignment"""
    id: int
    device_id: int
    tag_id: int
    tag_name: str
    tag_color: str
    assigned_at: datetime

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

class PlaylistAssignmentResponse(BaseModel):
    """Response for playlist assignment"""
    id: int
    device_id: int
    playlist_id: int
    playlist_name: str
    assigned_at: datetime

# =============================================================================
# TAG ASSIGNMENTS
# =============================================================================

@router.get("/devices/{device_id}/tags")
def get_device_tags(
    device_id: int,
    db: Session = Depends(get_db)
):
    """Get all tags assigned to a device"""
    query = text("""
        SELECT
            dt.id,
            dt.device_id,
            dt.tag_id,
            t.name as tag_name,
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

@router.post("/devices/{device_id}/tags", status_code=status.HTTP_201_CREATED)
def assign_tag_to_device(
    device_id: int,
    request: AssignTagRequest,
    db: Session = Depends(get_db)
):
    """Assign a tag to a device"""
    try:
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
        tag_query = text("SELECT name, color FROM tags WHERE id = :tag_id")
        tag = db.execute(tag_query, {"tag_id": request.tag_id}).fetchone()

        return {
            "id": row.id,
            "device_id": device_id,
            "tag_id": request.tag_id,
            "tag_name": tag.name,
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

@router.delete("/devices/{device_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_tag_from_device(
    device_id: int,
    tag_id: int,
    db: Session = Depends(get_db)
):
    """Remove a tag from a device"""
    try:
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

@router.get("/devices/{device_id}/contents")
def get_device_contents(
    device_id: int,
    db: Session = Depends(get_db)
):
    """Get all content directly assigned to a device"""
    query = text("""
        SELECT
            ca.id,
            ca.device_id,
            ca.content_id,
            c.name as content_name,
            c.type as content_type,
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

@router.post("/devices/{device_id}/contents", status_code=status.HTTP_201_CREATED)
def assign_content_to_device(
    device_id: int,
    request: AssignContentRequest,
    db: Session = Depends(get_db)
):
    """Assign content directly to a device"""
    try:
        # Check if already assigned
        check_query = text("""
            SELECT id FROM content_assignments
            WHERE device_id = :device_id AND content_id = :content_id
        """)
        existing = db.execute(check_query, {
            "device_id": device_id,
            "content_id": request.content_id
        }).fetchone()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content already assigned to this device"
            )

        # Insert assignment
        insert_query = text("""
            INSERT INTO content_assignments
            (device_id, content_id, priority, schedule, expires_at, assigned_at)
            VALUES (:device_id, :content_id, :priority, :schedule, :expires_at, NOW())
            RETURNING id, assigned_at
        """)

        result = db.execute(insert_query, {
            "device_id": device_id,
            "content_id": request.content_id,
            "priority": request.priority,
            "schedule": request.schedule,
            "expires_at": request.expires_at
        })
        db.commit()

        row = result.fetchone()

        # Get content details
        content_query = text("SELECT name, type FROM contents WHERE id = :content_id")
        content = db.execute(content_query, {"content_id": request.content_id}).fetchone()

        return {
            "id": row.id,
            "device_id": device_id,
            "content_id": request.content_id,
            "content_name": content.name,
            "content_type": content.type,
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

@router.delete("/devices/{device_id}/contents/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_content_from_device(
    device_id: int,
    content_id: int,
    db: Session = Depends(get_db)
):
    """Remove content from a device"""
    try:
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

@router.get("/devices/{device_id}/playlists")
def get_device_playlists(
    device_id: int,
    db: Session = Depends(get_db)
):
    """Get all playlists assigned to a device"""
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

@router.post("/devices/{device_id}/playlists", status_code=status.HTTP_201_CREATED)
def assign_playlist_to_device(
    device_id: int,
    request: AssignPlaylistRequest,
    db: Session = Depends(get_db)
):
    """Assign a playlist to a device"""
    try:
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

@router.delete("/devices/{device_id}/playlists/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_playlist_from_device(
    device_id: int,
    playlist_id: int,
    db: Session = Depends(get_db)
):
    """Remove a playlist from a device"""
    try:
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
