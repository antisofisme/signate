"""Auth API - HTTP endpoints for authentication."""

from .routes import router as auth_router
from .schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    VerifyEmailResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    RefreshResponse,
    LogoutResponse,
)

__all__ = [
    "auth_router",
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest",
    "LoginResponse",
    "VerifyEmailResponse",
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    "ResetPasswordRequest",
    "ResetPasswordResponse",
    "RefreshResponse",
    "LogoutResponse",
]
