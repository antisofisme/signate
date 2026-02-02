"""
Auth API Dependencies

Dependency injection for FastAPI auth routers.
Wires repositories, services, and use cases.
"""

from typing import AsyncGenerator, Optional, Union
from dataclasses import dataclass
from uuid import UUID
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.auth_provider import IAuthProvider
from ..interfaces.token_service import ITokenService, TokenPayload
from ..interfaces.user_repository import IUserRepository
from ..interfaces.api_key_repository import IApiKeyRepository
from ..adapters.local_auth import LocalAuthAdapter
from ..adapters.token_service import JWTTokenService
from ..adapters.user_repository import PostgresUserRepository
from ..adapters.api_key_repository import PostgresApiKeyRepository
from ..services.tenant_loader import TenantLoaderService
from ..use_cases import (
    RegisterUseCase,
    LoginUseCase,
    VerifyEmailUseCase,
    ForgotPasswordUseCase,
    ResetPasswordUseCase,
    # API Key use cases
    CreateApiKeyUseCase,
    ValidateApiKeyUseCase,
    ListApiKeysUseCase,
    GetApiKeyUseCase,
    RevokeApiKeyUseCase,
    DeleteApiKeyUseCase,
    ApiKeyContext,
)
from ..exceptions import TokenExpiredError, TokenInvalidError


# Security schemes for protected endpoints
security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class AuthenticatedContext:
    """Unified authentication context for JWT or API key.

    This allows routes to accept either JWT tokens or API keys.
    """
    # Common fields
    auth_type: str  # "jwt" or "api_key"

    # User info (from JWT or API key creator)
    user_id: str
    tenant_id: str
    project_id: Optional[str] = None

    # Roles/permissions
    roles: list = None
    scopes: list = None

    # API key specific
    api_key_id: Optional[str] = None
    api_key_name: Optional[str] = None
    environment: Optional[str] = None  # "live" or "test"

    # JWT specific
    email: Optional[str] = None
    display_name: Optional[str] = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.scopes is None:
            self.scopes = []

    def has_scope(self, required_scope: str) -> bool:
        """Check if context has required scope."""
        if not self.scopes:
            return True  # Empty = full access

        for scope in self.scopes:
            if scope == "*":
                return True
            if scope == required_scope:
                return True
            # Wildcard matching
            if scope.endswith(":*"):
                prefix = scope[:-1]
                if required_scope.startswith(prefix):
                    return True
        return False


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
    )


async def get_user_repository(
    session: AsyncSession = Depends(get_session)
) -> IUserRepository:
    """Get user repository."""
    return PostgresUserRepository(session)


async def get_api_key_repository(
    session: AsyncSession = Depends(get_session)
) -> IApiKeyRepository:
    """Get API key repository."""
    return PostgresApiKeyRepository(session)


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


async def get_tenant_loader(
    session: AsyncSession = Depends(get_session)
) -> TenantLoaderService:
    """Get tenant loader service."""
    return TenantLoaderService(session)


async def get_login_use_case(
    auth_provider: IAuthProvider = Depends(get_auth_provider),
    token_service: ITokenService = Depends(get_token_service),
    user_repo: IUserRepository = Depends(get_user_repository),
    tenant_loader: TenantLoaderService = Depends(get_tenant_loader),
) -> LoginUseCase:
    """Get LoginUseCase with injected dependencies."""
    return LoginUseCase(
        auth_provider=auth_provider,
        token_service=token_service,
        user_repo=user_repo,
        tenant_service=tenant_loader,  # Now using TenantLoaderService
        event_bus=None,                # TODO: Add event bus
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
# API Key Use Case Dependencies
# ============================================================================

async def get_create_api_key_use_case(
    api_key_repo: IApiKeyRepository = Depends(get_api_key_repository),
) -> CreateApiKeyUseCase:
    """Get CreateApiKeyUseCase with injected dependencies."""
    return CreateApiKeyUseCase(
        api_key_repo=api_key_repo,
        event_bus=None,
    )


async def get_validate_api_key_use_case(
    api_key_repo: IApiKeyRepository = Depends(get_api_key_repository),
) -> ValidateApiKeyUseCase:
    """Get ValidateApiKeyUseCase with injected dependencies."""
    return ValidateApiKeyUseCase(
        api_key_repo=api_key_repo,
        event_bus=None,
    )


async def get_list_api_keys_use_case(
    api_key_repo: IApiKeyRepository = Depends(get_api_key_repository),
) -> ListApiKeysUseCase:
    """Get ListApiKeysUseCase with injected dependencies."""
    return ListApiKeysUseCase(api_key_repo=api_key_repo)


async def get_api_key_use_case(
    api_key_repo: IApiKeyRepository = Depends(get_api_key_repository),
) -> GetApiKeyUseCase:
    """Get GetApiKeyUseCase with injected dependencies."""
    return GetApiKeyUseCase(api_key_repo=api_key_repo)


async def get_revoke_api_key_use_case(
    api_key_repo: IApiKeyRepository = Depends(get_api_key_repository),
) -> RevokeApiKeyUseCase:
    """Get RevokeApiKeyUseCase with injected dependencies."""
    return RevokeApiKeyUseCase(
        api_key_repo=api_key_repo,
        event_bus=None,
    )


async def get_delete_api_key_use_case(
    api_key_repo: IApiKeyRepository = Depends(get_api_key_repository),
) -> DeleteApiKeyUseCase:
    """Get DeleteApiKeyUseCase with injected dependencies."""
    return DeleteApiKeyUseCase(
        api_key_repo=api_key_repo,
        event_bus=None,
    )


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token_service: ITokenService = Depends(get_token_service),
) -> Optional[TokenPayload]:
    """Get current user from JWT token (optional).

    Checks for token in this order:
    1. httpOnly cookie (preferred, more secure)
    2. Authorization header (for backward compatibility & API clients)

    Returns None if no token provided.
    Raises HTTPException if token is invalid.
    """
    # Priority 1: Check httpOnly cookie
    access_token = request.cookies.get("access_token")

    # Priority 2: Check Authorization header (backward compatibility)
    if not access_token and credentials is not None:
        access_token = credentials.credentials

    if not access_token:
        return None

    try:
        payload = await token_service.verify_access_token(access_token)
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


