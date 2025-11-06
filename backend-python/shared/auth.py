"""
Authentication & Authorization Utilities
Consolidated auth module - password hashing, JWT tokens, and permissions

This module combines:
- Password hashing (bcrypt)
- JWT token generation & validation
- FastAPI authentication dependencies
- Role-based access control (RBAC)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from enum import Enum

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from shared.config import settings
from shared.errors import AuthenticationError, AuthorizationError, ErrorCodes


# =============================================================================
# CONFIGURATION
# =============================================================================

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme for FastAPI
security = HTTPBearer()


# =============================================================================
# MODELS
# =============================================================================

class CurrentUser(BaseModel):
    """Current authenticated user from JWT token"""
    id: int
    username: str
    role: str
    organization_id: Optional[int] = None


class Role(str, Enum):
    """User roles in hierarchical order"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"


# Role hierarchy: higher roles have all permissions of lower roles
ROLE_HIERARCHY = {
    Role.SUPER_ADMIN: 4,
    Role.ADMIN: 3,
    Role.MANAGER: 2,
    Role.VIEWER: 1
}


# =============================================================================
# PASSWORD HASHING
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed password

    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


# =============================================================================
# JWT TOKEN GENERATION
# =============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token

    Args:
        data: Payload data (user_id, username, role, etc.)
        expires_delta: Optional custom expiration time

    Returns:
        JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token

    Args:
        data: Payload data (usually just user_id)
        expires_delta: Optional custom expiration time

    Returns:
        JWT refresh token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days default

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# =============================================================================
# JWT TOKEN VALIDATION
# =============================================================================

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload dictionary

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError(
            message="Token sudah expired",
            code=ErrorCodes.INVALID_TOKEN,
            details={"error": "Token expired"}
        )
    except JWTError as e:
        raise AuthenticationError(
            message="Token tidak valid atau sudah expired",
            code=ErrorCodes.INVALID_TOKEN,
            details={"error": str(e)}
        )


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verify access token and return payload

    Args:
        token: JWT access token

    Returns:
        Token payload

    Raises:
        AuthenticationError: If token is invalid, expired, or not an access token
    """
    payload = decode_token(token)

    # Verify token type
    if payload.get("type") != "access":
        raise AuthenticationError(
            message="Invalid token type",
            code=ErrorCodes.INVALID_TOKEN,
            details={"expected": "access", "got": payload.get("type")}
        )

    return payload


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """
    Verify refresh token and return payload

    Args:
        token: JWT refresh token

    Returns:
        Token payload

    Raises:
        AuthenticationError: If token is invalid, expired, or not a refresh token
    """
    payload = decode_token(token)

    # Verify token type
    if payload.get("type") != "refresh":
        raise AuthenticationError(
            message="Invalid token type",
            code=ErrorCodes.INVALID_TOKEN,
            details={"expected": "refresh", "got": payload.get("type")}
        )

    return payload


# =============================================================================
# TOKEN PAYLOAD HELPERS
# =============================================================================

def create_token_payload(
    user_id: int,
    username: str,
    role: str,
    organization_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create standardized token payload

    Args:
        user_id: User ID
        username: Username
        role: User role (admin, manager, user)
        organization_id: Optional organization ID

    Returns:
        Token payload dictionary
    """
    return {
        "sub": str(user_id),  # Subject (user ID)
        "username": username,
        "role": role,
        "organization_id": organization_id
    }


def extract_user_from_token(token: str) -> Dict[str, Any]:
    """
    Extract user information from valid access token

    Args:
        token: JWT access token

    Returns:
        User information dictionary with:
        - user_id: int
        - username: str
        - role: str
        - organization_id: Optional[int]

    Raises:
        AuthenticationError: If token is invalid
    """
    payload = verify_access_token(token)

    return {
        "user_id": int(payload["sub"]),
        "username": payload["username"],
        "role": payload["role"],
        "organization_id": payload.get("organization_id")
    }


