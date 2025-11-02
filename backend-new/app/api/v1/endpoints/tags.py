"""
Tags API Endpoints
==================

Tag management dan device-tag assignment untuk organization.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.repositories import TagRepository, DeviceRepository, OrganizationRepository
from app.schemas.tag import (
    TagCreate,
    TagUpdate,
    DeviceTagAssign,
    DeviceTagBulkAssign,
    TagResponse,
    TagDetailResponse,
    TagListResponse,
    TagAssignmentResponse,
    TagStatsResponse
)

router = APIRouter()


@router.post(
    "/",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Tag",
    description="Create new tag for device categorization"
)
async def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create new tag.

    **Flow**:
    1. Validate organization exists and active
    2. Check tag name uniqueness (per organization)
    3. Create tag
    4. Return tag with device_count=0

    **Tag Naming**:
    - Automatically lowercased
    - Only alphanumeric, dash, underscore, spaces allowed
    - Must be unique per organization
    """
    # Validate organization
    org_repo = OrganizationRepository(db)
    org = org_repo.get(tag_data.organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {tag_data.organization_id} not found"
        )

    if not org.is_active:
        raise ForbiddenException(
            message="Organization is not active"
        )

    tag_repo = TagRepository(db)

    # Check uniqueness
    existing = tag_repo.get_by_name(tag_data.tag_name, tag_data.organization_id)
    if existing:
        raise BadRequestException(
            message=f"Tag '{tag_data.tag_name}' already exists in this organization"
        )

    # Create tag
    tag = tag_repo.create_tag(
        tag_name=tag_data.tag_name,
        organization_id=tag_data.organization_id,
        description=tag_data.description,
        color=tag_data.color,
        tag_priority=tag_data.tag_priority
    )

    tag_dict = tag.to_dict()
    tag_dict["device_count"] = 0
    return tag_dict


