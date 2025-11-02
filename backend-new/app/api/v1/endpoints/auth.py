"""
Authentication API Endpoints
=============================

JWT-based authentication with login, token refresh, and user info.

Clean Architecture: API → Service → Repository → Database
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, get_current_active_user
from app.core.logging import StructuredLogger
from app.middleware.request_id import get_request_id
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm
)
from app.schemas.common import success_response
from app.models.user import User

logger = StructuredLogger(__name__)
router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate user with username/password and return JWT tokens"
)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    User authentication endpoint.

    **Flow**:
    1. Validate username and password
    2. Check user is active
    3. Update last_login timestamp
    4. Generate access and refresh tokens
    5. Return tokens

    **Returns**:
    - access_token: JWT access token (15 min expiry)
    - refresh_token: JWT refresh token (7 day expiry)
    - token_type: "bearer"
    - expires_in: Token expiration in seconds

    **Errors**:
    - 401: Invalid credentials
    - 403: Inactive user account
    """
    request_id = get_request_id(request)

    logger.info(
        "Login attempt",
        request_id=request_id,
        username=login_data.username
    )

    auth_service = AuthService(db)
    token_data = auth_service.login(login_data.username, login_data.password)

    logger.info(
        "Login successful",
        request_id=request_id,
        username=login_data.username
    )

    return token_data


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="Generate new access and refresh tokens using refresh token"
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Token refresh endpoint.

    **Flow**:
    1. Verify refresh token
    2. Check user still exists and is active
    3. Generate new access and refresh tokens
    4. Return tokens

    **Returns**:
    - access_token: New JWT access token
    - refresh_token: New JWT refresh token
    - token_type: "bearer"
    - expires_in: Token expiration in seconds

    **Errors**:
    - 401: Invalid refresh token or user not found/inactive
    """
    request_id = get_request_id(request)

    logger.info(
        "Token refresh attempt",
        request_id=request_id
    )

    auth_service = AuthService(db)
    token_data = auth_service.refresh_tokens(refresh_data.refresh_token)

    logger.info(
        "Token refresh successful",
        request_id=request_id
    )

    return token_data


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="Get current authenticated user information"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current authenticated user information.

    **Requires**: Valid JWT access token in Authorization header

    **Returns**:
    - User information (id, username, email, role, etc.)
    - Does NOT include password_hash

    **Errors**:
    - 401: Invalid or missing token
    - 403: Inactive user
    """
    return current_user.to_dict()


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Logout user (token invalidation handled client-side)"
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    User logout endpoint.

    **NOTE**: With JWT stateless tokens, logout is primarily handled
    client-side by removing the token. For proper server-side invalidation,
    implement token blacklist using Redis (future enhancement).

    **Flow**:
    1. Verify user is authenticated (via dependency)
    2. Log the logout event
    3. Return success message

    **Returns**:
    - message: Success message
    """
    request_id = get_request_id(request)

    logger.info(
        "User logout",
        request_id=request_id,
        user_id=current_user.id,
        username=current_user.username
    )

    auth_service = AuthService(db)
    result = auth_service.logout()

    return result


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change Password",
    description="Change current user's password"
)
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Change password for current user.

    **Requires**: Valid JWT access token

    **Flow**:
    1. Verify old password is correct
    2. Validate new password meets security requirements
    3. Hash and update password
    4. Return success

    **Security Requirements** (validated by schema):
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit

    **Errors**:
    - 401: Incorrect old password or invalid token
    - 400: Invalid new password format
    """
    request_id = get_request_id(request)

    logger.info(
        "Password change attempt",
        request_id=request_id,
        user_id=current_user.id,
        username=current_user.username
    )

    auth_service = AuthService(db)
    auth_service.change_password(
        user_id=current_user.id,
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )

    logger.info(
        "Password changed successfully",
        request_id=request_id,
        user_id=current_user.id,
        username=current_user.username
    )

    return {"message": "Password changed successfully"}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Initiate Password Reset",
    description="Request password reset link (placeholder implementation)"
)
async def initiate_password_reset(
    reset_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Initiate password reset process.

    **NOTE**: This is a placeholder implementation.
    In production, this should:
    1. Generate a secure reset token
    2. Store token in database/Redis with expiration
    3. Send email with reset link
    4. Return success message

    **Security**: Always returns success even if user not found
    to prevent username enumeration attacks.

    **Current Behavior**: Validates user exists but doesn't send email.

    **Errors**:
    - None (always returns 200 for security)
    """
    request_id = get_request_id(request)

    logger.info(
        "Password reset requested",
        request_id=request_id,
        username=reset_data.username
    )

    auth_service = AuthService(db)
    result = auth_service.initiate_password_reset(
        username=reset_data.username,
        email=reset_data.email
    )

    return result


@router.post(
    "/reset-password/confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirm Password Reset",
    description="Reset password using reset token (not yet implemented)"
)
async def confirm_password_reset(
    confirm_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Reset password using reset token.

    **NOTE**: Not yet implemented. Requires token storage mechanism.

    **Future Implementation**:
    1. Verify reset token is valid and not expired
    2. Validate new password meets requirements
    3. Update user password
    4. Invalidate reset token
    5. Return success

    **Errors**:
    - 400: Not implemented
    """
    request_id = get_request_id(request)

    logger.info(
        "Password reset confirmation attempted",
        request_id=request_id
    )

    auth_service = AuthService(db)
    auth_service.reset_password_with_token(
        token=confirm_data.token,
        new_password=confirm_data.new_password
    )

    return {"message": "Password reset successfully"}
