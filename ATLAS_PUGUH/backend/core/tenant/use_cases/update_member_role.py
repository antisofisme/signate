"""
Update Member Role Use Case

Business logic for changing a member's role.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass
from uuid import UUID

from ..interfaces.tenant_repository import ITenantRepository
from ..interfaces.membership_repository import IMembershipRepository
from ..domain.membership import MemberRole
from ..domain.events import MemberRoleChangedEvent
from ..exceptions import (
    TenantNotFoundError,
    NotMemberError,
    InsufficientPermissionError,
    CannotDemoteOwnerError,
)


@dataclass
class UpdateMemberRoleInput:
    """Input data for updating member role."""
    tenant_id: UUID
    target_user_id: UUID  # Whose role to change
    actor_user_id: UUID  # Who is making the change
    new_role: MemberRole


@dataclass
class UpdateMemberRoleOutput:
    """Output data from updating member role."""
    success: bool
    old_role: MemberRole
    new_role: MemberRole
    events: list


class UpdateMemberRoleUseCase:
    """
    Update a member's role in a tenant.

    Rules:
    - Owner can change anyone's role
    - Admin can change member/viewer roles
    - Cannot demote yourself if you're the only owner
    - Cannot promote to a role higher than your own

    Source: INFRA-DEC-007-identity-model.md
    """

    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
    ):
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo

    async def execute(self, input_data: UpdateMemberRoleInput) -> UpdateMemberRoleOutput:
        """Execute the use case.

        Args:
            input_data: Role update data

        Returns:
            Update result

        Raises:
            TenantNotFoundError: If tenant not found
            NotMemberError: If target is not a member
            InsufficientPermissionError: If actor cannot change role
            CannotDemoteOwnerError: If demoting the only owner
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

        old_role = target_membership.role

        # 3. No change needed
        if old_role == input_data.new_role:
            return UpdateMemberRoleOutput(
                success=True,
                old_role=old_role,
                new_role=input_data.new_role,
                events=[],
            )

        # 4. Get actor membership
        actor_membership = await self._membership_repo.get_by_user_and_tenant(
            input_data.actor_user_id,
            input_data.tenant_id
        )
        if not actor_membership:
            raise InsufficientPermissionError("membership required")

        # 5. Check if actor can manage the target's current role
        if not actor_membership.can_manage_role(old_role):
            raise InsufficientPermissionError(f"cannot modify {old_role.value}")

        # 6. Check if actor can assign the new role
        if not actor_membership.can_manage_role(input_data.new_role):
            raise InsufficientPermissionError(f"cannot assign {input_data.new_role.value}")

        # 7. Check owner demotion
        if old_role == MemberRole.OWNER and input_data.new_role != MemberRole.OWNER:
            owner_count = await self._membership_repo.count_owners(input_data.tenant_id)
            if owner_count <= 1:
                raise CannotDemoteOwnerError(str(input_data.tenant_id))

        # 8. Update role
        await self._membership_repo.update_role(target_membership.membership_id, input_data.new_role)

        # 9. Create domain event
        events.append(MemberRoleChangedEvent(
            tenant_id=input_data.tenant_id,
            user_id=input_data.target_user_id,
            old_role=old_role.value,
            new_role=input_data.new_role.value,
            actor_user_id=input_data.actor_user_id,
        ))

        return UpdateMemberRoleOutput(
            success=True,
            old_role=old_role,
            new_role=input_data.new_role,
            events=events,
        )
