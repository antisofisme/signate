"""Auth Interfaces - Abstract contracts for dependency injection."""

from .auth_provider import IAuthProvider
from .token_service import ITokenService
from .user_repository import IUserRepository

__all__ = ["IAuthProvider", "ITokenService", "IUserRepository"]
