"""Auth Use Cases - Application business logic."""

from .register import RegisterUseCase, RegisterRequest, RegisterResult
from .login import LoginUseCase, LoginRequest, LoginResult
from .verify_email import VerifyEmailUseCase
from .forgot_password import ForgotPasswordUseCase
from .reset_password import ResetPasswordUseCase

# API Key use cases
from .create_api_key import CreateApiKeyUseCase, CreateApiKeyRequest, CreateApiKeyResult
from .validate_api_key import ValidateApiKeyUseCase, ApiKeyContext, ValidateApiKeyResult
from .list_api_keys import ListApiKeysUseCase, ListApiKeysRequest, ListApiKeysResult, GetApiKeyUseCase, ApiKeyInfo
from .revoke_api_key import RevokeApiKeyUseCase, RevokeApiKeyRequest, RevokeApiKeyResult, DeleteApiKeyUseCase

__all__ = [
    # User auth
    "RegisterUseCase",
    "RegisterRequest",
    "RegisterResult",
    "LoginUseCase",
    "LoginRequest",
    "LoginResult",
    "VerifyEmailUseCase",
    "ForgotPasswordUseCase",
    "ResetPasswordUseCase",
    # API Key
    "CreateApiKeyUseCase",
    "CreateApiKeyRequest",
    "CreateApiKeyResult",
    "ValidateApiKeyUseCase",
    "ApiKeyContext",
    "ValidateApiKeyResult",
    "ListApiKeysUseCase",
    "ListApiKeysRequest",
    "ListApiKeysResult",
    "GetApiKeyUseCase",
    "ApiKeyInfo",
    "RevokeApiKeyUseCase",
    "RevokeApiKeyRequest",
    "RevokeApiKeyResult",
    "DeleteApiKeyUseCase",
]
