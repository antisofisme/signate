"""
Device JWT Authentication Module

Provides JWT token generation and verification for device authentication.
Devices receive a JWT token upon activation which they use for all subsequent API calls.
This replaces the insecure device_id query parameter approach.

Security features:
- 30-day token expiration for devices
- Automatic token refresh when < 7 days remaining
- Signature verification using SECRET_KEY
- Backward compatibility with device_id during transition
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Header, Query, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import StructuredLogger
from app.models.device import Device

logger = StructuredLogger(__name__)

# Token configuration
DEVICE_TOKEN_EXPIRE_DAYS = 30  # Devices get 30-day tokens
DEVICE_TOKEN_REFRESH_THRESHOLD_DAYS = 7  # Refresh when < 7 days remaining


def create_device_token(
    device_id: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate JWT token for device authentication

    Args:
        device_id: The device ID to embed in token
        expires_delta: Optional custom expiration time (defaults to 30 days)

    Returns:
        str: Signed JWT token for device

    Example:
        token = create_device_token(device_id=123)
        # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    # Default to 30 days if not specified
    if expires_delta is None:
        expires_delta = timedelta(days=DEVICE_TOKEN_EXPIRE_DAYS)

    # Calculate expiration time
    expire = datetime.utcnow() + expires_delta

    # Create token payload
    payload = {
        "device_id": device_id,
        "type": "device",  # Distinguish from user tokens
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
        "iss": "signage-backend"  # Issuer
    }

    # Sign token with SECRET_KEY
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    logger.info(
        "Device token created",
        device_id=device_id,
        expires_at=expire.isoformat(),
        token_type="device"
    )

    return token


def verify_device_token(token: str) -> Dict[str, Any]:
    """
    Verify device JWT token and return payload

    Args:
        token: JWT token to verify

    Returns:
        dict: Decoded token payload containing device_id

    Raises:
        HTTPException: If token is invalid, expired, or not a device token
    """
    try:
        # Decode and verify token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify this is a device token (not user token)
        if payload.get("type") != "device":
            logger.warning(
                "Token type mismatch",
                expected_type="device",
                actual_type=payload.get("type")
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type - device token required"
            )

        # Check if token needs refresh soon
        exp = datetime.fromtimestamp(payload.get("exp", 0))
        days_until_expiry = (exp - datetime.utcnow()).days

        if days_until_expiry < DEVICE_TOKEN_REFRESH_THRESHOLD_DAYS:
            payload["needs_refresh"] = True
            logger.info(
                "Device token expiring soon",
                device_id=payload.get("device_id"),
                days_remaining=days_until_expiry
            )

        return payload

    except JWTError as e:
        logger.error(
            "JWT verification failed",
            error=str(e),
            token_preview=token[:20] + "..." if len(token) > 20 else token
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def get_current_device(
    authorization: Optional[str] = Header(None),
    device_id: Optional[int] = Query(None),  # Backward compatibility
    db: Session = Depends(get_db)
) -> Device:
    """
    FastAPI dependency to get current device from JWT token

    Supports both:
    1. New method: Authorization header with Bearer token (preferred)
    2. Old method: device_id query parameter (deprecated, logs warning)

    Args:
        authorization: Authorization header value
        device_id: Device ID from query param (backward compatibility)
        db: Database session

    Returns:
        Device: Authenticated device object

    Raises:
        HTTPException: If authentication fails

    Usage in endpoint:
        @router.get("/client/playlist")
        async def get_playlist(device: Device = Depends(get_current_device)):
            return {"device_id": device.id}
    """
    authenticated_device_id = None
    auth_method = None

    # Try JWT token authentication first (preferred)
    if authorization:
        # Extract Bearer token
        if not authorization.startswith("Bearer "):
            logger.warning(
                "Invalid authorization header format",
                header_preview=authorization[:20]
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Use: Bearer <token>"
            )

        token = authorization[7:]  # Remove "Bearer " prefix

        try:
            # Verify token and get device_id
            payload = verify_device_token(token)
            authenticated_device_id = payload.get("device_id")
            auth_method = "jwt"

            # Check if token needs refresh
            if payload.get("needs_refresh"):
                # Add refresh hint to response headers (handled by middleware)
                # Device should call /api/client/refresh endpoint
                pass

        except HTTPException:
            # Token verification failed
            raise

    # Fallback to device_id query parameter (backward compatibility)
    elif device_id:
        authenticated_device_id = device_id
        auth_method = "query_param"

        # Log deprecation warning
        logger.warning(
            "DEPRECATED: Device using insecure query parameter authentication",
            device_id=device_id,
            recommendation="Update device to use JWT Bearer token"
        )

    else:
        # No authentication provided
        logger.warning("No device authentication provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device authentication required. Provide Bearer token or device_id"
        )

    # Fetch device from database
    device = db.query(Device).filter(Device.id == authenticated_device_id).first()

    if not device:
        logger.error(
            "Device not found",
            device_id=authenticated_device_id,
            auth_method=auth_method
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {authenticated_device_id} not found"
        )

    # Verify device is active
    if device.status != "active":
        logger.warning(
            "Inactive device attempted access",
            device_id=device.id,
            status=device.status
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Device is {device.status}. Only active devices can access content"
        )

    # Update last_seen timestamp (for online/offline tracking)
    device.last_seen = datetime.utcnow()
    db.commit()

    logger.info(
        "Device authenticated successfully",
        device_id=device.id,
        device_name=device.device_name,
        auth_method=auth_method
    )

    return device


def get_optional_device(
    authorization: Optional[str] = Header(None),
    device_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> Optional[Device]:
    """
    Optional device authentication dependency

    Similar to get_current_device but returns None if no auth provided
    Used for endpoints that work with or without authentication

    Args:
        authorization: Authorization header value
        device_id: Device ID from query param
        db: Database session

    Returns:
        Optional[Device]: Authenticated device or None
    """
    if not authorization and not device_id:
        return None

    try:
        return get_current_device(authorization, device_id, db)
    except HTTPException:
        # Authentication failed but it's optional
        return None


def refresh_device_token(device_id: int) -> Dict[str, Any]:
    """
    Generate a new token for a device (token refresh)

    Args:
        device_id: Device ID to refresh token for

    Returns:
        dict: New token and expiration info
    """
    # Generate new token
    new_token = create_device_token(device_id)

    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=DEVICE_TOKEN_EXPIRE_DAYS)

    logger.info(
        "Device token refreshed",
        device_id=device_id,
        new_expires_at=expires_at.isoformat()
    )

    return {
        "device_token": new_token,
        "token_type": "Bearer",
        "expires_at": expires_at.isoformat(),
        "expires_in_days": DEVICE_TOKEN_EXPIRE_DAYS
    }