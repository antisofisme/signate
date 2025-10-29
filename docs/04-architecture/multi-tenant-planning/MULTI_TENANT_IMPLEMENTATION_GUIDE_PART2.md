# Multi-Tenant Implementation Guide - Part 2

## Organization Management API

### File: `/mnt/g/khoirul/signate/backend/app/api/organizations.py`

```python
"""
Organization Management API
Endpoints for managing organizations in multi-tenant system
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.deps import (
    get_current_user, get_current_organization,
    require_permission, get_current_superuser
)
from app.core.security.jwt import create_invitation_token
from app.models.user import User
from app.models.organization import Organization
from app.models.user_organization import UserOrganization
from app.models.role import Role
from app.models.device import Device
from app.models.content import Content
from app.models.playlist import Playlist
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationWithStats, OrganizationInviteRequest
)
from app.schemas.user import UserInviteResponse

router = APIRouter()


@router.get("/", response_model=List[OrganizationResponse])
def list_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    List all organizations the current user has access to
    """
    if current_user.is_super_admin:
        # Super admins see all organizations
        organizations = db.query(Organization).offset(skip).limit(limit).all()
    else:
        # Regular users see only their organizations
        user_orgs = db.query(Organization).join(
            UserOrganization, Organization.id == UserOrganization.organization_id
        ).filter(
            UserOrganization.user_id == current_user.id,
            UserOrganization.is_active == True
        ).offset(skip).limit(limit).all()
        organizations = user_orgs

    return [OrganizationResponse.model_validate(org) for org in organizations]


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new organization

    Creates organization and makes current user an admin
    """
    # Check if slug already exists
    existing = db.query(Organization).filter(Organization.slug == org_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already exists"
        )

    # Create organization
    organization = Organization(
        name=org_data.name,
        slug=org_data.slug,
        description=org_data.description,
        settings=org_data.settings,
        max_devices=org_data.max_devices,
        max_users=org_data.max_users,
        max_storage_gb=org_data.max_storage_gb,
        subscription_tier=org_data.subscription_tier,
        is_active=True
    )
    db.add(organization)
    db.flush()  # Get organization.id

    # Get admin role
    admin_role = db.query(Role).filter(
        Role.name == 'admin',
        Role.is_system_role == True
    ).first()

    if not admin_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin role not found in system"
        )

    # Make creator an admin of this organization
    user_org = UserOrganization(
        user_id=current_user.id,
        organization_id=organization.id,
        role_id=admin_role.id,
        is_primary=False,  # Don't change primary org
        is_active=True,
        joined_at=datetime.utcnow()
    )
    db.add(user_org)
    db.commit()
    db.refresh(organization)

    return OrganizationResponse.model_validate(organization)


@router.get("/{org_id}", response_model=OrganizationWithStats)
def get_organization(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get organization details with statistics
    """
    # Get organization
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Verify access (member or super admin)
    if not current_user.is_super_admin:
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == current_user.id,
            UserOrganization.organization_id == org_id,
            UserOrganization.is_active == True
        ).first()

        if not user_org:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this organization"
            )

    # Get statistics
    device_count = db.query(func.count(Device.id)).filter(
        Device.organization_id == org_id
    ).scalar() or 0

    content_count = db.query(func.count(Content.id)).filter(
        Content.organization_id == org_id
    ).scalar() or 0

    playlist_count = db.query(func.count(Playlist.id)).filter(
        Playlist.organization_id == org_id
    ).scalar() or 0

    user_count = db.query(func.count(UserOrganization.id)).filter(
        UserOrganization.organization_id == org_id,
        UserOrganization.is_active == True
    ).scalar() or 0

    org_dict = OrganizationResponse.model_validate(organization).model_dump()
    org_dict.update({
        'device_count': device_count,
        'content_count': content_count,
        'playlist_count': playlist_count,
        'user_count': user_count
    })

    return OrganizationWithStats(**org_dict)


@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: int,
    org_data: OrganizationUpdate,
    current_user: User = Depends(require_permission("organizations", "update")),
    db: Session = Depends(get_db)
):
    """
    Update organization settings

    Requires: organizations.update permission
    """
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Update fields
    update_data = org_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)

    db.commit()
    db.refresh(organization)

    return OrganizationResponse.model_validate(organization)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    org_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Delete organization

    Requires: Super admin only
    WARNING: This will cascade delete all related data
    """
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    db.delete(organization)
    db.commit()

    return None


@router.get("/{org_id}/users", response_model=List[dict])
def list_organization_users(
    org_id: int,
    current_user: User = Depends(require_permission("users", "read")),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    List all users in organization

    Requires: users.read permission
    """
    # Get all user-organization relationships
    user_orgs = db.query(
        User, UserOrganization, Role
    ).join(
        UserOrganization, User.id == UserOrganization.user_id
    ).join(
        Role, UserOrganization.role_id == Role.id
    ).filter(
        UserOrganization.organization_id == org_id,
        UserOrganization.is_active == True
    ).offset(skip).limit(limit).all()

    results = []
    for user, user_org, role in user_orgs:
        results.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role_name": role.name,
            "role_display_name": role.display_name or role.name,
            "is_primary": user_org.is_primary,
            "joined_at": user_org.joined_at.isoformat() if user_org.joined_at else None,
            "is_active": user.is_active
        })

    return results


@router.post("/{org_id}/invite", response_model=UserInviteResponse)
def invite_user_to_organization(
    org_id: int,
    invite_data: OrganizationInviteRequest,
    current_user: User = Depends(require_permission("users", "create")),
    db: Session = Depends(get_db)
):
    """
    Invite a user to organization

    Requires: users.create permission

    Creates an invitation that can be used during registration
    """
    # Get organization
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    if existing_user:
        # Check if already a member
        existing_membership = db.query(UserOrganization).filter(
            UserOrganization.user_id == existing_user.id,
            UserOrganization.organization_id == org_id
        ).first()

        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )

    # Get role
    role = db.query(Role).filter(
        Role.name == invite_data.role_name,
        ((Role.organization_id == org_id) | (Role.is_system_role == True))
    ).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{invite_data.role_name}' not found"
        )

    # Check user limit
    current_user_count = db.query(func.count(UserOrganization.id)).filter(
        UserOrganization.organization_id == org_id,
        UserOrganization.is_active == True
    ).scalar() or 0

    if not organization.check_user_limit(current_user_count):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization has reached maximum user limit ({organization.max_users})"
        )

    # Generate invitation token
    invitation_token = create_invitation_token(invite_data.email, org_id)
    expires_at = datetime.utcnow() + timedelta(days=7)

    if existing_user:
        # Create pending user-org relationship
        user_org = UserOrganization(
            user_id=existing_user.id,
            organization_id=org_id,
            role_id=role.id,
            is_primary=False,
            is_active=False,  # Inactive until accepted
            invited_by=current_user.id,
            invitation_token=invitation_token,
            invitation_expires_at=expires_at
        )
        db.add(user_org)
    else:
        # Create placeholder user-org (user_id will be filled during registration)
        user_org = UserOrganization(
            user_id=None,  # Will be filled during registration
            organization_id=org_id,
            role_id=role.id,
            is_primary=True,  # First organization
            is_active=False,
            invited_by=current_user.id,
            invitation_token=invitation_token,
            invitation_expires_at=expires_at
        )
        # We need to handle this differently - store invitation separately
        # For simplicity, we'll just return the token and handle during registration

    db.commit()

    # TODO: Send invitation email
    # invitation_link = f"{settings.FRONTEND_URL}/register?token={invitation_token}"

    return UserInviteResponse(
        email=invite_data.email,
        organization_id=org_id,
        invitation_token=invitation_token,
        expires_at=expires_at,
        invited_by=current_user.id
    )
```

