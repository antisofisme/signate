"""
Auth API Routes
HTTP endpoints for authentication

Updated to use centralized utilities:
- shared.errors for error handling
- shared.responses for standardized responses
- shared.logging for audit trails
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.config import settings
from shared.api_routes import AuthRoutes
from shared.errors import handle_errors
from shared.responses import success_response
from shared.logging import RequestLogger, AuditLogger
from shared.rate_limiter import rate_limit
import time

from .dtos import (
    LoginRequest, RegisterRequest, LoginResponse, UserResponse,
    OrganizationResponse, UserResponse as UserResponseDTO,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse
)
from .use_cases.login import LoginUseCase
from .use_cases.register import RegisterUseCase
from .use_cases.forgot_password import ForgotPasswordUseCase
from .use_cases.reset_password import ResetPasswordUseCase
from .use_cases.logout import LogoutUseCase
from .repositories.user_repo import UserRepository
from .repositories.organization_repo import OrganizationRepository
from services.session.repositories.session_repo import SessionRepository
from services.rbac.repositories.role_repo import RoleRepository  # P0-3: For permissions in JWT
from shared.auth import get_current_user, CurrentUser


router = APIRouter()

# Initialize loggers
request_logger = RequestLogger()
audit_logger = AuditLogger()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository instance"""
    return UserRepository(db)


def get_organization_repository(db: Session = Depends(get_db)) -> OrganizationRepository:
    """Get organization repository instance"""
    return OrganizationRepository(db)


def get_session_repository(db: Session = Depends(get_db)) -> SessionRepository:
    """Get session repository instance"""
    return SessionRepository(db)


def get_role_repository(db: Session = Depends(get_db)) -> RoleRepository:
    """Get role repository instance (P0-3: for embedding permissions in JWT)"""
    return RoleRepository(db)


def get_login_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
    org_repo: OrganizationRepository = Depends(get_organization_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    role_repo: RoleRepository = Depends(get_role_repository)
) -> LoginUseCase:
    """Get login use case instance with role repository (P0-3)"""
    return LoginUseCase(
        user_repository=user_repo,
        organization_repository=org_repo,
        session_repository=session_repo,
        role_repository=role_repo,  # P0-3: For fetching permissions during login
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


def get_register_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
    org_repo: OrganizationRepository = Depends(get_organization_repository)
) -> RegisterUseCase:
    """Get register use case instance with org validation (Critical Fix)"""
    return RegisterUseCase(
        user_repository=user_repo,
        organization_repository=org_repo
    )


def get_forgot_password_use_case(
    user_repo: UserRepository = Depends(get_user_repository)
) -> ForgotPasswordUseCase:
    """Get forgot password use case instance"""
    return ForgotPasswordUseCase(user_repository=user_repo)


def get_reset_password_use_case(
    user_repo: UserRepository = Depends(get_user_repository)
) -> ResetPasswordUseCase:
    """Get reset password use case instance"""
    return ResetPasswordUseCase(user_repository=user_repo)


def get_logout_use_case(
    session_repo: SessionRepository = Depends(get_session_repository)
) -> LogoutUseCase:
    """Get logout use case instance"""
    return LogoutUseCase(session_repository=session_repo)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(AuthRoutes.LOGIN)
