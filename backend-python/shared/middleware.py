"""
Authentication Middleware
FastAPI dependencies for JWT authentication and authorization
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import extract_user_from_token
from functools import wraps


# =============================================================================
# AUTHENTICATION DEPENDENCY
# =============================================================================

async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Extract and validate current user from Authorization header

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        User information dictionary

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Validate token and extract user info
    user_info = extract_user_from_token(token)

    return user_info


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Verify that current user is active in database

    Args:
        current_user: User info from token
        db: Database session

    Returns:
        User information dictionary

    Raises:
        HTTPException: If user is not active or not found
    """
    from services.user.repositories.user_repo import UserRepository

    user_repo = UserRepository(db)
    user = user_repo.find_by_id(current_user["user_id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return current_user


# =============================================================================
# ROLE-BASED AUTHORIZATION
# =============================================================================

class RoleChecker:
    """
    Dependency class to check user roles
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_active_user)):
        if current_user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}"
            )
        return current_user


# Predefined role checkers
require_admin = RoleChecker(["admin"])
require_admin_or_manager = RoleChecker(["admin", "manager"])
require_any_role = RoleChecker(["admin", "manager", "user"])


# =============================================================================
# ORGANIZATION ACCESS CONTROL
# =============================================================================

class OrganizationAccessChecker:
    """
    Dependency class to check organization access

    Rules:
    - Admin: Can access all organizations
    - Manager/User: Can only access their own organization
    """

    def __call__(
        self,
        org_id: int,
        current_user: dict = Depends(get_current_active_user)
    ):
        # Admin can access any organization
        if current_user["role"] == "admin":
            return current_user

        # Manager/User can only access their own organization
        if current_user["organization_id"] != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only access your own organization."
            )

        return current_user


require_org_access = OrganizationAccessChecker()


# =============================================================================
# RESOURCE OWNERSHIP CHECKER
# =============================================================================

class ResourceOwnershipChecker:
    """
    Dependency class to check resource ownership

    Rules:
    - Admin: Can access any resource
    - Manager: Can access resources in their organization
    - User: Can only access their own resources
    """

    def __call__(
        self,
        resource_user_id: int,
        resource_org_id: Optional[int],
        current_user: dict = Depends(get_current_active_user)
    ):
        # Admin can access anything
        if current_user["role"] == "admin":
            return current_user

        # Manager can access resources in their org
        if current_user["role"] == "manager":
            if resource_org_id != current_user["organization_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Resource belongs to different organization."
                )
            return current_user

        # User can only access their own resources
        if current_user["role"] == "user":
            if resource_user_id != current_user["user_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You can only access your own resources."
                )
            return current_user

        # Fallback: deny access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )


require_resource_access = ResourceOwnershipChecker()


# =============================================================================
# OPTIONAL AUTHENTICATION
# =============================================================================

async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    Optional authentication - returns user if token present, None otherwise
    Useful for endpoints that work for both authenticated and anonymous users

    Args:
        authorization: Optional Bearer token

    Returns:
        User information dictionary or None
    """
    if not authorization:
        return None

    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        user_info = extract_user_from_token(token)
        return user_info
    except:
        return None


# =============================================================================
# PERMISSION HELPERS
# =============================================================================

def can_manage_user(current_user: dict, target_user_org_id: Optional[int]) -> bool:
    """
    Check if current user can manage target user

    Args:
        current_user: Current authenticated user
        target_user_org_id: Organization ID of target user

    Returns:
        True if user can manage, False otherwise
    """
    # Admin can manage any user
    if current_user["role"] == "admin":
        return True

    # Manager can manage users in their organization
    if current_user["role"] == "manager":
        return target_user_org_id == current_user["organization_id"]

    # Regular users cannot manage other users
    return False


def can_manage_organization(current_user: dict, target_org_id: int) -> bool:
    """
    Check if current user can manage target organization

    Args:
        current_user: Current authenticated user
        target_org_id: Target organization ID

    Returns:
        True if user can manage, False otherwise
    """
    # Only admins can manage organizations
    return current_user["role"] == "admin"


def can_view_audit_logs(current_user: dict, log_org_id: Optional[int]) -> bool:
    """
    Check if current user can view audit log

    Args:
        current_user: Current authenticated user
        log_org_id: Organization ID of audit log

    Returns:
        True if user can view, False otherwise
    """
    # Admin can view all logs
    if current_user["role"] == "admin":
        return True

    # Manager can view logs from their organization
    if current_user["role"] == "manager":
        return log_org_id == current_user["organization_id"]

    # Regular users cannot view audit logs
    return False
