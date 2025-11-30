"""
Content API Routes
FastAPI endpoints with dependency injection
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException
from typing import Optional, List
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.api_routes import ContentRoutes
from shared.responses import success_response, error_response, paginated_response, created_response
from shared.auth import CurrentUser, get_current_user
from shared.middleware import require_permission
from shared.logging import AuditLogger
from shared.cache import cache, content_cache_key, list_cache_key
from shared.metrics import track_cache_operation

from .repositories.content_repo import get_content_repository
from .infrastructure.storage.local_storage import get_storage_service
from .infrastructure.storage.metadata_extractor import get_metadata_extractor

from .use_cases.upload_content import UploadContentUseCase
from .use_cases.list_content import ListContentUseCase
from .use_cases.get_content import GetContentUseCase
from .use_cases.update_content import UpdateContentUseCase

from .dtos import ContentResponse, PaginatedContentResponse, ContentUpdateRequest, BulkDeleteRequest, BulkUpdateRequest
from .domain.interfaces import IContentRepository
from .infrastructure.storage.interfaces import IStorageService
from .infrastructure.storage.metadata_extractor import MetadataExtractor

router = APIRouter(tags=["content"])


# Dependency injection functions
def get_upload_content_use_case(
    content_repo: IContentRepository = Depends(get_content_repository),
    storage_service: IStorageService = Depends(get_storage_service),
    metadata_extractor: MetadataExtractor = Depends(get_metadata_extractor)
) -> UploadContentUseCase:
    return UploadContentUseCase(content_repo, storage_service, metadata_extractor)


def get_list_content_use_case(
    content_repo: IContentRepository = Depends(get_content_repository)
) -> ListContentUseCase:
    return ListContentUseCase(content_repo)


def get_get_content_use_case(
    content_repo: IContentRepository = Depends(get_content_repository)
) -> GetContentUseCase:
    return GetContentUseCase(content_repo)


def get_update_content_use_case(
    content_repo: IContentRepository = Depends(get_content_repository)
) -> UpdateContentUseCase:
    return UpdateContentUseCase(content_repo)


def get_audit_log_repository(db: Session = Depends(get_db)):
    """Get audit log repository instance"""
    from services.audit.repositories.audit_log_repo import AuditLogRepository
    return AuditLogRepository(db)


def get_create_audit_log_use_case(audit_repo = Depends(get_audit_log_repository)):
    """Get create audit log use case"""
    from services.audit.use_cases.create_audit_log import CreateAuditLogUseCase
    return CreateAuditLogUseCase(audit_repo)


def get_audit_logger(create_audit_use_case = Depends(get_create_audit_log_use_case)) -> AuditLogger:
    """Get audit logger with database persistence"""
    return AuditLogger(create_audit_log_use_case=create_audit_use_case)


# API Endpoints
@router.post(ContentRoutes.UPLOAD, response_model=dict)
async def upload_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    duration: int = Form(10),
    is_active: bool = Form(True),
    upload_use_case: UploadContentUseCase = Depends(get_upload_content_use_case),
    current_user: dict = Depends(require_permission("contents", "create")),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    request: Request = None
):
    """
    Upload content file

    Requires 'contents:create' permission.
    - Supports: image (jpg, png, webp), video (mp4, webm), audio (mp3, aac)
    - Max sizes: Image 50MB, Video 500MB, Audio 100MB
    - Auto-extracts metadata (resolution, duration, codec)
    - Deduplication via file hash
    """
    try:
        content = await upload_use_case.execute(
            file=file,
            title=title,
            description=description,
            organization_id=current_user["organization_id"],
            uploaded_by_id=current_user["user_id"],
            duration=duration,
            is_active=is_active
        )

        # Audit log
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="content.upload",
            resource_type="content",
            resource_id=content.id,
            details={
                "title": content.title,
                "content_type": content.content_type,
                "file_size": content.file_size,
                "original_filename": content.original_filename
            },
            ip_address=request.client.host if request and request.client else None,
            organization_id=current_user["organization_id"]
        )

        # CRITICAL: Invalidate content list cache so new content appears immediately
        cache.invalidate_content(content.id, current_user["organization_id"])

        return created_response(
            data=ContentResponse.from_entity(content).dict(),
            message="Content uploaded successfully"
        )
    except ValueError as e:
        import logging
        logging.error(f"[Upload] ValueError: {str(e)} - file: {file.filename}, content_type: {file.content_type}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"[Upload] Exception: {str(e)} - file: {file.filename}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post(ContentRoutes.BULK_UPLOAD, response_model=dict)
async def bulk_upload_content(
    files: List[UploadFile] = File(...),
    duration: int = Form(10),
    is_active: bool = Form(True),
    upload_use_case: UploadContentUseCase = Depends(get_upload_content_use_case),
    current_user: dict = Depends(require_permission("contents", "create")),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    request: Request = None
):
    """
    Upload multiple content files at once

    Requires 'contents:create' permission.
    - Files: Multiple files (image/video/audio)
    - Default duration: 10 seconds per file
    - Default active: true
    - Title: Auto-generated from filename
    - Description: Optional (empty by default)

    Returns:
    - List of uploaded content with success/error status per file
    """
    results = []
    successful = 0
    failed = 0

    for file in files:
        try:
            # Auto-generate title from filename (remove extension)
            title = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename

            content = await upload_use_case.execute(
                file=file,
                title=title,
                description=None,  # No description for bulk upload
                organization_id=current_user["organization_id"],
                uploaded_by_id=current_user["user_id"],
                duration=duration,
                is_active=is_active
            )

            # Audit log for each successful upload
            audit_logger.log_action(
                user_id=current_user["user_id"],
                action="content.bulk_upload",
                resource_type="content",
                resource_id=content.id,
                details={
                    "title": content.title,
                    "content_type": content.content_type,
                    "file_size": content.file_size,
                    "original_filename": content.original_filename,
                    "bulk_upload": True
                },
                ip_address=request.client.host if request and request.client else None,
                organization_id=current_user["organization_id"]
            )

            results.append({
                "filename": file.filename,
                "status": "success",
                "content": ContentResponse.from_entity(content).dict()
            })
            successful += 1

        except ValueError as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
            failed += 1
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": f"Upload failed: {str(e)}"
            })
            failed += 1

    # CRITICAL: Invalidate content list cache once after all uploads
    # This ensures the list shows all newly uploaded content
    if successful > 0:
        cache.invalidate_content(0, current_user["organization_id"])  # 0 = invalidate all lists

    return created_response(
        data={
            "results": results,
            "summary": {
                "total": len(files),
                "successful": successful,
                "failed": failed
            }
        },
        message=f"Bulk upload completed: {successful} successful, {failed} failed"
    )


@router.get(ContentRoutes.LIST, response_model=dict)
async def list_content(
    skip: int = 0,
    limit: int = 20,
    content_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    list_use_case: ListContentUseCase = Depends(get_list_content_use_case),
    current_user: dict = Depends(require_permission("contents", "read"))
):
    """
    List content with filters

    Requires 'contents:read' permission.
    Query params:
    - skip: Offset for pagination (default 0)
    - limit: Number of records (default 20)
    - content_type: Filter by type (image/video/audio)
    - is_active: Filter by active status (true/false)
    """
    # Generate cache key
    cache_key = list_cache_key(
        entity="contents",
        org_id=current_user["organization_id"],
        page=(skip // limit) + 1 if limit > 0 else 1,
        limit=limit,
        content_type=content_type,
        is_active=is_active
    )

    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        track_cache_operation("get", hit=True)
        return cached_result

    track_cache_operation("get", hit=False)

    try:
        contents, total = list_use_case.execute(
            organization_id=current_user["organization_id"],
            skip=skip,
            limit=limit,
            content_type=content_type,
            is_active=is_active
        )

        # Convert skip/limit to page/page_size for paginated_response
        page = (skip // limit) + 1 if limit > 0 else 1
        page_size = limit

        result = paginated_response(
            data=[ContentResponse.from_entity(c).dict() for c in contents],
            total=total,
            page=page,
            page_size=page_size
        )

        # Cache for 5 minutes
        cache.set(cache_key, result, ttl=300)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")


@router.get(ContentRoutes.STATS, response_model=dict)
async def get_content_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("contents", "read"))
):
    """
    Get content storage statistics for the organization

    Requires 'contents:read' permission.
    Returns:
    - total_files: Total number of content files
    - total_size_bytes: Total storage used in bytes
    - total_size_readable: Human-readable storage size
    - by_type: Breakdown by content type (image, video, audio)
    """
    from sqlalchemy import func
    from .repositories.models import ContentModel
    from .dtos import ContentStatsResponse

    try:
        org_id = current_user["organization_id"]

        # Get total counts and size
        total_result = db.query(
            func.count(ContentModel.id).label('total_files'),
            func.coalesce(func.sum(ContentModel.file_size), 0).label('total_size')
        ).filter(
            ContentModel.organization_id == org_id,
            ContentModel.deleted_at == None
        ).first()

        total_files = total_result.total_files or 0
        total_size_bytes = int(total_result.total_size or 0)

        # Get breakdown by type
        type_stats = db.query(
            ContentModel.content_type,
            func.count(ContentModel.id).label('count'),
            func.coalesce(func.sum(ContentModel.file_size), 0).label('size')
        ).filter(
            ContentModel.organization_id == org_id,
            ContentModel.deleted_at == None
        ).group_by(ContentModel.content_type).all()

        by_type = {}
        for stat in type_stats:
            content_type = stat.content_type or 'unknown'
            # Normalize type names
            if content_type.startswith('image'):
                type_key = 'image'
            elif content_type.startswith('video'):
                type_key = 'video'
            elif content_type.startswith('audio'):
                type_key = 'audio'
            else:
                type_key = content_type

            if type_key not in by_type:
                by_type[type_key] = {'count': 0, 'size_bytes': 0}

            by_type[type_key]['count'] += stat.count
            by_type[type_key]['size_bytes'] += int(stat.size or 0)

        # Format readable size
        def format_size(size_bytes):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.2f} PB"

        stats = ContentStatsResponse(
            total_files=total_files,
            total_size_bytes=total_size_bytes,
            total_size_readable=format_size(total_size_bytes),
            by_type=by_type
        )

        return success_response(data=stats.dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")


# ==============================================================================
# Deleted Content (Recycle Bin) - MUST be before GET to avoid route conflict
# ==============================================================================

@router.get(ContentRoutes.LIST_DELETED, response_model=dict)
async def list_deleted_content(
    skip: int = 0,
    limit: int = 20,
    content_type: Optional[str] = None,
    content_repo: IContentRepository = Depends(get_content_repository),
    current_user: dict = Depends(require_permission("contents", "read"))
):
    """
    List soft-deleted content (Recycle Bin)

    Requires 'contents:read' permission.
    Query params:
    - skip: Offset for pagination (default 0)
    - limit: Number of records (default 20)
    - content_type: Filter by type (image/video/audio)
    """
    try:
        contents, total = content_repo.find_all_deleted(
            organization_id=current_user["organization_id"],
            skip=skip,
            limit=limit,
            content_type=content_type
        )

        # Convert skip/limit to page/page_size
        page = (skip // limit) + 1 if limit > 0 else 1
        page_size = limit

        return paginated_response(
            data=[ContentResponse.from_entity(c).dict() for c in contents],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List deleted failed: {str(e)}")


# ==============================================================================
# Duplicate Detection - MUST be before GET to avoid route conflict
# ==============================================================================

@router.get(ContentRoutes.DUPLICATES, response_model=dict)
async def get_duplicate_content(
    content_repo: IContentRepository = Depends(get_content_repository),
    current_user: dict = Depends(require_permission("contents", "read"))
):
    """
    Get duplicate content groups with usage info

    Requires 'contents:read' permission.
    Returns groups of content that share the same file (identical hash),
    with information about where each content is used (playlists, tags, devices).
    """
    try:
        duplicates = content_repo.find_duplicates_with_usage(
            organization_id=current_user["organization_id"]
        )

        # Calculate totals
        total_groups = len(duplicates)
        total_duplicates = sum(group["duplicate_count"] for group in duplicates)

        return success_response(
            data=duplicates,
            message=f"Found {total_groups} duplicate groups with {total_duplicates} total files"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get duplicates failed: {str(e)}")


@router.get(ContentRoutes.GET, response_model=dict)
async def get_content(
    content_id: int,
    get_use_case: GetContentUseCase = Depends(get_get_content_use_case),
    current_user: dict = Depends(require_permission("contents", "read"))
):
    """Get single content by ID. Requires 'contents:read' permission."""
    # Generate cache key
    cache_key = content_cache_key(content_id)

    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        track_cache_operation("get", hit=True)
        # Verify organization access
        if cached_result['data']['organization_id'] != current_user["organization_id"]:
            raise HTTPException(status_code=404, detail="Content not found")
        return cached_result

    track_cache_operation("get", hit=False)

    try:
        content = get_use_case.execute(content_id, current_user["organization_id"])

        result = success_response(
            data=ContentResponse.from_entity(content).dict()
        )

        # Cache for 5 minutes
        cache.set(cache_key, result, ttl=300)

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get failed: {str(e)}")


@router.put(ContentRoutes.UPDATE, response_model=dict)
async def update_content(
    content_id: int,
    request_body: ContentUpdateRequest,
    request: Request,
    update_use_case: UpdateContentUseCase = Depends(get_update_content_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_permission("contents", "edit"))
):
    """
    Update content metadata

    Requires 'contents:update' permission.
    - Updates title, description, duration, is_active
    - Validates organization ownership
    - Logs audit trail
    """
    try:
        updated_content = update_use_case.execute(
            content_id=content_id,
            organization_id=current_user["organization_id"],
            title=request_body.title,
            description=request_body.description,
            duration=request_body.duration,
            is_active=request_body.is_active,
            updated_by_id=current_user["user_id"],
        )

        # Invalidate cache
        cache.invalidate_content(content_id, current_user["organization_id"])

        # Audit log
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="content.update",
            resource_type="content",
            resource_id=content_id,
            details={
                "title": updated_content.title,
                "duration": updated_content.duration,
                "is_active": updated_content.is_active
            },
            ip_address=request.client.host if request.client else None,
            organization_id=current_user["organization_id"]
        )

        return success_response(
            data=ContentResponse.from_entity(updated_content).dict(),
            message="Content updated successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get(ContentRoutes.DOWNLOAD)
async def download_content(
    content_id: int,
    get_use_case: GetContentUseCase = Depends(get_get_content_use_case),
    current_user: dict = Depends(require_permission("contents", "read"))
):
    """Download content file (forces download instead of displaying in browser). Requires 'contents:read' permission."""
    from fastapi.responses import FileResponse
    from pathlib import Path

    try:
        # Get content
        content = get_use_case.execute(content_id, current_user["organization_id"])

        # Get file path
        file_path = Path(content.file_path)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        # Return file with Content-Disposition header to force download
        return FileResponse(
            path=str(file_path),
            filename=content.original_filename,
            media_type=content.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{content.original_filename}"'
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.delete(ContentRoutes.DELETE, status_code=204)
async def delete_content(
    content_id: int,
    request: Request,
    content_repo: IContentRepository = Depends(get_content_repository),
    get_use_case: GetContentUseCase = Depends(get_get_content_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_permission("contents", "delete"))
):
    """Delete content (soft delete - sets deleted_at timestamp). Requires 'contents:delete' permission."""
    try:
        # Get content first for audit log (before deletion)
        content = get_use_case.execute(content_id, current_user["organization_id"])

        # Soft delete - automatically checks organization ownership
        deleted = content_repo.soft_delete(
            content_id,
            current_user["organization_id"],
            deleted_by_id=current_user["user_id"]
        )

        # Invalidate cache
        if deleted:
            cache.invalidate_content(content_id, current_user["organization_id"])

        if not deleted:
            raise HTTPException(status_code=404, detail="Content not found or access denied")

        # Audit log
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="content.delete",
            resource_type="content",
            resource_id=content_id,
            details={
                "title": content.title,
                "content_type": content.content_type,
                "file_url": content.file_url
            },
            ip_address=request.client.host if request.client else None,
            organization_id=current_user["organization_id"]
        )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.post(ContentRoutes.BULK_DELETE, response_model=dict)
async def bulk_delete_content(
    request_body: BulkDeleteRequest,
    http_request: Request,
    content_repo: IContentRepository = Depends(get_content_repository),
    get_use_case: GetContentUseCase = Depends(get_get_content_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_permission("contents", "delete"))
):
    """
    Bulk delete content (soft delete)

    Requires 'contents:delete' permission.
    - Deletes multiple content items at once
    - Max 100 items per request
    - Validates organization ownership for each item
    - Logs audit trail for each deletion
    """
    deleted_count = 0
    failed_count = 0
    errors = []

    for content_id in request_body.content_ids:
        try:
            # Get content first for audit log
            content = get_use_case.execute(content_id, current_user["organization_id"])

            # Soft delete with audit tracking
            deleted = content_repo.soft_delete(
                content_id,
                current_user["organization_id"],
                deleted_by_id=current_user["user_id"]
            )

            if deleted:
                deleted_count += 1

                # Audit log
                audit_logger.log_action(
                    user_id=current_user["user_id"],
                    action="content.bulk_delete",
                    resource_type="content",
                    resource_id=content_id,
                    details={
                        "title": content.title,
                        "content_type": content.content_type
                    },
                    ip_address=http_request.client.host if http_request.client else None,
                    organization_id=current_user["organization_id"]
                )
            else:
                failed_count += 1
                errors.append({"content_id": content_id, "error": "Not found or access denied"})

        except ValueError as e:
            failed_count += 1
            errors.append({"content_id": content_id, "error": str(e)})
        except Exception as e:
            failed_count += 1
            errors.append({"content_id": content_id, "error": f"Delete failed: {str(e)}"})

    return success_response(
        data={
            "deleted": deleted_count,
            "failed": failed_count,
            "errors": errors if errors else None
        },
        message=f"Bulk delete completed: {deleted_count} deleted, {failed_count} failed"
    )


@router.post(ContentRoutes.BULK_UPDATE, response_model=dict)
async def bulk_update_content(
    request_body: BulkUpdateRequest,
    http_request: Request,
    update_use_case: UpdateContentUseCase = Depends(get_update_content_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_permission("contents", "edit"))
):
    """
    Bulk update content metadata

    Requires 'contents:update' permission.
    - Updates multiple content items at once
    - Max 100 items per request
    - Applies same updates to all items
    - Validates organization ownership for each item
    """
    updated_count = 0
    failed_count = 0
    errors = []

    for content_id in request_body.content_ids:
        try:
            updated_content = update_use_case.execute(
                content_id=content_id,
                organization_id=current_user["organization_id"],
                title=request_body.updates.title,
                description=request_body.updates.description,
                duration=request_body.updates.duration,
                is_active=request_body.updates.is_active,
                updated_by_id=current_user["user_id"],
            )

            updated_count += 1

            # Audit log
            audit_logger.log_action(
                user_id=current_user["user_id"],
                action="content.bulk_update",
                resource_type="content",
                resource_id=content_id,
                details={
                    "title": updated_content.title,
                    "duration": updated_content.duration,
                    "is_active": updated_content.is_active
                },
                ip_address=http_request.client.host if http_request.client else None,
                organization_id=current_user["organization_id"]
            )

        except ValueError as e:
            failed_count += 1
            errors.append({"content_id": content_id, "error": str(e)})
        except Exception as e:
            failed_count += 1
            errors.append({"content_id": content_id, "error": f"Update failed: {str(e)}"})

    return success_response(
        data={
            "updated": updated_count,
            "failed": failed_count,
            "errors": errors if errors else None
        },
        message=f"Bulk update completed: {updated_count} updated, {failed_count} failed"
    )


# ==============================================================================
# Restore & Permanent Delete (paths with content_id - safe after GET)
# ==============================================================================

@router.post(ContentRoutes.RESTORE, response_model=dict)
async def restore_content(
    content_id: int,
    request: Request,
    content_repo: IContentRepository = Depends(get_content_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_permission("contents", "edit"))
):
    """
    Restore soft-deleted content from Recycle Bin

    Requires 'contents:edit' permission.
    - Restores content to active state
    - Clears deleted_at and deleted_by_id
    """
    try:
        restored = content_repo.restore(content_id, current_user["organization_id"])

        if not restored:
            raise HTTPException(status_code=404, detail="Content not found in recycle bin")

        # Get restored content for response
        content = content_repo.find_by_id(content_id, current_user["organization_id"])

        # Audit log
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="content.restore",
            resource_type="content",
            resource_id=content_id,
            details={
                "title": content.title if content else None,
                "content_type": content.content_type if content else None
            },
            ip_address=request.client.host if request.client else None,
            organization_id=current_user["organization_id"]
        )

        # CRITICAL: Invalidate cache so restored content appears in list
        cache.invalidate_content(content_id, current_user["organization_id"])

        return success_response(
            data=ContentResponse.from_entity(content).dict() if content else None,
            message="Content restored successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.delete(ContentRoutes.PERMANENT_DELETE, status_code=204)
async def permanent_delete_content(
    content_id: int,
    request: Request,
    content_repo: IContentRepository = Depends(get_content_repository),
    storage_service: IStorageService = Depends(get_storage_service),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_permission("contents", "delete"))
):
    """
    Permanently delete content (cannot be recovered)

    Requires 'contents:delete' permission.
    - Only works on soft-deleted content (must be in recycle bin first)
    - Deletes file from storage
    - Removes database record permanently
    """
    from .repositories.models import ContentModel

    try:
        # Get content to verify it's soft-deleted and belongs to org
        db = content_repo.db
        db_content = db.query(ContentModel).filter(
            ContentModel.id == content_id,
            ContentModel.organization_id == current_user["organization_id"],
            ContentModel.deleted_at.isnot(None)  # Must be soft-deleted first
        ).first()

        if not db_content:
            raise HTTPException(
                status_code=404,
                detail="Content not found in recycle bin. Only deleted content can be permanently removed."
            )

        # Store info for audit log before deletion
        content_title = db_content.title
        content_type = db_content.content_type
        storage_key = db_content.storage_key
        file_size = db_content.file_size

        # Check if other content records use the same storage
        # (for deduplicated files, don't delete storage if still in use)
        same_storage_count = db.query(ContentModel).filter(
            ContentModel.storage_key == storage_key,
            ContentModel.id != content_id
        ).count()

        # Delete file from storage only if no other records use it
        if same_storage_count == 0 and storage_key:
            try:
                await storage_service.delete_file(storage_key)
            except Exception as e:
                import logging
                logging.warning(f"Failed to delete storage file: {e}")
                # Continue with DB deletion even if storage delete fails

        # Permanently delete from database
        deleted = content_repo.hard_delete(content_id)

        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete content from database")

        # Audit log
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="content.permanent_delete",
            resource_type="content",
            resource_id=content_id,
            details={
                "title": content_title,
                "content_type": content_type,
                "file_size": file_size,
                "storage_deleted": same_storage_count == 0
            },
            ip_address=request.client.host if request.client else None,
            organization_id=current_user["organization_id"]
        )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Permanent delete failed: {str(e)}")
