"""
Decision Repository Interface (Port)

Abstract interface for Decision data operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..domain import Rule, RuleStatus, Decision


class IDecisionRepository(ABC):
    """Decision repository interface."""

    # =========================================================================
    # Rule Operations
    # =========================================================================

    @abstractmethod
    async def list_rules(
        self,
        tenant_id: UUID,
        status: Optional[RuleStatus] = None,
        decision_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[Rule], int]:
        """List rules in a tenant."""
        pass

    @abstractmethod
    async def get_rule(self, tenant_id: UUID, rule_id: UUID) -> Optional[Rule]:
        """Get rule by ID."""
        pass

    @abstractmethod
    async def get_rule_versions(
        self, tenant_id: UUID, rule_id: UUID
    ) -> List[dict]:
        """Get version history for a rule."""
        pass

    @abstractmethod
    async def create_rule(
        self,
        tenant_id: UUID,
        rule_name: str,
        decision_type: str,
        conditions: dict,
        action: dict,
        created_by: UUID,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Rule:
        """Create a new rule in DRAFT status."""
        pass

    @abstractmethod
    async def activate_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        activated_by: UUID,
    ) -> Rule:
        """Activate a draft rule."""
        pass

    @abstractmethod
    async def deactivate_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        deactivated_by: UUID,
        reason: Optional[str] = None,
    ) -> Rule:
        """Deactivate an active rule (transition to DEPRECATED)."""
        pass

    @abstractmethod
    async def update_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        updated_by: UUID,
        rule_name: Optional[str] = None,
        description: Optional[str] = None,
        conditions: Optional[dict] = None,
        action: Optional[dict] = None,
    ) -> Rule:
        """Update a draft rule. Only DRAFT status rules can be updated."""
        pass

    @abstractmethod
    async def delete_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        deleted_by: UUID,
    ) -> bool:
        """Soft delete a rule. Sets deleted_at timestamp."""
        pass

    # =========================================================================
    # Decision Operations
    # =========================================================================

    @abstractmethod
    async def list_decisions(
        self,
        tenant_id: UUID,
        decision_type: Optional[str] = None,
        outcome: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[Decision], int]:
        """List decisions in a tenant."""
        pass

    @abstractmethod
    async def get_decision(
        self, tenant_id: UUID, decision_id: UUID
    ) -> Optional[Decision]:
        """Get decision by ID."""
        pass

    @abstractmethod
    async def get_decision_events(
        self, tenant_id: UUID, decision_id: UUID
    ) -> List[dict]:
        """Get events for a decision."""
        pass

    @abstractmethod
    async def get_decision_types(self, tenant_id: UUID) -> List[str]:
        """Get distinct decision types available in tenant."""
        pass
