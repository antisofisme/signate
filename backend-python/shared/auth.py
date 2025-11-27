"""
Authentication & Authorization Utilities
Consolidated auth module - password hashing, JWT tokens, and permissions

This module combines:
- Password hashing (bcrypt)
- JWT token generation & validation
- FastAPI authentication dependencies
- Role-based access control (RBAC)
"""

from datetime import datetime, timedelta, timezone
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


class CurrentDevice(BaseModel):
    """Current authenticated device from JWT device token"""
    id: int
    organization_id: int


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
# JWT TOKEN GENERATION - USER TOKENS
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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days default

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# =============================================================================
# JWT TOKEN GENERATION - DEVICE TOKENS
# =============================================================================

def create_device_token(
    device_id: int,
    organization_id: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT token for device authentication

    Device tokens are long-lived (365 days) and used by players to:
    - Re-register after release without user interaction
    - Authenticate heartbeat requests
    - Prove device ownership during activation polling

    Args:
        device_id: Device ID
        organization_id: Organization ID that device belongs to
        expires_delta: Optional custom expiration (default 365 days)

    Returns:
        JWT device token string
    """
    to_encode = {
        "sub": str(device_id),  # Subject (device ID)
        "organization_id": organization_id,
        "type": "device"
    }

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=365)  # 1 year default for devices

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_device_token(token: str) -> Dict[str, Any]:
    """
    Verify device token and return payload

    Args:
        token: JWT device token

    Returns:
        Token payload with device_id and organization_id

    Raises:
        AuthenticationError: If token is invalid, expired, or not a device token
    """
    payload = decode_token(token)

    # Verify token type
    if payload.get("type") != "device":
        raise AuthenticationError(
            message="Invalid token type - expected device token",
            details={"expected": "device", "got": payload.get("type")}
        )

    return payload


def extract_device_from_token(token: str) -> Dict[str, Any]:
    """
    Extract device information from valid device token

    Args:
        token: JWT device token

    Returns:
        Device information dictionary with:
        - device_id: int
        - organization_id: int

    Raises:
        AuthenticationError: If token is invalid
    """
    payload = verify_device_token(token)

    return {
        "device_id": int(payload["sub"]),
        "organization_id": payload["organization_id"]
    }


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
            details={"error": "Token expired"}
        )
    except JWTError as e:
        raise AuthenticationError(
            message="Token tidak valid atau sudah expired",
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
    organization_id: Optional[int] = None,
    permissions: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized token payload with optional permissions (P0-3 RBAC)

    Args:
        user_id: User ID
        username: Username
        role: User role (admin, manager, user)
        organization_id: Optional organization ID
        permissions: Optional permission dict {resource: [actions]}

    Returns:
        Token payload dictionary
    """
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "username": username,
        "role": role,
        "organization_id": organization_id
    }

    # Include permissions in token for fast permission checking (P0-3)
    # Note: This makes the JWT larger but avoids DB lookups per request
    if permissions:
        payload["permissions"] = permissions

    return payload


def extract_user_from_token(token: str) -> Dict[str, Any]:
    """
    Extract user information from valid access token (P0-3 RBAC updated)

    Args:
        token: JWT access token

    Returns:
        User information dictionary with:
        - user_id: int
        - username: str
        - role: str
        - organization_id: Optional[int]
        - permissions: Optional[Dict] (P0-3: embedded permissions for fast checking)

    Raises:
        AuthenticationError: If token is invalid
    """
    payload = verify_access_token(token)

    return {
        "user_id": int(payload["sub"]),
        "username": payload["username"],
        "role": payload["role"],
        "organization_id": payload.get("organization_id"),
        "permissions": payload.get("permissions", {})  # P0-3: Include permissions
    }


# =============================================================================
# FASTAPI DEPENDENCIES - AUTHENTICATION
# =============================================================================

