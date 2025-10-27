"""
Tags API endpoints
For managing device tags and grouping
"""

from fastapi import APIRouter, Depends, Request, status, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response
from app.models.user import User
from app.models.tag import Tag, DeviceTag
from app.models.device import Device
from app.models.assignment import ContentAssignment
from app.schemas.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagListResponse,
    DeviceTagAssign
)
from app.schemas.content import ContentAssignmentResponse

router = APIRouter()
logger = StructuredLogger(__name__)


@router.get("")
def list_tags(
    request: Request,
    sort_by: str = "newest",
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all tags with device counts

    Sort options:
    - name_asc: Sort by name A-Z
    - name_desc: Sort by name Z-A
    - newest: Sort by created date (newest first)
    - oldest: Sort by created date (oldest first)
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing tags",
        request_id=request_id,
        sort_by=sort_by
    )

    # Build query with sorting (with secondary sort by ID for consistency)
    query = db.query(Tag)

    if sort_by == "name_asc":
        query = query.order_by(Tag.tag_name.asc(), Tag.id.asc())
    elif sort_by == "name_desc":
        query = query.order_by(Tag.tag_name.desc(), Tag.id.desc())
    elif sort_by == "oldest":
        query = query.order_by(Tag.created_at.asc(), Tag.id.asc())
    else:  # newest (default)
        query = query.order_by(Tag.created_at.desc(), Tag.id.desc())

    tags = query.all()

    # Add device count for each tag
    tag_responses = []
    for tag in tags:
        device_count = db.query(func.count(DeviceTag.device_id)).filter(DeviceTag.tag_id == tag.id).scalar()
        tag_dict = tag.to_dict()
        tag_dict['device_count'] = device_count
        tag_responses.append(tag_dict)

    logger.info(
        "Tags listed successfully",
        request_id=request_id,
        total_tags=len(tag_responses)
    )

    return success_response(
        data={
            "total": len(tag_responses),
            "items": tag_responses
        },
        request_id=request_id
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_tag(
    request: Request,
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Create a new tag
    """
    request_id = get_request_id(request)

    logger.info(
        "Creating tag",
        request_id=request_id,
        tag_name=tag_data.tag_name
    )

    # Check if tag name already exists
    existing = db.query(Tag).filter(Tag.tag_name == tag_data.tag_name).first()
    if existing:
        logger.warning(
            "Tag name already exists",
            request_id=request_id,
            tag_name=tag_data.tag_name
        )
        raise ConflictException(
            message=f"Tag with name '{tag_data.tag_name}' already exists",
            details={"tag_name": tag_data.tag_name}
        )

    tag = Tag(
        tag_name=tag_data.tag_name,
        description=tag_data.description,
        color=tag_data.color
    )

    db.add(tag)
    db.commit()
    db.refresh(tag)

    tag_dict = tag.to_dict()
    tag_dict['device_count'] = 0

    logger.info(
        "Tag created successfully",
        request_id=request_id,
        tag_id=tag.id,
        tag_name=tag.tag_name
    )

    return success_response(
        data=tag_dict,
        request_id=request_id
    )


@router.post("/assign", status_code=status.HTTP_201_CREATED)
def assign_tag_to_device(
    request: Request,
    assignment: DeviceTagAssign,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Assign a tag to a device
    """
    request_id = get_request_id(request)

    logger.info(
        "Assigning tag to device",
        request_id=request_id,
        tag_id=assignment.tag_id,
        device_id=assignment.device_id
    )

    # Check if tag exists
    tag = db.query(Tag).filter(Tag.id == assignment.tag_id).first()
    if not tag:
        logger.warning(
            "Tag not found for assignment",
            request_id=request_id,
            tag_id=assignment.tag_id
        )
        raise NotFoundException(
            message=f"Tag with ID {assignment.tag_id} not found",
            resource_type="Tag",
            resource_id=assignment.tag_id
        )

    # Check if device exists and is active
    device = db.query(Device).filter(Device.id == assignment.device_id).first()
    if not device:
        logger.warning(
            "Device not found for tag assignment",
            request_id=request_id,
            device_id=assignment.device_id
        )
        raise NotFoundException(
            message=f"Device with ID {assignment.device_id} not found",
            resource_type="Device",
            resource_id=assignment.device_id
        )

    # Only allow assignment to active devices
    if device.status != 'active':
        logger.warning(
            "Cannot assign tag to inactive device",
            request_id=request_id,
            device_id=assignment.device_id,
            device_status=device.status
        )
        raise BadRequestException(
            message=f"Cannot assign tag to device with status '{device.status}'. Device must be active.",
            details={
                "device_id": assignment.device_id,
                "device_status": device.status
            }
        )

    # Check if already assigned
    existing = db.query(DeviceTag).filter(
        DeviceTag.device_id == assignment.device_id,
        DeviceTag.tag_id == assignment.tag_id
    ).first()

    if existing:
        logger.warning(
            "Tag already assigned to device",
            request_id=request_id,
            tag_id=assignment.tag_id,
            device_id=assignment.device_id
        )
        raise BadRequestException(
            message="Tag already assigned to this device",
            details={
                "tag_id": assignment.tag_id,
                "device_id": assignment.device_id
            }
        )

    # Create assignment
    device_tag = DeviceTag(
        device_id=assignment.device_id,
        tag_id=assignment.tag_id
    )

    db.add(device_tag)
    db.commit()

    logger.info(
        "Tag assigned to device successfully",
        request_id=request_id,
        tag_id=assignment.tag_id,
        device_id=assignment.device_id
    )

    return success_response(
        data={"message": "Tag assigned successfully"},
        request_id=request_id
    )


@router.delete("/assign")
def unassign_tag_from_device(
    request: Request,
    assignment: DeviceTagAssign = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Remove a tag from a device
    """
    request_id = get_request_id(request)

    logger.info(
        "Unassigning tag from device",
        request_id=request_id,
        tag_id=assignment.tag_id,
        device_id=assignment.device_id
    )

    device_tag = db.query(DeviceTag).filter(
        DeviceTag.device_id == assignment.device_id,
        DeviceTag.tag_id == assignment.tag_id
    ).first()

    if not device_tag:
        logger.warning(
            "Tag assignment not found",
            request_id=request_id,
            tag_id=assignment.tag_id,
            device_id=assignment.device_id
        )
        raise NotFoundException(
            message="Tag assignment not found",
            resource_type="DeviceTag",
            resource_id=None
        )

    db.delete(device_tag)
    db.commit()

    logger.info(
        "Tag unassigned from device successfully",
        request_id=request_id,
        tag_id=assignment.tag_id,
        device_id=assignment.device_id
    )

    return success_response(
        data={"message": "Tag unassigned successfully"},
        request_id=request_id
    )


@router.get("/{tag_id}")
def get_tag(
    request: Request,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a single tag by ID
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching tag",
        request_id=request_id,
        tag_id=tag_id
    )

    tag = db.query(Tag).filter(Tag.id == tag_id).first()

    if not tag:
        logger.warning(
            "Tag not found",
            request_id=request_id,
            tag_id=tag_id
        )
        raise NotFoundException(
            message=f"Tag with ID {tag_id} not found",
            resource_type="Tag",
            resource_id=tag_id
        )

    device_count = db.query(DeviceTag).filter(DeviceTag.tag_id == tag.id).count()
    tag_dict = tag.to_dict()
    tag_dict['device_count'] = device_count

    logger.info(
        "Tag fetched successfully",
        request_id=request_id,
        tag_id=tag.id,
        tag_name=tag.tag_name,
        device_count=device_count
    )

    return success_response(
        data=tag_dict,
        request_id=request_id
    )


@router.patch("/{tag_id}")
def update_tag(
    request: Request,
    tag_id: int,
    tag_data: TagUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update a tag
    """
    request_id = get_request_id(request)

    logger.info(
        "Updating tag",
        request_id=request_id,
        tag_id=tag_id,
        update_fields={
            "tag_name": tag_data.tag_name,
            "description": tag_data.description is not None,
            "color": tag_data.color
        }
    )

    tag = db.query(Tag).filter(Tag.id == tag_id).first()

    if not tag:
        logger.warning(
            "Tag not found for update",
            request_id=request_id,
            tag_id=tag_id
        )
        raise NotFoundException(
            message=f"Tag with ID {tag_id} not found",
            resource_type="Tag",
            resource_id=tag_id
        )

    # Update fields
    if tag_data.tag_name is not None:
        # Check if new name already exists
        existing = db.query(Tag).filter(
            Tag.tag_name == tag_data.tag_name,
            Tag.id != tag_id
        ).first()
        if existing:
            logger.warning(
                "Tag name already exists",
                request_id=request_id,
                tag_name=tag_data.tag_name,
                existing_tag_id=existing.id
            )
            raise ConflictException(
                message=f"Tag with name '{tag_data.tag_name}' already exists",
                details={"tag_name": tag_data.tag_name}
            )
        tag.tag_name = tag_data.tag_name

    if tag_data.description is not None:
        tag.description = tag_data.description

    if tag_data.color is not None:
        tag.color = tag_data.color

    db.commit()
    db.refresh(tag)

    device_count = db.query(DeviceTag).filter(DeviceTag.tag_id == tag.id).count()
    tag_dict = tag.to_dict()
    tag_dict['device_count'] = device_count

    logger.info(
        "Tag updated successfully",
        request_id=request_id,
        tag_id=tag.id,
        tag_name=tag.tag_name
    )

    return success_response(
        data=tag_dict,
        request_id=request_id
    )


@router.delete("/{tag_id}")
def delete_tag(
    request: Request,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete a tag
    """
    request_id = get_request_id(request)

    logger.info(
        "Deleting tag",
        request_id=request_id,
        tag_id=tag_id
    )

    tag = db.query(Tag).filter(Tag.id == tag_id).first()

    if not tag:
        logger.warning(
            "Tag not found for deletion",
            request_id=request_id,
            tag_id=tag_id
        )
        raise NotFoundException(
            message=f"Tag with ID {tag_id} not found",
            resource_type="Tag",
            resource_id=tag_id
        )

    tag_name = tag.tag_name
    db.delete(tag)
    db.commit()

    logger.info(
        "Tag deleted successfully",
        request_id=request_id,
        tag_id=tag_id,
        tag_name=tag_name
    )

    return success_response(
        data={"message": "Tag deleted successfully"},
        request_id=request_id
    )


@router.get("/{tag_id}/devices")
def get_tag_devices(
    request: Request,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all devices with this tag
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching devices for tag",
        request_id=request_id,
        tag_id=tag_id
    )

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        logger.warning(
            "Tag not found for devices fetch",
            request_id=request_id,
            tag_id=tag_id
        )
        raise NotFoundException(
            message=f"Tag with ID {tag_id} not found",
            resource_type="Tag",
            resource_id=tag_id
        )

    # Get devices with this tag
    device_tags = db.query(DeviceTag).filter(DeviceTag.tag_id == tag_id).all()
    device_ids = [dt.device_id for dt in device_tags]

    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
    devices_list = [device.to_dict() for device in devices]

    logger.info(
        "Tag devices fetched successfully",
        request_id=request_id,
        tag_id=tag_id,
        device_count=len(devices_list)
    )

    return success_response(
        data={
            "tag": tag.to_dict(),
            "devices": devices_list
        },
        request_id=request_id
    )


@router.get("/{tag_id}/content")
def get_tag_content(
    request: Request,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all content assigned to a tag

    Returns list of ContentAssignment objects for content assigned to this tag.

    Args:
        request: FastAPI request object
        tag_id: Tag ID
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        List[ContentAssignmentResponse]: List of content assignments

    Raises:
        404: Tag not found
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching content for tag",
        request_id=request_id,
        tag_id=tag_id
    )

    # Verify tag exists
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        logger.warning(
            "Tag not found for content fetch",
            request_id=request_id,
            tag_id=tag_id
        )
        raise NotFoundException(
            message=f"Tag with ID {tag_id} not found",
            resource_type="Tag",
            resource_id=tag_id
        )

    # Get tag content assignments with content relationship
    assignments = db.query(ContentAssignment).options(
        joinedload(ContentAssignment.content)
    ).filter(
        ContentAssignment.tag_id == tag_id,
        ContentAssignment.device_id == None
    ).order_by(ContentAssignment.display_order).all()

    assignments_list = [
        ContentAssignmentResponse.model_validate(assignment)
        for assignment in assignments
    ]

    logger.info(
        "Tag content fetched successfully",
        request_id=request_id,
        tag_id=tag_id,
        content_count=len(assignments_list)
    )

    return success_response(
        data=assignments_list,
        request_id=request_id
    )
