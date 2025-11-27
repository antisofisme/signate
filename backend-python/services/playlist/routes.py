"""
Playlist API Routes
FastAPI endpoints with DI, auth, and audit logging
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from shared.database import get_db
from shared.responses import success_response
from shared.logging import AuditLogger
from shared.auth import get_current_user, CurrentUser  # ⚠️ SECURITY FIX: Use real auth
from services.auth.domain.interfaces import IUserRepository
from services.auth.repositories.user_repo import UserRepository

from .domain.interfaces import IPlaylistRepository
from .repositories.playlist_repo import PlaylistRepository
from .use_cases.create_playlist import CreatePlaylistUseCase
from .use_cases.list_playlists import ListPlaylistsUseCase
from .use_cases.get_playlist import GetPlaylistUseCase
from .use_cases.update_playlist import UpdatePlaylistUseCase
from .use_cases.delete_playlist import DeletePlaylistUseCase
from .use_cases.manage_playlist_content import (
    AddContentToPlaylistUseCase,
    GetPlaylistContentUseCase,
    RemoveContentFromPlaylistUseCase,
    ReorderPlaylistContentUseCase,
)
from .use_cases.manage_playlist_assignments import (
    GetPlaylistAssignmentsUseCase,
    AssignPlaylistToDevicesUseCase,
    AssignPlaylistToTagsUseCase,
    UnassignPlaylistFromDevicesUseCase,
    UnassignPlaylistFromTagsUseCase,
)
from .domain.content_resolver import ContentResolver, ContentResolution
from .dtos import (
    PlaylistCreateRequest,
    PlaylistUpdateRequest,
    PlaylistResponse,
    PlaylistListResponse,
    AddContentRequest,
    ReorderContentRequest,
    AssignDevicesRequest,
    AssignTagsRequest,
    PlaylistContentListResponse,
    PlaylistContentItemResponse,
    BulkOperationResponse,
    RemoveOperationResponse,
    PlaylistAssignmentsResponse,
)

router = APIRouter(prefix="/api/v1/playlists")


# ========== Dependency Injection ==========

def get_playlist_repository(db: Session = Depends(get_db)) -> IPlaylistRepository:
    """Inject playlist repository"""
    return PlaylistRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> IUserRepository:
    """Inject user repository"""
    return UserRepository(db)


def get_audit_log_repository(db: Session = Depends(get_db)):
    """Get audit log repository instance"""
    from services.audit.repositories.audit_log_repo import AuditLogRepository
    return AuditLogRepository(db)


def get_create_audit_log_use_case(audit_repo = Depends(get_audit_log_repository)):
    """Get create audit log use case"""
    from services.audit.use_cases.create_audit_log import CreateAuditLogUseCase
    return CreateAuditLogUseCase(audit_repo)


# ⚠️ SECURITY FIX: Removed mock get_current_user() - now imported from shared.auth
# This was a CRITICAL security vulnerability (CVSS 8.5) - complete authentication bypass!


def get_audit_logger(create_audit_use_case = Depends(get_create_audit_log_use_case)) -> AuditLogger:
    """Get audit logger with database persistence"""
    return AuditLogger(create_audit_log_use_case=create_audit_use_case)


# ========== Use Case Factories ==========

def get_create_playlist_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> CreatePlaylistUseCase:
    return CreatePlaylistUseCase(playlist_repo)


def get_list_playlists_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> ListPlaylistsUseCase:
    return ListPlaylistsUseCase(playlist_repo)


def get_get_playlist_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> GetPlaylistUseCase:
    return GetPlaylistUseCase(playlist_repo)


def get_update_playlist_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> UpdatePlaylistUseCase:
    return UpdatePlaylistUseCase(playlist_repo)


def get_delete_playlist_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> DeletePlaylistUseCase:
    return DeletePlaylistUseCase(playlist_repo)


def get_add_content_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> AddContentToPlaylistUseCase:
    return AddContentToPlaylistUseCase(playlist_repo)


def get_get_content_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> GetPlaylistContentUseCase:
    return GetPlaylistContentUseCase(playlist_repo)


def get_remove_content_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> RemoveContentFromPlaylistUseCase:
    return RemoveContentFromPlaylistUseCase(playlist_repo)


def get_reorder_content_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> ReorderPlaylistContentUseCase:
    return ReorderPlaylistContentUseCase(playlist_repo)


def get_get_assignments_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> GetPlaylistAssignmentsUseCase:
    return GetPlaylistAssignmentsUseCase(playlist_repo)


def get_assign_devices_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> AssignPlaylistToDevicesUseCase:
    return AssignPlaylistToDevicesUseCase(playlist_repo)


def get_assign_tags_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> AssignPlaylistToTagsUseCase:
    return AssignPlaylistToTagsUseCase(playlist_repo)


def get_unassign_devices_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> UnassignPlaylistFromDevicesUseCase:
    return UnassignPlaylistFromDevicesUseCase(playlist_repo)


def get_unassign_tags_use_case(
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository)
) -> UnassignPlaylistFromTagsUseCase:
    return UnassignPlaylistFromTagsUseCase(playlist_repo)


# ========== PLAYLIST CRUD ENDPOINTS ==========

@router.post("", status_code=status.HTTP_201_CREATED)
def create_playlist(
    request_body: PlaylistCreateRequest,
    use_case: CreatePlaylistUseCase = Depends(get_create_playlist_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Create new playlist"""
    try:
        playlist = use_case.execute(
            name=request_body.name,
            description=request_body.description,
            is_active=request_body.is_active,
            priority=request_body.priority,
            schedule=request_body.schedule,
            organization_id=current_user.organization_id,
            created_by=current_user.id,
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="playlist.create",
            resource_type="playlist",
            resource_id=playlist.id,
            details={"name": playlist.name, "is_active": playlist.is_active},
            organization_id=current_user.organization_id,
        )

        return success_response(data=playlist.to_dict())

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("")
def list_playlists(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    use_case: ListPlaylistsUseCase = Depends(get_list_playlists_use_case),
    current_user: dict = Depends(get_current_user),
):
    """List all playlists for organization"""
    try:
        playlists, total = use_case.execute(
            organization_id=current_user.organization_id,
            skip=skip,
            limit=limit,
            is_active=is_active,
        )

        return success_response(
            data={
                "total": total,
                "items": [p.to_dict() for p in playlists]
            }
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{playlist_id}")
def get_playlist(
    playlist_id: int,
    use_case: GetPlaylistUseCase = Depends(get_get_playlist_use_case),
    current_user: dict = Depends(get_current_user),
):
    """Get single playlist by ID"""
    try:
        playlist = use_case.execute(
            playlist_id=playlist_id,
            organization_id=current_user.organization_id
        )

        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

        return success_response(data=playlist.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{playlist_id}")
def update_playlist(
    playlist_id: int,
    request_body: PlaylistUpdateRequest,
    use_case: UpdatePlaylistUseCase = Depends(get_update_playlist_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Update playlist"""
    try:
        playlist = use_case.execute(
            playlist_id=playlist_id,
            organization_id=current_user.organization_id,
            name=request_body.name,
            description=request_body.description,
            is_active=request_body.is_active,
            priority=request_body.priority,
            schedule=request_body.schedule,
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="playlist.update",
            resource_type="playlist",
            resource_id=playlist.id,
            details={
                "name": request_body.name,
                "is_active": request_body.is_active,
            },
            organization_id=current_user.organization_id,
        )

        return success_response(data=playlist.to_dict())

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{playlist_id}")
def delete_playlist(
    playlist_id: int,
    use_case: DeletePlaylistUseCase = Depends(get_delete_playlist_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Delete playlist (hard delete with cascade)"""
    try:
        deleted = use_case.execute(
            playlist_id=playlist_id,
            organization_id=current_user.organization_id
        )

        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="playlist.delete",
            resource_type="playlist",
            resource_id=playlist_id,
            details={"deleted": True},
            organization_id=current_user.organization_id,
        )

        return success_response(data={"message": "Playlist deleted successfully"})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ========== CONTENT MANAGEMENT ENDPOINTS ==========

@router.get("/{playlist_id}/content")
def get_playlist_content(
    playlist_id: int,
    use_case: GetPlaylistContentUseCase = Depends(get_get_content_use_case),
    current_user: dict = Depends(get_current_user),
):
    """Get all content in playlist"""
    try:
        content_items = use_case.execute(
            playlist_id=playlist_id,
            organization_id=current_user.organization_id
        )

        return success_response(
            data={
                "total": len(content_items),
                "items": [item.to_dict() for item in content_items]
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{playlist_id}/content", status_code=status.HTTP_201_CREATED)
def add_content_to_playlist(
    playlist_id: int,
    request_body: AddContentRequest,
    use_case: AddContentToPlaylistUseCase = Depends(get_add_content_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Add content to playlist (bulk)"""
    try:
        result = use_case.execute(
            playlist_id=playlist_id,
            content_ids=request_body.content_ids,
            organization_id=current_user.organization_id
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="playlist.add_content",
            resource_type="playlist",
            resource_id=playlist_id,
            details={
                "content_count": len(request_body.content_ids),
                "added": result["added"],
            },
            organization_id=current_user.organization_id,
        )

        message = f"Added {result['added']} content(s)"
        if result["skipped_duplicate"]:
            message += f", skipped {len(result['skipped_duplicate'])} duplicates"

        return success_response(
            data={
                "message": message,
                **result
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{playlist_id}/content/{content_item_id}")
def remove_content_from_playlist(
    playlist_id: int,
    content_item_id: int,
    use_case: RemoveContentFromPlaylistUseCase = Depends(get_remove_content_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Remove content from playlist"""
    try:
        removed = use_case.execute(
            playlist_content_id=content_item_id,
            playlist_id=playlist_id,
            organization_id=current_user.organization_id
        )

        if not removed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found in playlist")

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="playlist.remove_content",
            resource_type="playlist",
            resource_id=playlist_id,
            details={"content_item_id": content_item_id},
            organization_id=current_user.organization_id,
        )

        return success_response(data={"message": "Content removed from playlist"})

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{playlist_id}/reorder")
def reorder_playlist_content(
    playlist_id: int,
    request_body: ReorderContentRequest,
    use_case: ReorderPlaylistContentUseCase = Depends(get_reorder_content_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Reorder and update duration of playlist content"""
    try:
        updated_count = use_case.execute(
            playlist_id=playlist_id,
            content_items=request_body.content_items,
            organization_id=current_user.organization_id
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="playlist.reorder_content",
            resource_type="playlist",
            resource_id=playlist_id,
            details={"updated_count": updated_count},
            organization_id=current_user.organization_id,
        )

        return success_response(
            data={
                "message": f"Reordered {updated_count} content item(s)",
                "updated_count": updated_count
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ========== ASSIGNMENT ENDPOINTS ==========

@router.get("/{playlist_id}/assignments")
def get_playlist_assignments(
    playlist_id: int,
    use_case: GetPlaylistAssignmentsUseCase = Depends(get_get_assignments_use_case),
    current_user: dict = Depends(get_current_user),
):
    """Get all device and tag assignments"""
    try:
        assignments = use_case.execute(
            playlist_id=playlist_id,
            organization_id=current_user.organization_id
        )

        return success_response(data=assignments)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{playlist_id}/assign/devices", status_code=status.HTTP_201_CREATED)
def assign_to_devices(
    playlist_id: int,
    request_body: AssignDevicesRequest,
    use_case: AssignPlaylistToDevicesUseCase = Depends(get_assign_devices_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Assign playlist to devices (bulk)"""
    try:
        result = use_case.execute(
            playlist_id=playlist_id,
            device_ids=request_body.device_ids,
            organization_id=current_user.organization_id
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="playlist.assign_devices",
            resource_type="playlist",
            resource_id=playlist_id,
            details={
                "device_count": len(request_body.device_ids),
                "assigned": result["assigned"],
            },
            organization_id=current_user.organization_id,
        )

        message = f"Assigned to {result['assigned']} device(s)"
        if result["skipped_duplicate"]:
            message += f", skipped {len(result['skipped_duplicate'])} duplicates"

        return success_response(data={"message": message, **result})

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{playlist_id}/assign/tags", status_code=status.HTTP_201_CREATED)
def assign_to_tags(
    playlist_id: int,
    request_body: AssignTagsRequest,
    use_case: AssignPlaylistToTagsUseCase = Depends(get_assign_tags_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Assign playlist to tags (bulk)"""
    try:
        result = use_case.execute(
            playlist_id=playlist_id,
            tag_ids=request_body.tag_ids,
            organization_id=current_user.organization_id
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="playlist.assign_tags",
            resource_type="playlist",
            resource_id=playlist_id,
            details={
                "tag_count": len(request_body.tag_ids),
                "assigned": result["assigned"],
            },
            organization_id=current_user.organization_id,
        )

        message = f"Assigned to {result['assigned']} tag(s)"
        if result["skipped_duplicate"]:
            message += f", skipped {len(result['skipped_duplicate'])} duplicates"

        return success_response(data={"message": message, **result})

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{playlist_id}/assign/devices")
def unassign_from_devices(
    playlist_id: int,
    request_body: AssignDevicesRequest,
    use_case: UnassignPlaylistFromDevicesUseCase = Depends(get_unassign_devices_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Unassign playlist from devices"""
    try:
        removed = use_case.execute(
            playlist_id=playlist_id,
            device_ids=request_body.device_ids,
            organization_id=current_user.organization_id
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="playlist.unassign_devices",
            resource_type="playlist",
            resource_id=playlist_id,
            details={"removed_count": removed},
            organization_id=current_user.organization_id,
        )

        return success_response(
            data={
                "message": f"Unassigned from {removed} device(s)",
                "removed": removed
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{playlist_id}/assign/tags")
def unassign_from_tags(
    playlist_id: int,
    request_body: AssignTagsRequest,
    use_case: UnassignPlaylistFromTagsUseCase = Depends(get_unassign_tags_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Unassign playlist from tags"""
    try:
        removed = use_case.execute(
            playlist_id=playlist_id,
            tag_ids=request_body.tag_ids,
            organization_id=current_user.organization_id
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="playlist.unassign_tags",
            resource_type="playlist",
            resource_id=playlist_id,
            details={"removed_count": removed},
            organization_id=current_user.organization_id,
        )

        return success_response(
            data={
                "message": f"Unassigned from {removed} tag(s)",
                "removed": removed
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ========== Content Resolution Endpoints ==========

@router.get("/resolve/{device_id}", response_model=ContentResolution)
def resolve_content_for_device(
    device_id: int,
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resolve what content should play on a device
    
    This endpoint determines the playlist based on:
    1. Active schedules (highest priority)
    2. Direct device assignments
    3. Tag-based assignments
    4. PMS content (for hotel rooms)
    5. Default playlist
    
    Returns the resolved playlist with content items
    """
    try:
        # Import dependencies here to avoid circular imports
        from services.device.repositories.device_repo import DeviceRepository
        from services.tag.repositories.tag_repo import TagRepository
        from services.content.repositories.content_repo import ContentRepository
        from services.schedule.repositories.schedule_repo import ScheduleRepository
        from services.pms.repositories.pms_repo import PMSRepository
        
        # Initialize repositories
        device_repo = DeviceRepository(db)
        tag_repo = TagRepository(db)
        content_repo = ContentRepository(db)
        schedule_repo = ScheduleRepository(db)
        pms_repo = PMSRepository(db)
        
        # Verify device belongs to user's organization
        device = device_repo.find_by_id(device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
            
        if device.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access devices from other organizations"
            )
        
        # Initialize content resolver
        resolver = ContentResolver(
            playlist_repo=playlist_repo,
            device_repo=device_repo,
            tag_repo=tag_repo,
            schedule_repo=schedule_repo,
            content_repo=content_repo,
            pms_repo=pms_repo
        )
        
        # Resolve content
        resolution = resolver.resolve_content_for_device(device_id)
        
        if not resolution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No content available for this device"
            )
            
        return resolution
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve content: {str(e)}"
        )
