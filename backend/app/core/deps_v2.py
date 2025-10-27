"""
FastAPI dependencies for multi-tenant authentication and authorization
Version 2 with organization context support
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security.jwt import verify_token
from app.models.user import User
from app.models.organization import Organization
from app.models.user_organization import UserOrganization
from app.models.role import Role

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class OrganizationContext:
    """Organization context for multi-tenant requests"""

    def __init__(
        self,
        user: User,
        organization: Organization,
        user_organization: UserOrganization,
        role: Role,
        permissions: List[str]
    ):
        self.user = user
        self.organization = organization
        self.user_organization = user_organization
        self.role = role
        self.permissions = set(permissions)  # Use set for faster lookup

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has specific permission"""
        # Check for super admin
        if "*:*" in self.permissions:
            return True

        # Check for resource wildcard
        if f"{resource}:*" in self.permissions:
            return True

        # Check for specific permission
        return f"{resource}:{action}" in self.permissions

    def has_any_permission(self, *permissions) -> bool:
        """Check if user has any of the specified permissions"""
        for perm in permissions:
            if ":" in perm:
                resource, action = perm.split(":", 1)
                if self.has_permission(resource, action):
                    return True
        return False

    def has_all_permissions(self, *permissions) -> bool:
        """Check if user has all of the specified permissions"""
        for perm in permissions:
            if ":" in perm:
                resource, action = perm.split(":", 1)
                if not self.has_permission(resource, action):
                    return False
        return True

    def is_admin(self) -> bool:
        """Check if user is organization admin"""
        return self.role.name in ['admin', 'super_admin']

    def is_super_admin(self) -> bool:
        """Check if user is super admin"""
        return self.user.is_super_admin or self.role.name == 'super_admin'


async def get_current_user_with_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db)
) -> OrganizationContext:
    """
    Get current authenticated user with organization context

    Args:
        credentials: HTTP Bearer credentials
        x_organization_id: Optional organization ID from header
        db: Database session

    Returns:
        OrganizationContext: User's organization context

    Raises:
        HTTPException: If authentication or authorization fails
    """
    # Check if credentials provided
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
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Get organization context
    organization_id = x_organization_id or payload.get("organization_id")

    if not organization_id:
        # If no organization specified, try to get user's primary organization
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == user.id,
            UserOrganization.is_primary == True,
            UserOrganization.is_active == True
        ).first()

        if not user_org:
            # If no primary, get first available organization
            user_org = db.query(UserOrganization).filter(
                UserOrganization.user_id == user.id,
                UserOrganization.is_active == True
            ).first()

        if not user_org:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not associated with any organization",
            )

        organization_id = user_org.organization_id
    else:
        # Verify user belongs to specified organization
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == user.id,
            UserOrganization.organization_id == organization_id,
            UserOrganization.is_active == True
        ).first()

        if not user_org:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not member of specified organization",
            )

    # Get organization
    organization = db.query(Organization).filter(
        Organization.id == organization_id
    ).first()

    if not organization or not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization not found or inactive",
        )

    # Get role
    role = db.query(Role).filter(Role.id == user_org.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role not found",
        )

    # Get permissions list
    permissions = role.get_permission_list()

    # Add super admin permissions if applicable
    if user.is_super_admin:
        permissions = ["*:*"]

    return OrganizationContext(
        user=user,
        organization=organization,
        user_organization=user_org,
        role=role,
        permissions=permissions
    )


def require_permission(resource: str, action: str):
    """
    Dependency to require specific permission

    Args:
        resource: Resource name (e.g., 'devices', 'content')
        action: Action name (e.g., 'create', 'read', 'update', 'delete')

    Returns:
        Dependency function that checks permission

    Usage:
        @router.get("/devices")
        async def list_devices(
            context: OrganizationContext = Depends(require_permission("devices", "read"))
        ):
            ...
    """
    async def permission_checker(
        context: OrganizationContext = Depends(get_current_user_with_context)
    ) -> OrganizationContext:
        if not context.has_permission(resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {resource}:{action}"
            )
        return context

    return permission_checker


def require_any_permission(*permissions):
    """
    Dependency to require at least one of the specified permissions

    Args:
        *permissions: Permission strings in format "resource:action"

    Returns:
        Dependency function that checks permissions
    """
    async def permission_checker(
        context: OrganizationContext = Depends(get_current_user_with_context)
    ) -> OrganizationContext:
        if not context.has_any_permission(*permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(permissions)}"
            )
        return context

    return permission_checker


def require_admin():
    """
    Dependency to require admin role

    Returns:
        Dependency function that checks for admin role
    """
    async def admin_checker(
        context: OrganizationContext = Depends(get_current_user_with_context)
    ) -> OrganizationContext:
        if not context.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return context

    return admin_checker


def require_super_admin():
    """
    Dependency to require super admin role

    Returns:
        Dependency function that checks for super admin role
    """
    async def super_admin_checker(
        context: OrganizationContext = Depends(get_current_user_with_context)
    ) -> OrganizationContext:
        if not context.is_super_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required"
            )
        return context

    return super_admin_checker


def get_optional_context(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[OrganizationContext]:
    """
    Get organization context if authenticated, None otherwise

    Useful for endpoints that have different behavior for authenticated vs anonymous users
    """
    if not credentials:
        return None

    try:
        return get_current_user_with_context(credentials, x_organization_id, db)
    except HTTPException:
        return None


# Backward compatibility aliases
get_current_context = get_current_user_with_context