---

## User Management API

### File: `/mnt/g/khoirul/signate/backend/app/api/users.py`

```python
"""
User Management API
Endpoints for managing users within organizations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import (
    get_current_user, get_current_organization,
    require_permission, get_current_superuser
)
from app.core.security import hash_password
from app.models.user import User
from app.models.organization import Organization
from app.models.user_organization import UserOrganization
from app.models.role import Role
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    UserPasswordUpdate, UserWithOrganizations
)

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def list_users(
    current_user: User = Depends(require_permission("users", "read")),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[str] = Query(None, description="Filter by role name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """
    List all users in current organization

    Requires: users.read permission
    """
    query = db.query(User).join(
        UserOrganization, User.id == UserOrganization.user_id
    ).filter(
        UserOrganization.organization_id == organization.id,
        UserOrganization.is_active == True
    )

    # Apply filters
    if role:
        query = query.join(Role, UserOrganization.role_id == Role.id).filter(
            Role.name == role
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.offset(skip).limit(limit).all()

    return [UserResponse.model_validate(user) for user in users]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission("users", "create")),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
    role_name: str = Query("viewer", description="Role to assign")
):
    """
    Create a new user in current organization

    Requires: users.create permission
    """
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )

    # Check user limit
    from sqlalchemy import func
    current_user_count = db.query(func.count(UserOrganization.id)).filter(
        UserOrganization.organization_id == organization.id,
        UserOrganization.is_active == True
    ).scalar() or 0

    if not organization.check_user_limit(current_user_count):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization has reached maximum user limit ({organization.max_users})"
        )

    # Get role
    role = db.query(Role).filter(
        Role.name == role_name,
        ((Role.organization_id == organization.id) | (Role.is_system_role == True))
    ).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_name}' not found"
        )

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=role_name,  # Legacy field
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.flush()  # Get user.id

    # Create user-organization relationship
    user_org = UserOrganization(
        user_id=user.id,
        organization_id=organization.id,
        role_id=role.id,
        is_primary=True,
        is_active=True,
        invited_by=current_user.id,
        joined_at=datetime.utcnow()
    )
    db.add(user_org)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserWithOrganizations)
def get_user(
    user_id: int,
    current_user: User = Depends(require_permission("users", "read")),
    db: Session = Depends(get_db)
):
    """
    Get user details with organization memberships

    Requires: users.read permission
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get user's organizations
    user_orgs = db.query(
        UserOrganization, Organization, Role
    ).join(
        Organization, UserOrganization.organization_id == Organization.id
    ).join(
        Role, UserOrganization.role_id == Role.id
    ).filter(
        UserOrganization.user_id == user_id,
        UserOrganization.is_active == True
    ).all()

    from app.schemas.user import OrganizationMembership

    organizations = [
        OrganizationMembership(
            organization_id=org.id,
            organization_name=org.name,
            organization_slug=org.slug,
            role_name=role.name,
            role_display_name=role.display_name or role.name,
            is_primary=user_org.is_primary,
            joined_at=user_org.joined_at
        )
        for user_org, org, role in user_orgs
    ]

    user_dict = UserResponse.model_validate(user).model_dump()
    user_dict['organizations'] = organizations

    return UserWithOrganizations(**user_dict)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_permission("users", "update")),
    db: Session = Depends(get_db)
):
    """
    Update user information

    Requires: users.update permission
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_permission("users", "delete")),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Remove user from organization (or delete if last org)

    Requires: users.delete permission
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Cannot delete yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Remove from organization
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == user_id,
        UserOrganization.organization_id == organization.id
    ).first()

    if user_org:
        user_org.is_active = False
        user_org.left_at = datetime.utcnow()

    # Check if user has other organizations
    other_orgs = db.query(UserOrganization).filter(
        UserOrganization.user_id == user_id,
        UserOrganization.organization_id != organization.id,
        UserOrganization.is_active == True
    ).count()

    # If no other organizations, deactivate user
    if other_orgs == 0:
        user.is_active = False

    db.commit()

    return None


@router.put("/{user_id}/role")
def update_user_role(
    user_id: int,
    role_name: str = Query(..., description="New role name"),
    current_user: User = Depends(require_permission("users", "update")),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Update user's role in current organization

    Requires: users.update permission
    """
    # Get user-organization relationship
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == user_id,
        UserOrganization.organization_id == organization.id,
        UserOrganization.is_active == True
    ).first()

    if not user_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in organization"
        )

    # Cannot change your own role
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    # Get new role
    role = db.query(Role).filter(
        Role.name == role_name,
        ((Role.organization_id == organization.id) | (Role.is_system_role == True))
    ).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_name}' not found"
        )

    # Update role
    user_org.role_id = role.id
    db.commit()

    return {"message": "User role updated successfully", "role": role_name}
```

