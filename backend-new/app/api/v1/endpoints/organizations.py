"""
Organizations API Endpoints
===========================

Multi-tenant organization management with PIN authentication.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.services import OrganizationService
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationStatsResponse,
    OrganizationPinVerify,
    OrganizationQuotaResponse
)

router = APIRouter()


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
    description="Create new organization with unique 8-digit PIN and quota limits"
)
async def create_organization(
    organization: OrganizationCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new organization.

    **Returns PIN only once on creation!**

    Args:
        organization: Organization creation data

    Returns:
        Organization data with generated PIN

    Raises:
        BadRequestException: Invalid data or duplicate slug
    """
    service = OrganizationService(db)
    return service.create_organization(
        name=organization.name,
        slug=organization.slug,
        description=organization.description,
        max_devices=organization.max_devices,
        max_users=organization.max_users,
        max_storage_gb=organization.max_storage_gb
    )


@router.post(
    "/verify-pin",
    response_model=OrganizationResponse,
    summary="Verify Organization PIN",
    description="Verify 8-digit organization PIN (used for device registration)"
)
async def verify_organization_pin(
    pin_data: OrganizationPinVerify,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify organization PIN.

    **CRITICAL**: Used by devices during registration process.

    Args:
        pin_data: PIN verification request

    Returns:
        Organization data if PIN valid

    Raises:
        NotFoundException: Invalid or inactive PIN
    """
    service = OrganizationService(db)
    result = service.verify_pin(pin_data.pin)

    if not result:
        raise NotFoundException(
            message="Invalid organization PIN",
            details={"pin": "PIN not found or organization inactive"}
        )

    return result


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get Organization",
    description="Get organization details by ID"
)
async def get_organization(
    organization_id: int,
    include_stats: bool = Query(False, description="Include usage statistics"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get organization details.

    Args:
        organization_id: Organization ID
        include_stats: Include device/user/storage stats

    Returns:
        Organization data

    Raises:
        NotFoundException: Organization not found
    """
    service = OrganizationService(db)

    if include_stats:
        return service.get_organization_with_stats(organization_id)
    else:
        org = service.get_organization(organization_id)
        return org


@router.get(
    "/{organization_id}/stats",
    response_model=OrganizationStatsResponse,
    summary="Get Organization Statistics",
    description="Get comprehensive organization statistics (devices, users, storage, content)"
)
async def get_organization_stats(
    organization_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get organization statistics.

    Returns:
        - Device count & quota
        - User count & quota
        - Storage usage & quota
        - Content count by type
        - Playlist count
    """
    service = OrganizationService(db)
    return service.get_organization_stats(organization_id)


@router.get(
    "/{organization_id}/quota/{quota_type}",
    response_model=OrganizationQuotaResponse,
    summary="Check Organization Quota",
    description="Check specific quota type (devices, users, or storage)"
)
async def check_organization_quota(
    organization_id: int,
    quota_type: str = Query(..., regex="^(devices|users|storage)$"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check organization quota.

    Args:
        organization_id: Organization ID
        quota_type: Quota type (devices, users, or storage)

    Returns:
        Quota information with current usage

    Raises:
        NotFoundException: Organization not found
        BadRequestException: Invalid quota type
    """
    service = OrganizationService(db)

    if quota_type == "devices":
        return service.check_device_quota(organization_id)
    elif quota_type == "users":
        return service.check_user_quota(organization_id)
    elif quota_type == "storage":
        return service.check_storage_quota(organization_id)
    else:
        raise BadRequestException(
            message="Invalid quota type",
            details={"quota_type": "Must be 'devices', 'users', or 'storage'"}
        )


@router.put(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update Organization",
    description="Update organization details and quota limits"
)
async def update_organization(
    organization_id: int,
    organization: OrganizationUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update organization.

    Args:
        organization_id: Organization ID
        organization: Update data

    Returns:
        Updated organization data

    Raises:
        NotFoundException: Organization not found
        BadRequestException: Invalid data or duplicate slug
    """
    service = OrganizationService(db)

    # Build update dict (exclude None values)
    update_data = organization.model_dump(exclude_none=True)

    return service.update_organization(organization_id, update_data)


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Organization",
    description="Soft delete organization (sets is_active=False)"
)
async def delete_organization(
    organization_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete organization.

    **WARNING**: This deactivates the organization and all associated:
    - Devices
    - Users
    - Content
    - Playlists

    Args:
        organization_id: Organization ID

    Raises:
        NotFoundException: Organization not found
    """
    service = OrganizationService(db)
    service.delete_organization(organization_id)
    return None


@router.post(
    "/{organization_id}/reactivate",
    response_model=OrganizationResponse,
    summary="Reactivate Organization",
    description="Reactivate a soft-deleted organization"
)
async def reactivate_organization(
    organization_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reactivate a deleted organization.

    Args:
        organization_id: Organization ID

    Returns:
        Reactivated organization data

    Raises:
        NotFoundException: Organization not found
    """
    service = OrganizationService(db)
    return service.update_organization(organization_id, {"is_active": True})


@router.get(
    "/",
    response_model=OrganizationListResponse,
    summary="List Organizations",
    description="List all organizations with pagination and filtering"
)
async def list_organizations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or slug"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List organizations with pagination.

    Args:
        skip: Pagination offset
        limit: Maximum results
        is_active: Filter by active status
        search: Search term for name/slug

    Returns:
        List of organizations with pagination metadata
    """
    service = OrganizationService(db)

    # Build filter dict
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active

    # Get organizations
    organizations = service.list_organizations(
        skip=skip,
        limit=limit,
        filters=filters,
        search=search
    )

    # Get total count for pagination
    total = service.count_organizations(filters=filters, search=search)

    return {
        "organizations": organizations,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get(
    "/search",
    response_model=OrganizationListResponse,
    summary="Search Organizations",
    description="Search organizations by name, slug, or PIN"
)
async def search_organizations(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search organizations.

    Searches across:
    - Organization name
    - Organization slug
    - Organization PIN (exact match only)

    Args:
        q: Search query (min 2 characters)
        limit: Maximum results

    Returns:
        Matching organizations
    """
    service = OrganizationService(db)

    # Check if query is 8-digit PIN
    if len(q) == 8 and q.isdigit():
        # PIN search (exact match)
        result = service.verify_pin(q)
        organizations = [result] if result else []
        total = len(organizations)
    else:
        # Text search
        organizations = service.list_organizations(
            skip=0,
            limit=limit,
            search=q
        )
        total = len(organizations)

    return {
        "organizations": organizations,
        "total": total,
        "skip": 0,
        "limit": limit
    }