@router.get(
    "/{tag_id}",
    response_model=TagDetailResponse,
    summary="Get Tag Details",
    description="Get tag with devices list"
)
async def get_tag(
    tag_id: int,
    include_devices: bool = Query(False, description="Include devices list"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get tag details.

    **Options**:
    - include_devices=false: Just tag info + device_count
    - include_devices=true: Tag + full devices list
    """
    tag_repo = TagRepository(db)
    tag = tag_repo.get(tag_id)

    if not tag:
        raise NotFoundException(
            message=f"Tag {tag_id} not found"
        )

    tag_dict = tag_repo.get_tag_with_device_count(tag_id)

    if include_devices:
        devices = tag_repo.get_tag_devices(tag_id)
        tag_dict["devices"] = [
            {
                "id": d.id,
                "device_name": d.device_name,
                "location": d.location,
                "status": d.status
            }
            for d in devices
        ]
    else:
        tag_dict["devices"] = []

    return tag_dict


@router.put(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Update Tag",
    description="Update tag metadata"
)
async def update_tag(
    tag_id: int,
    tag_update: TagUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update tag metadata.

    **Updatable Fields**:
    - tag_name (must remain unique)
    - description
    - color
    - tag_priority
    """
    tag_repo = TagRepository(db)
    tag = tag_repo.get(tag_id)

    if not tag:
        raise NotFoundException(
            message=f"Tag {tag_id} not found"
        )

    # Build update dict
    update_data = tag_update.model_dump(exclude_none=True)

    # Check name uniqueness if changing name
    if "tag_name" in update_data:
        existing = tag_repo.get_by_name(update_data["tag_name"], tag.organization_id)
        if existing and existing.id != tag_id:
            raise BadRequestException(
                message=f"Tag '{update_data['tag_name']}' already exists"
            )

    # Update tag
    updated_tag = tag_repo.update(tag_id, update_data)

    return tag_repo.get_tag_with_device_count(updated_tag.id)


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Tag",
    description="Delete tag (also removes from all devices)"
)
async def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete tag.

    **Cascade**:
    - Removes tag from all devices (device_tags deleted)
    - Does NOT delete devices themselves
    """
    tag_repo = TagRepository(db)
    tag = tag_repo.get(tag_id)

    if not tag:
        raise NotFoundException(
            message=f"Tag {tag_id} not found"
        )

    # Delete tag (cascade deletes device_tags)
    tag_repo.delete(tag_id)
    return None


@router.get(
    "/",
    response_model=TagListResponse,
    summary="List Tags",
    description="List organization tags with pagination"
)
async def list_tags(
    organization_id: int = Query(..., description="Organization ID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    search: Optional[str] = Query(None, min_length=2, description="Search in name/description"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List organization tags.

    **Features**:
    - Pagination (skip/limit)
    - Search by name or description
    - Sorted by priority (desc), then name (asc)
    - Includes device_count for each tag
    """
    # Validate organization
    org_repo = OrganizationRepository(db)
    org = org_repo.get(organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {organization_id} not found"
        )

    tag_repo = TagRepository(db)

    if search:
        tags = tag_repo.search_tags(organization_id, search, skip, limit)
        total = len(tags)  # Approximation for search
    else:
        tags = tag_repo.get_organization_tags_with_counts(organization_id)
        total = len(tags)
        tags = tags[skip:skip+limit]  # Manual pagination for pre-counted query

    return {
        "tags": tags,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ============================================================================
# DEVICE-TAG ASSIGNMENT ENDPOINTS
# ============================================================================

@router.post(
    "/{tag_id}/assign",
    response_model=TagAssignmentResponse,
    summary="Assign Tag to Device(s)",
    description="Assign tag to one or more devices"
)
async def assign_tag_to_devices(
    tag_id: int,
    assignment: DeviceTagBulkAssign,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Assign tag to devices.

    **Features**:
    - Bulk assignment (multiple devices at once)
    - Idempotent (safe to call multiple times)
    - Validates all devices exist

    **Example**:
    ```bash
    curl -X POST /api/v1/tags/1/assign \
      -d '{"device_ids": [5, 8, 12]}'
    ```
    """
    tag_repo = TagRepository(db)
    tag = tag_repo.get(tag_id)

    if not tag:
        raise NotFoundException(
            message=f"Tag {tag_id} not found"
        )

    # Validate all devices exist
    device_repo = DeviceRepository(db)
    for device_id in assignment.device_ids:
        device = device_repo.get(device_id)
        if not device:
            raise NotFoundException(
                message=f"Device {device_id} not found"
            )

        # Check device belongs to same organization as tag
        if device.organization_id != tag.organization_id:
            raise ForbiddenException(
                message=f"Device {device_id} belongs to different organization"
            )

    # Assign tag to devices
    assigned_count = tag_repo.bulk_assign_tag(tag_id, assignment.device_ids)

    return {
        "tag_id": tag_id,
        "tag_name": tag.tag_name,
        "devices_assigned": assigned_count,
        "device_ids": assignment.device_ids
    }


@router.delete(
    "/{tag_id}/assign/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Tag from Device",
    description="Remove tag assignment from device"
)
async def remove_tag_from_device(
    tag_id: int,
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove tag from device.

    **Idempotent**: Safe to call even if tag not assigned
    """
    tag_repo = TagRepository(db)

    # Verify tag exists
    tag = tag_repo.get(tag_id)
    if not tag:
        raise NotFoundException(
            message=f"Tag {tag_id} not found"
        )

    # Remove assignment
    removed = tag_repo.remove_tag_from_device(tag_id, device_id)

    if not removed:
        # Not an error, just wasn't assigned
        pass

    return None


@router.get(
    "/stats/{organization_id}",
    response_model=TagStatsResponse,
    summary="Get Tag Statistics",
    description="Get tag usage statistics for organization"
)
async def get_tag_stats(
    organization_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get tag statistics.

    **Includes**:
    - Total tags
    - Total device-tag assignments
    - Most used tags (top 5)
    - Devices without any tags
    """
    # Validate organization
    org_repo = OrganizationRepository(db)
    org = org_repo.get(organization_id)
    if not org:
        raise NotFoundException(
            message=f"Organization {organization_id} not found"
        )

    tag_repo = TagRepository(db)
    stats = tag_repo.get_tag_statistics(organization_id)
    stats["organization_id"] = organization_id

    return stats
