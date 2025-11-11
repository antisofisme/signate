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
    current_user: CurrentUser = Depends(get_current_user),
    request: Request = None
):
    """
    Upload content file

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
            organization_id=current_user.organization_id,
            uploaded_by=current_user.id,
            duration=duration,
            is_active=is_active
        )

        return created_response(
            data=ContentResponse.from_entity(content).dict(),
            message="Content uploaded successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post(ContentRoutes.BULK_UPLOAD, response_model=dict)
async def bulk_upload_content(
    files: List[UploadFile] = File(...),
    duration: int = Form(10),
    is_active: bool = Form(True),
    upload_use_case: UploadContentUseCase = Depends(get_upload_content_use_case),
    current_user: CurrentUser = Depends(get_current_user),
    request: Request = None
):
    """
    Upload multiple content files at once

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
                organization_id=current_user.organization_id,
                uploaded_by=current_user.id,
                duration=duration,
                is_active=is_active
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List content with filters

    Query params:
    - skip: Offset for pagination (default 0)
    - limit: Number of records (default 20)
    - content_type: Filter by type (image/video/audio)
    - is_active: Filter by active status (true/false)
    """
    # Generate cache key
    cache_key = list_cache_key(
        entity="contents",
        org_id=current_user.organization_id,
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
            organization_id=current_user.organization_id,
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


@router.get(ContentRoutes.GET, response_model=dict)
async def get_content(
    content_id: int,
    get_use_case: GetContentUseCase = Depends(get_get_content_use_case),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get single content by ID"""
    # Generate cache key
    cache_key = content_cache_key(content_id)
    
    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        track_cache_operation("get", hit=True)
        # Verify organization access
        if cached_result['data']['organization_id'] != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Content not found")
        return cached_result
    
    track_cache_operation("get", hit=False)
    
    try:
        content = get_use_case.execute(content_id, current_user.organization_id)

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
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update content metadata

    - Updates title, description, duration, is_active
    - Validates organization ownership
    - Logs audit trail
    """
    try:
        updated_content = update_use_case.execute(
            content_id=content_id,
            organization_id=current_user.organization_id,
            title=request_body.title,
            description=request_body.description,
            duration=request_body.duration,
            is_active=request_body.is_active
        )

        # Invalidate cache
        cache.invalidate_content(content_id, current_user.organization_id)

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="content.update",
            resource_type="content",
            resource_id=content_id,
            details={
                "title": updated_content.title,
                "duration": updated_content.duration,
                "is_active": updated_content.is_active,
                "ip_address": request.client.host if request.client else None
            }
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """Download content file (forces download instead of displaying in browser)"""
    from fastapi.responses import FileResponse
    from pathlib import Path

    try:
        # Get content
        content = get_use_case.execute(content_id, current_user.organization_id)

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


@router.delete("/{content_id}", status_code=204)
async def delete_content(
    content_id: int,
    request: Request,
    content_repo: IContentRepository = Depends(get_content_repository),
    get_use_case: GetContentUseCase = Depends(get_get_content_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete content (soft delete - sets deleted_at timestamp)"""
    try:
        # Get content first for audit log (before deletion)
        content = get_use_case.execute(content_id, current_user.organization_id)

        # Soft delete - automatically checks organization ownership
        deleted = content_repo.soft_delete(content_id, current_user.organization_id)
        
        # Invalidate cache
        if deleted:
            cache.invalidate_content(content_id, current_user.organization_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Content not found or access denied")

        # Audit log
        audit_logger.log_action(
            user_id=current_user.id,
            action="content.delete",
            resource_type="content",
            resource_id=content_id,
            details={
                "title": content.title,
                "content_type": content.content_type,
                "file_url": content.file_url,
                "organization_id": content.organization_id,
                "ip_address": request.client.host if request.client else None
            }
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Bulk delete content (soft delete)

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
            content = get_use_case.execute(content_id, current_user.organization_id)

            # Soft delete
            deleted = content_repo.soft_delete(content_id, current_user.organization_id)

            if deleted:
                deleted_count += 1

                # Audit log
                audit_logger.log_action(
                    user_id=current_user.id,
                    action="content.bulk_delete",
                    resource_type="content",
                    resource_id=content_id,
                    details={
                        "title": content.title,
                        "content_type": content.content_type,
                        "ip_address": http_request.client.host if http_request.client else None
                    }
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Bulk update content metadata

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
                organization_id=current_user.organization_id,
                title=request_body.updates.title,
                description=request_body.updates.description,
                duration=request_body.updates.duration,
                is_active=request_body.updates.is_active
            )

            updated_count += 1

            # Audit log
            audit_logger.log_action(
                user_id=current_user.id,
                action="content.bulk_update",
                resource_type="content",
                resource_id=content_id,
                details={
                    "title": updated_content.title,
                    "duration": updated_content.duration,
                    "is_active": updated_content.is_active,
                    "ip_address": http_request.client.host if http_request.client else None
                }
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
