"""
Tags API endpoints
For managing device tags and grouping
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.tag import Tag, DeviceTag
from app.models.device import Device
from app.schemas.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagListResponse,
    DeviceTagAssign
)

router = APIRouter()


@router.get("", response_model=TagListResponse)
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all tags with device counts
    """
    tags = db.query(Tag).all()

    # Add device count for each tag
    tag_responses = []
    for tag in tags:
        device_count = db.query(DeviceTag).filter(DeviceTag.tag_id == tag.id).count()
        tag_dict = tag.to_dict()
        tag_dict['device_count'] = device_count
        tag_responses.append(TagResponse(**tag_dict))

    return TagListResponse(
        total=len(tag_responses),
        items=tag_responses
    )


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new tag
    """
    # Check if tag name already exists
    existing = db.query(Tag).filter(Tag.tag_name == tag_data.tag_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag with name '{tag_data.tag_name}' already exists"
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

    return TagResponse(**tag_dict)


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a single tag by ID
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )

    device_count = db.query(DeviceTag).filter(DeviceTag.tag_id == tag.id).count()
    tag_dict = tag.to_dict()
    tag_dict['device_count'] = device_count

    return TagResponse(**tag_dict)


@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a tag
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )

    # Update fields
    if tag_data.tag_name is not None:
        # Check if new name already exists
        existing = db.query(Tag).filter(
            Tag.tag_name == tag_data.tag_name,
            Tag.id != tag_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with name '{tag_data.tag_name}' already exists"
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

    return TagResponse(**tag_dict)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a tag
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )

    db.delete(tag)
    db.commit()

    return None


@router.post("/assign", status_code=status.HTTP_201_CREATED)
def assign_tag_to_device(
    assignment: DeviceTagAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Assign a tag to a device
    """
    # Check if tag exists
    tag = db.query(Tag).filter(Tag.id == assignment.tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {assignment.tag_id} not found"
        )

    # Check if device exists
    device = db.query(Device).filter(Device.id == assignment.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {assignment.device_id} not found"
        )

    # Check if already assigned
    existing = db.query(DeviceTag).filter(
        DeviceTag.device_id == assignment.device_id,
        DeviceTag.tag_id == assignment.tag_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag already assigned to this device"
        )

    # Create assignment
    device_tag = DeviceTag(
        device_id=assignment.device_id,
        tag_id=assignment.tag_id
    )

    db.add(device_tag)
    db.commit()

    return {"message": "Tag assigned successfully"}


@router.delete("/assign", status_code=status.HTTP_204_NO_CONTENT)
def unassign_tag_from_device(
    assignment: DeviceTagAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove a tag from a device
    """
    device_tag = db.query(DeviceTag).filter(
        DeviceTag.device_id == assignment.device_id,
        DeviceTag.tag_id == assignment.tag_id
    ).first()

    if not device_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag assignment not found"
        )

    db.delete(device_tag)
    db.commit()

    return None


@router.get("/{tag_id}/devices")
def get_tag_devices(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all devices with this tag
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )

    # Get devices with this tag
    device_tags = db.query(DeviceTag).filter(DeviceTag.tag_id == tag_id).all()
    device_ids = [dt.device_id for dt in device_tags]

    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()

    return {
        "tag": tag.to_dict(),
        "devices": [device.to_dict() for device in devices]
    }
