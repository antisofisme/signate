"""Auth API - HTTP endpoints for authentication."""

from .routes import router as auth_router
from .api_key_routes import router as api_key_router
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
from .api_key_schemas import (
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    ListApiKeysResponse,
    GetApiKeyResponse,
    RevokeApiKeyResponse,
    DeleteApiKeyResponse,
    ApiKeyInfo,
)

__all__ = [
    # Routers
    "auth_router",
    "api_key_router",
    # Auth schemas
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
    # API Key schemas
    "CreateApiKeyRequest",
    "CreateApiKeyResponse",
    "ListApiKeysResponse",
    "GetApiKeyResponse",
    "RevokeApiKeyResponse",
    "DeleteApiKeyResponse",
    "ApiKeyInfo",
]
