"""
Create Tenant Use Case

Business logic for creating a new tenant.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..interfaces.tenant_repository import ITenantRepository
from ..interfaces.membership_repository import IMembershipRepository
from ..domain.tenant import Tenant, TenantPlan
from ..domain.membership import TenantMembership
from ..domain.events import TenantCreatedEvent, MemberAddedEvent


@dataclass
class CreateTenantInput:
    """Input data for creating a tenant."""
    name: str
    owner_user_id: UUID
    slug: Optional[str] = None
    billing_email: Optional[str] = None


@dataclass
class CreateTenantOutput:
    """Output data from creating a tenant."""
    tenant: Tenant
    owner_membership: TenantMembership
    events: list


class CreateTenantUseCase:
    """
    Create a new tenant.

    Creates:
    1. The tenant entity
    2. Owner membership for the creator

    Source: INFRA-DEC-007-identity-model.md
    """

    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
    ):
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo

    async def execute(self, input_data: CreateTenantInput) -> CreateTenantOutput:
        """Execute the use case.

        Args:
            input_data: Tenant creation data

        Returns:
            Created tenant and owner membership

        Raises:
            TenantSlugExistsError: If slug already exists
        """
        events = []

        # 1. Create tenant entity
        tenant = Tenant.create(
            name=input_data.name,
            owner_user_id=input_data.owner_user_id,
            slug=input_data.slug,
            plan=TenantPlan.FREE,
            billing_email=input_data.billing_email,
        )

        # 2. Persist tenant
        tenant = await self._tenant_repo.create(tenant)

        # 3. Create owner membership
        owner_membership = TenantMembership.create_owner(
            user_id=input_data.owner_user_id,
            tenant_id=tenant.tenant_id,
        )

        # 4. Persist membership
        owner_membership = await self._membership_repo.create(owner_membership)

        # 5. Create domain events
        events.append(TenantCreatedEvent(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            owner_user_id=tenant.owner_user_id,
            plan=tenant.plan.value,
            actor_user_id=input_data.owner_user_id,
        ))

        events.append(MemberAddedEvent(
            tenant_id=tenant.tenant_id,
            user_id=input_data.owner_user_id,
            role="owner",
            added_via="direct",
            actor_user_id=input_data.owner_user_id,
        ))

        return CreateTenantOutput(
            tenant=tenant,
            owner_membership=owner_membership,
            events=events,
        )
