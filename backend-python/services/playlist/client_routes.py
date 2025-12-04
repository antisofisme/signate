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
    schedule_id: Optional[int] = Query(None, description="Active schedule ID (for override mode)"),
    schedule_mode: Optional[str] = Query(None, description="Schedule playback mode: 'override' or 'rotate'"),
    db: Session = Depends(get_db)
):
    """
    Get content assigned to a device (PUBLIC - No Auth Required)

    Supports 3 assignment methods (in priority order):
    1. Direct Assignment: content_assignments table (device_id + content_id) - HIGHEST
    2. Tag-based Assignment: device_tags → tags → content_tags - MEDIUM
    3. Playlist Assignment: playlist_assignments table (device_id + playlist_id) - LOWEST

    All content from all sources is MERGED into a single playlist.
    Used by player to sync content.
    Returns None if no content is assigned.

    **OVERRIDE MODE:**
    If schedule_mode='override' and schedule_id is provided:
    - Returns ONLY the content from the schedule's playlist
    - Direct and tag assignments are IGNORED
    - This allows scheduled playlists to completely override other content

    Query Parameters:
    - device_id: The device ID
    - schedule_id: (optional) Active schedule ID when using override mode
    - schedule_mode: (optional) 'override' to only show scheduled playlist, 'rotate' for normal merge

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
        from services.content.repositories.models import ContentAssignmentModel
        from services.playlist.repositories.models import PlaylistModel, PlaylistContentModel, PlaylistAssignmentModel
        from services.tag.repositories.models import ContentTag
        from services.schedule.repositories.models import Schedule as ScheduleModel
        from sqlalchemy import text

        # ======================================================================
        # OVERRIDE MODE: Return ONLY scheduled playlist content
        # When schedule_mode='override', ignore direct & tag assignments
        # ======================================================================
        if schedule_mode == 'override' and schedule_id:
            print(f"[Client Playlist] 🎯 OVERRIDE MODE: Schedule {schedule_id} active")

            # Get the schedule
            schedule = db.query(ScheduleModel).filter(
                ScheduleModel.id == schedule_id,
                ScheduleModel.is_active == True
            ).first()

            if not schedule or not schedule.playlist_id:
                print(f"[Client Playlist] ⚠️ Override schedule {schedule_id} not found or has no playlist")
                # Fall through to normal behavior if schedule not found
            else:
                # Get the playlist
                playlist = db.query(PlaylistModel).filter(
                    PlaylistModel.id == schedule.playlist_id,
                    PlaylistModel.deleted_at.is_(None),
                    PlaylistModel.is_active == True
                ).first()

                if not playlist:
                    print(f"[Client Playlist] ⚠️ Playlist {schedule.playlist_id} not found for override schedule")
                else:
                    # Get playlist contents
                    playlist_contents = db.query(PlaylistContentModel).filter(
                        PlaylistContentModel.playlist_id == playlist.id
                    ).order_by(PlaylistContentModel.order_index).all()

                    override_items = []
                    for idx, pc in enumerate(playlist_contents):
                        content = db.query(ContentModel).filter(
                            ContentModel.id == pc.content_id,
                            ContentModel.deleted_at.is_(None)
                        ).first()

                        if content:
                            # Build content item (inline helper for override mode)
                            playback_url = content.file_url
                            if content.content_type == 'video' and content.hls_master_playlist_url:
                                playback_url = content.hls_master_playlist_url
                                print(f"[Client Playlist] Content {content.id} (override): Using HLS URL")

                            override_items.append({
                                'id': content.id * 1000 + idx,
                                'content_id': content.id,
                                'duration': pc.duration or content.duration,
                                'order': idx,
                                'is_muted': getattr(pc, 'is_muted', False),
                                'source': f'schedule-override:{schedule_id}',
                                'content': {
                                    'id': content.id,
                                    'name': content.title,
                                    'type': content.content_type,
                                    'file_path': playback_url,
                                    'url': playback_url,
                                    'thumbnail_path': content.thumbnail_url,
                                    'mime_type': content.mime_type,
                                    'metadata': {
                                        'file_size': content.file_size,
                                        'width': content.width,
                                        'height': content.height,
                                    },
                                    'updated_at': content.updated_at.isoformat() if content.updated_at else None,
                                }
                            })

                    if override_items:
                        # Build device settings
                        device_settings = build_device_settings(device, db)

                        playlist_data = {
                            'id': playlist.id,
                            'name': f'[Override] {playlist.name}',
                            'description': f'Override mode: Schedule "{schedule.name}" - Only playlist content',
                            'is_active': True,
                            'created_at': playlist.created_at.isoformat() if playlist.created_at else None,
                            'updated_at': playlist.updated_at.isoformat() if playlist.updated_at else None,
                            'items': override_items
                        }

                        print(f"[Client Playlist] ✅ OVERRIDE: Returning {len(override_items)} items from playlist '{playlist.name}' (schedule: {schedule.name})")

                        return PlaylistSyncResponse(
                            playlist=playlist_data,
                            device_settings=device_settings,
                            has_changes=True,
                            message=f"Override mode: {len(override_items)} items from scheduled playlist '{playlist.name}'"
                        )
                    else:
                        print(f"[Client Playlist] ⚠️ Override playlist '{playlist.name}' has no content")
                        # Fall through to show no content

        # Track all content items (deduplicated by content_id)
        all_items = []
        seen_content_ids = set()
        sources_summary = []

        def build_content_item(content, order_idx, source, is_muted=False, duration_override=None):
            """Helper to build content item dict"""
            # ✅ HLS PRIORITY: Use HLS URL for videos if available
            playback_url = content.file_url  # Default: direct file

            if content.content_type == 'video' and content.hls_master_playlist_url:
                playback_url = content.hls_master_playlist_url
                print(f"[Client Playlist] Content {content.id} ({source}): Using HLS URL")

            return {
                'id': content.id * 1000 + order_idx,  # Unique ID
                'content_id': content.id,
                'duration': duration_override or content.duration,
                'order': order_idx,
                'is_muted': is_muted,
                'source': source,  # For debugging
                'content': {
                    'id': content.id,
                    'name': content.title,
                    'type': content.content_type,
                    'file_path': playback_url,
                    'url': playback_url,
                    'thumbnail_path': content.thumbnail_url,
                    'mime_type': content.mime_type,
                    'metadata': {
                        'file_size': content.file_size,
                        'width': content.width,
                        'height': content.height,
                    },
                    'updated_at': content.updated_at.isoformat() if content.updated_at else None,
                }
            }

        # ======================================================================
        # PRIORITY 1: Direct content assignments (HIGHEST)
        # ======================================================================
        direct_assignments = db.query(ContentAssignmentModel).filter(
            ContentAssignmentModel.device_id == device_id
        ).order_by(ContentAssignmentModel.priority.asc()).all()

        if direct_assignments:
            print(f"[Client Playlist] Found {len(direct_assignments)} direct assignments for device {device_id}")
            sources_summary.append(f"{len(direct_assignments)} direct")

            for assignment in direct_assignments:
                if assignment.content_id in seen_content_ids:
                    continue

                content = db.query(ContentModel).filter(
                    ContentModel.id == assignment.content_id,
                    ContentModel.deleted_at.is_(None)
                ).first()

                if content:
                    seen_content_ids.add(content.id)
                    all_items.append(build_content_item(
                        content,
                        len(all_items),
                        'direct',
                        getattr(assignment, 'is_muted', False)
                    ))

        # ======================================================================
        # PRIORITY 2: Tag-based content (MEDIUM)
        # Device has tags → Tags have content via content_tags table
        # Single source of truth - same table used by Tag Management Modal
        # ======================================================================
        # Get all tag IDs assigned to this device
        device_tag_ids = db.execute(text("""
            SELECT tag_id FROM device_tags WHERE device_id = :device_id
        """), {"device_id": device_id}).fetchall()

        if device_tag_ids:
            tag_ids = [t[0] for t in device_tag_ids]
            print(f"[Client Playlist] Device {device_id} has tags: {tag_ids}")

            tag_content_count = 0

            # Query content_tags table (single source of truth)
            tag_contents = db.query(ContentTag).filter(
                ContentTag.tag_id.in_(tag_ids)
            ).all()

            for tc in tag_contents:
                if tc.content_id in seen_content_ids:
                    continue

                content = db.query(ContentModel).filter(
                    ContentModel.id == tc.content_id,
                    ContentModel.deleted_at.is_(None)
                ).first()

                if content:
                    seen_content_ids.add(content.id)
                    all_items.append(build_content_item(
                        content,
                        len(all_items),
                        f'tag:{tc.tag_id}',
                        False
                    ))
                    tag_content_count += 1

            if tag_content_count > 0:
                print(f"[Client Playlist] Found {tag_content_count} tag-based content for device {device_id}")
                sources_summary.append(f"{tag_content_count} tag-based")

        # ======================================================================
        # PRIORITY 3: Playlist assignments (LOWEST)
        # Device has playlists assigned via playlist_assignments table
        # ======================================================================
        playlist_assignments = db.query(PlaylistAssignmentModel).filter(
            PlaylistAssignmentModel.device_id == device_id
        ).all()

        if playlist_assignments:
            print(f"[Client Playlist] Device {device_id} has {len(playlist_assignments)} playlist assignments")

            for pa in playlist_assignments:
                # Get playlist
                playlist = db.query(PlaylistModel).filter(
                    PlaylistModel.id == pa.playlist_id,
                    PlaylistModel.deleted_at.is_(None),
                    PlaylistModel.is_active == True
                ).first()

                if not playlist:
                    continue

                # Get playlist contents
                playlist_contents = db.query(PlaylistContentModel).filter(
                    PlaylistContentModel.playlist_id == playlist.id
                ).order_by(PlaylistContentModel.order_index).all()

                playlist_content_count = 0
                for pc in playlist_contents:
                    if pc.content_id in seen_content_ids:
                        continue

                    content = db.query(ContentModel).filter(
                        ContentModel.id == pc.content_id,
                        ContentModel.deleted_at.is_(None)
                    ).first()

                    if content:
                        seen_content_ids.add(content.id)
                        all_items.append(build_content_item(
                            content,
                            len(all_items),
                            f'playlist:{playlist.id}',
                            getattr(pc, 'is_muted', False),
                            pc.duration
                        ))
                        playlist_content_count += 1

                if playlist_content_count > 0:
                    sources_summary.append(f"{playlist_content_count} from playlist '{playlist.name}'")

        # ======================================================================
        # FALLBACK: Check legacy assigned_playlist_id on device
        # ======================================================================
        if not all_items and device.assigned_playlist_id:
            print(f"[Client Playlist] Checking legacy playlist assignment for device {device_id}")

            playlist_repo = PlaylistRepository(db)
            playlist = playlist_repo.find_by_id(device.assigned_playlist_id, device.organization_id)

            if playlist and playlist.is_active:
                items = db.query(PlaylistContentModel).filter(
                    PlaylistContentModel.playlist_id == playlist.id
                ).order_by(PlaylistContentModel.order_index).all()

                for item in items:
                    if item.content_id in seen_content_ids:
                        continue

                    content = db.query(ContentModel).filter(
                        ContentModel.id == item.content_id,
                        ContentModel.deleted_at.is_(None)
                    ).first()

                    if content:
                        seen_content_ids.add(content.id)
                        all_items.append(build_content_item(
                            content,
                            len(all_items),
                            f'legacy-playlist:{playlist.id}',
                            getattr(item, 'is_muted', False),
                            item.duration
                        ))

                if all_items:
                    sources_summary.append(f"{len(all_items)} from legacy playlist '{playlist.name}'")

        # ======================================================================
        # BUILD FINAL RESPONSE
        # ======================================================================
        if all_items:
            playlist_data = {
                'id': 0,  # Virtual merged playlist
                'name': f'Merged Content - Device {device_id}',
                'description': f'Content from: {", ".join(sources_summary)}',
                'is_active': True,
                'created_at': None,
                'updated_at': None,
                'items': all_items
            }

            # Build device settings
            device_settings = build_device_settings(device, db)

            print(f"[Client Playlist] Returning {len(all_items)} items for device {device_id}: {', '.join(sources_summary)}")

            return PlaylistSyncResponse(
                playlist=playlist_data,
                device_settings=device_settings,
                has_changes=True,
                message=f"Retrieved {len(all_items)} content items ({', '.join(sources_summary)})"
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
