"""
JWT Token Validation
Extract and validate JWT tokens from requests
"""

from typing import Optional
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from shared.config import settings
from shared.errors import AuthenticationError, ErrorCodes


# Security scheme for FastAPI
security = HTTPBearer()


class CurrentUser(BaseModel):
    """Current authenticated user from JWT token"""
    id: int
    username: str
    role: str
    organization_id: Optional[int] = None


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

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
    except JWTError as e:
        raise AuthenticationError(
            message="Token tidak valid atau sudah expired",
            code=ErrorCodes.INVALID_TOKEN,
            details={"error": str(e)}
        )


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
