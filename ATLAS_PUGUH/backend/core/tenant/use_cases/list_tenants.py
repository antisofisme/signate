"""
List Tenants Use Case

Business logic for listing tenants.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from ..interfaces.tenant_repository import ITenantRepository
from ..interfaces.membership_repository import IMembershipRepository
from ..domain.tenant import Tenant
from ..domain.membership import TenantMembership


@dataclass
class ListTenantsInput:
    """Input data for listing tenants."""
    user_id: UUID
    include_inactive: bool = False


@dataclass
class TenantWithMembership:
    """Tenant with user's membership info."""
    tenant: Tenant
    membership: TenantMembership
    member_count: int


@dataclass
class ListTenantsOutput:
    """Output data from listing tenants."""
    tenants: List[TenantWithMembership]
    total: int


class ListTenantsUseCase:
    """
    List tenants that user is a member of.

    Returns tenants with membership info and member counts.

    Source: INFRA-DEC-007-identity-model.md
    """

    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
    ):
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo

    async def execute(self, input_data: ListTenantsInput) -> ListTenantsOutput:
        """Execute the use case.

        Args:
            input_data: List filter data

        Returns:
            List of tenants with membership info
        """
        # 1. Get user's memberships
        memberships = await self._membership_repo.list_by_user(
            input_data.user_id,
            include_inactive=input_data.include_inactive
        )

        # 2. Get tenants
        tenants = await self._tenant_repo.list_by_user(
            input_data.user_id,
            include_inactive=input_data.include_inactive
        )

        # 3. Build membership map
        membership_map = {m.tenant_id: m for m in memberships}

        # 4. Get member counts and combine
        results = []
        for tenant in tenants:
            membership = membership_map.get(tenant.tenant_id)
            if membership:
                member_count = await self._membership_repo.count_by_tenant(tenant.tenant_id)
                results.append(TenantWithMembership(
                    tenant=tenant,
                    membership=membership,
                    member_count=member_count,
                ))

        return ListTenantsOutput(
            tenants=results,
            total=len(results),
        )
