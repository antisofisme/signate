"""
Invite Member Use Case

Business logic for inviting a user to a tenant.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..interfaces.tenant_repository import ITenantRepository
from ..interfaces.membership_repository import IMembershipRepository
from ..interfaces.invitation_repository import IInvitationRepository
from ..domain.tenant import Tenant
from ..domain.membership import TenantMembership, MemberRole
from ..domain.invitation import Invitation
from ..domain.events import InvitationSentEvent
from ..exceptions import (
    TenantNotFoundError,
    InsufficientPermissionError,
    AlreadyMemberError,
    MaxMembersExceededError,
)


# User repository interface for checking if email exists
class IUserRepository:
    """Minimal interface for user lookup."""
    async def get_by_email(self, email: str):
        pass


@dataclass
class InviteMemberInput:
    """Input data for inviting a member."""
    tenant_id: UUID
    actor_user_id: UUID  # Who is inviting
    email: str
    role: MemberRole
    message: Optional[str] = None


@dataclass
class InviteMemberOutput:
    """Output data from inviting a member."""
    invitation: Invitation
    is_existing_user: bool
    events: list


class InviteMemberUseCase:
    """
    Invite a user to join a tenant.

    Rules:
    - Admin or owner can invite
    - Can only invite to roles below your own level
    - Cannot invite existing members
    - Must not exceed plan limits

    Source: INFRA-DEC-007-identity-model.md
    """

    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
        invitation_repo: IInvitationRepository,
        user_repo: Optional[IUserRepository] = None,
    ):
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo
        self._invitation_repo = invitation_repo
        self._user_repo = user_repo

    async def execute(self, input_data: InviteMemberInput) -> InviteMemberOutput:
        """Execute the use case.

        Args:
            input_data: Invitation data

        Returns:
            Created invitation

        Raises:
            TenantNotFoundError: If tenant not found
            InsufficientPermissionError: If actor cannot invite
            AlreadyMemberError: If email is already a member
            MaxMembersExceededError: If plan limit reached
        """
        events = []

        # 1. Get tenant
        tenant = await self._tenant_repo.get_by_id(input_data.tenant_id)
        if not tenant:
            raise TenantNotFoundError(str(input_data.tenant_id))

        # 2. Check actor's permissions
        actor_membership = await self._membership_repo.get_by_user_and_tenant(
            input_data.actor_user_id,
            input_data.tenant_id
        )

        if not actor_membership or not actor_membership.is_admin_or_higher():
            raise InsufficientPermissionError("admin")

        # 3. Check if actor can assign this role
        if not actor_membership.can_manage_role(input_data.role):
            raise InsufficientPermissionError(f"cannot assign {input_data.role.value} role")

        # 4. Check plan limits
        current_count = await self._membership_repo.count_by_tenant(input_data.tenant_id)
        pending_count = await self._invitation_repo.count_by_tenant(input_data.tenant_id, "pending")
        total = current_count + pending_count

        if not tenant.can_add_member(total):
            raise MaxMembersExceededError(tenant.plan.value, tenant.get_limit("max_members"))

        # 5. Check if user exists and is already a member
        target_user_id = None
        is_existing_user = False

        if self._user_repo:
            existing_user = await self._user_repo.get_by_email(input_data.email)
            if existing_user:
                is_existing_user = True
                target_user_id = existing_user.user_id

                # Check if already a member
                existing_membership = await self._membership_repo.get_by_user_and_tenant(
                    existing_user.user_id,
                    input_data.tenant_id
                )
                if existing_membership:
                    raise AlreadyMemberError(str(existing_user.user_id), str(input_data.tenant_id))

        # 6. Create invitation
        invitation = Invitation.create(
            email=input_data.email,
            tenant_id=input_data.tenant_id,
            role=input_data.role,
            invited_by=input_data.actor_user_id,
            message=input_data.message,
            target_user_id=target_user_id,
        )

        # 7. Persist invitation
        invitation = await self._invitation_repo.create(invitation)

        # 8. Create domain event
        events.append(InvitationSentEvent(
            invitation_id=invitation.invitation_id,
            tenant_id=invitation.tenant_id,
            email=invitation.email,
            role=invitation.role.value,
            actor_user_id=input_data.actor_user_id,
        ))

        return InviteMemberOutput(
            invitation=invitation,
            is_existing_user=is_existing_user,
            events=events,
        )
