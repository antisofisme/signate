"""
Login Use Case

Handles user login with email/password.
Returns JWT tokens with tenant/project context.

Source: INFRA-DEC-008-auth-flow.md
"""

from dataclasses import dataclass
from typing import Optional, List

from ..interfaces.auth_provider import IAuthProvider
from ..interfaces.token_service import ITokenService, TenantContext
from ..interfaces.user_repository import IUserRepository
from ..domain.user import UserStatus
from ..domain.events import UserLoggedIn, LoginFailed
from ..exceptions import (
    InvalidCredentialsError,
    AccountNotVerifiedError,
    AccountSuspendedError,
    AccountLockedError,
    ValidationError,
)


@dataclass
class LoginRequest:
    """Login request data."""
    email: str
    password: str
    remember_me: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class TenantInfo:
    """Tenant info in login response."""
    tenant_id: str
    name: str
    slug: str
    role: str
    projects: List[dict]


@dataclass
class LoginResult:
    """Login result."""
    user_id: str
    email: str
    display_name: Optional[str]
    access_token: str
    refresh_token: str
    expires_in: int
    tenants: List[TenantInfo]
    active_tenant: Optional[TenantInfo]
    active_project: Optional[dict]
    requires_context_selection: bool
    redirect_url: str


class LoginUseCase:
    """Login user with email/password."""

    def __init__(
        self,
        auth_provider: IAuthProvider,
        token_service: ITokenService,
        user_repo: IUserRepository,
        tenant_service=None,  # For loading user's tenants
        event_bus=None,
    ):
        self._auth = auth_provider
        self._tokens = token_service
        self._users = user_repo
        self._tenants = tenant_service
        self._events = event_bus

    async def execute(self, request: LoginRequest) -> LoginResult:
        """Execute login.

        Args:
            request: Login credentials

        Returns:
            LoginResult with tokens and context

        Raises:
            InvalidCredentialsError: If credentials are wrong
            AccountNotVerifiedError: If email not verified
            AccountSuspendedError: If account is suspended
        """
        # 1. Validate input
        if not request.email or not request.email.strip():
            raise ValidationError("Email is required", field="email")
        if not request.password:
            raise ValidationError("Password is required", field="password")

        # 2. Find user by email
        user = await self._users.get_by_email(request.email)
        if not user:
            await self._emit_login_failed(request.email, "invalid_credentials", request.ip_address)
            raise InvalidCredentialsError()

        # 3. Check if account is locked (brute force protection)
        if await self._users.is_account_locked(user.user_id):
            lockout_info = await self._users.get_lockout_info(user.user_id)
            unlock_at = lockout_info.get("locked_until") if lockout_info else None
            await self._emit_login_failed(request.email, "account_locked", request.ip_address)
            raise AccountLockedError(unlock_at=unlock_at)

        # 4. Verify password
        if not await self._auth.verify_password(request.password, user.password_hash or ""):
            # Record failed attempt (may trigger lockout)
            lockout_result = await self._users.record_failed_login(
                user.user_id,
                ip_address=request.ip_address
            )
            await self._emit_login_failed(request.email, "invalid_credentials", request.ip_address)

            if lockout_result.get("is_locked"):
                # Account just got locked - inform user
                raise AccountLockedError()

            raise InvalidCredentialsError()

        # 6. Check account status
        if user.status == UserStatus.PENDING_VERIFICATION:
            await self._emit_login_failed(request.email, "not_verified", request.ip_address)
            raise AccountNotVerifiedError()

        if user.status == UserStatus.SUSPENDED:
            await self._emit_login_failed(request.email, "suspended", request.ip_address)
            raise AccountSuspendedError()

        # 7. Reset failed login counter and update last login
        await self._users.reset_failed_logins(user.user_id)
        await self._users.update_last_login(user.user_id)

        # 8. Load user's tenants
        tenants = await self._load_user_tenants(str(user.user_id))

        # 9. Determine context
        active_tenant = None
        active_project = None
        requires_selection = False
        redirect_url = "/app/select-tenant"

        if len(tenants) == 1:
            # Single tenant - auto-select
            active_tenant = tenants[0]
            if active_tenant.projects:
                # Find default project or first project
                default_project = next(
                    (p for p in active_tenant.projects if p.get("is_default")),
                    active_tenant.projects[0]
                )
                active_project = default_project
                redirect_url = f"/app/{active_tenant.slug}/{default_project['slug']}/dashboard"
        elif len(tenants) > 1:
            # Multiple tenants - require selection
            requires_selection = True

        # 10. Create token pair
        token_contexts = [
            TenantContext(
                tenant_id=t.tenant_id,
                slug=t.slug,
                role=t.role,
                projects=t.projects,
            )
            for t in tenants
        ]

        token_pair = await self._tokens.create_token_pair(
            user_id=str(user.user_id),
            email=user.email,
            display_name=user.display_name,
            tenants=token_contexts,
            active_tenant_id=active_tenant.tenant_id if active_tenant else None,
            active_project_id=active_project["project_id"] if active_project else None,
            remember_me=request.remember_me,
        )

        # 11. Emit login event
        if self._events:
            await self._events.publish(UserLoggedIn(
                user_id=user.user_id,
                email=user.email,
                auth_provider=user.auth_provider.value,
                ip_address=request.ip_address,
                user_agent=request.user_agent,
            ))

        return LoginResult(
            user_id=str(user.user_id),
            email=user.email,
            display_name=user.display_name,
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_in=token_pair.expires_in,
            tenants=tenants,
            active_tenant=active_tenant,
            active_project=active_project,
            requires_context_selection=requires_selection,
            redirect_url=redirect_url,
        )

    async def _load_user_tenants(self, user_id: str) -> List[TenantInfo]:
        """Load user's tenants and projects.

        Uses TenantLoaderService to fetch tenants with their projects.
        """
        if not self._tenants:
            return []

        # Use tenant loader service to get tenants with projects
        tenant_infos = await self._tenants.get_user_tenants(user_id)

        return [
            TenantInfo(
                tenant_id=t.tenant_id,
                name=t.name,
                slug=t.slug,
                role=t.role,
                projects=t.projects,
            )
            for t in tenant_infos
        ]

    async def _emit_login_failed(
        self,
        email: str,
        reason: str,
        ip_address: Optional[str]
    ) -> None:
        """Emit login failed event."""
        if self._events:
            await self._events.publish(LoginFailed(
                email=email,
                reason=reason,
                ip_address=ip_address,
            ))