# =============================================================================
# FASTAPI DEPENDENCIES - AUTHENTICATION
# =============================================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    FastAPI dependency to get current authenticated user from JWT token

    Usage:
        @router.get("/protected")
        def protected_route(current_user: CurrentUser = Depends(get_current_user)):
            return {"user_id": current_user.id}

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        CurrentUser object with user info from token

    Raises:
        AuthenticationError: If token is invalid or missing
    """
    if not credentials:
        raise AuthenticationError(
            message="Token tidak ditemukan",
            code=ErrorCodes.MISSING_TOKEN
        )

    # Decode token
    payload = decode_token(credentials.credentials)

    # Extract user info
    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")
    organization_id = payload.get("organization_id")

    if not user_id or not username or not role:
        raise AuthenticationError(
            message="Token tidak valid - data user tidak lengkap",
            code=ErrorCodes.INVALID_TOKEN
        )

    return CurrentUser(
        id=int(user_id),
        username=username,
        role=role,
        organization_id=organization_id
    )


def get_optional_user(request: Request) -> Optional[CurrentUser]:
    """
    Get current user from token, but don't raise error if missing
    Useful for endpoints that work both authenticated and unauthenticated

    Args:
        request: FastAPI Request object

    Returns:
        CurrentUser if token is valid, None otherwise
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        payload = decode_token(token)

        return CurrentUser(
            id=int(payload.get("sub")),
            username=payload.get("username"),
            role=payload.get("role"),
            organization_id=payload.get("organization_id")
        )
    except:
        return None


# =============================================================================
# ROLE PERMISSION HELPERS
# =============================================================================

def get_role_level(role: str) -> int:
    """Get numeric level for role (higher = more permissions)"""
    return ROLE_HIERARCHY.get(Role(role), 0)


def has_role(user: CurrentUser, required_role: str) -> bool:
    """
    Check if user has required role or higher

    Args:
        user: Current user
        required_role: Minimum required role

    Returns:
        True if user has required role or higher
    """
    user_level = get_role_level(user.role)
    required_level = get_role_level(required_role)
    return user_level >= required_level


def is_super_admin(user: CurrentUser) -> bool:
    """Check if user is super admin"""
    return user.role == Role.SUPER_ADMIN


def is_admin(user: CurrentUser) -> bool:
    """Check if user is admin or higher"""
    return has_role(user, Role.ADMIN)


def is_manager(user: CurrentUser) -> bool:
    """Check if user is manager or higher"""
    return has_role(user, Role.MANAGER)


def is_same_organization(user: CurrentUser, organization_id: int) -> bool:
    """Check if user belongs to the specified organization"""
    return user.organization_id == organization_id


def can_access_organization(user: CurrentUser, organization_id: int) -> bool:
    """
    Check if user can access resources from specified organization

    Rules:
    - super_admin: can access all organizations
    - admin: can access all organizations
    - manager/viewer: can only access own organization
    """
    if is_admin(user):
        return True
    return is_same_organization(user, organization_id)


# =============================================================================
# FASTAPI DEPENDENCIES - AUTHORIZATION
# =============================================================================

def require_role(required_role: str) -> Callable:
    """
    FastAPI dependency to require minimum role

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(Role.ADMIN))])
        def admin_endpoint():
            return {"message": "Admin access"}

    Args:
        required_role: Minimum required role

    Returns:
        FastAPI dependency function
    """
    def check_role(current_user: CurrentUser = Depends(get_current_user)):
        if not has_role(current_user, required_role):
            raise AuthorizationError(
                message=f"Akses ditolak. Role minimal: {required_role}",
                code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
                details={
                    "user_role": current_user.role,
                    "required_role": required_role
                }
            )
        return current_user
    return check_role


def require_super_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    FastAPI dependency to require super admin role

    Usage:
        @router.post("/system-config")
        def update_system_config(current_user: CurrentUser = Depends(require_super_admin)):
            return {"message": "Config updated"}
    """
    if not is_super_admin(current_user):
        raise AuthorizationError(
            message="Akses ditolak. Hanya super admin yang diizinkan",
            code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
            details={"user_role": current_user.role}
        )
    return current_user


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    FastAPI dependency to require admin role or higher

    Usage:
        @router.post("/organizations")
        def create_organization(current_user: CurrentUser = Depends(require_admin)):
            return {"message": "Org created"}
    """
    if not is_admin(current_user):
        raise AuthorizationError(
            message="Akses ditolak. Role minimal: admin",
            code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
            details={"user_role": current_user.role}
        )
    return current_user


