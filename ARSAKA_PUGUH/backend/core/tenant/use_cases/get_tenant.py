"""
Get Tenant Use Case

Business logic for retrieving tenant details.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..interfaces.tenant_repository import ITenantRepository
from ..interfaces.membership_repository import IMembershipRepository
from ..domain.tenant import Tenant
from ..domain.membership import TenantMembership
from ..exceptions import TenantNotFoundError, NotMemberError


@dataclass
class GetTenantInput:
    """Input data for getting a tenant."""
    tenant_id: Optional[UUID] = None
    tenant_slug: Optional[str] = None
    actor_user_id: Optional[UUID] = None  # For permission check


@dataclass
class GetTenantOutput:
    """Output data from getting a tenant."""
    tenant: Tenant
    membership: Optional[TenantMembership] = None
    member_count: int = 0


class GetTenantUseCase:
    """
    Get tenant by ID or slug.

    Optionally validates that actor is a member.

    Source: INFRA-DEC-007-identity-model.md
    """

    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
    ):
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo

    async def execute(self, input_data: GetTenantInput) -> GetTenantOutput:
        """Execute the use case.

        Args:
            input_data: Tenant lookup data

        Returns:
            Tenant details

        Raises:
            TenantNotFoundError: If tenant not found
            NotMemberError: If actor is not a member (when actor_user_id provided)
        """
        # 1. Get tenant by ID or slug
        tenant = None
        if input_data.tenant_id:
            tenant = await self._tenant_repo.get_by_id(input_data.tenant_id)
        elif input_data.tenant_slug:
            tenant = await self._tenant_repo.get_by_slug(input_data.tenant_slug)

        if not tenant:
            raise TenantNotFoundError(str(input_data.tenant_id or input_data.tenant_slug))

        # 2. Check membership if actor provided
        membership = None
        if input_data.actor_user_id:
            membership = await self._membership_repo.get_by_user_and_tenant(
                input_data.actor_user_id,
                tenant.tenant_id
            )

            if not membership or not membership.is_active():
                raise NotMemberError(str(input_data.actor_user_id), str(tenant.tenant_id))

        # 3. Get member count
        member_count = await self._membership_repo.count_by_tenant(tenant.tenant_id)

        return GetTenantOutput(
            tenant=tenant,
            membership=membership,
            member_count=member_count,
        )
