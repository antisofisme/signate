"""
Use Case Interfaces

Repository and service interfaces for dependency injection.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ..domain import (
    Decision,
    Workflow,
    TenantId,
    DecisionId,
    WorkflowId,
    Context,
    Outcome,
    IdempotencyKey,
    RuleId,
    RuleVersion
)


class IUnitOfWork(ABC):
    """
    Unit of Work pattern for transaction management
    Source: INFRA-LAY3-002 §2.3
    """

    @abstractmethod
    async def __aenter__(self):
        """Begin transaction"""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction"""
        pass

    @abstractmethod
    async def commit(self):
        """Commit transaction"""
        pass

    @abstractmethod
    async def rollback(self):
        """Rollback transaction"""
        pass


class IDecisionRepository(ABC):
    """
    Decision repository interface
    Source: INFRA-LAY3-002 §2
    """

    @abstractmethod
    async def save(self, decision: Decision) -> None:
        """Save decision to persistence"""
        pass

    @abstractmethod
    async def find_by_id(
        self,
        decision_id: DecisionId,
        tenant_id: TenantId
    ) -> Optional[Decision]:
        """Find decision by ID (tenant-scoped)"""
        pass

    @abstractmethod
    async def find_by_idempotency_key(
        self,
        tenant_id: TenantId,
        idempotency_key: IdempotencyKey
    ) -> Optional[Decision]:
        """
        Find decision by idempotency key
        Source: INFRA-LAY3-002 §2.2
        """
        pass


class IWorkflowRepository(ABC):
    """
    Workflow repository interface
    Source: INFRA-LAY3-002 §3
    """

    @abstractmethod
    async def save(self, workflow: Workflow) -> None:
        """Save workflow to persistence"""
        pass

    @abstractmethod
    async def find_by_id(
        self,
        workflow_id: WorkflowId,
        tenant_id: TenantId
    ) -> Optional[Workflow]:
        """Find workflow by ID (tenant-scoped)"""
        pass


class Rule:
    """
    Rule value object for rule evaluation
    Minimal representation for Phase 1
    """
    def __init__(
        self,
        rule_id: RuleId,
        rule_name: str,
        version: RuleVersion,
        conditions: dict,
        action: dict,
        evaluation_sequence: int
    ):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.version = version
        self.conditions = conditions
        self.action = action
        self.evaluation_sequence = evaluation_sequence


class IRuleRepository(ABC):
    """
    Rule repository interface
    Source: INFRA-LAY3-002 §1
    """

    @abstractmethod
    async def find_active_rules(
        self,
        tenant_id: TenantId,
        decision_type: str
    ) -> List[Rule]:
        """
        Load ACTIVE rules for tenant and decision type
        Ordered by evaluation_sequence ASC
        Source: INFRA-LAY3-002 §1.4, Phase 1 Clarification 1
        """
        pass


class RuleEvaluationResult:
    """Result of rule evaluation"""
    def __init__(
        self,
        outcome: Outcome,
        rule_matched_id: Optional[RuleId] = None,
        rule_version: Optional[RuleVersion] = None
    ):
        self.outcome = outcome
        self.rule_matched_id = rule_matched_id
        self.rule_version = rule_version


class IRuleEvaluationService(ABC):
    """
    Rule evaluation service interface
    Source: INFRA-LAY3-002 §1
    """

    @abstractmethod
    async def evaluate(
        self,
        rules: List[Rule],
        context: Context
    ) -> RuleEvaluationResult:
        """
        Evaluate rules against context
        Returns: outcome + matched rule (if any)
        Source: INFRA-LAY3-002 §1.1 (First-match-wins, deterministic)
        """
        pass


class IIdempotencyRepository(ABC):
    """
    Idempotency cache repository interface
    Source: INFRA-LAY3-002 §2.2, Phase 1 Clarification 2
    """

    @abstractmethod
    async def find(
        self,
        tenant_id: TenantId,
        idempotency_key: IdempotencyKey
    ) -> Optional[DecisionId]:
        """Find cached decision ID by idempotency key"""
        pass

    @abstractmethod
    async def save(
        self,
        tenant_id: TenantId,
        idempotency_key: IdempotencyKey,
        decision_id: DecisionId,
        context_hash: str
    ) -> None:
        """
        Save idempotency cache entry
        context_hash: SHA-256 hash of canonicalized context (Architecture Layer 2.6)
        """
        pass

    @abstractmethod
    async def get_context_hash(
        self,
        tenant_id: TenantId,
        idempotency_key: IdempotencyKey
    ) -> Optional[str]:
        """Get context hash for conflict detection"""
        pass


class IEventRepository(ABC):
    """
    Event log repository interface
    Source: INFRA-DEC-006 (Event & Audit as Immutable Facts)

    Events are FACTS, not triggers. They are persisted synchronously
    within the same transaction as the decision/workflow.
    """

    @abstractmethod
    async def persist_events(
        self,
        tenant_id: TenantId,
        events: list
    ) -> None:
        """
        Persist domain events to event_log table
        MUST be called within the same transaction as decision/workflow save
        Source: INFRA-DEC-006 §3.1
        """
        pass

    @abstractmethod
    async def find_by_aggregate(
        self,
        tenant_id: TenantId,
        aggregate_id: UUID,
        aggregate_type: str
    ) -> list:
        """Find events by aggregate (decision or workflow)"""
        pass
