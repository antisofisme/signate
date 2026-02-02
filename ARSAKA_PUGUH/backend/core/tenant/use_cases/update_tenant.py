"""
Update Tenant Use Case

Business logic for updating tenant details.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from uuid import UUID

from ..interfaces.tenant_repository import ITenantRepository
from ..interfaces.membership_repository import IMembershipRepository
from ..domain.tenant import Tenant
from ..domain.events import TenantUpdatedEvent
from ..exceptions import TenantNotFoundError, InsufficientPermissionError


@dataclass
class UpdateTenantInput:
    """Input data for updating a tenant."""
    tenant_id: UUID
    actor_user_id: UUID  # Who is making the update
    name: Optional[str] = None
    billing_email: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


@dataclass
class UpdateTenantOutput:
    """Output data from updating a tenant."""
    tenant: Tenant
    changes: Dict[str, Any]
    events: list


class UpdateTenantUseCase:
    """
    Update tenant details.

    Only owner or admin can update tenant.

    Source: INFRA-DEC-007-identity-model.md
    """

    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
    ):
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo

    async def execute(self, input_data: UpdateTenantInput) -> UpdateTenantOutput:
        """Execute the use case.

        Args:
            input_data: Tenant update data

        Returns:
            Updated tenant

        Raises:
            TenantNotFoundError: If tenant not found
            InsufficientPermissionError: If actor cannot update tenant
        """
        events = []
        changes = {}

        # 1. Get tenant
        tenant = await self._tenant_repo.get_by_id(input_data.tenant_id)
        if not tenant:
            raise TenantNotFoundError(str(input_data.tenant_id))

        # 2. Check permissions
        membership = await self._membership_repo.get_by_user_and_tenant(
            input_data.actor_user_id,
            input_data.tenant_id
        )

        if not membership or not membership.is_admin_or_higher():
            raise InsufficientPermissionError("admin")

        # 3. Track changes and update
        if input_data.name is not None and input_data.name != tenant.name:
            changes["name"] = {"old": tenant.name, "new": input_data.name}
            tenant.name = input_data.name

        if input_data.billing_email is not None and input_data.billing_email != tenant.billing_email:
            changes["billing_email"] = {"old": tenant.billing_email, "new": input_data.billing_email}
            tenant.billing_email = input_data.billing_email

        if input_data.settings is not None:
            changes["settings"] = {"old": tenant.settings.copy(), "new": input_data.settings}
            tenant.settings.update(input_data.settings)

        # 4. Persist if there are changes
        if changes:
            tenant = await self._tenant_repo.update(tenant)

            # 5. Create domain event
            events.append(TenantUpdatedEvent(
                tenant_id=tenant.tenant_id,
                changes=changes,
                actor_user_id=input_data.actor_user_id,
            ))

        return UpdateTenantOutput(
            tenant=tenant,
            changes=changes,
            events=events,
        )
