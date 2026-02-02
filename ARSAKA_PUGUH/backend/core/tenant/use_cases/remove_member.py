"""
Remove Member Use Case

Business logic for removing a member from a tenant.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..interfaces.tenant_repository import ITenantRepository
from ..interfaces.membership_repository import IMembershipRepository
from ..domain.events import MemberRemovedEvent
from ..exceptions import (
    TenantNotFoundError,
    NotMemberError,
    InsufficientPermissionError,
    CannotRemoveOwnerError,
)


@dataclass
class RemoveMemberInput:
    """Input data for removing a member."""
    tenant_id: UUID
    target_user_id: UUID  # Who to remove
    actor_user_id: UUID  # Who is removing
    reason: Optional[str] = None


@dataclass
class RemoveMemberOutput:
    """Output data from removing a member."""
    success: bool
    events: list


class RemoveMemberUseCase:
    """
    Remove a member from a tenant.

    Rules:
    - Owner can remove anyone except themselves (must transfer ownership first)
    - Admin can remove members and viewers
    - Members can remove themselves (leave)
    - Cannot remove the only owner

    Source: INFRA-DEC-007-identity-model.md
    """

    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
    ):
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo

    async def execute(self, input_data: RemoveMemberInput) -> RemoveMemberOutput:
        """Execute the use case.

        Args:
            input_data: Removal data

        Returns:
            Removal result

        Raises:
            TenantNotFoundError: If tenant not found
            NotMemberError: If target is not a member
            InsufficientPermissionError: If actor cannot remove target
            CannotRemoveOwnerError: If trying to remove the only owner
        """
        events = []

        # 1. Get tenant
        tenant = await self._tenant_repo.get_by_id(input_data.tenant_id)
        if not tenant:
            raise TenantNotFoundError(str(input_data.tenant_id))

        # 2. Get target membership
        target_membership = await self._membership_repo.get_by_user_and_tenant(
            input_data.target_user_id,
            input_data.tenant_id
        )
        if not target_membership:
            raise NotMemberError(str(input_data.target_user_id), str(input_data.tenant_id))

        # 3. Self-leave check
        is_self_leave = input_data.actor_user_id == input_data.target_user_id

        if is_self_leave:
            # Cannot leave if you're the only owner
            if target_membership.is_owner():
                owner_count = await self._membership_repo.count_owners(input_data.tenant_id)
                if owner_count <= 1:
                    raise CannotRemoveOwnerError(str(input_data.tenant_id))
        else:
            # 4. Get actor membership
            actor_membership = await self._membership_repo.get_by_user_and_tenant(
                input_data.actor_user_id,
                input_data.tenant_id
            )
            if not actor_membership:
                raise InsufficientPermissionError("membership required")

            # 5. Check if actor can remove target
            if not actor_membership.can_manage_role(target_membership.role):
                raise InsufficientPermissionError(f"cannot remove {target_membership.role.value}")

            # 6. Cannot remove owner unless you're also an owner
            if target_membership.is_owner() and not actor_membership.is_owner():
                raise InsufficientPermissionError("owner")

        # 7. Delete membership
        await self._membership_repo.delete(target_membership.membership_id)

        # 8. Create domain event
        events.append(MemberRemovedEvent(
            tenant_id=input_data.tenant_id,
            user_id=input_data.target_user_id,
            removed_by_user_id=input_data.actor_user_id,
            reason=input_data.reason,
            actor_user_id=input_data.actor_user_id,
        ))

        return RemoveMemberOutput(
            success=True,
            events=events,
        )