---

## Update Configuration for Multi-Tenancy

### File: `/mnt/g/khoirul/signate/backend/app/core/config.py` (ADD)

Add these new settings:

```python
# =============================================================================
# EMAIL SETTINGS (for invitations and password reset)
# =============================================================================
SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
SMTP_USER: str = Field(default="", env="SMTP_USER")
SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
SMTP_FROM_EMAIL: str = Field(default="noreply@signage.com", env="SMTP_FROM_EMAIL")
SMTP_FROM_NAME: str = Field(default="Smart TV Signage", env="SMTP_FROM_NAME")

# =============================================================================
# FRONTEND URL (for email links)
# =============================================================================
FRONTEND_URL: str = Field(default="http://localhost:3000", env="FRONTEND_URL")

# =============================================================================
# SESSION SETTINGS
# =============================================================================
SESSION_CLEANUP_INTERVAL: int = Field(default=3600, env="SESSION_CLEANUP_INTERVAL")  # 1 hour
```

---

## Update requirements.txt

### File: `/mnt/g/khoirul/signate/backend/requirements.txt` (ADD)

Add these dependencies:

```txt
# Slugify for organization slugs
python-slugify==8.0.1

# Email sending
aiosmtplib==3.0.1  # Async SMTP client
email-validator==2.1.0  # Already in your requirements

# Optional: Better HTML emails
jinja2==3.1.2  # Template engine for email templates
```

