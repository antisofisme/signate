"""
Content API Endpoints
====================

Content management with storage integration (Anthias).
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, File, UploadFile, Form, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.storage import StorageService
from app.repositories import ContentRepository, OrganizationRepository
from app.schemas.content import (
    ContentResponse,
    ContentUploadResponse,
    ContentUpdate,
    ContentListResponse,
    ContentStatsResponse,
    StorageUsageResponse,
    ContentFileServeResponse
)

router = APIRouter()


@router.post(
    "/upload",
    response_model=ContentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Content File",
    description="Upload content file with storage integration (video, image, or web)"
)
async def upload_content(
    file: UploadFile = File(..., description="Content file to upload"),
    organization_id: int = Form(..., description="Organization ID"),
    title: Optional[str] = Form(None, description="Content title"),
    description: Optional[str] = Form(None, description="Content description"),
    content_type: str = Form(..., description="Content type: video, image, or web"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    check_quota: bool = Form(True, description="Check storage quota before upload"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload content file to Anthias storage.

    **Flow**:
    1. Validate file type and size
    2. Check organization storage quota
    3. Upload to Anthias storage service
    4. Create Content database record
    5. Return complete metadata

    **File Limits**:
    - Video: 500 MB
    - Image: 10 MB
    - Web (HTML/PDF): 5 MB

    **Supported Formats**:
    - Video: MP4, WebM, OGG, AVI, MOV
    - Image: JPEG, PNG, GIF, WebP, SVG
    - Web: HTML, PDF
    """
    # Validate organization exists
    org_repo = OrganizationRepository(db)
    org = org_repo.get(organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {organization_id} not found"
        )

    if not org.is_active:
        raise ForbiddenException(
            message="Organization is not active"
        )

    # Parse tags
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    # Initialize storage service
    storage_service = StorageService(db)

    try:
        # Upload content
        content = await storage_service.upload_content(
            file=file.file,
            filename=file.filename,
            organization_id=organization_id,
            title=title,
            description=description,
            content_type=content_type,
            check_quota=check_quota
        )

        # Add tags if provided
        if tag_list:
            content_repo = ContentRepository(db)
            content_obj = content_repo.get(content["id"])
            if content_obj:
                content_obj.tags = tag_list
                db.commit()
                content["tags"] = tag_list

        # Calculate file size in MB
        content["file_size_mb"] = round(content["file_size"] / (1024 * 1024), 2)

        return {
            **content,
            "upload_info": {
                "storage_service": "anthias",
                "quota_checked": check_quota
            }
        }

    except Exception as e:
        # Re-raise known exceptions
        if isinstance(e, (BadRequestException, ForbiddenException)):
            raise

        # Wrap unknown exceptions
        raise BadRequestException(
            message="Upload failed",
            details={"error": str(e)}
        )