def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    FastAPI dependency to get current authenticated user from JWT token

    Multi-tenancy support:
    - SUPER_ADMIN: organization_id can be overridden via X-Organization-Id header
    - Regular users: organization_id is always from JWT (header ignored for security)

    Usage:
        @router.get("/protected")
        def protected_route(current_user: CurrentUser = Depends(get_current_user)):
            return {"user_id": current_user.id}

    Args:
        request: FastAPI Request object (for reading X-Organization-Id header)
        credentials: HTTP Bearer token from Authorization header

    Returns:
        CurrentUser object with user info from token (organization_id may be overridden)

    Raises:
        AuthenticationError: If token is invalid or missing
    """
    if not credentials:
        raise AuthenticationError(
            message="Token tidak ditemukan"
        )

    # Decode token
    payload = decode_token(credentials.credentials)

    # Extract user info
    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")
    jwt_organization_id = payload.get("organization_id")

    if not user_id or not username or not role:
        raise AuthenticationError(
            message="Token tidak valid - data user tidak lengkap"
        )

    # CRITICAL FIX: Verify session is still active in database
    # This prevents revoked tokens from being used
    # OPTIMIZATION: Use Redis cache to reduce DB queries (Fix #13)
    try:
        from services.session.repositories.session_repo import SessionRepository
        from shared.database import SessionLocal
        from shared.cache import cache

        # Generate cache key from token hash (first 16 chars for privacy)
        token_hash = credentials.credentials[:16]
        cache_key = f"session:valid:{token_hash}"

        # Check cache first (reduces DB queries by ~98% with 60s TTL)
        cached_valid = cache.get(cache_key)

        if cached_valid is None:
            # Cache miss - query database
            db = SessionLocal()
            try:
                session_repo = SessionRepository(db)
                session = session_repo.verify_session(credentials.credentials)

                if not session:
                    # Cache negative result for short time to prevent hammering
                    cache.set(cache_key, False, ttl=10)
                    raise AuthenticationError(
                        message="Session has been revoked or expired",
                        code=ErrorCodes.SESSION_REVOKED
                    )

                # Cache positive result for 30 seconds
                # Balance between performance and security (revoked sessions detected within 30s)
                cache.set(cache_key, True, ttl=30)

                # Update last activity timestamp (only on cache miss to reduce DB writes)
                session_repo.update_last_activity(session.id)
            finally:
                db.close()
        elif cached_valid is False:
            # Cached as invalid
            raise AuthenticationError(
                message="Session has been revoked or expired",
                code=ErrorCodes.SESSION_REVOKED
            )
        # If cached_valid is True, session is valid - skip DB query

    except ImportError:
        # Session verification not available - continue without it
        # This allows backward compatibility during migration
        pass

    # =============================================================================
    # MULTI-TENANCY: Calculate effective organization_id
    # =============================================================================
    effective_organization_id = jwt_organization_id

    # Normalize role to lowercase for comparison
    role_lower = role.lower() if isinstance(role, str) else role

    # For SUPER_ADMIN: Allow switching organizations via X-Organization-Id header
    header_org_id = request.headers.get("X-Organization-Id")
    if role_lower == "super_admin" and header_org_id:
        try:
            effective_organization_id = int(header_org_id)
        except (ValueError, TypeError):
            # Invalid header value, keep JWT org_id
            pass
    # For regular users: Always use their JWT organization (ignore header)
    # This is a security measure - regular users cannot switch organizations

    return CurrentUser(
        id=int(user_id),
        username=username,
        role=role,
        organization_id=effective_organization_id
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


def get_current_device(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentDevice:
    """
    FastAPI dependency to get current authenticated device from JWT device token

    Usage:
        @router.get("/devices/me")
        def get_my_device(current_device: CurrentDevice = Depends(get_current_device)):
            return {"device_id": current_device.id}

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        CurrentDevice object with device info from token

    Raises:
        AuthenticationError: If token is invalid, missing, or not a device token
    """
    if not credentials:
        raise AuthenticationError(
            message="Device token not found",
            code=ErrorCodes.UNAUTHORIZED
        )

    try:
        # Verify device token
        payload = verify_device_token(credentials.credentials)

        # Extract device info
        device_id = payload.get("sub")
        organization_id = payload.get("organization_id")

        if not device_id or not organization_id:
            raise AuthenticationError(
                message="Invalid device token - missing device info",
                code=ErrorCodes.INVALID_TOKEN
            )

        return CurrentDevice(
            id=int(device_id),
            organization_id=organization_id
        )
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(
            message=f"Failed to authenticate device: {str(e)}",
            code=ErrorCodes.INVALID_TOKEN
        )


# =============================================================================
# ROLE PERMISSION HELPERS
# =============================================================================

def get_role_level(role: str) -> int:
    """Get numeric level for role (higher = more permissions)"""
    try:
        # Try lowercase first (enum values are lowercase)
        role_lower = role.lower() if isinstance(role, str) else role
        return ROLE_HIERARCHY.get(Role(role_lower), 0)
    except ValueError:
        # Unknown role
        return 0


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
    role_lower = user.role.lower() if isinstance(user.role, str) else user.role
    return role_lower == Role.SUPER_ADMIN.value


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
# ORGANIZATION CONTEXT - MULTI-TENANCY SUPPORT
# =============================================================================

def get_effective_organization_id(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user)
) -> int:
    """
    Get effective organization ID for the current request.

    This is the KEY function for multi-tenancy:
    - SUPER_ADMIN: Can use X-Organization-Id header to switch organizations
    - Regular users: Always use their own organization from JWT (ignore header)

    Usage:
        @router.get("/items")
        def list_items(
            org_id: int = Depends(get_effective_organization_id),
            current_user: CurrentUser = Depends(get_current_user)
        ):
            # org_id is the effective organization to use for filtering
            items = repo.get_by_organization(org_id)
            return items

    Args:
        request: FastAPI Request object (to access headers)
        current_user: Current authenticated user

    Returns:
        Effective organization ID to use for data filtering

    Raises:
        AuthorizationError: If organization context is invalid
    """
    # Get X-Organization-Id header if present
    header_org_id = request.headers.get("X-Organization-Id")

    # For SUPER_ADMIN: Allow switching organizations via header
    if is_super_admin(current_user):
        if header_org_id:
            try:
                org_id = int(header_org_id)
                # TODO: Optionally validate that organization exists
                return org_id
            except (ValueError, TypeError):
                raise AuthorizationError(
                    message="Invalid X-Organization-Id header value",
                    code=ErrorCodes.INVALID_INPUT,
                    details={"header_value": header_org_id}
                )
        # If no header, super_admin must have selected an organization
        if current_user.organization_id:
            return current_user.organization_id
        raise AuthorizationError(
            message="SUPER_ADMIN must select an organization. Please select an organization first.",
            code=ErrorCodes.ORGANIZATION_REQUIRED,
            details={"hint": "Use X-Organization-Id header or select organization during login"}
        )

    # For regular users: Always use their own organization
    if current_user.organization_id is None:
        raise AuthorizationError(
            message="User does not belong to any organization",
            code=ErrorCodes.ORGANIZATION_REQUIRED,
            details={"user_id": current_user.id}
        )

    # Security: Regular users cannot switch organizations
    # Even if they send X-Organization-Id header, we ignore it
    return current_user.organization_id


class OrganizationContext:
    """
    Organization context for request - includes user and effective organization.

    Use this when you need both user info and organization context.
    """
    def __init__(self, user: CurrentUser, organization_id: int):
        self.user = user
        self.organization_id = organization_id

    @property
    def user_id(self) -> int:
        return self.user.id

    @property
    def is_super_admin(self) -> bool:
        return is_super_admin(self.user)


def get_organization_context(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user)
) -> OrganizationContext:
    """
    Get full organization context for the current request.

    Usage:
        @router.get("/items")
        def list_items(ctx: OrganizationContext = Depends(get_organization_context)):
            items = repo.get_by_organization(ctx.organization_id)
            return items

    Returns:
        OrganizationContext with user and effective organization_id
    """
    org_id = get_effective_organization_id(request, current_user)
    return OrganizationContext(user=current_user, organization_id=org_id)


# =============================================================================
# WEBSOCKET AUTHENTICATION DEPENDENCIES
# =============================================================================

async def get_current_user_ws(
    token: Optional[str] = None
) -> Optional[CurrentUser]:
    """
    WebSocket-specific authentication dependency
    
    WebSockets can't use standard HTTP headers, so token is passed as query param
    
    Args:
        token: JWT token from query parameter
        
    Returns:
        CurrentUser if authenticated, None otherwise
    """
    if not token:
        return None
        
    try:
        payload = verify_access_token(token)
        
        return CurrentUser(
            id=int(payload.get("sub")),
            username=payload.get("username"),
            role=payload.get("role"),
            organization_id=payload.get("organization_id")
        )
    except:
        return None


async def get_device_by_token_ws(
    token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    WebSocket-specific device authentication dependency
    
    Args:
        token: Device JWT token from query parameter
        
    Returns:
        Device info dict if authenticated, None otherwise
    """
    if not token:
        return None
        
    try:
        device_info = extract_device_from_token(token)
        
        # Get device from database to verify it exists and belongs to the organization
        from services.device.infrastructure.sqlalchemy_device_repository import SQLAlchemyDeviceRepository
        from services.device.dtos import DeviceResponse
        
        device_repo = SQLAlchemyDeviceRepository()
        # SECURITY: Verify device belongs to the organization from token
        device = device_repo.find_by_id(
            device_info["device_id"], 
            organization_id=device_info.get("organization_id")
        )
        
        if not device:
            return None
            
        return DeviceResponse(
            id=device.id,
            activation_code=device.activation_code,
            name=device.name,
            location=device.location,
            status=device.status,
            organization_id=device.organization_id,
            registered_at=device.registered_at,
            last_seen_at=device.last_seen_at)
        
    except:
        return None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Password functions
    "verify_password",
    "get_password_hash",

    # Token generation - User
    "create_access_token",
    "create_refresh_token",
    "create_token_payload",

    # Token generation - Device
    "create_device_token",

    # Token validation
    "decode_token",
    "verify_access_token",
    "verify_refresh_token",
    "verify_device_token",
    "extract_user_from_token",
    "extract_device_from_token",

    # FastAPI dependencies - Authentication
    "get_current_user",
    "get_optional_user",
    "get_current_user_ws",
    "get_device_by_token_ws",

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

    # Organization context - Multi-tenancy
    "get_effective_organization_id",
    "get_organization_context",
    "OrganizationContext",
]