---

## Update main.py to Include New Routers

### File: `/mnt/g/khoirul/signate/backend/app/main.py` (UPDATE)

Update the imports and router includes:

```python
# Import new routers
from app.api import (
    auth, devices, content, client, tags, logs,
    websocket, speedtest, playlists, activities,
    organizations, users  # NEW
)

# Include new routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])  # NEW
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])  # NEW
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
# ... rest of existing routers
```

---

## Update Existing Endpoints to Filter by Organization

### Example: Update Device Endpoints

### File: `/mnt/g/khoirul/signate/backend/app/api/devices.py` (UPDATE)

Add organization filtering to all queries:

```python
from app.core.deps import get_current_organization, require_permission

# Update list_devices endpoint
@router.get("/", response_model=List[DeviceResponse])
def list_devices(
    organization: Organization = Depends(get_current_organization),  # NEW
    current_user: User = Depends(require_permission("devices", "read")),  # NEW (instead of get_current_user)
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """List all devices in organization"""
    query = db.query(Device).filter(
        Device.organization_id == organization.id  # NEW - Filter by organization
    )

    # Rest of existing logic...
    if status:
        query = query.filter(Device.status == status)
    if device_type:
        query = query.filter(Device.device_type == device_type)

    devices = query.offset(skip).limit(limit).all()
    return [DeviceResponse.model_validate(device) for device in devices]


# Update create_device endpoint
@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(
    device_data: DeviceCreate,
    organization: Organization = Depends(get_current_organization),  # NEW
    current_user: User = Depends(require_permission("devices", "create")),  # NEW
    db: Session = Depends(get_db)
):
    """Create a new device"""

    # Check device limit
    from sqlalchemy import func
    current_device_count = db.query(func.count(Device.id)).filter(
        Device.organization_id == organization.id
    ).scalar() or 0

    if not organization.check_device_limit(current_device_count):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization has reached maximum device limit ({organization.max_devices})"
        )

    # Create device
    device = Device(
        **device_data.model_dump(),
        organization_id=organization.id,  # NEW
        created_by=current_user.id,  # NEW
        status="pending"
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    return DeviceResponse.model_validate(device)


# Update get_device endpoint
@router.get("/{device_id}", response_model=DeviceDetail)
def get_device(
    device_id: int,
    organization: Organization = Depends(get_current_organization),  # NEW
    current_user: User = Depends(require_permission("devices", "read")),  # NEW
    db: Session = Depends(get_db)
):
    """Get device details"""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.organization_id == organization.id  # NEW - Ensure device belongs to org
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Rest of existing logic...
    return device


# Similar updates for update_device, delete_device, etc.
```