def require_manager(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    FastAPI dependency to require manager role or higher

    Usage:
        @router.get("/users")
        def list_users(current_user: CurrentUser = Depends(require_manager)):
            return {"users": []}
    """
    if not is_manager(current_user):
        raise AuthorizationError(
            message="Akses ditolak. Role minimal: manager",
            code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
            details={"user_role": current_user.role}
        )
    return current_user


def require_same_organization(
    organization_id: int,
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Check if user can access resources from specified organization

    Admins can access all organizations, others only their own

    Usage:
        @router.get("/organizations/{org_id}/users")
        def get_org_users(
            org_id: int,
            current_user: CurrentUser = Depends(lambda: require_same_organization(org_id))
        ):
            return {"users": []}
    """
    if not can_access_organization(current_user, organization_id):
        raise AuthorizationError(
            message="Akses ditolak. Anda tidak memiliki akses ke organization ini",
            code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
            details={
                "user_organization": current_user.organization_id,
                "requested_organization": organization_id
            }
        )
    return current_user


# =============================================================================
# PERMISSION CHECKER CLASS
# =============================================================================

class PermissionChecker:
    """
    Permission checker class for complex permission logic

    Usage:
        checker = PermissionChecker(current_user)
        if checker.can_edit_user(target_user_id):
            # Allow edit
        else:
            # Deny
    """

    def __init__(self, current_user: CurrentUser):
        self.current_user = current_user

    def can_edit_user(self, target_user_id: int, target_organization_id: int) -> bool:
        """Check if current user can edit target user"""
        # Super admin can edit anyone
        if is_super_admin(self.current_user):
            return True

        # Admin can edit users in any organization
        if is_admin(self.current_user):
            return True

        # Manager can edit users in same organization (but not admins)
        if is_manager(self.current_user):
            return is_same_organization(self.current_user, target_organization_id)

        # Viewer can't edit anyone
        return False

    def can_delete_user(self, target_user_id: int, target_organization_id: int, target_role: str) -> bool:
        """Check if current user can delete target user"""
        # Can't delete yourself
        if target_user_id == self.current_user.id:
            return False

        # Super admin can delete anyone (except self)
        if is_super_admin(self.current_user):
            return True

        # Admin can delete users in any organization (but not other admins)
        if is_admin(self.current_user):
            return not is_admin(CurrentUser(
                id=target_user_id,
                username="",
                role=target_role,
                organization_id=target_organization_id
            ))

        # Manager can delete users in same organization (but not admins/managers)
        if is_manager(self.current_user):
            is_same_org = is_same_organization(self.current_user, target_organization_id)
            is_lower_role = get_role_level(target_role) < get_role_level(Role.MANAGER)
            return is_same_org and is_lower_role

        # Viewer can't delete anyone
        return False

    def can_create_user_with_role(self, role: str, organization_id: int) -> bool:
        """Check if current user can create user with specified role"""
        # Super admin can create any role
        if is_super_admin(self.current_user):
            return True

        # Admin can create any role except super_admin
        if is_admin(self.current_user):
            return role != Role.SUPER_ADMIN

        # Manager can create manager/viewer in same organization
        if is_manager(self.current_user):
            is_same_org = is_same_organization(self.current_user, organization_id)
            is_allowed_role = role in [Role.MANAGER, Role.VIEWER]
            return is_same_org and is_allowed_role

        # Viewer can't create users
        return False

    def can_manage_organization(self, organization_id: Optional[int] = None) -> bool:
        """Check if current user can manage organizations"""
        # Only admins and above can manage organizations
        return is_admin(self.current_user)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Password functions
    "verify_password",
    "get_password_hash",

    # Token generation
    "create_access_token",
    "create_refresh_token",
    "create_token_payload",

    # Token validation
    "decode_token",
    "verify_access_token",
    "verify_refresh_token",
    "extract_user_from_token",

    # FastAPI dependencies - Authentication
    "get_current_user",
    "get_optional_user",

    # Models
    "CurrentUser",
    "Role",

    # Role checking functions
    "get_role_level",
    "has_role",
    "is_super_admin",
    "is_admin",
    "is_manager",
    "is_same_organization",
    "can_access_organization",

    # FastAPI dependencies - Authorization
    "require_role",
    "require_super_admin",
    "require_admin",
    "require_manager",
    "require_same_organization",

    # Permission checker
    "PermissionChecker",
]
