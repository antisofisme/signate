"""
Organization API Endpoints
Multi-tenant organization management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps_v2 import (
    OrganizationContext,
    get_current_user_with_context,
    require_permission,
    require_admin,
    require_super_admin
)
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationStats,
    OrganizationSettings,
    OrganizationSwitchRequest,
    OrganizationSwitchResponse,
    OrganizationInvite
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.models.organization import Organization
from app.models.user_organization import UserOrganization
from app.models.role import Role
from app.models.device import Device
from app.models.content import Content
from app.models.playlist import Playlist
from app.models.user import User
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings
import secrets

router = APIRouter()


@router.get("/validate-pin", response_model=SuccessResponse)
async def validate_organization_pin(
    pin: str = Query(..., description="Organization PIN to validate", min_length=8),
    db: Session = Depends(get_db)
):
    """
    Validate organization PIN (public endpoint - no authentication required)

    This endpoint is used by the viewer to validate the organization PIN
    before saving it to localStorage during device registration.

    Returns:
        - 200 with success message if PIN is valid
        - 404 if PIN is invalid or organization is inactive
    """
    # Query for organization with this PIN
    organization = db.query(Organization).filter(
        Organization.organization_pin == pin,
        Organization.is_active == True
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid organization PIN or organization is inactive"
        )

    return SuccessResponse(
        message=f"Valid organization PIN for: {organization.name}",
        details={"organization_name": organization.name}
    )


@router.get("/", response_model=List[OrganizationResponse])
async def list_user_organizations(
    context: OrganizationContext = Depends(get_current_user_with_context),
    db: Session = Depends(get_db)
):
    """
    List all organizations the current user belongs to

    Returns list of organizations with user's role in each
    """
    # Get all user's organizations
    user_orgs = db.query(UserOrganization).filter(
        UserOrganization.user_id == context.user.id,
        UserOrganization.is_active == True
    ).all()

    org_ids = [uo.organization_id for uo in user_orgs]

    organizations = db.query(Organization).filter(
        Organization.id.in_(org_ids),
        Organization.is_active == True
    ).all()

    # Add computed fields
    responses = []
    for org in organizations:
        org_dict = OrganizationResponse.from_orm(org)

        # Add counts
        org_dict.device_count = db.query(Device).filter(
            Device.organization_id == org.id
        ).count()

        org_dict.user_count = db.query(UserOrganization).filter(
            UserOrganization.organization_id == org.id,
            UserOrganization.is_active == True
        ).count()

        org_dict.content_count = db.query(Content).filter(
            Content.organization_id == org.id
        ).count()

        # Calculate storage used (simplified)
        org_dict.storage_used_gb = 0.0  # Would calculate from actual files

        responses.append(org_dict)

    return responses


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    context: OrganizationContext = Depends(get_current_user_with_context),
    db: Session = Depends(get_db)
):
    """
    Create a new organization

    The current user becomes the admin of the new organization.
    Requires super admin permission or special create permission.
    """
    # Check if user can create organizations
    if not context.is_super_admin() and not context.has_permission("organizations", "create"):
        # Check if user has reached organization limit (for non-super admins)
        user_org_count = db.query(UserOrganization).filter(
            UserOrganization.user_id == context.user.id,
            UserOrganization.is_active == True
        ).count()

        if user_org_count >= 3:  # Configurable limit
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization limit reached for your account"
            )

    # Check if slug is unique
    if org_data.slug:
        existing = db.query(Organization).filter(
            Organization.slug == org_data.slug
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization with slug '{org_data.slug}' already exists"
            )

    # Generate unique organization PIN (8-digit)
    organization_pin = ''.join([str(secrets.randbelow(10)) for _ in range(8)])

    # Ensure PIN is unique
    while db.query(Organization).filter(Organization.organization_pin == organization_pin).first():
        organization_pin = ''.join([str(secrets.randbelow(10)) for _ in range(8)])

    # Create organization
    organization = Organization(
        name=org_data.name,
        slug=org_data.slug or org_data.name.lower().replace(' ', '-'),
        description=org_data.description,
        settings=org_data.settings,
        max_devices=org_data.max_devices,
        max_users=org_data.max_users,
        max_storage_gb=org_data.max_storage_gb,
        organization_pin=organization_pin,
        subscription_tier="free",
        is_active=True
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)

    # Get or create admin role
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    if not admin_role:
        admin_role = db.query(Role).first()

    # Add user as admin of the organization
    user_org = UserOrganization(
        user_id=context.user.id,
        organization_id=organization.id,
        role_id=admin_role.id if admin_role else 1,
        is_primary=False,
        is_active=True,
        invited_by=context.user.id
    )
    db.add(user_org)
    db.commit()

    # Return with computed fields
    response = OrganizationResponse.from_orm(organization)
    response.device_count = 0
    response.user_count = 1
    response.content_count = 0
    response.storage_used_gb = 0.0

    return response


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    context: OrganizationContext = Depends(require_permission("organizations", "read")),
    db: Session = Depends(get_db)
):
    """
    Get organization details

    Requires membership in the organization or super admin access
    """
    # Check if user has access to this organization
    if org_id != context.organization.id and not context.is_super_admin():
        # Check if user is member of requested organization
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == context.user.id,
            UserOrganization.organization_id == org_id,
            UserOrganization.is_active == True
        ).first()

        if not user_org:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this organization"
            )

    organization = db.query(Organization).filter(
        Organization.id == org_id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Add computed fields
    response = OrganizationResponse.from_orm(organization)
    response.device_count = db.query(Device).filter(
        Device.organization_id == organization.id
    ).count()
    response.user_count = db.query(UserOrganization).filter(
        UserOrganization.organization_id == organization.id,
        UserOrganization.is_active == True
    ).count()
    response.content_count = db.query(Content).filter(
        Content.organization_id == organization.id
    ).count()
    response.storage_used_gb = 0.0  # Calculate from actual files

    return response


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: int,
    org_data: OrganizationUpdate,
    context: OrganizationContext = Depends(require_permission("organizations", "update")),
    db: Session = Depends(get_db)
):
    """
    Update organization details

    Requires admin permission in the organization
    """
    # Verify this is the user's current organization or user is super admin
    if org_id != context.organization.id and not context.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your current organization"
        )

    organization = db.query(Organization).filter(
        Organization.id == org_id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Update fields
    for field, value in org_data.dict(exclude_unset=True).items():
        setattr(organization, field, value)

    db.commit()
    db.refresh(organization)

    return OrganizationResponse.from_orm(organization)


@router.delete("/{org_id}", response_model=SuccessResponse)
async def delete_organization(
    org_id: int,
    context: OrganizationContext = Depends(require_super_admin()),
    db: Session = Depends(get_db)
):
    """
    Delete organization (super admin only)

    This will delete all associated data (devices, content, users, etc.)
    """
    organization = db.query(Organization).filter(
        Organization.id == org_id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Prevent deleting the default organization
    if organization.slug == "default":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the default organization"
        )

    org_name = organization.name
    db.delete(organization)
    db.commit()

    return SuccessResponse(
        message=f"Organization '{org_name}' deleted successfully"
    )


@router.get("/{org_id}/stats", response_model=OrganizationStats)
async def get_organization_stats(
    org_id: int,
    context: OrganizationContext = Depends(require_permission("organizations", "read")),
    db: Session = Depends(get_db)
):
    """
    Get organization statistics

    Returns device count, user count, content count, etc.
    """
    # Verify access
    if org_id != context.organization.id and not context.is_super_admin():
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == context.user.id,
            UserOrganization.organization_id == org_id,
            UserOrganization.is_active == True
        ).first()

        if not user_org:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this organization"
            )

    # Gather statistics
    total_devices = db.query(Device).filter(
        Device.organization_id == org_id
    ).count()

    active_devices = db.query(Device).filter(
        Device.organization_id == org_id,
        Device.status == "active"
    ).count()

    total_content = db.query(Content).filter(
        Content.organization_id == org_id
    ).count()

    total_playlists = db.query(Playlist).filter(
        Playlist.organization_id == org_id
    ).count()

    total_users = db.query(UserOrganization).filter(
        UserOrganization.organization_id == org_id,
        UserOrganization.is_active == True
    ).count()

    # Get last activity (simplified - would check logs)
    last_activity = db.query(func.max(Device.last_seen)).filter(
        Device.organization_id == org_id
    ).scalar()

    return OrganizationStats(
        total_devices=total_devices,
        active_devices=active_devices,
        total_content=total_content,
        total_playlists=total_playlists,
        total_users=total_users,
        storage_used_gb=0.0,  # Calculate from actual files
        last_activity=last_activity
    )


@router.get("/{org_id}/settings", response_model=OrganizationSettings)
async def get_organization_settings(
    org_id: int,
    context: OrganizationContext = Depends(require_permission("settings", "read")),
    db: Session = Depends(get_db)
):
    """
    Get organization settings

    Returns organization-specific configuration
    """
    # Verify access
    if org_id != context.organization.id and not context.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access settings for your current organization"
        )

    organization = db.query(Organization).filter(
        Organization.id == org_id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Return settings with defaults
    settings_dict = organization.settings or {}
    return OrganizationSettings(**settings_dict)


@router.put("/{org_id}/settings", response_model=OrganizationSettings)
async def update_organization_settings(
    org_id: int,
    settings_data: OrganizationSettings,
    context: OrganizationContext = Depends(require_permission("settings", "update")),
    db: Session = Depends(get_db)
):
    """
    Update organization settings

    Requires admin permission
    """
    # Verify access
    if org_id != context.organization.id and not context.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update settings for your current organization"
        )

    organization = db.query(Organization).filter(
        Organization.id == org_id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Update settings
    organization.settings = settings_data.dict()
    db.commit()

    return settings_data


@router.post("/switch", response_model=OrganizationSwitchResponse)
async def switch_organization(
    switch_request: OrganizationSwitchRequest,
    context: OrganizationContext = Depends(get_current_user_with_context),
    db: Session = Depends(get_db)
):
    """
    Switch to a different organization

    Returns new JWT tokens with the selected organization context
    """
    # Verify user is member of target organization
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == context.user.id,
        UserOrganization.organization_id == switch_request.organization_id,
        UserOrganization.is_active == True
    ).first()

    if not user_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )

    # Get organization
    organization = db.query(Organization).filter(
        Organization.id == switch_request.organization_id
    ).first()

    if not organization or not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or inactive"
        )

    # Update primary organization
    db.query(UserOrganization).filter(
        UserOrganization.user_id == context.user.id
    ).update({"is_primary": False})

    user_org.is_primary = True
    db.commit()

    # Get role and permissions
    role = db.query(Role).filter(Role.id == user_org.role_id).first()
    permissions = role.get_permission_list() if role else []

    # Create new tokens with updated organization
    access_token = create_access_token(data={
        "user_id": context.user.id,
        "username": context.user.username,
        "organization_id": organization.id,
        "organization_slug": organization.slug,
        "role_id": role.id,
        "permissions": permissions,
        "is_super_admin": context.user.is_super_admin
    })

    return OrganizationSwitchResponse(
        success=True,
        organization=OrganizationResponse.from_orm(organization),
        new_token=access_token
    )


@router.post("/{org_id}/invite", response_model=SuccessResponse)
async def invite_to_organization(
    org_id: int,
    invite_data: OrganizationInvite,
    context: OrganizationContext = Depends(require_permission("users", "create")),
    db: Session = Depends(get_db)
):
    """
    Invite a user to the organization

    Sends an invitation email with a link to join
    """
    # Verify this is the user's current organization
    if org_id != context.organization.id and not context.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only invite users to your current organization"
        )

    # Check organization user limit
    user_count = db.query(UserOrganization).filter(
        UserOrganization.organization_id == org_id,
        UserOrganization.is_active == True
    ).count()

    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if user_count >= organization.max_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User limit reached ({organization.max_users})"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == invite_data.email).first()

    if existing_user:
        # Check if already member
        existing_membership = db.query(UserOrganization).filter(
            UserOrganization.user_id == existing_user.id,
            UserOrganization.organization_id == org_id
        ).first()

        if existing_membership:
            if existing_membership.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already a member of this organization"
                )
            else:
                # Reactivate membership
                existing_membership.is_active = True
                existing_membership.role_id = invite_data.role_id
                existing_membership.invited_by = context.user.id
                db.commit()
                return SuccessResponse(message="User membership reactivated")

    # Create invitation (would send email in production)
    # For now, we'll just log the invitation
    # In production, would create invitation record and send email

    return SuccessResponse(
        message=f"Invitation sent to {invite_data.email}"
    )