---

## Audit Logging Utility

### File: `/mnt/g/khoirul/signate/backend/app/utils/audit.py`

```python
"""
Audit logging utility
Tracks all important actions in the system
"""

from sqlalchemy.orm import Session
from fastapi import Request
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.audit_log import AuditLog
from app.models.user import User


def create_audit_log(
    db: Session,
    user: Optional[User],
    organization_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[int],
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
):
    """
    Create an audit log entry

    Args:
        db: Database session
        user: User who performed the action (None for system actions)
        organization_id: Organization context
        action: Action performed (e.g., 'create', 'update', 'delete', 'login')
        resource_type: Type of resource (e.g., 'device', 'user', 'content')
        resource_id: ID of affected resource
        details: Additional details (JSON)
        request: FastAPI request object (for IP and user agent)
    """
    audit_log = AuditLog(
        user_id=user.id if user else None,
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
        created_at=datetime.utcnow()
    )

    db.add(audit_log)
    db.commit()


# Decorator for automatic audit logging
def audit_action(action: str, resource_type: str):
    """
    Decorator for automatic audit logging on endpoints

    Example:
        @router.post("/devices")
        @audit_action("create", "device")
        def create_device(...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get dependencies from kwargs
            db: Session = kwargs.get('db')
            current_user: User = kwargs.get('current_user')
            organization = kwargs.get('organization')
            request: Request = kwargs.get('request')

            # Execute function
            result = await func(*args, **kwargs)

            # Create audit log
            if db and current_user:
                resource_id = getattr(result, 'id', None) if hasattr(result, 'id') else None
                create_audit_log(
                    db=db,
                    user=current_user,
                    organization_id=organization.id if organization else None,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    request=request
                )

            return result

        return wrapper
    return decorator
```

---

## Environment Variables (.env)

Add these to your `.env` file:

```bash
# =============================================================================
# MULTI-TENANCY & AUTH
# =============================================================================

# JWT Settings (already exists, but ensure these are set)
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production_min_32_chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Settings (for invitations and password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@signage.com
SMTP_FROM_NAME=Smart TV Signage

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:3000

# Session Settings
SESSION_CLEANUP_INTERVAL=3600

# =============================================================================
# DEFAULT ADMIN USER (for initial setup)
# =============================================================================
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@signage.com
DEFAULT_ADMIN_PASSWORD=Admin@123456
```

---

## Database Migration Script

### File: `/mnt/g/khoirul/signate/backend/scripts/run_migration.py`

```python
"""
Run database migration for multi-tenancy
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the multi-tenancy migration"""
    engine = create_engine(settings.DATABASE_URL)

    migration_file = Path(__file__).parent.parent / "migrations" / "006_add_multi_tenancy.sql"

    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False

    logger.info(f"Running migration: {migration_file}")

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    try:
        with engine.connect() as conn:
            # Execute migration in transaction
            conn.execute(text("BEGIN;"))

            # Split by semicolon and execute each statement
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]

            for i, statement in enumerate(statements, 1):
                if statement:
                    logger.info(f"Executing statement {i}/{len(statements)}")
                    conn.execute(text(statement))

            conn.execute(text("COMMIT;"))

        logger.info("Migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
```

---

**This completes Part 2. Ready for Part 3 with:**
- Testing Strategy
- Deployment Guide
- Frontend Integration Examples
- Security Checklist
- Performance Optimization Tips

Would you like me to continue with Part 3?
