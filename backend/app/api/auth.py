"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from app.core.deps import get_current_user, get_current_active_user
from app.core.config import settings
from app.core.logging import StructuredLogger
from app.core.exceptions import UnauthorizedException, ForbiddenException, ValidationException
from app.schemas.common import success_response, APIResponse
from app.middleware.request_id import get_request_id
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, RefreshTokenRequest

logger = StructuredLogger(__name__)
router = APIRouter()


@router.post("/login")
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticate user and return JWT tokens

    Args:
        login_data: Login credentials (username and password)
        request: FastAPI request object (for request_id)
        db: Database session

    Returns:
        APIResponse: Access and refresh tokens wrapped in standardized response

    Raises:
        UnauthorizedException: If credentials are invalid
        ForbiddenException: If user is inactive
    """
    request_id = get_request_id(request)

    logger.info(
        "Login attempt",
        request_id=request_id,
        username=login_data.username
    )

    # Find user by username
    user = db.query(User).filter(User.username == login_data.username).first()

    # Verify user exists and password is correct
    if not user or not verify_password(login_data.password, user.password_hash):
        logger.warning(
            "Login failed - invalid credentials",
            request_id=request_id,
            username=login_data.username
        )
        raise UnauthorizedException(
            message="Incorrect username or password"
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(
            "Login failed - inactive user",
            request_id=request_id,
            username=login_data.username,
            user_id=user.id
        )
        raise ForbiddenException(
            message="Inactive user"
        )

    # Create tokens
    access_token = create_access_token(data={
        "user_id": user.id,
        "username": user.username,
        "is_superuser": user.is_superuser
    })

    refresh_token = create_refresh_token(data={
        "user_id": user.id
    })

    logger.info(
        "Login successful",
        request_id=request_id,
        user_id=user.id,
        username=user.username
    )

    token_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

    return success_response(
        data=token_data,
        request_id=request_id
    )


@router.post("/refresh")
def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token

    Args:
        refresh_data: Refresh token
        request: FastAPI request object (for request_id)
        db: Database session

    Returns:
        APIResponse: New access and refresh tokens wrapped in standardized response

    Raises:
        UnauthorizedException: If refresh token is invalid or user not found/inactive
    """
    request_id = get_request_id(request)

    logger.info(
        "Token refresh attempt",
        request_id=request_id
    )

    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token, token_type="refresh")
    if not payload:
        logger.warning(
            "Token refresh failed - invalid token",
            request_id=request_id
        )
        raise UnauthorizedException(
            message="Invalid refresh token"
        )

    # Get user
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        logger.warning(
            "Token refresh failed - user not found or inactive",
            request_id=request_id,
            user_id=user_id
        )
        raise UnauthorizedException(
            message="User not found or inactive"
        )

    # Create new tokens
    access_token = create_access_token(data={
        "user_id": user.id,
        "username": user.username,
        "is_superuser": user.is_superuser
    })

    new_refresh_token = create_refresh_token(data={
        "user_id": user.id
    })

    logger.info(
        "Token refresh successful",
        request_id=request_id,
        user_id=user.id,
        username=user.username
    )

    token_data = {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

    return success_response(
        data=token_data,
        request_id=request_id
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        UserResponse: Current user information
    """
    return current_user


@router.post("/logout")
def logout():
    """
    Logout endpoint (token invalidation handled on client side)

    Returns:
        dict: Success message
    """
    return {"message": "Successfully logged out"}
