"""Menu Media API Routes - Image management for menus"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from PIL import Image
import io

from shared.database import get_db
from shared.responses import success_response
from shared.auth import get_current_user, CurrentUser
from shared.config import settings

from .repositories import MenuMediaRepository
from .dtos import MenuMediaResponseDTO, MenuMediaListDTO, MenuMediaUpdateDTO

router = APIRouter(prefix="/api/v1/menu-media", tags=["menu-media"])

# Allowed image types
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# ========== Dependency Injection ==========

def get_menu_media_repository(db: Session = Depends(get_db)) -> MenuMediaRepository:
    """Inject menu media repository"""
    return MenuMediaRepository(db)


def build_media_url(file_path: str) -> str:
    """Build full URL for menu media"""
    return f"{settings.API_URL}/menu-media-files/{file_path}"


# ========== Menu Media Endpoints ==========

@router.get("")
def list_menu_media(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
    current_user: CurrentUser = Depends(get_current_user),
    media_repo: MenuMediaRepository = Depends(get_menu_media_repository)
):
    """List all menu media for current organization"""
    media_list, total = media_repo.find_all(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit,
        is_active=is_active
    )

    # Build response with URLs
    items = []
    for media in media_list:
        response = MenuMediaResponseDTO.model_validate(media)
        response.url = build_media_url(media.file_path)
        items.append(response)

    return success_response(data={
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_next": (skip + limit) < total
    })


@router.post("", status_code=201)
async def upload_menu_media(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    alt_text: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    media_repo: MenuMediaRepository = Depends(get_menu_media_repository)
):
    """Upload new menu media image"""
    # Validate file extension
    original_filename = file.filename or "unknown"
    ext = os.path.splitext(original_filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Get image dimensions
    try:
        img = Image.open(io.BytesIO(content))
        width, height = img.size
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Generate unique filename
    unique_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"menu_{timestamp}_{unique_id}{ext}"

    # Create directory for organization
    org_dir = f"menu_media/org_{current_user.organization_id}"
    upload_dir = os.path.join(settings.UPLOAD_DIR, org_dir)
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = f"{org_dir}/{filename}"
    full_path = os.path.join(settings.UPLOAD_DIR, file_path)

    with open(full_path, "wb") as f:
        f.write(content)

    # Create database record
    media = media_repo.create(
        organization_id=current_user.organization_id,
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type or "image/jpeg",
        uploaded_by_id=current_user.id,
        width=width,
        height=height,
        title=title,
        alt_text=alt_text
    )

    response = MenuMediaResponseDTO.model_validate(media)
    response.url = build_media_url(media.file_path)

    return success_response(data=response)


@router.get("/{media_id}")
def get_menu_media(
    media_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    media_repo: MenuMediaRepository = Depends(get_menu_media_repository)
):
    """Get single menu media"""
    media = media_repo.find_by_id(media_id, current_user.organization_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    response = MenuMediaResponseDTO.model_validate(media)
    response.url = build_media_url(media.file_path)

    return success_response(data=response)


@router.patch("/{media_id}")
def update_menu_media(
    media_id: int,
    payload: MenuMediaUpdateDTO,
    current_user: CurrentUser = Depends(get_current_user),
    media_repo: MenuMediaRepository = Depends(get_menu_media_repository)
):
    """Update menu media metadata"""
    media = media_repo.find_by_id(media_id, current_user.organization_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    update_data = payload.model_dump(exclude_unset=True)
    media = media_repo.update(media, **update_data)

    response = MenuMediaResponseDTO.model_validate(media)
    response.url = build_media_url(media.file_path)

    return success_response(data=response)


@router.delete("/{media_id}", status_code=204)
def delete_menu_media(
    media_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    media_repo: MenuMediaRepository = Depends(get_menu_media_repository)
):
    """Soft delete menu media"""
    media = media_repo.find_by_id(media_id, current_user.organization_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    media_repo.soft_delete(media)

    return None
