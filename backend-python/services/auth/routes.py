"""
Auth API Routes
HTTP endpoints for authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.config import settings
from shared.api_routes import AuthRoutes

from .dtos import (
    LoginRequest, RegisterRequest, LoginResponse, UserResponse,
    OrganizationResponse, UserResponse as UserResponseDTO
)
from .use_cases.login import LoginUseCase
from .use_cases.register import RegisterUseCase
from .repositories.user_repo import UserRepository
from .repositories.organization_repo import OrganizationRepository


router = APIRouter()


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

@router.post(AuthRoutes.LOGIN, response_model=LoginResponse)
def login(
    request: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case)
):
    """
    Login endpoint

    Returns user data, JWT token, and accessible organizations
    """
    try:
        result = use_case.execute(
            username=request.username,
            password=request.password
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

        return LoginResponse(
            success=True,
            data={
                "user": user_response,
                "token": result["token"],
                "organizations": org_responses
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post(AuthRoutes.REGISTER, response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    use_case: RegisterUseCase = Depends(get_register_use_case)
):
    """
    Register new user

    Creates new user account
    """
    try:
        user = use_case.execute(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            organization_id=request.organization_id
        )
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            organization_id=user.organization_id,
            is_active=user.is_active
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
