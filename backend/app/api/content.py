"""
Content Management API endpoints
Integrates with Anthias for file storage and PostgreSQL for metadata
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
import tempfile
import os

from app.core.database import get_db
from app.core.deps import get_current_active_user
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

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=ContentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    duration: int = Form(10),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload content file to Anthias and save metadata to database

    Flow:
    1. Validate file type (image or video)
    2. Upload to Anthias
    3. Save metadata to PostgreSQL with Anthias URL

    Args:
        file: Content file (image or video)
        title: Content title
        description: Content description (optional)
        duration: Display duration in seconds (default 10)
        is_active: Whether content is active (default True)
        db: Database session
        current_user: Authenticated user

    Returns:
        ContentUploadResponse: Created content with Anthias URL

    Raises:
        HTTPException: If upload fails or invalid file type
    """
    try:
        # Validate file type
        if not file.content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not determine file type"
            )

        # Determine content type
        if file.content_type.startswith("image/"):
            content_type = "image"
        elif file.content_type.startswith("video/"):
            content_type = "video"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}. Only images and videos are supported."
            )

        logger.info(f"Uploading {content_type} to Anthias: {file.filename}")

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

        # Save metadata to database
        content = Content(
            title=title,
            description=description,
            content_type=content_type,
            anthias_url=anthias_url,
            anthias_asset_id=anthias_asset["asset_id"],
            duration=duration,
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
            video_duration=metadata.get("duration"),
            audio_codec=metadata.get("audio_codec"),
            audio_bitrate=metadata.get("audio_bitrate"),
            audio_sample_rate=metadata.get("audio_sample_rate")
        )

        db.add(content)
        db.commit()
        db.refresh(content)

        logger.info(f"Content created: ID={content.id}, Anthias ID={content.anthias_asset_id}")

        return content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/", response_model=ContentListResponse)
def list_content(
    skip: int = 0,
    limit: int = 100,
    content_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all content with optional filters

    Args:
        skip: Number of records to skip (pagination)
        limit: Max number of records to return
        content_type: Filter by content type (image/video)
        is_active: Filter by active status
        db: Database session
        current_user: Authenticated user

    Returns:
        ContentListResponse: List of content with total count
    """
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

    return ContentListResponse(
        total=total,
        items=contents
    )


@router.get("/{content_id}", response_model=ContentResponse)
def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get content by ID

    Args:
        content_id: Content ID
        db: Database session
        current_user: Authenticated user

    Returns:
        ContentResponse: Content details

    Raises:
        HTTPException: If content not found
    """
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )

    return content


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    content_data: ContentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update content metadata

    Args:
        content_id: Content ID
        content_data: Update data
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
        # Update local database
        if content_data.title is not None:
            content.title = content_data.title
        if content_data.description is not None:
            content.description = content_data.description
        if content_data.duration is not None:
            content.duration = content_data.duration
        if content_data.is_active is not None:
            content.is_active = content_data.is_active

        # Update Anthias if needed
        if content.anthias_asset_id and (content_data.title or content_data.duration or content_data.is_active is not None):
            await anthias_service.update_asset(
                asset_id=content.anthias_asset_id,
                name=content.title if content_data.title else None,
                duration=content.duration if content_data.duration else None,
                is_enabled=content.is_active if content_data.is_active is not None else None
            )

        db.commit()
        db.refresh(content)

        logger.info(f"Content updated: ID={content.id}")
        return content

    except Exception as e:
        logger.error(f"Update error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
