"""
List Members Use Case

Business logic for listing tenant members.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from ..interfaces.tenant_repository import ITenantRepository
from ..interfaces.membership_repository import IMembershipRepository
from ..interfaces.invitation_repository import IInvitationRepository
from ..domain.membership import TenantMembership
from ..domain.invitation import Invitation
from ..exceptions import TenantNotFoundError, NotMemberError


@dataclass
class ListMembersInput:
    """Input data for listing members."""
    tenant_id: UUID
    actor_user_id: UUID
    include_invitations: bool = True


@dataclass
class MemberInfo:
    """Member info with user details."""
    membership: TenantMembership
    user_email: Optional[str] = None
    user_name: Optional[str] = None


@dataclass
class ListMembersOutput:
    """Output data from listing members."""
    members: List[MemberInfo]
    pending_invitations: List[Invitation]
    total_members: int
    total_pending: int


# User repository interface for getting user details
class IUserRepository:
    """Minimal interface for user lookup."""
    async def get_by_id(self, user_id: UUID):
        pass


class ListMembersUseCase:
    """
    List members of a tenant.

    Includes pending invitations if requested.

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

    async def execute(self, input_data: ListMembersInput) -> ListMembersOutput:
        """Execute the use case.

        Args:
            input_data: List filter data

        Returns:
            List of members and invitations

        Raises:
            TenantNotFoundError: If tenant not found
            NotMemberError: If actor is not a member
        """
        # 1. Get tenant
        tenant = await self._tenant_repo.get_by_id(input_data.tenant_id)
        if not tenant:
            raise TenantNotFoundError(str(input_data.tenant_id))

        # 2. Check actor is a member
        actor_membership = await self._membership_repo.get_by_user_and_tenant(
            input_data.actor_user_id,
            input_data.tenant_id
        )
        if not actor_membership or not actor_membership.is_active():
            raise NotMemberError(str(input_data.actor_user_id), str(input_data.tenant_id))

        # 3. Get memberships
        memberships = await self._membership_repo.list_by_tenant(input_data.tenant_id)

        # 4. Enrich with user details
        members = []
        for membership in memberships:
            user_email = None
            user_name = None

            if self._user_repo:
                user = await self._user_repo.get_by_id(membership.user_id)
                if user:
                    user_email = user.email
                    user_name = user.display_name

            members.append(MemberInfo(
                membership=membership,
                user_email=user_email,
                user_name=user_name,
            ))

        # 5. Get pending invitations if requested
        pending_invitations = []
        if input_data.include_invitations and actor_membership.is_admin_or_higher():
            pending_invitations = await self._invitation_repo.list_by_tenant(
                input_data.tenant_id,
                status="pending"
            )

        return ListMembersOutput(
            members=members,
            pending_invitations=pending_invitations,
            total_members=len(members),
            total_pending=len(pending_invitations),
        )
