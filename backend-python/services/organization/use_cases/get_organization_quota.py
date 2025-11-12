"""
Get Organization Quota Use Case
"""

from sqlalchemy.orm import Session
from services.organization.domain.quota_service import OrganizationQuotaService
from services.organization.dtos import (
    OrganizationQuotaResponse,
    QuotaInfo,
    StorageQuotaInfo
)


def get_organization_quota_use_case(
    organization_id: int,
    db: Session
) -> OrganizationQuotaResponse:
    """
    Get organization quota status
    
    Args:
        organization_id: Organization ID
        db: Database session
        
    Returns:
        OrganizationQuotaResponse with current quota status
    """
    # Get quota service
    quota_service = OrganizationQuotaService(db)
    
    # Get quota data
    quota = quota_service.get_organization_quota(organization_id)
    
    # Build response
    response = OrganizationQuotaResponse(
        devices=QuotaInfo(
            max=quota.max_devices,
            current=quota.current_devices,
            available=quota.devices_available
        ),
        users=QuotaInfo(
            max=quota.max_users,
            current=quota.current_users,
            available=quota.users_available
        ),
        content=StorageQuotaInfo(
            max_items=quota.max_content_items,
            current_items=quota.current_content_items,
            available_items=quota.content_items_available,
            max_size_gb=quota.max_content_size_gb,
            current_size_gb=round(quota.current_content_size_gb, 2),
            available_size_gb=round(quota.content_size_available_gb, 2)
        ),
        playlists=QuotaInfo(
            max=quota.max_playlists,
            current=quota.current_playlists,
            available=quota.playlists_available
        )
    )
    
    # Calculate summary
    response.calculate_summary()
    
    return response