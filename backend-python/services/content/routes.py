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

from .repositories.content_repo import get_content_repository
from .infrastructure.storage.local_storage import get_storage_service
from .infrastructure.storage.metadata_extractor import get_metadata_extractor

from .use_cases.upload_content import UploadContentUseCase
from .use_cases.list_content import ListContentUseCase
from .use_cases.get_content import GetContentUseCase

from .dtos import ContentResponse, PaginatedContentResponse
from .domain.interfaces import IContentRepository
from .infrastructure.storage.interfaces import IStorageService
from .infrastructure.storage.metadata_extractor import MetadataExtractor

router = APIRouter(prefix="/api/v1/contents", tags=["content"])


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
@router.post("/upload", response_model=dict)
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


@router.post("/bulk-upload", response_model=dict)
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


@router.get("", response_model=dict)
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

        return paginated_response(
            data=[ContentResponse.from_entity(c).dict() for c in contents],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")


@router.get("/{content_id}", response_model=dict)
async def get_content(
    content_id: int,
    get_use_case: GetContentUseCase = Depends(get_get_content_use_case),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get single content by ID"""
    try:
        content = get_use_case.execute(content_id, current_user.organization_id)

        return success_response(
            data=ContentResponse.from_entity(content).dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get failed: {str(e)}")


@router.get("/{content_id}/download")
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
