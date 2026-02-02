"""
Auth Module - Clean Architecture

This module handles authentication for ARSAKA_PUGUH SaaS platform:
- User registration and login
- OAuth authentication (Google, GitHub)
- Token management (JWT)
- Password reset and email verification

Source: INFRA-DEC-008-auth-flow.md
"""

from .interfaces.auth_provider import IAuthProvider
from .interfaces.token_service import ITokenService, TokenPayload, TenantContext
from .domain.user import User, UserStatus
from .domain.events import UserRegistered, UserVerified, UserLoggedIn
from .api.routes import router as auth_router
from .api.dependencies import init_auth_dependencies, get_current_user

__all__ = [
    # Interfaces
    "IAuthProvider",
    "ITokenService",
    "TokenPayload",
    "TenantContext",
    # Domain
    "User",
    "UserStatus",
    # Events
    "UserRegistered",
    "UserVerified",
    "UserLoggedIn",
    # API
    "auth_router",
    "init_auth_dependencies",
    "get_current_user",
]