# ============================================================================
# API Key Authentication Dependencies
# ============================================================================

async def get_api_key_context(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
    validate_use_case: ValidateApiKeyUseCase = Depends(get_validate_api_key_use_case),
) -> Optional[ApiKeyContext]:
    """Get context from API key (optional).

    Returns None if no API key provided.
    Raises HTTPException if API key is invalid.
    """
    if api_key is None:
        return None

    ip_address = get_client_ip(request)
    result = await validate_use_case.execute(api_key, ip_address=ip_address)

    if not result.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_API_KEY",
                "message": result.error or "Invalid API key"
            }
        )

    return result.context


async def get_authenticated_context(
    request: Request,
    jwt_payload: Optional[TokenPayload] = Depends(get_current_user_optional),
    api_key_context: Optional[ApiKeyContext] = Depends(get_api_key_context),
) -> AuthenticatedContext:
    """Get unified authentication context (JWT or API key).

    Supports both JWT token and API key authentication.
    API key takes precedence if both are provided.

    Raises HTTPException if neither is provided.
    """
    # API key takes precedence
    if api_key_context is not None:
        return AuthenticatedContext(
            auth_type="api_key",
            user_id=str(api_key_context.created_by_user_id),
            tenant_id=str(api_key_context.tenant_id),
            project_id=None,  # API keys don't have project context by default
            scopes=api_key_context.scopes,
            api_key_id=str(api_key_context.key_id),
            api_key_name=api_key_context.name,
            environment=api_key_context.environment,
        )

    # Fall back to JWT
    if jwt_payload is not None:
        return AuthenticatedContext(
            auth_type="jwt",
            user_id=jwt_payload.sub,
            tenant_id=jwt_payload.active_tenant_id,
            project_id=jwt_payload.active_project_id,
            roles=jwt_payload.roles or [],
            email=jwt_payload.email,
            display_name=jwt_payload.display_name,
        )

    # Neither provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "UNAUTHORIZED",
            "message": "Authentication required. Provide JWT token or API key."
        }
    )


async def get_authenticated_context_optional(
    request: Request,
    jwt_payload: Optional[TokenPayload] = Depends(get_current_user_optional),
    api_key_context: Optional[ApiKeyContext] = Depends(get_api_key_context),
) -> Optional[AuthenticatedContext]:
    """Get unified authentication context (optional).

    Returns None if neither JWT nor API key is provided.
    """
    if api_key_context is not None:
        return AuthenticatedContext(
            auth_type="api_key",
            user_id=str(api_key_context.created_by_user_id),
            tenant_id=str(api_key_context.tenant_id),
            project_id=None,
            scopes=api_key_context.scopes,
            api_key_id=str(api_key_context.key_id),
            api_key_name=api_key_context.name,
            environment=api_key_context.environment,
        )

    if jwt_payload is not None:
        return AuthenticatedContext(
            auth_type="jwt",
            user_id=jwt_payload.sub,
            tenant_id=jwt_payload.active_tenant_id,
            project_id=jwt_payload.active_project_id,
            roles=jwt_payload.roles or [],
            email=jwt_payload.email,
            display_name=jwt_payload.display_name,
        )

    return None


def require_scope(required_scope: str):
    """Dependency factory to require a specific scope.

    Usage:
        @app.get("/decisions")
        async def list_decisions(
            ctx: AuthenticatedContext = Depends(require_scope("read:decisions"))
        ):
            ...
    """
    async def _require_scope(
        ctx: AuthenticatedContext = Depends(get_authenticated_context),
    ) -> AuthenticatedContext:
        if not ctx.has_scope(required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_SCOPE",
                    "message": f"This action requires scope: {required_scope}"
                }
            )
        return ctx

    return _require_scope
