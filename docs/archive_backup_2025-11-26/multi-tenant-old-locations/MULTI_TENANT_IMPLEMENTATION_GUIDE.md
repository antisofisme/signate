# Multi-Tenant User Management Implementation Guide

## Table of Contents
1. [Overview](#overview)
2. [Database Schema](#database-schema)
3. [Step-by-Step Implementation](#step-by-step-implementation)
4. [Security Best Practices](#security-best-practices)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Guide](#deployment-guide)

---

## Overview

This guide provides a production-ready implementation for adding multi-tenant user management to the Smart TV Digital Signage FastAPI backend.

### Current Stack
- FastAPI 0.109.0
- PostgreSQL with SQLAlchemy 2.0.25
- Pydantic 2.5.3
- python-jose[cryptography] for JWT
- bcrypt for password hashing
- Docker containerized on port 8001

### Key Features to Implement
- JWT authentication with access and refresh tokens
- Multi-tenant organization support
- Role-based access control (RBAC)
- User invitations and email verification
- Password reset flow
- Session management
- Audit logging
- Rate limiting per organization

---

## Database Schema

Your migration file `006_add_multi_tenancy.sql` already includes the necessary tables. Here's the schema overview:

### Core Tables

```
organizations (multi-tenant isolation)
├── id (PK)
├── name
├── slug (unique, URL-friendly)
├── settings (JSONB)
├── max_devices, max_users, max_storage_gb
├── subscription_tier
├── is_active
└── timestamps

users (enhanced existing table)
├── id (PK)
├── username, email, password_hash
├── full_name, phone (NEW)
├── role (legacy field, keep for backward compatibility)
├── is_active
├── is_super_admin (NEW - for platform admins)
└── timestamps

roles (RBAC)
├── id (PK)
├── name, display_name
├── organization_id (FK, NULL for system roles)
├── is_system_role
├── permissions (JSONB)
└── timestamps

user_organizations (many-to-many with role)
├── id (PK)
├── user_id (FK)
├── organization_id (FK)
├── role_id (FK)
├── is_primary (default org for user)
├── is_active
├── invitation_token, invitation_expires_at
└── timestamps

user_sessions (session tracking)
├── id (PK)
├── user_id, organization_id (FK)
├── session_token, refresh_token
├── ip_address, user_agent
├── is_active
└── timestamps

audit_logs (audit trail)
├── id (PK)
├── user_id, organization_id (FK)
├── action, resource_type, resource_id
├── details (JSONB)
└── timestamps
```

### Data Isolation

All tenant-scoped tables now have `organization_id`:
- `devices.organization_id` → FK to organizations
- `content.organization_id` → FK to organizations
- `playlists.organization_id` → FK to organizations
- `tags.organization_id` → FK to organizations
- All junction tables also include `organization_id`

---

## Step-by-Step Implementation

### PHASE 1: Database Models

#### 1.1 Create Organization Model

**File:** `/mnt/g/khoirul/signate/backend/app/models/organization.py`

```python
"""
Organization Model
Multi-tenant organization management
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Organization(Base):
    """
    Organization model for multi-tenancy

    Attributes:
        id: Primary key
        name: Organization name
        slug: URL-friendly unique identifier
        description: Organization description
        settings: JSON settings (branding, features, etc.)
        max_devices: Device limit
        max_users: User limit
        max_storage_gb: Storage limit
        subscription_tier: Subscription plan (free, basic, premium, enterprise)
        subscription_expires_at: Subscription expiry date
        is_active: Whether organization is active
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "organizations"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Organization Info
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500))

    # Settings (JSON)
    settings = Column(JSONB, default={})

    # Limits
    max_devices = Column(Integer, default=10)
    max_users = Column(Integer, default=5)
    max_storage_gb = Column(Integer, default=10)

    # Subscription
    subscription_tier = Column(String(50), default='free')
    subscription_expires_at = Column(DateTime)

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    users = relationship("UserOrganization", back_populates="organization", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="organization", cascade="all, delete-orphan")
    content = relationship("Content", back_populates="organization", cascade="all, delete-orphan")
    playlists = relationship("Playlist", back_populates="organization", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', slug='{self.slug}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "settings": self.settings,
            "max_devices": self.max_devices,
            "max_users": self.max_users,
            "max_storage_gb": self.max_storage_gb,
            "subscription_tier": self.subscription_tier,
            "subscription_expires_at": self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def check_device_limit(self, current_count: int) -> bool:
        """Check if organization can add more devices"""
        return current_count < self.max_devices

    def check_user_limit(self, current_count: int) -> bool:
        """Check if organization can add more users"""
        return current_count < self.max_users
```

#### 1.2 Create Role Model

**File:** `/mnt/g/khoirul/signate/backend/app/models/role.py`

```python
"""
Role Model
RBAC role definitions
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSONB, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Role(Base):
    """
    Role model for RBAC

    Attributes:
        id: Primary key
        name: Role name (unique within organization)
        display_name: Human-readable role name
        description: Role description
        organization_id: Organization (NULL for system roles)
        is_system_role: Whether this is a built-in role
        permissions: JSON permission matrix
        created_at: Creation timestamp
    """

    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='uix_role_name_org'),
    )

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Role Info
    name = Column(String(50), nullable=False)
    display_name = Column(String(100))
    description = Column(String(500))

    # Organization (NULL for system roles)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), index=True)

    # System Role Flag
    is_system_role = Column(Boolean, default=False, index=True)

    # Permissions (JSON)
    # Example: {"devices": ["read", "create", "update"], "content": ["read"]}
    permissions = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="roles")
    user_organizations = relationship("UserOrganization", back_populates="role")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', org_id={self.organization_id})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "organization_id": self.organization_id,
            "is_system_role": self.is_system_role,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def has_permission(self, resource: str, action: str) -> bool:
        """
        Check if role has specific permission

        Args:
            resource: Resource name (e.g., 'devices', 'content')
            action: Action name (e.g., 'read', 'create', 'update', 'delete')

        Returns:
            bool: True if role has permission
        """
        # Super admin has all permissions
        if self.permissions.get("*") == ["*"]:
            return True

        # Check specific resource permission
        resource_perms = self.permissions.get(resource, [])
        return action in resource_perms or "*" in resource_perms
```

#### 1.3 Create UserOrganization Model

**File:** `/mnt/g/khoirul/signate/backend/app/models/user_organization.py`

```python
"""
UserOrganization Model
Junction table for user-organization relationship with roles
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserOrganization(Base):
    """
    UserOrganization model - User membership in organizations

    Attributes:
        id: Primary key
        user_id: User foreign key
        organization_id: Organization foreign key
        role_id: Role foreign key
        is_primary: Whether this is the user's primary organization
        is_active: Whether membership is active
        invited_by: User who invited this user
        invitation_token: Token for invitation acceptance
        invitation_expires_at: Invitation expiry timestamp
        joined_at: When user joined
        left_at: When user left (NULL if active)
    """

    __tablename__ = "user_organizations"
    __table_args__ = (
        UniqueConstraint('user_id', 'organization_id', name='uix_user_org'),
    )

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False, index=True)

    # Membership Info
    is_primary = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)

    # Invitation Info
    invited_by = Column(Integer, ForeignKey('users.id'))
    invitation_token = Column(String(100), unique=True)
    invitation_expires_at = Column(DateTime)

    # Timestamps
    joined_at = Column(DateTime, server_default=func.now())
    left_at = Column(DateTime)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="organizations")
    organization = relationship("Organization", back_populates="users")
    role = relationship("Role", back_populates="user_organizations")
    inviter = relationship("User", foreign_keys=[invited_by])

    def __repr__(self):
        return f"<UserOrganization(user_id={self.user_id}, org_id={self.organization_id}, role_id={self.role_id})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "role_id": self.role_id,
            "is_primary": self.is_primary,
            "is_active": self.is_active,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
        }
```

#### 1.4 Create UserSession Model

**File:** `/mnt/g/khoirul/signate/backend/app/models/user_session.py`

```python
"""
UserSession Model
Track active user sessions for security
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserSession(Base):
    """
    UserSession model for session tracking

    Attributes:
        id: Primary key
        user_id: User foreign key
        organization_id: Current organization context
        session_token: Unique session identifier (JTI from JWT)
        refresh_token: Refresh token
        ip_address: Client IP address
        user_agent: Client user agent
        device_info: Additional device information (JSON)
        is_active: Whether session is active
        created_at: Session creation time
        expires_at: Session expiry time
        last_activity: Last activity timestamp
    """

    __tablename__ = "user_sessions"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), index=True)

    # Session Info
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, index=True)

    # Client Info
    ip_address = Column(INET)
    user_agent = Column(String)
    device_info = Column(JSONB, default={})

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False, index=True)
    last_activity = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "user_agent": self.user_agent,
            "device_info": self.device_info,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }
```

#### 1.5 Create AuditLog Model

**File:** `/mnt/g/khoirul/signate/backend/app/models/audit_log.py`

```python
"""
AuditLog Model
Audit trail for all system actions
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """
    AuditLog model for tracking all system actions

    Attributes:
        id: Primary key
        user_id: User who performed the action
        organization_id: Organization context
        action: Action performed (e.g., 'create', 'update', 'delete')
        resource_type: Resource type (e.g., 'device', 'user', 'content')
        resource_id: ID of the affected resource
        details: Additional details (JSON)
        ip_address: Client IP address
        user_agent: Client user agent
        created_at: Timestamp of action
    """

    __tablename__ = "audit_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), index=True)

    # Action Info
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(Integer, index=True)

    # Details
    details = Column(JSONB, default={})

    # Client Info
    ip_address = Column(INET)
    user_agent = Column(String)

    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', resource='{self.resource_type}:{self.resource_id}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
```

#### 1.6 Update Existing User Model

**File:** `/mnt/g/khoirul/signate/backend/app/models/user.py` (UPDATE)

Add these fields and relationships to your existing User model:

```python
# Add these columns
full_name = Column(String(100))
phone = Column(String(20))
is_super_admin = Column(Boolean, default=False)
email_verified = Column(Boolean, default=False)
email_verification_token = Column(String(100))
password_reset_token = Column(String(100))
password_reset_expires_at = Column(DateTime)

# Add these relationships
organizations = relationship("UserOrganization", foreign_keys="[UserOrganization.user_id]", back_populates="user", cascade="all, delete-orphan")
sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
```

#### 1.7 Update Existing Models with organization_id

Update these models to add organization relationship:

```python
# In Device model
organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
organization = relationship("Organization", back_populates="devices")
created_by = Column(Integer, ForeignKey('users.id'))

# In Content model
organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
organization = relationship("Organization", back_populates="content")
created_by = Column(Integer, ForeignKey('users.id'))

# In Playlist model
organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
organization = relationship("Organization", back_populates="playlists")
created_by = Column(Integer, ForeignKey('users.id'))

# In Tag model
organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
organization = relationship("Organization", back_populates="tags")
created_by = Column(Integer, ForeignKey('users.id'))
```

#### 1.8 Update Models __init__.py

**File:** `/mnt/g/khoirul/signate/backend/app/models/__init__.py` (UPDATE)

```python
# Add these imports
from app.models.organization import Organization
from app.models.role import Role
from app.models.user_organization import UserOrganization
from app.models.user_session import UserSession
from app.models.audit_log import AuditLog

# Update __all__ list
__all__ = [
    # ... existing exports ...
    "Organization",
    "Role",
    "UserOrganization",
    "UserSession",
    "AuditLog",
]
```

---

### PHASE 2: Pydantic Schemas

#### 2.1 Organization Schemas

**File:** `/mnt/g/khoirul/signate/backend/app/schemas/organization.py`

```python
"""
Organization Schemas
Pydantic models for organization validation and serialization
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Organization name")
    description: Optional[str] = Field(None, max_length=500, description="Organization description")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Organization settings (JSON)")


class OrganizationCreate(OrganizationBase):
    """Schema for creating organization"""
    slug: str = Field(..., min_length=3, max_length=100, pattern="^[a-z0-9-]+$", description="URL-friendly slug")
    max_devices: Optional[int] = Field(10, ge=1, description="Maximum number of devices")
    max_users: Optional[int] = Field(5, ge=1, description="Maximum number of users")
    max_storage_gb: Optional[int] = Field(10, ge=1, description="Maximum storage in GB")
    subscription_tier: Optional[str] = Field("free", description="Subscription tier")


class OrganizationUpdate(BaseModel):
    """Schema for updating organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    settings: Optional[Dict[str, Any]] = None
    max_devices: Optional[int] = Field(None, ge=1)
    max_users: Optional[int] = Field(None, ge=1)
    max_storage_gb: Optional[int] = Field(None, ge=1)
    subscription_tier: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    max_devices: int
    max_users: int
    max_storage_gb: int
    subscription_tier: str
    subscription_expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class OrganizationWithStats(OrganizationResponse):
    """Schema for organization with statistics"""
    device_count: int = 0
    user_count: int = 0
    content_count: int = 0
    playlist_count: int = 0


class OrganizationInviteRequest(BaseModel):
    """Schema for inviting user to organization"""
    email: str = Field(..., description="Email address of user to invite")
    role_name: str = Field(..., description="Role name (admin, editor, viewer)")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
```

#### 2.2 Role Schemas

**File:** `/mnt/g/khoirul/signate/backend/app/schemas/role.py`

```python
"""
Role Schemas
Pydantic models for role validation and serialization
"""

from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, ConfigDict


class RoleBase(BaseModel):
    """Base role schema"""
    name: str = Field(..., min_length=1, max_length=50, description="Role name")
    display_name: Optional[str] = Field(None, max_length=100, description="Display name")
    description: Optional[str] = Field(None, max_length=500, description="Role description")
    permissions: Dict[str, List[str]] = Field(default_factory=dict, description="Permission matrix")


class RoleCreate(RoleBase):
    """Schema for creating role"""
    pass


class RoleUpdate(BaseModel):
    """Schema for updating role"""
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[Dict[str, List[str]]] = None


class RoleResponse(RoleBase):
    """Schema for role response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: Optional[int] = None
    is_system_role: bool
    created_at: datetime


class PermissionCheck(BaseModel):
    """Schema for checking permissions"""
    resource: str = Field(..., description="Resource name (e.g., 'devices', 'content')")
    action: str = Field(..., description="Action name (e.g., 'read', 'create', 'update', 'delete')")


class PermissionResponse(BaseModel):
    """Schema for permission check response"""
    has_permission: bool
    resource: str
    action: str
```

#### 2.3 Enhanced User Schemas

**File:** `/mnt/g/khoirul/signate/backend/app/schemas/user.py` (UPDATE)

```python
"""
User Schemas
Pydantic models for user validation and serialization
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for creating user"""
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(UserBase):
    """Schema for user response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str  # Legacy field for backward compatibility
    is_active: bool
    is_super_admin: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserWithOrganizations(UserResponse):
    """Schema for user with organizations"""
    organizations: List['OrganizationMembership'] = []


class OrganizationMembership(BaseModel):
    """Schema for user's organization membership"""
    model_config = ConfigDict(from_attributes=True)

    organization_id: int
    organization_name: str
    organization_slug: str
    role_name: str
    role_display_name: str
    is_primary: bool
    joined_at: datetime


class UserInviteResponse(BaseModel):
    """Schema for user invitation response"""
    email: str
    organization_id: int
    invitation_token: str
    expires_at: datetime
    invited_by: int
```

#### 2.4 Enhanced Auth Schemas

**File:** `/mnt/g/khoirul/signate/backend/app/schemas/auth.py` (UPDATE)

```python
"""
Authentication Schemas
Pydantic models for authentication validation and serialization
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=1, description="Password")
    organization_slug: Optional[str] = Field(None, description="Organization to log into")


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: 'UserResponse'
    organization: Optional['OrganizationResponse'] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


class RegisterRequest(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    organization_name: Optional[str] = Field(None, description="Organization name (creates new org)")
    invitation_token: Optional[str] = Field(None, description="Invitation token (joins existing org)")


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., description="Email address")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str = Field(..., description="Reset token from email")
    new_password: str = Field(..., min_length=8, max_length=100)


class EmailVerificationRequest(BaseModel):
    """Schema for email verification"""
    token: str = Field(..., description="Verification token from email")


class ChangeOrganizationRequest(BaseModel):
    """Schema for changing current organization"""
    organization_id: int = Field(..., description="Organization ID to switch to")


# Forward references
from app.schemas.user import UserResponse
from app.schemas.organization import OrganizationResponse

TokenResponse.model_rebuild()
```

---

### PHASE 3: Enhanced Security

#### 3.1 Update JWT Functions

**File:** `/mnt/g/khoirul/signate/backend/app/core/security/jwt.py` (UPDATE)

```python
"""
JWT token creation and verification with session tracking
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import secrets
import hashlib

from app.core.config import settings


def create_access_token(
    data: Dict[str, Any],
    organization_id: Optional[int] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token with organization context

    Args:
        data: Data to encode in token (user_id, username, etc.)
        organization_id: Current organization context
        expires_delta: Custom expiration time, defaults to settings

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    # Generate unique JTI (JWT ID) for session tracking
    jti = secrets.token_urlsafe(32)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": jti,  # Session identifier
        "org_id": organization_id  # Organization context
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    organization_id: Optional[int] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token with organization context

    Args:
        data: Data to encode in token (usually user_id)
        organization_id: Current organization context
        expires_delta: Custom expiration time, defaults to settings

    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    # Generate unique JTI for refresh token
    jti = secrets.token_urlsafe(32)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": jti,
        "org_id": organization_id
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Optional[Dict]: Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify token type
        if payload.get("type") != token_type:
            return None

        return payload

    except JWTError:
        return None


def create_invitation_token(email: str, organization_id: int) -> str:
    """
    Create invitation token for user invitations

    Args:
        email: Email address of invitee
        organization_id: Organization ID

    Returns:
        str: Invitation token
    """
    # Create deterministic but secure token
    payload = f"{email}:{organization_id}:{secrets.token_urlsafe(16)}"
    return hashlib.sha256(payload.encode()).hexdigest()


def create_password_reset_token(user_id: int, email: str) -> str:
    """
    Create password reset token

    Args:
        user_id: User ID
        email: User email

    Returns:
        str: Password reset token
    """
    payload = f"{user_id}:{email}:{secrets.token_urlsafe(16)}"
    return hashlib.sha256(payload.encode()).hexdigest()


def create_email_verification_token(user_id: int, email: str) -> str:
    """
    Create email verification token

    Args:
        user_id: User ID
        email: User email

    Returns:
        str: Email verification token
    """
    payload = f"{user_id}:{email}:{secrets.token_urlsafe(16)}"
    return hashlib.sha256(payload.encode()).hexdigest()
```

#### 3.2 Enhanced Dependencies

**File:** `/mnt/g/khoirul/signate/backend/app/core/deps.py` (UPDATE)

```python
"""
FastAPI dependencies for authentication and authorization with multi-tenancy
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security.jwt import verify_token
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.user_organization import UserOrganization
from app.models.role import Role
from app.models.user_session import UserSession

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Verify token
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Verify session is still active
    jti = payload.get("jti")
    if jti:
        session = db.query(UserSession).filter(
            UserSession.session_token == jti,
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last activity
        session.last_activity = datetime.utcnow()
        db.commit()

    # Store organization context in request state
    org_id = payload.get("org_id")
    if org_id:
        request.state.organization_id = org_id

    return user


def get_current_organization(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Organization:
    """
    Get current organization context from JWT token

    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session

    Returns:
        Organization: Current organization

    Raises:
        HTTPException: If organization not found or user not a member
    """
    # Get organization ID from request state (set by get_current_user)
    org_id = getattr(request.state, 'organization_id', None)

    if org_id is None:
        # Fallback to user's primary organization
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == current_user.id,
            UserOrganization.is_primary == True,
            UserOrganization.is_active == True
        ).first()

        if not user_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No organization context"
            )

        org_id = user_org.organization_id

    # Get organization
    organization = db.query(Organization).filter(
        Organization.id == org_id,
        Organization.is_active == True
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Verify user is a member (unless super admin)
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

    return organization


def get_current_user_role(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> Role:
    """
    Get current user's role in the organization

    Args:
        current_user: Current authenticated user
        organization: Current organization
        db: Database session

    Returns:
        Role: User's role in organization
    """
    # Super admins have all permissions
    if current_user.is_super_admin:
        # Return super admin system role
        role = db.query(Role).filter(
            Role.name == 'super_admin',
            Role.is_system_role == True
        ).first()
        if role:
            return role

    # Get user's role in organization
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == current_user.id,
        UserOrganization.organization_id == organization.id,
        UserOrganization.is_active == True
    ).first()

    if not user_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    role = db.query(Role).filter(Role.id == user_org.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User role not found"
        )

    return role


def require_permission(resource: str, action: str):
    """
    Dependency factory for requiring specific permission

    Args:
        resource: Resource name (e.g., 'devices', 'content')
        action: Action name (e.g., 'read', 'create', 'update', 'delete')

    Returns:
        Dependency function

    Example:
        @app.get("/devices")
        def list_devices(user = Depends(require_permission("devices", "read"))):
            ...
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        role: Role = Depends(get_current_user_role)
    ) -> User:
        """Check if user has required permission"""
        if not role.has_permission(resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource}.{action}"
            )
        return current_user

    return permission_checker


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        User: Active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current superuser (platform admin)

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        User: Super admin user
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, or None if not authenticated
    For public endpoints that support optional authentication
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token, token_type="access")
        if payload:
            user_id = payload.get("user_id")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.is_active:
                    return user
    except Exception:
        pass

    return None
```

---

### PHASE 4: API Endpoints

#### 4.1 Enhanced Auth Endpoints

**File:** `/mnt/g/khoirul/signate/backend/app/api/auth.py` (REPLACE)

```python
"""
Enhanced Authentication API endpoints with multi-tenancy
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from app.core.security.jwt import create_invitation_token, create_password_reset_token, create_email_verification_token
from app.core.deps import get_current_user, get_current_active_user, get_current_organization
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.user_organization import UserOrganization
from app.models.role import Role
from app.models.user_session import UserSession
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshTokenRequest, RegisterRequest,
    PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest,
    ChangeOrganizationRequest
)
from app.schemas.user import UserResponse, UserWithOrganizations
from app.schemas.organization import OrganizationResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticate user and return JWT tokens

    Features:
    - Supports login with username or email
    - Optional organization selection
    - Creates session tracking entry
    - Returns user and organization info
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()

    # Verify user exists and password is correct
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Determine organization context
    organization = None
    if login_data.organization_slug:
        # Login to specific organization
        organization = db.query(Organization).filter(
            Organization.slug == login_data.organization_slug,
            Organization.is_active == True
        ).first()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # Verify user is a member
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == user.id,
            UserOrganization.organization_id == organization.id,
            UserOrganization.is_active == True
        ).first()

        if not user_org and not user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this organization"
            )
    else:
        # Login to primary organization
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == user.id,
            UserOrganization.is_primary == True,
            UserOrganization.is_active == True
        ).first()

        if user_org:
            organization = db.query(Organization).filter(
                Organization.id == user_org.organization_id
            ).first()

    organization_id = organization.id if organization else None

    # Create tokens
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "username": user.username,
            "is_super_admin": user.is_super_admin
        },
        organization_id=organization_id
    )

    refresh_token = create_refresh_token(
        data={"user_id": user.id},
        organization_id=organization_id
    )

    # Decode tokens to get JTI
    access_payload = verify_token(access_token, "access")
    refresh_payload = verify_token(refresh_token, "refresh")

    # Create session record
    session = UserSession(
        user_id=user.id,
        organization_id=organization_id,
        session_token=access_payload["jti"],
        refresh_token=refresh_payload["jti"],
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.utcfromtimestamp(access_payload["exp"]),
        is_active=True
    )
    db.add(session)

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(organization) if organization else None
    )


@router.post("/register", response_model=TokenResponse)
def register(
    register_data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register new user

    Features:
    - Create user account
    - Create new organization OR join via invitation
    - Assign appropriate role
    - Generate email verification token
    """
    # Check if username already exists
    existing_user = db.query(User).filter(
        (User.username == register_data.username) | (User.email == register_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Create user
    user = User(
        username=register_data.username,
        email=register_data.email,
        password_hash=hash_password(register_data.password),
        full_name=register_data.full_name,
        role='viewer',  # Legacy field
        is_active=True,
        email_verified=False,
        email_verification_token=create_email_verification_token(0, register_data.email)
    )
    db.add(user)
    db.flush()  # Get user.id

    organization = None

    # Handle invitation token OR create new organization
    if register_data.invitation_token:
        # Join existing organization via invitation
        user_org = db.query(UserOrganization).filter(
            UserOrganization.invitation_token == register_data.invitation_token,
            UserOrganization.invitation_expires_at > datetime.utcnow()
        ).first()

        if not user_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token"
            )

        # Update user_org with actual user_id
        user_org.user_id = user.id
        user_org.invitation_token = None
        user_org.joined_at = datetime.utcnow()
        user_org.is_active = True
        user_org.is_primary = True

        organization = db.query(Organization).filter(
            Organization.id == user_org.organization_id
        ).first()

    elif register_data.organization_name:
        # Create new organization
        from slugify import slugify
        slug = slugify(register_data.organization_name)

        # Ensure slug is unique
        counter = 1
        original_slug = slug
        while db.query(Organization).filter(Organization.slug == slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1

        organization = Organization(
            name=register_data.organization_name,
            slug=slug,
            is_active=True
        )
        db.add(organization)
        db.flush()  # Get organization.id

        # Get admin role
        admin_role = db.query(Role).filter(
            Role.name == 'admin',
            Role.is_system_role == True
        ).first()

        # Create user-organization relationship as admin
        user_org = UserOrganization(
            user_id=user.id,
            organization_id=organization.id,
            role_id=admin_role.id,
            is_primary=True,
            is_active=True,
            joined_at=datetime.utcnow()
        )
        db.add(user_org)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either organization_name or invitation_token is required"
        )

    db.commit()

    # Create tokens
    organization_id = organization.id if organization else None

    access_token = create_access_token(
        data={
            "user_id": user.id,
            "username": user.username,
            "is_super_admin": user.is_super_admin
        },
        organization_id=organization_id
    )

    refresh_token = create_refresh_token(
        data={"user_id": user.id},
        organization_id=organization_id
    )

    # Create session
    access_payload = verify_token(access_token, "access")
    refresh_payload = verify_token(refresh_token, "refresh")

    session = UserSession(
        user_id=user.id,
        organization_id=organization_id,
        session_token=access_payload["jti"],
        refresh_token=refresh_payload["jti"],
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.utcfromtimestamp(access_payload["exp"]),
        is_active=True
    )
    db.add(session)
    db.commit()

    # TODO: Send verification email

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(organization) if organization else None
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify session is still valid
    jti = payload.get("jti")
    session = db.query(UserSession).filter(
        UserSession.refresh_token == jti,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )

    # Get user
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    organization_id = payload.get("org_id")
    organization = None
    if organization_id:
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()

    # Create new tokens
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "username": user.username,
            "is_super_admin": user.is_super_admin
        },
        organization_id=organization_id
    )

    new_refresh_token = create_refresh_token(
        data={"user_id": user.id},
        organization_id=organization_id
    )

    # Update session
    access_payload = verify_token(access_token, "access")
    refresh_payload = verify_token(new_refresh_token, "refresh")

    session.session_token = access_payload["jti"]
    session.refresh_token = refresh_payload["jti"]
    session.expires_at = datetime.utcfromtimestamp(access_payload["exp"])
    session.last_activity = datetime.utcnow()
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(organization) if organization else None
    )


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Logout endpoint - invalidate current session
    """
    # Get JTI from request (you'll need to extract from token)
    # For now, invalidate all user's sessions (simpler approach)
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).update({"is_active": False})

    db.commit()

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserWithOrganizations)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information with organizations
    """
    # Get user's organizations
    user_orgs = db.query(
        UserOrganization,
        Organization,
        Role
    ).join(
        Organization, UserOrganization.organization_id == Organization.id
    ).join(
        Role, UserOrganization.role_id == Role.id
    ).filter(
        UserOrganization.user_id == current_user.id,
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

    user_dict = UserResponse.model_validate(current_user).model_dump()
    user_dict['organizations'] = organizations

    return UserWithOrganizations(**user_dict)


@router.post("/change-organization", response_model=TokenResponse)
def change_organization(
    data: ChangeOrganizationRequest,
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Change current organization context (issue new tokens)
    """
    # Verify user is a member
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == current_user.id,
        UserOrganization.organization_id == data.organization_id,
        UserOrganization.is_active == True
    ).first()

    if not user_org and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    organization = db.query(Organization).filter(
        Organization.id == data.organization_id,
        Organization.is_active == True
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Create new tokens with new organization context
    access_token = create_access_token(
        data={
            "user_id": current_user.id,
            "username": current_user.username,
            "is_super_admin": current_user.is_super_admin
        },
        organization_id=organization.id
    )

    refresh_token = create_refresh_token(
        data={"user_id": current_user.id},
        organization_id=organization.id
    )

    # Create new session
    access_payload = verify_token(access_token, "access")
    refresh_payload = verify_token(refresh_token, "refresh")

    session = UserSession(
        user_id=current_user.id,
        organization_id=organization.id,
        session_token=access_payload["jti"],
        refresh_token=refresh_payload["jti"],
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
        expires_at=datetime.utcfromtimestamp(access_payload["exp"]),
        is_active=True
    )
    db.add(session)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(current_user),
        organization=OrganizationResponse.model_validate(organization)
    )


@router.post("/forgot-password")
def forgot_password(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset - sends email with reset token
    """
    user = db.query(User).filter(User.email == data.email).first()

    # Don't reveal if user exists (security best practice)
    if user:
        # Generate reset token
        token = create_password_reset_token(user.id, user.email)
        user.password_reset_token = token
        user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        db.commit()

        # TODO: Send email with reset link
        # reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
def reset_password(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password using token from email
    """
    user = db.query(User).filter(
        User.password_reset_token == data.token,
        User.password_reset_expires_at > datetime.utcnow()
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Update password
    user.password_hash = hash_password(data.new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None

    # Invalidate all sessions
    db.query(UserSession).filter(
        UserSession.user_id == user.id
    ).update({"is_active": False})

    db.commit()

    return {"message": "Password reset successful"}


@router.post("/verify-email")
def verify_email(
    data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email address using token
    """
    user = db.query(User).filter(
        User.email_verification_token == data.token
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

    user.email_verified = True
    user.email_verification_token = None
    db.commit()

    return {"message": "Email verified successfully"}
```

---

**This is Part 1 of the implementation guide. Would you like me to continue with:**

- **Part 2:** Organization Management API Endpoints
- **Part 3:** User Management API Endpoints
- **Part 4:** Role & Permission Management
- **Part 5:** Updating Existing Endpoints (Devices, Content, etc.)
- **Part 6:** Testing Strategy & Deployment Guide

The document is already quite comprehensive. Should I continue with the remaining parts?
