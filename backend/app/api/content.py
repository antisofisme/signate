"""
Content Management API endpoints
Integrates with Anthias for file storage and PostgreSQL for metadata
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
import tempfile
import os

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException, ValidationException, InternalServerException
from app.schemas.common import success_response, paginated_response, APIResponse, PaginatedAPIResponse
from app.middleware.request_id import get_request_id
from typing import Optional
from app.models.user import User
from app.models.content import Content
from app.models.assignment import ContentAssignment
from app.models.device import Device
from app.models.tag import Tag
from app.schemas.content import (
    ContentUploadResponse,
    ContentResponse,
    ContentListResponse,
    ContentUpdateRequest,
    ContentAssignRequest,
    ContentAssignmentResponse
)
from app.services.anthias_service import anthias_service
from app.utils.media_metadata import MediaMetadataExtractor

logger = StructuredLogger(__name__)
router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_content(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    duration: int = Form(10),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Upload content file to Anthias and save metadata to database

    Flow:
    1. Validate file type (image or video)
    2. Upload to Anthias
    3. Save metadata to PostgreSQL with Anthias URL

    Args:
        request: FastAPI request object (for request_id)
        file: Content file (image or video)
        title: Content title
        description: Content description (optional)
        duration: Display duration in seconds (default 10)
        is_active: Whether content is active (default True)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Created content with Anthias URL wrapped in standardized response

    Raises:
        BadRequestException: If file type invalid or upload fails
        InternalServerException: If unexpected error occurs
    """
    request_id = get_request_id(request)

    logger.info(
        "Content upload started",
        request_id=request_id,
        filename=file.filename,
        title=title,
        content_type=file.content_type
    )

    try:
        # Validate file type
        if not file.content_type:
            raise BadRequestException(
                message="Could not determine file type",
                details={"filename": file.filename}
            )

        # Determine content type
        if file.content_type.startswith("image/"):
            content_type = "image"
        elif file.content_type.startswith("video/"):
            content_type = "video"
        else:
            raise BadRequestException(
                message=f"Unsupported file type: {file.content_type}. Only images and videos are supported.",
                details={"content_type": file.content_type, "filename": file.filename}
            )

        logger.info(
            "Uploading to Anthias",
            request_id=request_id,
            content_type=content_type,
            filename=file.filename
        )

        # Upload to Anthias
        anthias_asset = await anthias_service.upload_asset(
            file=file,
            name=title,
            duration=duration,
            is_enabled=is_active
        )

        # Get Anthias asset URL
        anthias_url = await anthias_service.get_asset_url(anthias_asset["asset_id"])

        # Get file size from anthias response
        file_size = anthias_asset.get("file_size", 0)

        # Extract metadata using FFprobe
        metadata = {}
        temp_file_path = None
        try:
            # Save uploaded file to temporary location for metadata extraction
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                # Reset file pointer to beginning
                await file.seek(0)
                content_bytes = await file.read()
                temp_file.write(content_bytes)
                temp_file_path = temp_file.name

            # Extract metadata based on content type
            logger.info(f"Extracting metadata from {temp_file_path}")
            metadata = MediaMetadataExtractor.extract_metadata(temp_file_path, content_type)
            logger.info(f"Extracted metadata: {metadata}")

        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            # Continue without metadata if extraction fails
            metadata = {}
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")

        # Auto-set duration for videos without segment timing
        # For videos: duration should default to video_duration, not 10 seconds
        final_duration = duration
        video_duration_val = metadata.get("duration")
        if content_type == "video" and video_duration_val:
            # Default: use full video duration
            final_duration = int(video_duration_val)
            logger.info(f"Video duration auto-set to {final_duration}s (from video_duration)")

        # Save metadata to database
        content = Content(
            title=title,
            description=description,
            content_type=content_type,
            anthias_url=anthias_url,
            anthias_asset_id=anthias_asset["asset_id"],
            duration=final_duration,
            is_active=is_active,
            file_size=metadata.get("file_size") or file_size,
            mime_type=file.content_type,
            # Media metadata from FFprobe
            resolution=metadata.get("resolution"),
            width=metadata.get("width"),
            height=metadata.get("height"),
            codec=metadata.get("codec"),
            fps=metadata.get("fps"),
            bitrate=metadata.get("bitrate"),
            video_duration=video_duration_val,
            audio_codec=metadata.get("audio_codec"),
            audio_bitrate=metadata.get("audio_bitrate"),
            audio_sample_rate=metadata.get("audio_sample_rate")
        )

        db.add(content)
        db.commit()
        db.refresh(content)

        logger.info(
            "Content upload completed",
            request_id=request_id,
            content_id=content.id,
            anthias_asset_id=content.anthias_asset_id,
            title=content.title
        )

        # Convert SQLAlchemy model to dict for response
        content_dict = {
            "id": content.id,
            "title": content.title,
            "description": content.description,
            "content_type": content.content_type,
            "anthias_url": content.anthias_url,
            "anthias_asset_id": content.anthias_asset_id,
            "duration": content.duration,
            "is_active": content.is_active,
            "file_size": content.file_size,
            "mime_type": content.mime_type,
            "resolution": content.resolution,
            "width": content.width,
            "height": content.height,
            "codec": content.codec,
            "fps": content.fps,
            "bitrate": content.bitrate,
            "video_duration": content.video_duration,
            "audio_codec": content.audio_codec,
            "audio_bitrate": content.audio_bitrate,
            "audio_sample_rate": content.audio_sample_rate,
            "created_at": content.created_at,
            "updated_at": content.updated_at
        }

        return success_response(
            data=content_dict,
            request_id=request_id
        )

    except (BadRequestException, ValidationException):
        # Re-raise custom exceptions (already have proper format)
        raise
    except Exception as e:
        logger.error(
            "Content upload failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        db.rollback()
        raise InternalServerException(
            message="Upload failed",
            details={"error": str(e)}
        )


@router.get("/")
def list_content(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    content_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    List all content with optional filters

    Args:
        request: FastAPI request object (for request_id)
        skip: Number of records to skip (pagination)
        limit: Max number of records to return
        content_type: Filter by content type (image/video)
        is_active: Filter by active status
        db: Database session
        current_user: Authenticated user

    Returns:
        PaginatedAPIResponse: List of content with pagination metadata
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing content",
        request_id=request_id,
        skip=skip,
        limit=limit,
        content_type=content_type,
        is_active=is_active
    )

    # Build query
    query = db.query(Content)

    # Apply filters
    if content_type:
        query = query.filter(Content.content_type == content_type)
    if is_active is not None:
        query = query.filter(Content.is_active == is_active)

    # Get total count
    total = query.count()

    # Get content with pagination
    contents = query.order_by(Content.created_at.desc()).offset(skip).limit(limit).all()

    logger.info(
        "Content listed successfully",
        request_id=request_id,
        total=total,
        returned=len(contents)
    )

    # Convert to dicts
    content_list = []
    for content in contents:
        content_dict = {
            "id": content.id,
            "title": content.title,
            "description": content.description,
            "content_type": content.content_type,
            "anthias_url": content.anthias_url,
            "anthias_asset_id": content.anthias_asset_id,
            "duration": content.duration,
            "is_active": content.is_active,
            "file_size": content.file_size,
            "mime_type": content.mime_type,
            "resolution": content.resolution,
            "width": content.width,
            "height": content.height,
            "created_at": content.created_at,
            "updated_at": content.updated_at
        }
        content_list.append(content_dict)

    # Calculate page number (1-indexed)
    page = (skip // limit) + 1 if limit > 0 else 1

    return paginated_response(
        data=content_list,
        total=total,
        page=page,
        page_size=limit,
        request_id=request_id
    )


@router.get("/{content_id}")
def get_content(
    content_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get content by ID

    Args:
        content_id: Content ID
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Content details wrapped in standardized response

    Raises:
        NotFoundException: If content not found
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching content",
        request_id=request_id,
        content_id=content_id
    )

    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        logger.warning(
            "Content not found",
            request_id=request_id,
            content_id=content_id
        )
        raise NotFoundException(
            message=f"Content with ID {content_id} not found",
            resource_type="Content",
            resource_id=content_id
        )

    logger.info(
        "Content fetched successfully",
        request_id=request_id,
        content_id=content_id,
        title=content.title
    )

    # Convert to dict
    content_dict = {
        "id": content.id,
        "title": content.title,
        "description": content.description,
        "content_type": content.content_type,
        "anthias_url": content.anthias_url,
        "anthias_asset_id": content.anthias_asset_id,
        "duration": content.duration,
        "is_active": content.is_active,
        "file_size": content.file_size,
        "mime_type": content.mime_type,
        "resolution": content.resolution,
        "width": content.width,
        "height": content.height,
        "codec": content.codec,
        "fps": content.fps,
        "bitrate": content.bitrate,
        "video_duration": content.video_duration,
        "created_at": content.created_at,
        "updated_at": content.updated_at
    }

    return success_response(
        data=content_dict,
        request_id=request_id
    )


@router.patch("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    content_data: ContentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update content metadata (partial update)

    Args:
        content_id: Content ID
        content_data: Update data (partial - only changed fields)
        db: Database session
        current_user: Authenticated user

    Returns:
        ContentResponse: Updated content

    Raises:
        HTTPException: If content not found or update fails
    """
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )

    try:
        # Update local database (primary source of truth for viewers)
        if content_data.title is not None:
            content.title = content_data.title
        if content_data.description is not None:
            content.description = content_data.description
        if content_data.duration is not None:
            content.duration = content_data.duration
        if content_data.video_start_time is not None:
            content.video_start_time = content_data.video_start_time
        if content_data.video_end_time is not None:
            content.video_end_time = content_data.video_end_time
        if content_data.is_active is not None:
            content.is_active = content_data.is_active

        # Commit database changes first (this is what viewers use)
        db.commit()
        db.refresh(content)

        # Try to update Anthias (optional - for consistency only)
        # If this fails, database update still succeeds since it's already committed
        if content.anthias_asset_id and (content_data.title or content_data.duration or content_data.is_active is not None):
            try:
                await anthias_service.update_asset(
                    asset_id=content.anthias_asset_id,
                    name=content.title if content_data.title else None,
                    duration=content.duration if content_data.duration else None,
                    is_enabled=content.is_active if content_data.is_active is not None else None
                )
                logger.info(f"Anthias asset {content.anthias_asset_id} updated")
            except Exception as anthias_error:
                # Log warning but don't fail the request
                # Viewers use our database, not Anthias metadata
                logger.warning(f"Failed to update Anthias asset {content.anthias_asset_id}: {anthias_error}")
                logger.warning("Database update succeeded, but Anthias sync failed (non-critical)")

        logger.info(f"Content updated: ID={content.id}")
        return content

    except Exception as e:
        logger.error(f"Database update error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete content from both Anthias and database

    Args:
        content_id: Content ID
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If content not found or deletion fails

    Notes:
        - Deletes file from Anthias
        - Deletes metadata from PostgreSQL
        - Cascades to content_assignments
    """
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )

    try:
        # Delete from Anthias if asset ID exists
        if content.anthias_asset_id:
            await anthias_service.delete_asset(content.anthias_asset_id)
            logger.info(f"Deleted from Anthias: {content.anthias_asset_id}")

        # Delete from database (cascades to assignments)
        db.delete(content)
        db.commit()

        logger.info(f"Content deleted: ID={content_id}")
        return None

    except Exception as e:
        logger.error(f"Delete error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )


@router.post("/{content_id}/assign", response_model=ContentAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_content(
    content_id: int,
    assignment_data: ContentAssignRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Assign content to a device or tag

    Args:
        content_id: Content ID
        assignment_data: Assignment data (device_id or tag_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        ContentAssignmentResponse: Created assignment

    Raises:
        HTTPException: If content, device, or tag not found

    Notes:
        - Must assign to EITHER device OR tag (not both)
        - If assigned to tag, content will show on all devices with that tag
    """
    # Validate content exists
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )

    # Validate assignment target (must be device OR tag, not both)
    if not assignment_data.device_id and not assignment_data.tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must assign to either device_id or tag_id"
        )

    if assignment_data.device_id and assignment_data.tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign to both device_id and tag_id"
        )

    # Validate device or tag exists
    if assignment_data.device_id:
        device = db.query(Device).filter(Device.id == assignment_data.device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {assignment_data.device_id} not found"
            )

        # Only allow assignment to active devices
        if device.status != 'active':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot assign content to device with status '{device.status}'. Device must be active."
            )

    if assignment_data.tag_id:
        tag = db.query(Tag).filter(Tag.id == assignment_data.tag_id).first()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {assignment_data.tag_id} not found"
            )

    # Check if assignment already exists
    existing = db.query(ContentAssignment).filter(
        ContentAssignment.content_id == content_id,
        ContentAssignment.device_id == assignment_data.device_id,
        ContentAssignment.tag_id == assignment_data.tag_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignment already exists"
        )

    # Create assignment
    assignment = ContentAssignment(
        content_id=content_id,
        device_id=assignment_data.device_id,
        tag_id=assignment_data.tag_id,
        priority=assignment_data.priority
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    logger.info(f"Content assigned: content_id={content_id}, device_id={assignment_data.device_id}, tag_id={assignment_data.tag_id}")

    return assignment


@router.get("/{content_id}/assignments", response_model=List[ContentAssignmentResponse])
def get_content_assignments(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all assignments for a content

    Args:
        content_id: Content ID
        db: Database session
        current_user: Authenticated user

    Returns:
        List[ContentAssignmentResponse]: List of assignments
    """
    # Validate content exists
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )

    assignments = db.query(ContentAssignment).filter(
        ContentAssignment.content_id == content_id
    ).all()

    return assignments


@router.delete("/{content_id}/assign", status_code=status.HTTP_204_NO_CONTENT)
def unassign_content(
    content_id: int,
    assignment_data: ContentAssignRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Unassign content from a device or tag

    Args:
        content_id: Content ID
        assignment_data: Assignment data (device_id or tag_id)
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If assignment not found

    Notes:
        - Removes the assignment relationship
        - Content will no longer appear in device/tag playlist
    """
    # Validate assignment target
    if not assignment_data.device_id and not assignment_data.tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either device_id or tag_id"
        )

    if assignment_data.device_id and assignment_data.tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot specify both device_id and tag_id"
        )

    # Find assignment
    assignment = db.query(ContentAssignment).filter(
        ContentAssignment.content_id == content_id,
        ContentAssignment.device_id == assignment_data.device_id,
        ContentAssignment.tag_id == assignment_data.tag_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    # Delete assignment
    db.delete(assignment)
    db.commit()

    logger.info(f"Content unassigned: content_id={content_id}, device_id={assignment_data.device_id}, tag_id={assignment_data.tag_id}")

    return None


@router.get("/{content_id}/image")
async def get_content_image(
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    Proxy endpoint to serve content image with correct Content-Type

    This endpoint fetches the image from Anthias (which stores files without extensions)
    and serves it with the correct Content-Type header so browsers can display it.

    Args:
        content_id: Content ID
        db: Database session

    Returns:
        Response: Image file with correct Content-Type

    Raises:
        HTTPException: If content not found or fetch fails
    """
    # Get content metadata from database
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )

    if not content.anthias_asset_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content has no associated Anthias asset"
        )

    try:
        # Fetch image content from Anthias
        image_bytes = await anthias_service.get_asset_content(content.anthias_asset_id)

        # Determine Content-Type from mime_type in database
        media_type = content.mime_type or "application/octet-stream"

        # Return image with correct Content-Type
        return Response(content=image_bytes, media_type=media_type)

    except Exception as e:
        logger.error(f"Error serving image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve image: {str(e)}"
        )


@router.get("/{content_id}/video")
async def get_content_video(
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    Proxy endpoint to serve content video with correct Content-Type

    This endpoint fetches the video from Anthias and serves it with the correct
    Content-Type header and supports range requests for video streaming.

    Args:
        content_id: Content ID
        db: Database session

    Returns:
        Response: Video file with correct Content-Type

    Raises:
        HTTPException: If content not found or fetch fails
    """
    # Get content metadata from database
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )

    if not content.anthias_asset_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content has no associated Anthias asset"
        )

    try:
        # Fetch video content from Anthias
        video_bytes = await anthias_service.get_asset_content(content.anthias_asset_id)

        # Determine Content-Type from mime_type in database
        media_type = content.mime_type or "video/mp4"

        # Return video with correct Content-Type and Accept-Ranges header for streaming
        return Response(
            content=video_bytes,
            media_type=media_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(len(video_bytes))
            }
        )

    except Exception as e:
        logger.error(f"Error serving video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve video: {str(e)}"
        )
