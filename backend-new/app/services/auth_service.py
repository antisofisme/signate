"""
Authentication Service
======================

Business logic layer for authentication and authorization.
Handles login, token generation, password management, etc.

Clean Architecture: API → Service → Repository → Database
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.exceptions import (
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    BadRequestException
)
from app.repositories.user_repository import UserRepository
from app.models.user import User


class AuthService:
    """
    Authentication Service

    Handles all authentication business logic:
    - User login/logout
    - Token generation and refresh
    - Password management
    - Account lockout (future)
    """

    def __init__(self, db: Session):
        """
        Initialize AuthService

        Args:
            db: Database session
        """
        self.db = db
        self.user_repo = UserRepository(db)

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and generate tokens

        Args:
            username: Username
            password: Plain text password

        Returns:
            Dict with access_token, refresh_token, token_type, expires_in

        Raises:
            UnauthorizedException: If credentials are invalid
            ForbiddenException: If user is inactive
        """
        # Find user by username
        user = self.user_repo.get_by_username(username)

        # Verify user exists and password is correct
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException(
                message="Incorrect username or password"
            )

        # Check if user is active
        if not user.is_active:
            raise ForbiddenException(
                message="Inactive user account"
            )

        # Update last login timestamp
        self.user_repo.update_last_login(user.id)

        # Get user's primary organization
        self.db.refresh(user)  # Ensure relationships are loaded
        organization_id = user.get_primary_organization_id()

        # Create tokens with user info and organization_id
        access_token = create_access_token(data={
            "user_id": user.id,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "organization_id": organization_id
        })

        refresh_token = create_refresh_token(data={
            "user_id": user.id,
            "organization_id": organization_id
        })

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """
        Generate new access and refresh tokens using refresh token

        Args:
            refresh_token: Valid JWT refresh token

        Returns:
            Dict with new access_token, refresh_token, token_type, expires_in

        Raises:
            UnauthorizedException: If refresh token is invalid or user not found/inactive
        """
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise UnauthorizedException(
                message="Invalid refresh token"
            )

        # Get user
        user_id = payload.get("user_id")
        user = self.user_repo.get(user_id)

        if not user or not user.is_active:
            raise UnauthorizedException(
                message="User not found or inactive"
            )

        # Get user's primary organization
        self.db.refresh(user)  # Ensure relationships are loaded
        organization_id = user.get_primary_organization_id()

        # Create new tokens with organization_id
        access_token = create_access_token(data={
            "user_id": user.id,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "organization_id": organization_id
        })

        new_refresh_token = create_refresh_token(data={
            "user_id": user.id,
            "organization_id": organization_id
        })

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    def get_current_user(self, user_id: int) -> User:
        """
        Get current authenticated user by ID

        Args:
            user_id: User ID from JWT token

        Returns:
            User model

        Raises:
            NotFoundException: If user not found
            ForbiddenException: If user is inactive
        """
        user = self.user_repo.get(user_id)

        if not user:
            raise NotFoundException(message="User not found")

        if not user.is_active:
            raise ForbiddenException(message="Inactive user account")

        return user

    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> None:
        """
        Change user password

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Raises:
            NotFoundException: If user not found
            UnauthorizedException: If old password is incorrect
            BadRequestException: If new password is invalid
        """
        user = self.user_repo.get(user_id)

        if not user:
            raise NotFoundException(message="User not found")

        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise UnauthorizedException(message="Incorrect current password")

        # Validate new password (basic validation, schema handles detailed validation)
        if len(new_password) < settings.PASSWORD_MIN_LENGTH:
            raise BadRequestException(
                message=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
            )

        # Hash and update password
        new_password_hash = hash_password(new_password)
        self.user_repo.update(user_id, {"password_hash": new_password_hash})

    def initiate_password_reset(self, username: str, email: str) -> Dict[str, str]:
        """
        Initiate password reset process

        NOTE: In production, this should send an email with reset link.
        For now, it just validates user exists and returns success.

        Args:
            username: Username
            email: Email address for verification

        Returns:
            Dict with success message

        Raises:
            NotFoundException: If user not found or email doesn't match
        """
        user = self.user_repo.get_by_username(username)

        if not user or user.email != email:
            # Security: Don't reveal if username exists
            # Return success even if user not found
            return {
                "message": "If the username and email match, a password reset link will be sent"
            }

        # TODO: Generate reset token and send email
        # For now, just return success
        return {
            "message": "If the username and email match, a password reset link will be sent"
        }

    def reset_password_with_token(self, token: str, new_password: str) -> None:
        """
        Reset password using reset token

        NOTE: This is a placeholder implementation.
        In production, implement proper token-based reset.

        Args:
            token: Password reset token
            new_password: New password

        Raises:
            UnauthorizedException: If token is invalid
            BadRequestException: If password is invalid
        """
        # TODO: Implement token verification and password reset
        # This requires storing reset tokens in database or Redis
        raise BadRequestException(
            message="Password reset not yet implemented. Please contact administrator."
        )

    def logout(self) -> Dict[str, str]:
        """
        Logout user (token invalidation handled on client side)

        NOTE: With JWT stateless tokens, logout is handled client-side
        by removing the token. For proper server-side invalidation,
        implement token blacklist using Redis.

        Returns:
            Dict with success message
        """
        return {"message": "Successfully logged out"}
