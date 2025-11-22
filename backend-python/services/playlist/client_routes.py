"""
Client Playlist Routes
Public endpoints for player/viewer to fetch playlists (no authentication required)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from shared.database import get_db
from services.playlist.repositories.playlist_repo import PlaylistRepository
from services.device.repositories.device_repo import DeviceRepository
from pydantic import BaseModel


# Create router for client endpoints
router = APIRouter(
    prefix="/api/v1/client",
    tags=["Client - Player/Viewer"]
)


# ========== DTOs ==========

class DeviceSettings(BaseModel):
    """Device audio and display settings"""
    volume_level: int = 75
    is_volume_enabled: bool = True
    rotation: int = 0
    background_audio_id: Optional[int] = None
    background_audio_url: Optional[str] = None
    background_audio_name: Optional[str] = None


class PlaylistSyncResponse(BaseModel):
    """Response for playlist sync endpoint"""
    playlist: Optional[dict] = None
    device_settings: Optional[DeviceSettings] = None
    has_changes: bool = False
    message: str


# ========== HELPER FUNCTIONS ==========

def build_device_settings(device, db: Session) -> DeviceSettings:
    """
    Build device settings including background audio details

    Priority for background audio:
    1. Device-level background_audio_id (highest)
    2. Playlist-level background_audio_id (if device has assigned playlist)
    """
    from services.content.repositories.models import ContentModel
    from services.playlist.repositories.models import PlaylistModel

    background_audio_id = None
    background_audio_url = None
    background_audio_name = None

    # Priority 1: Device-level background audio
    device_bg_audio_id = getattr(device, 'background_audio_id', None)
    if device_bg_audio_id:
        bg_audio = db.query(ContentModel).filter(
            ContentModel.id == device_bg_audio_id,
            ContentModel.organization_id == device.organization_id  # Multi-tenancy check
        ).first()

        if bg_audio:
            background_audio_id = bg_audio.id
            background_audio_url = bg_audio.file_url
            background_audio_name = bg_audio.title
            print(f"[Device Settings] Using device-level background audio: {bg_audio.title}")

    # Priority 2: Playlist-level background audio (if no device-level)
    elif device.assigned_playlist_id:
        playlist = db.query(PlaylistModel).filter(
            PlaylistModel.id == device.assigned_playlist_id,
            PlaylistModel.organization_id == device.organization_id  # Multi-tenancy check
        ).first()

        playlist_bg_audio_id = getattr(playlist, 'background_audio_id', None) if playlist else None
        if playlist and playlist_bg_audio_id:
            bg_audio = db.query(ContentModel).filter(
                ContentModel.id == playlist_bg_audio_id,
                ContentModel.organization_id == device.organization_id  # Multi-tenancy check
            ).first()

            if bg_audio:
                background_audio_id = bg_audio.id
                background_audio_url = bg_audio.file_url
                background_audio_name = bg_audio.title
                print(f"[Device Settings] Using playlist-level background audio: {bg_audio.title}")

    return DeviceSettings(
        volume_level=getattr(device, 'volume_level', 75),
        is_volume_enabled=getattr(device, 'is_volume_enabled', True),
        rotation=getattr(device, 'rotation', 0),
        background_audio_id=background_audio_id,
        background_audio_url=background_audio_url,
        background_audio_name=background_audio_name
    )


# ========== ENDPOINTS ==========

@router.get("/playlist", response_model=PlaylistSyncResponse)
def get_playlist_for_device(
    device_id: int = Query(..., description="Device ID"),
    db: Session = Depends(get_db)
):
    """
    Get content assigned to a device (PUBLIC - No Auth Required)

    Supports 3 assignment methods (in priority order):
    1. Direct Assignment: content_assignments table (device_id + content_id)
    2. Playlist Assignment: playlist_contents via assigned_playlist_id
    3. Tag-based Assignment: content_assignments table (tag_id + content_id) - TODO

    Used by player to sync content.
    Returns None if no content is assigned.

    Query Parameters:
    - device_id: The device ID

    Returns:
    - playlist: Content object with items, or None if not assigned
    - has_changes: Always True for now (can implement version checking later)
    - message: Human-readable message
    """
    try:
        # Initialize repositories
        device_repo = DeviceRepository(db)

        # Get device
        device = device_repo.find_by_id(device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )

        # Check if device is active
        if device.status != 'active':
            return PlaylistSyncResponse(
                playlist=None,
                has_changes=False,
                message=f"Device is {device.status}, not active"
            )

        # Import models
        from services.content.repositories.models import ContentModel

        # ======================================================================
        # METHOD 1: Check for DIRECT content assignments (HIGHEST PRIORITY)
        # ======================================================================
        from services.content.repositories.models import ContentAssignmentModel

        direct_assignments = db.query(ContentAssignmentModel).filter(
            ContentAssignmentModel.device_id == device_id
        ).order_by(ContentAssignmentModel.priority.asc()).all()

        if direct_assignments and len(direct_assignments) > 0:
            print(f"[Client Playlist] Found {len(direct_assignments)} direct assignments for device {device_id}")

            # Build playlist data from direct assignments
            playlist_data = {
                'id': 0,  # Virtual playlist ID for direct assignments
                'name': f'Direct Assignments - Device {device_id}',
                'description': 'Content directly assigned to this device',
                'is_active': True,
                'created_at': None,
                'updated_at': None,
                'items': []
            }

            # Build items with content details
            for idx, assignment in enumerate(direct_assignments):
                content = db.query(ContentModel).filter(
                    ContentModel.id == assignment.content_id
                ).first()

                if content:
                    # ✅ HLS PRIORITY: Use HLS URL for videos if available (adaptive bitrate streaming)
                    # For videos: Prefer HLS → fallback to direct file
                    # For images/audio: Use direct file URL
                    playback_url = content.file_url  # Default: direct file

                    if content.content_type == 'video' and content.hls_master_playlist_url:
                        # Use HLS for adaptive bitrate streaming
                        playback_url = content.hls_master_playlist_url
                        print(f"[Client Playlist] Content {content.id}: Using HLS URL: {playback_url}")
                    else:
                        print(f"[Client Playlist] Content {content.id}: Using direct URL: {playback_url}")

                    playlist_data['items'].append({
                        'id': assignment.id,
                        'content_id': assignment.content_id,
                        'duration': content.duration,  # Use content duration
                        'order': idx,  # Use array index as order
                        'is_muted': getattr(assignment, 'is_muted', False),  # Per-content mute flag
                        'content': {
                            'id': content.id,
                            'name': content.title,  # Player expects 'name', not 'title'
                            'type': content.content_type,  # Player expects 'type', not 'content_type'
                            'file_path': playback_url,  # HLS URL or direct file URL
                            'url': playback_url,  # For URL-based content
                            'thumbnail_path': content.thumbnail_url,
                            'mime_type': content.mime_type,
                            'metadata': None,  # No metadata for now
                            'updated_at': content.updated_at.isoformat() if content.updated_at else None,  # For cache validation
                        }
                    })

            # If we have items, return them
            if len(playlist_data['items']) > 0:
                # Build device settings
                device_settings = build_device_settings(device, db)

                return PlaylistSyncResponse(
                    playlist=playlist_data,
                    device_settings=device_settings,
                    has_changes=True,
                    message=f"Retrieved {len(playlist_data['items'])} directly assigned content items"
                )

        # ======================================================================
        # METHOD 2: Check for PLAYLIST assignments (FALLBACK)
        # ======================================================================
        if device.assigned_playlist_id:
            print(f"[Client Playlist] Checking playlist assignment for device {device_id}")

            playlist_repo = PlaylistRepository(db)
            playlist = playlist_repo.find_by_id(device.assigned_playlist_id, device.organization_id)

            if not playlist:
                return PlaylistSyncResponse(
                    playlist=None,
                    has_changes=False,
                    message=f"Assigned playlist {device.assigned_playlist_id} not found"
                )

            # Check if playlist is active
            if not playlist.is_active:
                return PlaylistSyncResponse(
                    playlist=None,
                    has_changes=False,
                    message="Assigned playlist is inactive"
                )

            # Get playlist items with content details
            from services.playlist.repositories.models import PlaylistContentModel

            items = db.query(PlaylistContentModel).join(
                ContentModel, PlaylistContentModel.content_id == ContentModel.id
            ).filter(
                PlaylistContentModel.playlist_id == playlist.id
            ).order_by(PlaylistContentModel.order_index).all()

            # Build response
            playlist_data = {
                'id': playlist.id,
                'name': playlist.name,
                'description': playlist.description,
                'is_active': playlist.is_active,
                'created_at': playlist.created_at.isoformat() if playlist.created_at else None,
                'updated_at': playlist.updated_at.isoformat() if playlist.updated_at else None,
                'items': []
            }

            # Build items with content details
            for item in items:
                content = db.query(ContentModel).filter(ContentModel.id == item.content_id).first()
                if content:
                    # ✅ HLS PRIORITY: Use HLS URL for videos if available (same as direct assignments)
                    playback_url = content.file_url  # Default: direct file

                    if content.content_type == 'video' and content.hls_master_playlist_url:
                        playback_url = content.hls_master_playlist_url
                        print(f"[Client Playlist] Content {content.id}: Using HLS URL: {playback_url}")

                    playlist_data['items'].append({
                        'id': item.id,
                        'content_id': item.content_id,
                        'duration': item.duration,
                        'order': item.order_index,
                        'is_muted': getattr(item, 'is_muted', False),  # Per-content mute flag
                        'content': {
                            'id': content.id,
                            'name': content.title,  # Player expects 'name', not 'title'
                            'type': content.content_type,  # Player expects 'type', not 'content_type'
                            'file_path': playback_url,  # HLS URL or direct file URL
                            'url': playback_url,  # For URL-based content
                            'thumbnail_path': content.thumbnail_url,
                            'mime_type': content.mime_type,
                            'metadata': None,  # No metadata for now
                            'updated_at': content.updated_at.isoformat() if content.updated_at else None,  # For cache validation
                        }
                    })

            # If playlist has content items, return them
            if len(playlist_data['items']) > 0:
                # Add background_audio_id to playlist data
                playlist_data['background_audio_id'] = getattr(playlist, 'background_audio_id', None)

                # Build device settings
                device_settings = build_device_settings(device, db)

                return PlaylistSyncResponse(
                    playlist=playlist_data,
                    device_settings=device_settings,
                    has_changes=True,
                    message="Playlist retrieved successfully"
                )

        # ======================================================================
        # NO CONTENT ASSIGNED - Show "Waiting for Content" screen
        # ======================================================================
        return PlaylistSyncResponse(
            playlist=None,
            has_changes=False,
            message="No content assigned to device"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Client Playlist] Error fetching content for device {device_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch content: {str(e)}"
        )
