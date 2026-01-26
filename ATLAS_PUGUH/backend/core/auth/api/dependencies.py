"""
Auth API Dependencies

Dependency injection for FastAPI auth routers.
Wires repositories, services, and use cases.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.auth_provider import IAuthProvider
from ..interfaces.token_service import ITokenService, TokenPayload
from ..interfaces.user_repository import IUserRepository
from ..adapters.local_auth import LocalAuthAdapter
from ..adapters.token_service import JWTTokenService
from ..adapters.user_repository import PostgresUserRepository
from ..use_cases import (
    RegisterUseCase,
    LoginUseCase,
    VerifyEmailUseCase,
    ForgotPasswordUseCase,
    ResetPasswordUseCase,
)
from ..exceptions import TokenExpiredError, TokenInvalidError


# Security scheme for protected endpoints
security = HTTPBearer(auto_error=False)


# ============================================================================
# Session Factory (initialized at startup)
# ============================================================================

_session_factory = None
_jwt_secret: str = None
_jwt_issuer: str = "atlaspuguh"


def init_auth_dependencies(
    session_factory,
    jwt_secret: str,
    jwt_issuer: str = "atlaspuguh",
):
    """Initialize auth dependencies at app startup.

    Args:
        session_factory: SQLAlchemy async session factory
        jwt_secret: Secret key for JWT signing
        jwt_issuer: JWT issuer claim
    """
    global _session_factory, _jwt_secret, _jwt_issuer
    _session_factory = session_factory
    _jwt_secret = jwt_secret
    _jwt_issuer = jwt_issuer


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    if _session_factory is None:
        raise RuntimeError("Auth dependencies not initialized. Call init_auth_dependencies() at startup.")

    async with _session_factory() as session:
        yield session


# ============================================================================
# Service Dependencies
# ============================================================================

def get_auth_provider() -> IAuthProvider:
    """Get auth provider (password hashing)."""
    return LocalAuthAdapter()


def get_token_service() -> ITokenService:
    """Get token service (JWT management)."""
    if _jwt_secret is None:
        raise RuntimeError("JWT secret not configured")
    return JWTTokenService(
        secret_key=_jwt_secret,
        issuer=_jwt_issuer,
    )


async def get_user_repository(
    session: AsyncSession = Depends(get_session)
) -> IUserRepository:
    """Get user repository."""
    return PostgresUserRepository(session)


# ============================================================================
# Use Case Dependencies
# ============================================================================

async def get_register_use_case(
    auth_provider: IAuthProvider = Depends(get_auth_provider),
    token_service: ITokenService = Depends(get_token_service),
    user_repo: IUserRepository = Depends(get_user_repository),
) -> RegisterUseCase:
    """Get RegisterUseCase with injected dependencies."""
    return RegisterUseCase(
        auth_provider=auth_provider,
        token_service=token_service,
        user_repo=user_repo,
        tenant_service=None,  # TODO: Add tenant service
        event_bus=None,       # TODO: Add event bus
    )


async def get_login_use_case(
    auth_provider: IAuthProvider = Depends(get_auth_provider),
    token_service: ITokenService = Depends(get_token_service),
    user_repo: IUserRepository = Depends(get_user_repository),
) -> LoginUseCase:
    """Get LoginUseCase with injected dependencies."""
    return LoginUseCase(
        auth_provider=auth_provider,
        token_service=token_service,
        user_repo=user_repo,
        tenant_service=None,  # TODO: Add tenant service
        event_bus=None,       # TODO: Add event bus
    )


async def get_verify_email_use_case(
    token_service: ITokenService = Depends(get_token_service),
    user_repo: IUserRepository = Depends(get_user_repository),
) -> VerifyEmailUseCase:
    """Get VerifyEmailUseCase with injected dependencies."""
    return VerifyEmailUseCase(
        token_service=token_service,
        user_repo=user_repo,
        tenant_service=None,  # TODO: Add tenant service
        event_bus=None,       # TODO: Add event bus
    )


async def get_forgot_password_use_case(
    token_service: ITokenService = Depends(get_token_service),
    user_repo: IUserRepository = Depends(get_user_repository),
) -> ForgotPasswordUseCase:
    """Get ForgotPasswordUseCase with injected dependencies."""
    return ForgotPasswordUseCase(
        token_service=token_service,
        user_repo=user_repo,
        email_service=None,  # TODO: Add email service
    )


async def get_reset_password_use_case(
    auth_provider: IAuthProvider = Depends(get_auth_provider),
    token_service: ITokenService = Depends(get_token_service),
    user_repo: IUserRepository = Depends(get_user_repository),
) -> ResetPasswordUseCase:
    """Get ResetPasswordUseCase with injected dependencies."""
    return ResetPasswordUseCase(
        auth_provider=auth_provider,
        token_service=token_service,
        user_repo=user_repo,
        event_bus=None,  # TODO: Add event bus
    )


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token_service: ITokenService = Depends(get_token_service),
) -> Optional[TokenPayload]:
    """Get current user from JWT token (optional).

    Returns None if no token provided.
    Raises HTTPException if token is invalid.
    """
    if credentials is None:
        return None

    try:
        payload = await token_service.verify_access_token(credentials.credentials)
        return payload
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "TOKEN_EXPIRED",
                "message": "Access token has expired"
            }
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Invalid access token"
            }
        )


async def get_current_user(
    user: Optional[TokenPayload] = Depends(get_current_user_optional),
) -> TokenPayload:
    """Get current user from JWT token (required).

    Raises HTTPException if no token or invalid token.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Authentication required"
            }
        )
    return user


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request."""
    # Check X-Forwarded-For header (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client
    if request.client:
        return request.client.host

    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")
