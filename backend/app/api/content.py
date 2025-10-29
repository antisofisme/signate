"""
Content Management API endpoints
Integrates with Anthias for file storage and PostgreSQL for metadata
"""

from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, List
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

        # Get Anthias asset URL and cache the file URI
        # PHASE 1 OPTIMIZATION: Cache URI to avoid repeated API calls
        anthias_url = await anthias_service.get_asset_url(anthias_asset["asset_id"])

        # Extract and cache the file URI from the get_asset response
        # This eliminates the need to call get_asset_url() on every content list/get operation
        asset_details = await anthias_service.get_asset(anthias_asset["asset_id"])
        anthias_file_uri = asset_details.get("uri")  # e.g., "/data/screenly_assets/abc123.jpg"

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
            anthias_file_uri=anthias_file_uri,  # PHASE 1: Cache URI for performance
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
            "anthias_file_uri": content.anthias_file_uri,
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
    page: int = 1,
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
        page: Page number (1-indexed, default 1)
        limit: Max number of records to return (default 100)
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
        page=page,
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

    # Calculate offset from page number
    offset = (page - 1) * limit

    # Get content with pagination
    contents = query.order_by(Content.created_at.desc()).offset(offset).limit(limit).all()

    logger.info(
        "Content listed successfully",
        request_id=request_id,
        total=total,
        returned=len(contents),
        page=page
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
            "anthias_file_uri": content.anthias_file_uri,
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
        "anthias_file_uri": content.anthias_file_uri,
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update content metadata (partial update)

    Args:
        content_id: Content ID
        content_data: Update data (partial - only changed fields)
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Updated content wrapped in standardized response

    Raises:
        NotFoundException: If content not found
        InternalServerException: If update fails
    """
    request_id = get_request_id(request)

    logger.info(
        "Updating content",
        request_id=request_id,
        content_id=content_id,
        fields_to_update=content_data.dict(exclude_unset=True)
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
                logger.info(
                    "Anthias asset updated",
                    request_id=request_id,
                    anthias_asset_id=content.anthias_asset_id
                )
            except Exception as anthias_error:
                # Log warning but don't fail the request
                # Viewers use our database, not Anthias metadata
                logger.warning(
                    "Anthias sync failed (non-critical)",
                    request_id=request_id,
                    anthias_asset_id=content.anthias_asset_id,
                    error=str(anthias_error)
                )

        logger.info(
            "Content updated successfully",
            request_id=request_id,
            content_id=content.id,
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
            "anthias_file_uri": content.anthias_file_uri,
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

    except Exception as e:
        logger.error(
            "Content update failed",
            request_id=request_id,
            content_id=content_id,
            error=str(e),
            exc_info=True
        )
        db.rollback()
        raise InternalServerException(
            message="Update failed",
            details={"error": str(e)}
        )


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete content with cascade delete to Anthias storage

    Implements cascade delete mechanism:
    1. Attempts to delete file from Anthias storage
    2. Deletes metadata from PostgreSQL (even if Anthias delete fails)
    3. Cascades to content_assignments via SQLAlchemy relationship

    Args:
        content_id: Content ID
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Success message wrapped in standardized response

    Raises:
        NotFoundException: If content not found
        InternalServerException: If database deletion fails

    Notes:
        - PostgreSQL deletion always succeeds (even if Anthias fails)
        - Anthias deletion failure is logged but non-blocking
        - Prevents orphaned files when possible, but prioritizes data consistency
    """
    request_id = get_request_id(request)

    logger.info(
        "Cascade delete initiated",
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

    anthias_asset_id = content.anthias_asset_id
    anthias_deleted = False
    anthias_error = None

    # STEP 1: Try to delete from Anthias storage (cascade delete)
    if anthias_asset_id:
        try:
            await anthias_service.delete_asset(anthias_asset_id)
            anthias_deleted = True
            logger.info(
                "Cascade delete: Anthias asset deleted",
                request_id=request_id,
                content_id=content_id,
                anthias_asset_id=anthias_asset_id
            )
        except Exception as e:
            # Log error but continue to delete from database
            # This prevents blocking deletion if Anthias is unavailable
            anthias_error = str(e)
            logger.warning(
                "Cascade delete: Anthias deletion failed (non-blocking)",
                request_id=request_id,
                content_id=content_id,
                anthias_asset_id=anthias_asset_id,
                error=anthias_error,
                resolution="Proceeding with database deletion"
            )
    else:
        logger.info(
            "Cascade delete: No Anthias asset to delete",
            request_id=request_id,
            content_id=content_id
        )

    # STEP 2: Delete from PostgreSQL (always execute)
    try:
        # This cascades to content_assignments via SQLAlchemy relationship
        db.delete(content)
        db.commit()

        logger.info(
            "Cascade delete completed",
            request_id=request_id,
            content_id=content_id,
            anthias_deleted=anthias_deleted,
            database_deleted=True
        )

        # Build response message
        response_data = {
            "message": f"Content {content_id} deleted successfully",
            "cascade_results": {
                "database_deleted": True,
                "anthias_deleted": anthias_deleted
            }
        }

        if anthias_error:
            response_data["cascade_results"]["anthias_error"] = anthias_error
            response_data["cascade_results"]["warning"] = "Anthias file may be orphaned (manual cleanup may be required)"

        return success_response(
            data=response_data,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Cascade delete: Database deletion failed",
            request_id=request_id,
            content_id=content_id,
            error=str(e),
            exc_info=True
        )
        db.rollback()
        raise InternalServerException(
            message="Database deletion failed",
            details={"error": str(e)}
        )


@router.post("/{content_id}/assign", response_model=ContentAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_content(
    content_id: int,
    assignment_data: ContentAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Assign content to a device or tag

    Args:
        content_id: Content ID
        assignment_data: Assignment data (device_id or tag_id)
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Created assignment wrapped in standardized response

    Raises:
        NotFoundException: If content, device, or tag not found
        BadRequestException: If validation fails
        ConflictException: If assignment already exists

    Notes:
        - Must assign to EITHER device OR tag (not both)
        - If assigned to tag, content will show on all devices with that tag
    """
    request_id = get_request_id(request)

    logger.info(
        "Assigning content",
        request_id=request_id,
        content_id=content_id,
        device_id=assignment_data.device_id,
        tag_id=assignment_data.tag_id,
        priority=assignment_data.priority
    )

    # Validate content exists
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

    # Validate assignment target (must be device OR tag, not both)
    if not assignment_data.device_id and not assignment_data.tag_id:
        logger.warning(
            "Invalid assignment - no target specified",
            request_id=request_id,
            content_id=content_id
        )
        raise BadRequestException(
            message="Must assign to either device_id or tag_id",
            details={"content_id": content_id}
        )

    if assignment_data.device_id and assignment_data.tag_id:
        logger.warning(
            "Invalid assignment - both targets specified",
            request_id=request_id,
            content_id=content_id,
            device_id=assignment_data.device_id,
            tag_id=assignment_data.tag_id
        )
        raise BadRequestException(
            message="Cannot assign to both device_id and tag_id",
            details={
                "content_id": content_id,
                "device_id": assignment_data.device_id,
                "tag_id": assignment_data.tag_id
            }
        )

    # Validate device or tag exists
    if assignment_data.device_id:
        device = db.query(Device).filter(Device.id == assignment_data.device_id).first()
        if not device:
            logger.warning(
                "Device not found",
                request_id=request_id,
                device_id=assignment_data.device_id
            )
            raise NotFoundException(
                message=f"Device with ID {assignment_data.device_id} not found",
                resource_type="Device",
                resource_id=assignment_data.device_id
            )

        # Only allow assignment to active devices
        if device.status != 'active':
            logger.warning(
                "Cannot assign to inactive device",
                request_id=request_id,
                device_id=device.id,
                device_status=device.status
            )
            raise BadRequestException(
                message=f"Cannot assign content to device with status '{device.status}'. Device must be active.",
                details={
                    "device_id": device.id,
                    "device_status": device.status,
                    "required_status": "active"
                }
            )

    if assignment_data.tag_id:
        tag = db.query(Tag).filter(Tag.id == assignment_data.tag_id).first()
        if not tag:
            logger.warning(
                "Tag not found",
                request_id=request_id,
                tag_id=assignment_data.tag_id
            )
            raise NotFoundException(
                message=f"Tag with ID {assignment_data.tag_id} not found",
                resource_type="Tag",
                resource_id=assignment_data.tag_id
            )

    # Check if assignment already exists
    existing = db.query(ContentAssignment).filter(
        ContentAssignment.content_id == content_id,
        ContentAssignment.device_id == assignment_data.device_id,
        ContentAssignment.tag_id == assignment_data.tag_id
    ).first()

    if existing:
        logger.warning(
            "Assignment already exists",
            request_id=request_id,
            content_id=content_id,
            device_id=assignment_data.device_id,
            tag_id=assignment_data.tag_id
        )
        raise ConflictException(
            message="Assignment already exists",
            details={
                "content_id": content_id,
                "device_id": assignment_data.device_id,
                "tag_id": assignment_data.tag_id
            }
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

    logger.info(
        "Content assigned successfully",
        request_id=request_id,
        content_id=content_id,
        device_id=assignment_data.device_id,
        tag_id=assignment_data.tag_id,
        assignment_id=assignment.id
    )

    # Convert to dict
    assignment_dict = {
        "id": assignment.id,
        "content_id": assignment.content_id,
        "device_id": assignment.device_id,
        "tag_id": assignment.tag_id,
        "priority": assignment.priority,
        "created_at": assignment.created_at
    }

    return success_response(
        data=assignment_dict,
        request_id=request_id
    )


@router.get("/{content_id}/assignments", response_model=List[ContentAssignmentResponse])
def get_content_assignments(
    content_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all assignments for a content

    Args:
        content_id: Content ID
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: List of assignments wrapped in standardized response

    Raises:
        NotFoundException: If content not found
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching content assignments",
        request_id=request_id,
        content_id=content_id
    )

    # Validate content exists
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

    assignments = db.query(ContentAssignment).filter(
        ContentAssignment.content_id == content_id
    ).all()

    logger.info(
        "Content assignments fetched successfully",
        request_id=request_id,
        content_id=content_id,
        assignment_count=len(assignments)
    )

    # Convert to list of dicts
    assignments_list = [
        {
            "id": a.id,
            "content_id": a.content_id,
            "device_id": a.device_id,
            "tag_id": a.tag_id,
            "priority": a.priority,
            "created_at": a.created_at
        }
        for a in assignments
    ]

    return success_response(
        data=assignments_list,
        request_id=request_id
    )


@router.delete("/{content_id}/assign", status_code=status.HTTP_204_NO_CONTENT)
def unassign_content(
    content_id: int,
    assignment_data: ContentAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Unassign content from a device or tag

    Args:
        content_id: Content ID
        assignment_data: Assignment data (device_id or tag_id)
        request: FastAPI request object (for request_id)
        db: Database session
        current_user: Authenticated user

    Returns:
        APIResponse: Success message wrapped in standardized response

    Raises:
        BadRequestException: If validation fails
        NotFoundException: If assignment not found

    Notes:
        - Removes the assignment relationship
        - Content will no longer appear in device/tag playlist
    """
    request_id = get_request_id(request)

    logger.info(
        "Unassigning content",
        request_id=request_id,
        content_id=content_id,
        device_id=assignment_data.device_id,
        tag_id=assignment_data.tag_id
    )

    # Validate assignment target
    if not assignment_data.device_id and not assignment_data.tag_id:
        logger.warning(
            "Invalid unassignment - no target specified",
            request_id=request_id,
            content_id=content_id
        )
        raise BadRequestException(
            message="Must specify either device_id or tag_id",
            details={"content_id": content_id}
        )

    if assignment_data.device_id and assignment_data.tag_id:
        logger.warning(
            "Invalid unassignment - both targets specified",
            request_id=request_id,
            content_id=content_id,
            device_id=assignment_data.device_id,
            tag_id=assignment_data.tag_id
        )
        raise BadRequestException(
            message="Cannot specify both device_id and tag_id",
            details={
                "content_id": content_id,
                "device_id": assignment_data.device_id,
                "tag_id": assignment_data.tag_id
            }
        )

    # Find assignment
    assignment = db.query(ContentAssignment).filter(
        ContentAssignment.content_id == content_id,
        ContentAssignment.device_id == assignment_data.device_id,
        ContentAssignment.tag_id == assignment_data.tag_id
    ).first()

    if not assignment:
        logger.warning(
            "Assignment not found",
            request_id=request_id,
            content_id=content_id,
            device_id=assignment_data.device_id,
            tag_id=assignment_data.tag_id
        )
        raise NotFoundException(
            message="Assignment not found",
            resource_type="ContentAssignment",
            details={
                "content_id": content_id,
                "device_id": assignment_data.device_id,
                "tag_id": assignment_data.tag_id
            }
        )

    # Delete assignment
    db.delete(assignment)
    db.commit()

    logger.info(
        "Content unassigned successfully",
        request_id=request_id,
        content_id=content_id,
        device_id=assignment_data.device_id,
        tag_id=assignment_data.tag_id
    )

    return success_response(
        data={"message": f"Content {content_id} unassigned successfully"},
        request_id=request_id
    )


@router.get("/{content_id}/image")
async def get_content_image(
    content_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Proxy endpoint to serve content image with correct Content-Type

    This endpoint fetches the image from Anthias (which stores files without extensions)
    and serves it with the correct Content-Type header so browsers can display it.

    Args:
        content_id: Content ID
        request: FastAPI request object (for request_id)
        db: Database session

    Returns:
        Response: Image file with correct Content-Type

    Raises:
        NotFoundException: If content not found or no Anthias asset
        InternalServerException: If fetch fails
    """
    request_id = get_request_id(request)

    logger.info(
        "Serving content image",
        request_id=request_id,
        content_id=content_id
    )

    # Get content metadata from database
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        logger.warning(
            "Content not found for image proxy",
            request_id=request_id,
            content_id=content_id
        )
        raise NotFoundException(
            message=f"Content with ID {content_id} not found",
            resource_type="Content",
            resource_id=content_id
        )

    if not content.anthias_asset_id:
        logger.warning(
            "Content has no Anthias asset",
            request_id=request_id,
            content_id=content_id
        )
        raise NotFoundException(
            message="Content has no associated Anthias asset",
            resource_type="Content",
            resource_id=content_id
        )

    try:
        # Fetch image content from Anthias
        image_bytes = await anthias_service.get_asset_content(content.anthias_asset_id)

        # Determine Content-Type from mime_type in database
        media_type = content.mime_type or "application/octet-stream"

        logger.info(
            "Image served successfully",
            request_id=request_id,
            content_id=content_id,
            media_type=media_type,
            size_bytes=len(image_bytes)
        )

        # Return image with correct Content-Type
        return Response(content=image_bytes, media_type=media_type)

    except Exception as e:
        logger.error(
            "Error serving image",
            request_id=request_id,
            content_id=content_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message="Failed to serve image",
            details={"error": str(e), "content_id": content_id}
        )


@router.get("/{content_id}/video")
async def get_content_video(
    content_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Proxy endpoint to serve content video with correct Content-Type

    This endpoint fetches the video from Anthias and serves it with the correct
    Content-Type header and supports range requests for video streaming.

    Args:
        content_id: Content ID
        request: FastAPI request object (for request_id)
        db: Database session

    Returns:
        Response: Video file with correct Content-Type

    Raises:
        NotFoundException: If content not found or no Anthias asset
        InternalServerException: If fetch fails
    """
    request_id = get_request_id(request)

    logger.info(
        "Serving content video",
        request_id=request_id,
        content_id=content_id
    )

    # Get content metadata from database
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        logger.warning(
            "Content not found for video proxy",
            request_id=request_id,
            content_id=content_id
        )
        raise NotFoundException(
            message=f"Content with ID {content_id} not found",
            resource_type="Content",
            resource_id=content_id
        )

    if not content.anthias_asset_id:
        logger.warning(
            "Content has no Anthias asset",
            request_id=request_id,
            content_id=content_id
        )
        raise NotFoundException(
            message="Content has no associated Anthias asset",
            resource_type="Content",
            resource_id=content_id
        )

    try:
        # Fetch video content from Anthias
        video_bytes = await anthias_service.get_asset_content(content.anthias_asset_id)

        # Determine Content-Type from mime_type in database
        media_type = content.mime_type or "video/mp4"

        logger.info(
            "Video served successfully",
            request_id=request_id,
            content_id=content_id,
            media_type=media_type,
            size_bytes=len(video_bytes)
        )

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
        logger.error(
            "Error serving video",
            request_id=request_id,
            content_id=content_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message="Failed to serve video",
            details={"error": str(e), "content_id": content_id}
        )
