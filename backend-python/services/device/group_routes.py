"""
Device Group Routes
FastAPI endpoints for device group management
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.auth import get_current_user, CurrentUser

from services.device.dtos import (
    CreateDeviceGroupRequest,
    UpdateDeviceGroupRequest,
    AddDeviceToGroupRequest,
    RemoveDeviceFromGroupRequest,
    DeviceGroupResponse,
    DeviceGroupListResponse,
    DeviceGroupStatsResponse,
    GroupDevicesResponse,
)

from services.device.use_cases.create_device_group import CreateDeviceGroupUseCase
from services.device.use_cases.update_device_group import UpdateDeviceGroupUseCase
from services.device.use_cases.delete_device_group import DeleteDeviceGroupUseCase
from services.device.use_cases.get_device_groups import GetDeviceGroupsUseCase
from services.device.use_cases.add_device_to_group import AddDeviceToGroupUseCase
from services.device.use_cases.remove_device_from_group import RemoveDeviceFromGroupUseCase

router = APIRouter(prefix="/groups", tags=["Device Groups"])


# =============================================================================
# CREATE
# =============================================================================


@router.post("", response_model=DeviceGroupResponse, status_code=status.HTTP_201_CREATED)
def create_device_group(
    request: CreateDeviceGroupRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create a new device group

    - **name**: Group name (required)
    - **description**: Optional description
    - **parent_group_id**: Optional parent group for hierarchy
    - **group_type**: Type (chain, hotel, floor, location, custom)
    - **sort_order**: Display order
    - **default_playlist_id**: Default playlist for devices in this group
    """
    try:
        use_case = CreateDeviceGroupUseCase(db)
        group = use_case.execute(
            name=request.name,
            organization_id=current_user.organization_id,
            description=request.description,
            parent_group_id=request.parent_group_id,
            group_type=request.group_type,
            sort_order=request.sort_order,
            default_playlist_id=request.default_playlist_id,
            created_by=current_user.id,
        )

        return DeviceGroupResponse(**group.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create group: {str(e)}",
        )


# =============================================================================
# READ
# =============================================================================


@router.get("", response_model=DeviceGroupListResponse)
def get_device_groups(
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get all device groups for the organization

    - **include_deleted**: Include soft-deleted groups (default: false)
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        groups = use_case.get_all_by_organization(current_user.organization_id, include_deleted)

        group_responses = [DeviceGroupResponse(**g.to_dict()) for g in groups]

        return DeviceGroupListResponse(items=group_responses, total=len(group_responses))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get groups: {str(e)}",
        )


@router.get("/roots", response_model=DeviceGroupListResponse)
def get_root_groups(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get root device groups (no parent) for the organization
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        groups = use_case.get_root_groups(current_user.organization_id)

        group_responses = [DeviceGroupResponse(**g.to_dict()) for g in groups]

        return DeviceGroupListResponse(items=group_responses, total=len(group_responses))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get root groups: {str(e)}",
        )


@router.get("/{group_id}", response_model=DeviceGroupResponse)
def get_device_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get a single device group by ID
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        group = use_case.get_by_id(group_id, current_user.organization_id)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found",
            )

        return DeviceGroupResponse(**group.to_dict())
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get group: {str(e)}",
        )


@router.get("/{group_id}/children", response_model=DeviceGroupListResponse)
def get_group_children(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get child groups of a parent group
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        children = use_case.get_children(group_id, current_user.organization_id)

        group_responses = [DeviceGroupResponse(**g.to_dict()) for g in children]

        return DeviceGroupListResponse(items=group_responses, total=len(group_responses))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get children: {str(e)}",
        )


@router.get("/{group_id}/devices", response_model=GroupDevicesResponse)
def get_group_devices(
    group_id: int,
    recursive: bool = False,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get device IDs in a group

    - **recursive**: Include devices in child groups (default: false)
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        device_ids = use_case.get_devices_in_group(group_id, current_user.organization_id, recursive)

        return GroupDevicesResponse(
            group_id=group_id,
            devices=device_ids,
            count=len(device_ids),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get devices: {str(e)}",
        )


@router.get("/{group_id}/stats", response_model=DeviceGroupStatsResponse)
def get_group_stats(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get group statistics (device count, online/offline)
    """
    try:
        use_case = GetDeviceGroupsUseCase(db)
        stats = use_case.get_group_stats(group_id, current_user.organization_id)

        return DeviceGroupStatsResponse(
            group_id=group_id,
            total_devices=stats["total_devices"],
            online_devices=stats["online_devices"],
            offline_devices=stats["offline_devices"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )


# =============================================================================
# UPDATE
# =============================================================================


@router.put("/{group_id}", response_model=DeviceGroupResponse)
def update_device_group(
    group_id: int,
    request: UpdateDeviceGroupRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update a device group
    """
    try:
        use_case = UpdateDeviceGroupUseCase(db)
        group = use_case.execute(
            group_id=group_id,
            organization_id=current_user.organization_id,
            name=request.name,
            description=request.description,
            parent_group_id=request.parent_group_id,
            group_type=request.group_type,
            sort_order=request.sort_order,
            default_playlist_id=request.default_playlist_id,
        )

        return DeviceGroupResponse(**group.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update group: {str(e)}",
        )


@router.post("/{group_id}/devices", status_code=status.HTTP_204_NO_CONTENT)
def add_device_to_group(
    group_id: int,
    request: AddDeviceToGroupRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Add a device to a group
    """
    try:
        use_case = AddDeviceToGroupUseCase(db)
        use_case.execute(
            device_id=request.device_id,
            group_id=group_id,
            organization_id=current_user.organization_id,
            added_by=current_user.id,
        )

        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add device to group: {str(e)}",
        )


@router.delete("/{group_id}/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_device_from_group(
    group_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Remove a device from a group
    """
    try:
        use_case = RemoveDeviceFromGroupUseCase(db)
        use_case.execute(
            device_id=device_id,
            group_id=group_id,
            organization_id=current_user.organization_id,
        )

        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove device from group: {str(e)}",
        )


# =============================================================================
# DELETE
# =============================================================================


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Soft delete a device group

    Note: Cannot delete groups with child groups. Delete or reassign children first.
    """
    try:
        use_case = DeleteDeviceGroupUseCase(db)
        use_case.execute(group_id=group_id, organization_id=current_user.organization_id)

        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete group: {str(e)}",
        )
