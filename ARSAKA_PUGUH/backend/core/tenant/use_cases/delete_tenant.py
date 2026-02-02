"""
Delete Tenant Use Case

Business logic for soft-deleting a tenant.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass
from uuid import UUID

from ..interfaces.tenant_repository import ITenantRepository
from ..interfaces.membership_repository import IMembershipRepository
from ..domain.events import TenantDeletedEvent
from ..exceptions import TenantNotFoundError, InsufficientPermissionError


@dataclass
class DeleteTenantInput:
    """Input data for deleting a tenant."""
    tenant_id: UUID
    actor_user_id: UUID  # Who is deleting


@dataclass
class DeleteTenantOutput:
    """Output data from deleting a tenant."""
    success: bool
    events: list


class DeleteTenantUseCase:
    """
    Soft-delete a tenant.

    Only owner can delete tenant.
    This performs a soft delete (sets is_deleted = true).

    Source: INFRA-DEC-007-identity-model.md
    """

    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
    ):
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo

    async def execute(self, input_data: DeleteTenantInput) -> DeleteTenantOutput:
        """Execute the use case.

        Args:
            input_data: Tenant deletion data

        Returns:
            Deletion result

        Raises:
            TenantNotFoundError: If tenant not found
            InsufficientPermissionError: If actor is not owner
        """
        events = []

        # 1. Get tenant
        tenant = await self._tenant_repo.get_by_id(input_data.tenant_id)
        if not tenant:
            raise TenantNotFoundError(str(input_data.tenant_id))

        # 2. Check permissions - only owner can delete
        membership = await self._membership_repo.get_by_user_and_tenant(
            input_data.actor_user_id,
            input_data.tenant_id
        )

        if not membership or not membership.is_owner():
            raise InsufficientPermissionError("owner")

        # 3. Soft delete
        await self._tenant_repo.soft_delete(input_data.tenant_id)

        # 4. Create domain event
        events.append(TenantDeletedEvent(
            tenant_id=input_data.tenant_id,
            deleted_by_user_id=input_data.actor_user_id,
            actor_user_id=input_data.actor_user_id,
        ))

        return DeleteTenantOutput(
            success=True,
            events=events,
        )
