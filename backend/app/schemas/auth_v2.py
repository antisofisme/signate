"""
Enhanced Authentication Schemas
Pydantic models for multi-tenant authentication
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from app.schemas.organization import OrganizationResponse
from app.schemas.role import RoleResponse


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Username or email")
    password: str = Field(..., min_length=8, description="Password")
    organization_slug: Optional[str] = Field(None, description="Optional organization slug to login to")
    remember_me: bool = Field(False, description="Extended session duration")

    class Config:
        schema_extra = {
            "example": {
                "username": "john.doe",
                "password": "SecurePass123!",
                "organization_slug": "acme-corp",
                "remember_me": False
            }
        }


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    user: 'UserAuthResponse' = Field(..., description="Authenticated user info")
    organization: OrganizationResponse = Field(..., description="Current organization")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": 1,
                    "username": "john.doe",
                    "email": "john@example.com"
                },
                "organization": {
                    "id": 1,
                    "name": "Acme Corp",
                    "slug": "acme-corp"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
            }
        }


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="Email address")
    organization_slug: Optional[str] = Field(None, description="Organization slug (for branded reset emails)")

    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "organization_slug": "acme-corp"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        # Optional: Check for special characters
        # if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in v):
        #     raise ValueError('Password must contain at least one special character')
        return v

    class Config:
        schema_extra = {
            "example": {
                "token": "reset-token-here",
                "new_password": "NewSecurePass123!"
            }
        }


class PasswordChangeRequest(BaseModel):
    """Password change request (for authenticated users)"""
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator('new_password')
    def validate_password(cls, v, values):
        # Check it's different from current password
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')

        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPassword123",
                "new_password": "NewSecurePass456!"
            }
        }


class EmailVerificationRequest(BaseModel):
    """Email verification request"""
    token: str = Field(..., description="Email verification token")

    class Config:
        schema_extra = {
            "example": {
                "token": "verification-token-here"
            }
        }


class TwoFactorSetupResponse(BaseModel):
    """Two-factor authentication setup response"""
    secret: str = Field(..., description="TOTP secret")
    qr_code: str = Field(..., description="QR code as base64 image")
    backup_codes: List[str] = Field(..., description="Backup codes")

    class Config:
        schema_extra = {
            "example": {
                "secret": "JBSWY3DPEHPK3PXP",
                "qr_code": "data:image/png;base64,iVBORw0...",
                "backup_codes": ["123456", "234567", "345678"]
            }
        }


class TwoFactorVerifyRequest(BaseModel):
    """Two-factor verification request"""
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")

    class Config:
        schema_extra = {
            "example": {
                "code": "123456"
            }
        }


class UserAuthResponse(BaseModel):
    """User information in auth response"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_super_admin: bool
    current_role: Optional[RoleResponse]
    organizations: List[dict] = Field(..., description="List of user's organizations")
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class LogoutRequest(BaseModel):
    """Logout request"""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")
    logout_all_devices: bool = Field(False, description="Logout from all devices")

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "logout_all_devices": False
            }
        }


class SessionInfo(BaseModel):
    """Active session information"""
    session_id: str
    device: str
    ip_address: str
    location: Optional[str]
    last_activity: datetime
    is_current: bool

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ActiveSessionsResponse(BaseModel):
    """List of active sessions"""
    sessions: List[SessionInfo]
    total: int

    class Config:
        schema_extra = {
            "example": {
                "sessions": [
                    {
                        "session_id": "sess_123",
                        "device": "Chrome on Windows",
                        "ip_address": "192.168.1.100",
                        "location": "New York, US",
                        "last_activity": "2024-01-01T12:00:00Z",
                        "is_current": True
                    }
                ],
                "total": 1
            }
        }