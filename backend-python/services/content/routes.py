"""
Content API Routes
FastAPI endpoints with dependency injection
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException
from typing import Optional
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.api_routes import ContentRoutes
from shared.responses import success_response, error_response, paginated_response, created_response
from shared.auth import CurrentUser, get_current_user

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


@router.delete("/{content_id}", status_code=204)
async def delete_content(
    content_id: int,
    content_repo: IContentRepository = Depends(get_content_repository),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete content (soft delete - sets deleted_at timestamp)"""
    try:
        # Soft delete - automatically checks organization ownership
        deleted = content_repo.soft_delete(content_id, current_user.organization_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Content not found or access denied")

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