@router.get(
    "/{content_id}",
    response_model=ContentResponse,
    summary="Get Content Details",
    description="Get content metadata by ID"
)
async def get_content(
    content_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get content details.

    Returns complete content metadata including:
    - Basic info (title, description, type)
    - File info (size, MIME type)
    - Storage info (Anthias asset ID, URL)
    - Tags
    - Timestamps
    """
    content_repo = ContentRepository(db)
    content = content_repo.get(content_id)

    if not content:
        raise NotFoundException(
            message=f"Content {content_id} not found"
        )

    content_dict = content.to_dict()
    content_dict["file_size_mb"] = round(content.file_size / (1024 * 1024), 2)

    return content_dict


@router.get(
    "/{content_id}/file",
    response_class=RedirectResponse,
    summary="Serve Content File",
    description="Redirect to Anthias file serve URL"
)
async def serve_content_file(
    content_id: int,
    db: Session = Depends(get_db)
) -> RedirectResponse:
    """
    Serve content file.

    **Returns**: Redirect (302) to Anthias storage serve URL

    **Usage**:
    ```html
    <video src="http://192.168.5.12:8001/api/v1/content/1/file" />
    <img src="http://192.168.5.12:8001/api/v1/content/2/file" />
    ```
    """
    content_repo = ContentRepository(db)
    content = content_repo.get(content_id)

    if not content:
        raise NotFoundException(
            message=f"Content {content_id} not found"
        )

    if not content.anthias_url:
        raise BadRequestException(
            message="Content file URL not available"
        )

    # Redirect to Anthias serve URL
    return RedirectResponse(
        url=content.anthias_url,
        status_code=status.HTTP_302_FOUND
    )


@router.put(
    "/{content_id}",
    response_model=ContentResponse,
    summary="Update Content",
    description="Update content metadata (not file)"
)
async def update_content(
    content_id: int,
    content_update: ContentUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update content metadata.

    **Note**: Cannot update the file itself. To replace file:
    1. Delete old content
    2. Upload new content

    **Updatable Fields**:
    - title
    - description
    - tags
    - is_active
    - display_duration
    """
    content_repo = ContentRepository(db)
    content = content_repo.get(content_id)

    if not content:
        raise NotFoundException(
            message=f"Content {content_id} not found"
        )

    # Build update dict
    update_data = content_update.model_dump(exclude_none=True)

    # Update content
    updated_content = content_repo.update(content_id, update_data)

    content_dict = updated_content.to_dict()
    content_dict["file_size_mb"] = round(updated_content.file_size / (1024 * 1024), 2)

    return content_dict


@router.delete(
    "/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Content",
    description="Delete content and its Anthias storage asset"
)
async def delete_content(
    content_id: int,
    organization_id: int = Query(..., description="Organization ID for validation"),
    db: Session = Depends(get_db)
):
    """
    Delete content.

    **Flow**:
    1. Validate content exists
    2. Validate organization ownership
    3. Delete from Anthias storage (graceful if fails)
    4. Delete from database

    **Cascade**: Also removes from playlists
    """
    storage_service = StorageService(db)

    try:
        await storage_service.delete_content(
            content_id=content_id,
            organization_id=organization_id
        )
        return None

    except NotFoundException:
        raise

    except Exception as e:
        raise BadRequestException(
            message="Delete failed",
            details={"error": str(e)}
        )


@router.get(
    "/",
    response_model=ContentListResponse,
    summary="List Content",
    description="List organization content with pagination and filtering"
)
async def list_content(
    organization_id: int = Query(..., description="Organization ID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    content_type: Optional[str] = Query(None, description="Filter by type: video, image, web"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, min_length=2, description="Search in title/description"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List organization content.

    **Filters**:
    - content_type: Filter by video/image/web
    - is_active: Filter by active status
    - search: Search in title and description

    **Sorting**: By created_at DESC (newest first)
    """
    # Validate organization
    org_repo = OrganizationRepository(db)
    org = org_repo.get(organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {organization_id} not found"
        )

    content_repo = ContentRepository(db)

    # Build filters
    filters = {"organization_id": organization_id}
    if content_type:
        if content_type not in ["video", "image", "web"]:
            raise BadRequestException(
                message="content_type must be: video, image, or web"
            )
        filters["content_type"] = content_type

    if is_active is not None:
        filters["is_active"] = is_active

    # Get content list
    content_list = content_repo.get_by_organization(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        filters=filters,
        search=search
    )

    # Get total count
    total = content_repo.count_by_organization(
        organization_id=organization_id,
        filters=filters,
        search=search
    )

    # Format response
    contents = []
    for content in content_list:
        content_dict = content.to_dict()
        content_dict["file_size_mb"] = round(content.file_size / (1024 * 1024), 2)
        contents.append(content_dict)

    return {
        "contents": contents,
        "total": total,
        "skip": skip,
        "limit": limit,
        "filters": filters
    }


@router.get(
    "/stats/{organization_id}",
    response_model=ContentStatsResponse,
    summary="Get Content Statistics",
    description="Get content statistics by type and MIME type"
)
async def get_content_stats(
    organization_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get content statistics.

    **Returns**:
    - Total content count
    - Total size (bytes and GB)
    - Count by type (video, image, web)
    - Count by MIME type
    - Active/inactive count
    """
    # Validate organization
    org_repo = OrganizationRepository(db)
    org = org_repo.get(organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {organization_id} not found"
        )

    content_repo = ContentRepository(db)

    # Get stats from repository
    stats = content_repo.get_organization_stats(organization_id)

    return {
        "organization_id": organization_id,
        "total_content": stats["total"],
        "total_size_bytes": stats["total_size_bytes"],
        "total_size_gb": round(stats["total_size_bytes"] / (1024 * 1024 * 1024), 2),
        "by_type": stats["by_type"],
        "by_mime_type": stats["by_mime_type"],
        "active_count": stats["active"],
        "inactive_count": stats["inactive"]
    }


@router.get(
    "/storage/usage/{organization_id}",
    response_model=StorageUsageResponse,
    summary="Get Storage Usage",
    description="Get organization storage usage with quota comparison"
)
async def get_storage_usage(
    organization_id: int,
    include_largest: bool = Query(True, description="Include top 5 largest files"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get storage usage statistics.

    **Returns**:
    - Total storage used (bytes and GB)
    - Maximum storage quota (GB)
    - Available storage (GB)
    - Usage percentage
    - Content count
    - Optional: Top 5 largest files
    """
    # Validate organization
    org_repo = OrganizationRepository(db)
    org = org_repo.get(organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {organization_id} not found"
        )

    content_repo = ContentRepository(db)

    # Get storage usage
    usage = org_repo.get_storage_usage(organization_id)

    # Get content count
    content_count = content_repo.count_by_organization(
        organization_id=organization_id,
        filters={"is_active": True}
    )

    # Get largest files if requested
    largest_files = None
    if include_largest:
        largest_content = content_repo.get_largest_files(
            organization_id=organization_id,
            limit=5
        )
        largest_files = [
            {
                "id": content.id,
                "title": content.title,
                "file_size_mb": round(content.file_size / (1024 * 1024), 2),
                "content_type": content.content_type
            }
            for content in largest_content
        ]

    return {
        "organization_id": organization_id,
        "total_size_bytes": usage["total_size_bytes"],
        "total_size_gb": usage["used_storage_gb"],
        "max_storage_gb": org.max_storage_gb,
        "available_gb": org.max_storage_gb - usage["used_storage_gb"],
        "usage_percentage": (usage["used_storage_gb"] / org.max_storage_gb * 100) if org.max_storage_gb > 0 else 0,
        "content_count": content_count,
        "largest_files": largest_files
    }
