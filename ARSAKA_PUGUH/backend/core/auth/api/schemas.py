"""
Auth API Request/Response Schemas

Pydantic models for HTTP transport.
Source: INFRA-LAY2-005-identity-api-contracts.md
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# ============================================================================
# Registration
# ============================================================================

class RegisterRequest(BaseModel):
    """POST /auth/register request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., min_length=2, max_length=100)


class RegisterData(BaseModel):
    """Registration response data."""
    user_id: str
    email: str
    display_name: str
    status: str
    message: str = "Please check your email to verify your account"


class RegisterResponse(BaseModel):
    """POST /auth/register response."""
    success: bool = True
    data: RegisterData


# ============================================================================
# Login
# ============================================================================

class LoginRequest(BaseModel):
    """POST /auth/login request."""
    email: EmailStr
    password: str
    remember_me: bool = False


class UserInfo(BaseModel):
    """User info in login response."""
    user_id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str] = None


class ProjectInfo(BaseModel):
    """Project info in responses."""
    project_id: str
    name: str
    slug: str
    is_default: bool = False


class TenantInfo(BaseModel):
    """Tenant info in login response."""
    tenant_id: str
    name: str
    slug: str
    role: str
    projects: List[ProjectInfo] = []


class LoginData(BaseModel):
    """Login response data."""
    user: UserInfo
    access_token: Optional[str] = None  # Stored in httpOnly cookie
    refresh_token: Optional[str] = None  # Stored in httpOnly cookie
    expires_in: int
    tenants: List[TenantInfo] = []
    active_tenant: Optional[TenantInfo] = None
    active_project: Optional[ProjectInfo] = None
    requires_context_selection: bool = False
    redirect_url: str


class LoginResponse(BaseModel):
    """POST /auth/login response."""
    success: bool = True
    data: LoginData


# ============================================================================
# Email Verification
# ============================================================================

class VerifyEmailUserInfo(BaseModel):
    """User info after email verification."""
    user_id: str
    email: str
    display_name: Optional[str]
    status: str


class VerifyEmailTenant(BaseModel):
    """Tenant created on verification."""
    tenant_id: str
    name: str
    slug: str


class VerifyEmailProject(BaseModel):
    """Project created on verification."""
    project_id: str
    name: str
    slug: str


class VerifyEmailData(BaseModel):
    """Email verification response data."""
    user: VerifyEmailUserInfo
    access_token: str
    refresh_token: str
    expires_in: int
    tenant: Optional[VerifyEmailTenant] = None
    project: Optional[VerifyEmailProject] = None
    redirect_url: str


class VerifyEmailResponse(BaseModel):
    """GET /auth/verify-email response."""
    success: bool = True
    data: VerifyEmailData


# ============================================================================
# Forgot Password
# ============================================================================

class ForgotPasswordRequest(BaseModel):
    """POST /auth/forgot-password request."""
    email: EmailStr


class ForgotPasswordData(BaseModel):
    """Forgot password response data."""
    message: str = "If an account exists with this email, a password reset link has been sent"


class ForgotPasswordResponse(BaseModel):
    """POST /auth/forgot-password response."""
    success: bool = True
    data: ForgotPasswordData


# ============================================================================
# Reset Password
# ============================================================================

class ResetPasswordRequest(BaseModel):
    """POST /auth/reset-password request."""
    token: str
    new_password: str = Field(..., min_length=8)


class ResetPasswordData(BaseModel):
    """Reset password response data."""
    message: str


class ResetPasswordResponse(BaseModel):
    """POST /auth/reset-password response."""
    success: bool = True
    data: ResetPasswordData


# ============================================================================
# Token Refresh
# ============================================================================

class RefreshData(BaseModel):
    """Token refresh response data."""
    access_token: str
    expires_in: int


class RefreshResponse(BaseModel):
    """POST /auth/refresh response."""
    success: bool = True
    data: RefreshData


# ============================================================================
# Logout
# ============================================================================

class LogoutData(BaseModel):
    """Logout response data."""
    message: str = "Logged out successfully"


class LogoutResponse(BaseModel):
    """POST /auth/logout response."""
    success: bool = True
    data: LogoutData


# ============================================================================
# Resend Verification
# ============================================================================

class ResendVerificationRequest(BaseModel):
    """POST /auth/resend-verification request."""
    email: EmailStr


class ResendVerificationData(BaseModel):
    """Resend verification response data."""
    message: str = "If an account exists with this email, a verification email has been sent"


class ResendVerificationResponse(BaseModel):
    """POST /auth/resend-verification response."""
    success: bool = True
    data: ResendVerificationData


# ============================================================================
# Error Response
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[dict] = None
    retry_after: Optional[int] = None
    can_resend: Optional[bool] = None
    unlock_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: ErrorDetail
