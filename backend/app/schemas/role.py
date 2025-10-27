"""
Role and Permission Schemas
Pydantic models for RBAC-related requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime


class RoleBase(BaseModel):
    """Base role schema"""
    name: str = Field(..., min_length=2, max_length=50, regex="^[a-z_]+$", description="Internal role name")
    display_name: str = Field(..., min_length=2, max_length=100, description="User-friendly display name")
    description: Optional[str] = Field(None, max_length=500, description="Role description")

    @validator('name')
    def validate_name(cls, v):
        if not v.replace('_', '').isalpha():
            raise ValueError('Role name must contain only lowercase letters and underscores')
        return v.lower()


class RoleCreate(RoleBase):
    """Schema for creating role"""
    permissions: Dict[str, List[str]] = Field(
        ...,
        description="Permissions map: {resource: [actions]}",
        example={
            "devices": ["create", "read", "update"],
            "content": ["read", "update"]
        }
    )
    organization_id: Optional[int] = Field(None, description="Organization ID (null for system roles)")

    @validator('permissions')
    def validate_permissions(cls, v):
        if not v:
            raise ValueError('At least one permission must be specified')

        valid_resources = [
            "organizations", "users", "roles", "devices",
            "content", "playlists", "tags", "logs", "settings", "*"
        ]
        valid_actions = ["create", "read", "update", "delete", "manage", "*"]

        for resource, actions in v.items():
            if resource not in valid_resources:
                raise ValueError(f'Invalid resource: {resource}')

            if not isinstance(actions, list):
                raise ValueError(f'Actions for {resource} must be a list')

            for action in actions:
                if action not in valid_actions:
                    raise ValueError(f'Invalid action: {action} for resource: {resource}')

        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "content_manager",
                "display_name": "Content Manager",
                "description": "Manages all content and playlists",
                "permissions": {
                    "content": ["create", "read", "update", "delete"],
                    "playlists": ["create", "read", "update", "delete"],
                    "devices": ["read"],
                    "tags": ["create", "read", "update"]
                }
            }
        }


class RoleUpdate(BaseModel):
    """Schema for updating role"""
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[Dict[str, List[str]]] = None

    @validator('permissions')
    def validate_permissions(cls, v):
        if v is not None:
            # Apply same validation as RoleCreate
            valid_resources = [
                "organizations", "users", "roles", "devices",
                "content", "playlists", "tags", "logs", "settings", "*"
            ]
            valid_actions = ["create", "read", "update", "delete", "manage", "*"]

            for resource, actions in v.items():
                if resource not in valid_resources:
                    raise ValueError(f'Invalid resource: {resource}')

                for action in actions:
                    if action not in valid_actions:
                        raise ValueError(f'Invalid action: {action}')

        return v


class RoleResponse(RoleBase):
    """Schema for role response"""
    id: int
    organization_id: Optional[int]
    is_system_role: bool
    permissions: Dict[str, List[str]]
    user_count: Optional[int] = Field(0, description="Number of users with this role")
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PermissionCheck(BaseModel):
    """Schema for checking permissions"""
    resource: str = Field(..., description="Resource to check permission for")
    action: str = Field(..., description="Action to check permission for")
    resource_id: Optional[int] = Field(None, description="Specific resource ID (for future use)")

    class Config:
        schema_extra = {
            "example": {
                "resource": "devices",
                "action": "update",
                "resource_id": 123
            }
        }


class PermissionCheckResponse(BaseModel):
    """Response for permission check"""
    has_permission: bool
    resource: str
    action: str
    resource_id: Optional[int]
    reason: Optional[str] = Field(None, description="Reason for permission denial")


class PermissionResource(BaseModel):
    """Schema for permission resource definition"""
    name: str = Field(..., description="Resource name")
    display_name: str = Field(..., description="User-friendly display name")
    description: str = Field(..., description="Resource description")
    actions: List[str] = Field(..., description="Available actions for this resource")

    class Config:
        schema_extra = {
            "example": {
                "name": "devices",
                "display_name": "Devices",
                "description": "TV and monitor devices",
                "actions": ["create", "read", "update", "delete"]
            }
        }


class AvailablePermissions(BaseModel):
    """Schema for listing all available permissions"""
    resources: List[PermissionResource]

    class Config:
        schema_extra = {
            "example": {
                "resources": [
                    {
                        "name": "devices",
                        "display_name": "Devices",
                        "description": "Manage devices",
                        "actions": ["create", "read", "update", "delete"]
                    },
                    {
                        "name": "content",
                        "display_name": "Content",
                        "description": "Manage content",
                        "actions": ["create", "read", "update", "delete"]
                    }
                ]
            }
        }


class RoleAssignment(BaseModel):
    """Schema for assigning role to user"""
    user_id: int = Field(..., description="User ID")
    role_id: int = Field(..., description="Role ID to assign")
    organization_id: Optional[int] = Field(None, description="Organization ID (defaults to current)")

    class Config:
        schema_extra = {
            "example": {
                "user_id": 5,
                "role_id": 3
            }
        }


class BulkRoleAssignment(BaseModel):
    """Schema for assigning role to multiple users"""
    user_ids: List[int] = Field(..., min_items=1, description="List of user IDs")
    role_id: int = Field(..., description="Role ID to assign")
    organization_id: Optional[int] = Field(None, description="Organization ID")

    class Config:
        schema_extra = {
            "example": {
                "user_ids": [5, 6, 7],
                "role_id": 3
            }
        }