@rate_limit(max_requests=5, window_seconds=300)  # 5 login attempts per 5 minutes
@handle_errors
def login(
    request_body: LoginRequest,
    http_request: Request,
    use_case: LoginUseCase = Depends(get_login_use_case)
):
    """
    Login endpoint

    Returns user data, JWT token, and accessible organizations
    Uses centralized error handling and logging
    """
    start_time = time.time()

    # Extract client information for session tracking
    ip_address = http_request.client.host if http_request.client else "unknown"
    user_agent = http_request.headers.get("user-agent", "unknown")

    # Parse device info from user agent (simple parsing)
    device_info = {
        "user_agent": user_agent,
        "platform": "unknown"
    }

    # Simple platform detection
    if user_agent:
        ua_lower = user_agent.lower()
        if "windows" in ua_lower:
            device_info["platform"] = "Windows"
        elif "mac" in ua_lower or "darwin" in ua_lower:
            device_info["platform"] = "macOS"
        elif "linux" in ua_lower:
            device_info["platform"] = "Linux"
        elif "android" in ua_lower:
            device_info["platform"] = "Android"
        elif "ios" in ua_lower or "iphone" in ua_lower or "ipad" in ua_lower:
            device_info["platform"] = "iOS"

    # Execute login use case (will raise AuthenticationError if fails)
    result = use_case.execute(
        username=request_body.username,
        password=request_body.password,
        ip_address=ip_address,
        user_agent=user_agent,
        device_info=device_info
    )

    # Convert to response models
    user_response = UserResponseDTO(
        id=result["user"].id,
        username=result["user"].username,
        email=result["user"].email,
        full_name=result["user"].full_name,
        role=result["user"].role,
        organization_id=result["user"].organization_id,
        is_active=result["user"].is_active
    )

    org_responses = [
        OrganizationResponse.model_validate(org)
        for org in result["organizations"]
    ]

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log successful login request
    request_logger.log_request(
        method="POST",
        path=AuthRoutes.LOGIN,
        status_code=200,
        duration_ms=duration_ms,
        user_id=result["user"].id
    )

    # Audit log
    audit_logger.log_action(
        user_id=result["user"].id,
        action="auth.login",
        resource_type="user",
        resource_id=result["user"].id,
        details={
            "username": request_body.username,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    # Return standardized success response
    return success_response(
        data={
            "user": user_response,
            "token": result["token"],
            "organizations": org_responses
        },
        message=f"Selamat datang, {result['user'].full_name or result['user'].username}!"
    )


@router.post(AuthRoutes.REGISTER, status_code=status.HTTP_201_CREATED)
@rate_limit(max_requests=3, window_seconds=3600)  # 3 registration attempts per hour
@handle_errors
def register(
    request_body: RegisterRequest,
    http_request: Request,
    use_case: RegisterUseCase = Depends(get_register_use_case)
):
    """
    Register new user

    Creates new user account
    Uses centralized validation, error handling, and logging
    """
    start_time = time.time()

    # Execute register use case (will raise ValidationError if fails)
    user = use_case.execute(
        username=request_body.username,
        email=request_body.email,
        password=request_body.password,
        full_name=request_body.full_name,
        organization_id=request_body.organization_id
    )

    # Convert to response model
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        is_active=user.is_active
    )

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log successful registration request
    request_logger.log_request(
        method="POST",
        path=AuthRoutes.REGISTER,
        status_code=201,
        duration_ms=duration_ms,
        user_id=user.id
    )

    # Audit log
    audit_logger.log_action(
        user_id=user.id,
        action="auth.register",
        resource_type="user",
        resource_id=user.id,
        details={
            "username": request_body.username,
            "email": request_body.email,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    # Return standardized success response
    return success_response(
        data=user_response,
        message="Registrasi berhasil! Silakan login."
    )


@router.post(AuthRoutes.FORGOT_PASSWORD, response_model=ForgotPasswordResponse)
@rate_limit(max_requests=3, window_seconds=3600)  # 3 attempts per hour
@handle_errors
def forgot_password(
    request_body: ForgotPasswordRequest,
    http_request: Request,
    use_case: ForgotPasswordUseCase = Depends(get_forgot_password_use_case),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Forgot password endpoint

    Initiates password reset process. Generates a reset token.
    In production, this would send an email with the reset link.
    For development/testing, the token is returned in the response.

    Security: Returns same message regardless of whether email exists (prevents email enumeration)
    P0-4: Added audit logging for security tracking
    """
    start_time = time.time()

    # Execute use case
    result = use_case.execute(email=request_body.email)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request (don't log user_id since we don't want to reveal if email exists)
    request_logger.log_request(
        method="POST",
        path=AuthRoutes.FORGOT_PASSWORD,
        status_code=200,
        duration_ms=duration_ms
    )

    # P0-4: Audit log for password reset request (security event)
    # Log regardless of whether email exists (but don't reveal user existence)
    # Use a system user_id (0) for audit when actual user unknown
    user = user_repo.find_by_email(request_body.email)
    audit_logger.log_action(
        user_id=user.id if user else 0,  # 0 = system/unknown user
        action="auth.forgot_password_request",
        resource_type="user",
        resource_id=user.id if user else 0,
        details={
            "email_requested": request_body.email[:3] + "***" if request_body.email else None,  # Partially mask email
            "ip_address": http_request.client.host if http_request.client else None,
            "token_generated": result.get("reset_token") is not None
        }
    )

    # Return response
    return ForgotPasswordResponse(
        message=result["message"],
        reset_token=result.get("reset_token")  # Only included in development
    )


@router.post(AuthRoutes.RESET_PASSWORD, response_model=ResetPasswordResponse)
@rate_limit(max_requests=5, window_seconds=3600)  # 5 attempts per hour
@handle_errors
def reset_password(
    request_body: ResetPasswordRequest,
    http_request: Request,
    use_case: ResetPasswordUseCase = Depends(get_reset_password_use_case)
):
    """
    Reset password endpoint

    Completes password reset using a valid token.
    Validates token and updates user's password.
    P0-4: Added audit logging for security tracking
    """
    start_time = time.time()

    # Decode token to get user_id for audit logging (before consuming it)
    from shared.password_reset import get_password_reset_manager
    reset_manager = get_password_reset_manager()
    token_info = reset_manager.validate_token(request_body.token)
    user_id = token_info.get("user_id") if token_info else None

    # Execute use case (will raise ValidationError if token invalid)
    result = use_case.execute(
        token=request_body.token,
        new_password=request_body.new_password
    )

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="POST",
        path=AuthRoutes.RESET_PASSWORD,
        status_code=200,
        duration_ms=duration_ms,
        user_id=user_id
    )

    # P0-4: Audit log for password reset (critical security event)
    if user_id:
        audit_logger.log_action(
            user_id=user_id,
            action="auth.reset_password",
            resource_type="user",
            resource_id=user_id,
            details={
                "ip_address": http_request.client.host if http_request.client else None,
                "method": "token_reset"  # Distinguish from change_password (authenticated)
            }
        )

    # Return response
    return ResetPasswordResponse(
        message=result["message"]
    )


@router.get(AuthRoutes.ME)
@handle_errors
def get_current_user_info(
    http_request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    org_repo: OrganizationRepository = Depends(get_organization_repository)
):
    """
    Get current authenticated user info

    Returns the currently logged in user's profile data.
    Requires valid JWT token in Authorization header.
    """
    # Get full user data from database
    user = user_repo.get_by_id(current_user.id)
    if not user:
        from shared.errors import NotFoundError
        raise NotFoundError("User not found")

    # Get organization if exists
    organization = None
    if user.organization_id:
        organization = org_repo.get_by_id(user.organization_id)

    user_response = UserResponseDTO(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        is_active=user.is_active
    )

    return success_response(
        data={
            "user": user_response,
            "organization": OrganizationResponse.model_validate(organization) if organization else None
        },
        message="User info retrieved successfully"
    )


@router.post(AuthRoutes.REFRESH)
@handle_errors
def refresh_token(
    http_request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Refresh JWT token

    Generates a new JWT token using the current valid token.
    The old token remains valid until its expiration.
    Requires valid JWT token in Authorization header.
    """
    from datetime import datetime, timedelta, timezone
    from jose import jwt

    # Get user from database to ensure still active
    user = user_repo.get_by_id(current_user.id)
    if not user or not user.is_active:
        from shared.errors import AuthenticationError
        raise AuthenticationError("User account is disabled or not found")

    # Create new token with extended expiration
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "organization_id": user.organization_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }

    new_token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # Update session with new token
    auth_header = http_request.headers.get("authorization", "")
    old_token = auth_header.replace("Bearer ", "")
    session_repo.update_token(old_token, new_token)

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="auth.refresh_token",
        resource_type="user",
        resource_id=current_user.id,
        details={
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return success_response(
        data={"token": new_token},
        message="Token refreshed successfully"
    )


@router.post(AuthRoutes.LOGOUT)
@handle_errors
def logout(
    http_request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    use_case: LogoutUseCase = Depends(get_logout_use_case)
):
    """
    Logout endpoint

    Revokes current session by invalidating the JWT token.
    After logout, the token cannot be used for authentication until re-login.

    Requires valid JWT token in Authorization header.
    """
    start_time = time.time()

    # Extract token from Authorization header
    auth_header = http_request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "")

    # Execute logout use case
    result = use_case.execute(token)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log successful logout request
    request_logger.log_request(
        method="POST",
        path=AuthRoutes.LOGOUT,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user.id
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="auth.logout",
        resource_type="user",
        resource_id=current_user.id,
        details={
            "username": current_user.username,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    # Return standardized success response
    return success_response(
        data=result,
        message=result["message"]
    )
