"""
Accept Invitation Use Case

Business logic for accepting a tenant invitation.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass
from uuid import UUID

from ..interfaces.tenant_repository import ITenantRepository
from ..interfaces.membership_repository import IMembershipRepository
from ..interfaces.invitation_repository import IInvitationRepository
from ..domain.membership import TenantMembership
from ..domain.events import InvitationAcceptedEvent, MemberAddedEvent
from ..exceptions import (
    InvitationNotFoundError,
    InvitationExpiredError,
    InvitationAlreadyUsedError,
    AlreadyMemberError,
)


@dataclass
class AcceptInvitationInput:
    """Input data for accepting an invitation."""
    token: str  # Invitation token from email link
    user_id: UUID  # Who is accepting


@dataclass
class AcceptInvitationOutput:
    """Output data from accepting an invitation."""
    membership: TenantMembership
    tenant_id: UUID
    events: list


class AcceptInvitationUseCase:
    """
    Accept a tenant invitation.

    Creates membership and updates invitation status.

    Source: INFRA-DEC-007-identity-model.md
    """

    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
        invitation_repo: IInvitationRepository,
    ):
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo
        self._invitation_repo = invitation_repo

    async def execute(self, input_data: AcceptInvitationInput) -> AcceptInvitationOutput:
        """Execute the use case.

        Args:
            input_data: Acceptance data

        Returns:
            Created membership

        Raises:
            InvitationNotFoundError: If token invalid
            InvitationExpiredError: If invitation expired
            InvitationAlreadyUsedError: If already accepted/rejected
            AlreadyMemberError: If user is already a member
        """
        events = []

        # 1. Get invitation by token
        invitation = await self._invitation_repo.get_by_token(input_data.token)
        if not invitation:
            raise InvitationNotFoundError(input_data.token)

        # 2. Validate invitation status
        if not invitation.is_pending():
            raise InvitationAlreadyUsedError(str(invitation.invitation_id))

        if invitation.is_expired():
            # Update status to expired
            invitation.mark_expired()
            await self._invitation_repo.update(invitation)
            raise InvitationExpiredError(str(invitation.invitation_id))

        # 3. Check if already a member
        existing_membership = await self._membership_repo.get_by_user_and_tenant(
            input_data.user_id,
            invitation.tenant_id
        )
        if existing_membership:
            raise AlreadyMemberError(str(input_data.user_id), str(invitation.tenant_id))

        # 4. Create membership
        membership = TenantMembership.create_direct(
            user_id=input_data.user_id,
            tenant_id=invitation.tenant_id,
            role=invitation.role,
            added_by=invitation.invited_by_user_id,
        )

        membership = await self._membership_repo.create(membership)

        # 5. Update invitation
        invitation.accept(input_data.user_id)
        await self._invitation_repo.update(invitation)

        # 6. Create domain events
        events.append(InvitationAcceptedEvent(
            invitation_id=invitation.invitation_id,
            tenant_id=invitation.tenant_id,
            user_id=input_data.user_id,
            actor_user_id=input_data.user_id,
        ))

        events.append(MemberAddedEvent(
            tenant_id=invitation.tenant_id,
            user_id=input_data.user_id,
            role=invitation.role.value,
            added_via="invitation",
            actor_user_id=input_data.user_id,
        ))

        return AcceptInvitationOutput(
            membership=membership,
            tenant_id=invitation.tenant_id,
            events=events,
        )
