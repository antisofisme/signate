"""
Verify Email Use Case

Handles email verification after registration.
Activates user account and creates tenant/project.

Source: INFRA-DEC-008-auth-flow.md
"""

from dataclasses import dataclass
from typing import Optional, List

from ..interfaces.token_service import ITokenService, TenantContext
from ..interfaces.user_repository import IUserRepository
from ..domain.events import UserVerified


@dataclass
class VerifyEmailResult:
    """Email verification result."""
    user_id: str
    email: str
    status: str
    access_token: str
    refresh_token: str
    expires_in: int
    tenant: Optional[dict]
    project: Optional[dict]
    redirect_url: str


class VerifyEmailUseCase:
    """Verify email and activate user account."""

    def __init__(
        self,
        token_service: ITokenService,
        user_repo: IUserRepository,
        tenant_service=None,  # For auto-provisioning
        event_bus=None,
    ):
        self._tokens = token_service
        self._users = user_repo
        self._tenants = tenant_service
        self._events = event_bus

    async def execute(self, token: str) -> VerifyEmailResult:
        """Execute email verification.

        Args:
            token: Verification token from email

        Returns:
            VerifyEmailResult with tokens and tenant/project

        Raises:
            TokenInvalidError: If token is invalid
            TokenExpiredError: If token is expired
        """
        # 1. Verify token and get user_id
        user_id = await self._tokens.verify_verification_token(token)

        # 2. Get user
        from uuid import UUID
        user = await self._users.get_by_id(UUID(user_id))
        if not user:
            from ..exceptions import TokenInvalidError
            raise TokenInvalidError("User not found")

        # 3. Mark email as verified
        await self._users.verify_email(user.user_id)

        # 4. Mark token as used
        await self._tokens.mark_token_used(token)

        # 5. Auto-provision tenant and project
        tenant = None
        project = None
        redirect_url = "/app/select-tenant"

        if self._tenants:
            # Create default tenant
            tenant_result = await self._tenants.create_tenant(
                name=f"{user.display_name}'s Workspace",
                owner_user_id=str(user.user_id),
            )
            tenant = {
                "tenant_id": tenant_result.tenant_id,
                "name": tenant_result.name,
                "slug": tenant_result.slug,
            }
            # Default project is created with tenant
            project = {
                "project_id": tenant_result.default_project.project_id,
                "name": tenant_result.default_project.name,
                "slug": tenant_result.default_project.slug,
            }
            redirect_url = f"/app/{tenant['slug']}/{project['slug']}/dashboard"

        # 6. Create token pair
        tenant_contexts = []
        if tenant:
            tenant_contexts = [
                TenantContext(
                    tenant_id=tenant["tenant_id"],
                    slug=tenant["slug"],
                    role="owner",
                    projects=[project] if project else [],
                )
            ]

        token_pair = await self._tokens.create_token_pair(
            user_id=str(user.user_id),
            email=user.email,
            display_name=user.display_name,
            tenants=tenant_contexts,
            active_tenant_id=tenant["tenant_id"] if tenant else None,
            active_project_id=project["project_id"] if project else None,
        )

        # 7. Emit verification event
        if self._events:
            await self._events.publish(UserVerified(
                user_id=user.user_id,
                email=user.email,
            ))

        return VerifyEmailResult(
            user_id=str(user.user_id),
            email=user.email,
            status="active",
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_in=token_pair.expires_in,
            tenant=tenant,
            project=project,
            redirect_url=redirect_url,
        )
