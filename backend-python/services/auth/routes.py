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
import time

from .dtos import (
    LoginRequest, RegisterRequest, LoginResponse, UserResponse,
    OrganizationResponse, UserResponse as UserResponseDTO
)
from .use_cases.login import LoginUseCase
from .use_cases.register import RegisterUseCase
from .repositories.user_repo import UserRepository
from .repositories.organization_repo import OrganizationRepository


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


def get_login_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
    org_repo: OrganizationRepository = Depends(get_organization_repository)
) -> LoginUseCase:
    """Get login use case instance"""
    return LoginUseCase(
        user_repository=user_repo,
        organization_repository=org_repo,
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


def get_register_use_case(
    user_repo: UserRepository = Depends(get_user_repository)
) -> RegisterUseCase:
    """Get register use case instance"""
    return RegisterUseCase(user_repository=user_repo)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(AuthRoutes.LOGIN)
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

    # Execute login use case (will raise AuthenticationError if fails)
    result = use_case.execute(
        username=request_body.username,
        password=request_body.password
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
