"""
Domain Events for ARSAKA_PUGUH Core Service

Events represent state changes in aggregates.
Source: INFRA-LAY3-002 §4 (Event Emission Standards)
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Any, Dict, Optional


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """
    Base class for all domain events
    Source: INFRA-DEC-006 (Event & Audit as Immutable Facts)
    """
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    # Persistence metadata
    trace_id: Optional[UUID] = None
    caused_by_user_id: Optional[UUID] = None
    source: str = "core"
    schema_version: str = "1.0"

    @property
    def event_type(self) -> str:
        """Return event type for persistence"""
        raise NotImplementedError

    @property
    def aggregate_id(self) -> UUID:
        """Return aggregate ID (decision_id or workflow_id)"""
        raise NotImplementedError

    @property
    def aggregate_type(self) -> str:
        """Return aggregate type ('decision' or 'workflow')"""
        raise NotImplementedError

    def to_payload(self) -> Dict[str, Any]:
        """Convert event to payload for persistence"""
        raise NotImplementedError


@dataclass(frozen=True)
class DecisionCreated(DomainEvent):
    """
    Event: decision.created
    Source: INFRA-LAY3-002 §4.3 EVENT 1
    """
    decision_id: UUID = field(default=None)
    tenant_id: UUID = field(default=None)
    decision_type: str = field(default=None)
    outcome: str = field(default=None)
    rule_matched_id: Optional[UUID] = None
    rule_version: Optional[str] = None
    context_summary: Dict[str, Any] = field(default_factory=dict)
    latency_ms: Optional[int] = None

    @property
    def event_type(self) -> str:
        return "decision.created"

    @property
    def aggregate_id(self) -> UUID:
        return self.decision_id

    @property
    def aggregate_type(self) -> str:
        return "decision"

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "decision_id": str(self.decision_id),
            "tenant_id": str(self.tenant_id),
            "decision_type": self.decision_type,
            "outcome": self.outcome,
            "context_summary": self.context_summary,
        }
        if self.rule_matched_id:
            payload["rule_matched_id"] = str(self.rule_matched_id)
        if self.rule_version:
            payload["rule_version"] = self.rule_version
        if self.latency_ms is not None:
            payload["latency_ms"] = self.latency_ms
        return payload


@dataclass(frozen=True)
class WorkflowPendingApproval(DomainEvent):
    """
    Event: workflow.pending_approval
    Source: INFRA-LAY3-002 §4.3 EVENT 2
    """
    workflow_id: UUID = field(default=None)
    decision_id: UUID = field(default=None)
    tenant_id: UUID = field(default=None)
    approver_role: str = field(default=None)

    @property
    def event_type(self) -> str:
        return "workflow.pending_approval"

    @property
    def aggregate_id(self) -> UUID:
        return self.workflow_id

    @property
    def aggregate_type(self) -> str:
        return "workflow"

    def to_payload(self) -> Dict[str, Any]:
        return {
            "workflow_id": str(self.workflow_id),
            "decision_id": str(self.decision_id),
            "tenant_id": str(self.tenant_id),
            "approver_role": self.approver_role,
        }


@dataclass(frozen=True)
class WorkflowApproved(DomainEvent):
    """
    Event: workflow.approved
    Source: INFRA-LAY3-002 §4.3 EVENT 3
    """
    workflow_id: UUID = field(default=None)
    decision_id: UUID = field(default=None)
    tenant_id: UUID = field(default=None)
    approver_role: str = field(default=None)
    acted_by_user_id: Optional[UUID] = None
    comment: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "workflow.approved"

    @property
    def aggregate_id(self) -> UUID:
        return self.workflow_id

    @property
    def aggregate_type(self) -> str:
        return "workflow"

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "workflow_id": str(self.workflow_id),
            "decision_id": str(self.decision_id),
            "tenant_id": str(self.tenant_id),
            "approver_role": self.approver_role,
            "approved_at": self.occurred_at.isoformat(),
        }
        if self.acted_by_user_id:
            payload["acted_by_user_id"] = str(self.acted_by_user_id)
        if self.comment:
            payload["comment"] = self.comment
        return payload


@dataclass(frozen=True)
class WorkflowRejected(DomainEvent):
    """
    Event: workflow.rejected
    Source: INFRA-LAY3-002 §4.3 EVENT 4
    """
    workflow_id: UUID = field(default=None)
    decision_id: UUID = field(default=None)
    tenant_id: UUID = field(default=None)
    approver_role: str = field(default=None)
    acted_by_user_id: Optional[UUID] = None
    reason: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "workflow.rejected"

    @property
    def aggregate_id(self) -> UUID:
        return self.workflow_id

    @property
    def aggregate_type(self) -> str:
        return "workflow"

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "workflow_id": str(self.workflow_id),
            "decision_id": str(self.decision_id),
            "tenant_id": str(self.tenant_id),
            "approver_role": self.approver_role,
            "rejected_at": self.occurred_at.isoformat(),
        }
        if self.acted_by_user_id:
            payload["acted_by_user_id"] = str(self.acted_by_user_id)
        if self.reason:
            payload["reason"] = self.reason
        return payload


@dataclass(frozen=True)
class WorkflowDelegated(DomainEvent):
    """
    Event: workflow.delegated
    Source: INFRA-LAY3-002 §4.3 EVENT 5
    """
    workflow_id: UUID = field(default=None)
    decision_id: UUID = field(default=None)
    tenant_id: UUID = field(default=None)
    from_approver_role: str = field(default=None)
    delegated_to_user_id: UUID = field(default=None)
    acted_by_user_id: Optional[UUID] = None
    reason: str = field(default=None)

    @property
    def event_type(self) -> str:
        return "workflow.delegated"

    @property
    def aggregate_id(self) -> UUID:
        return self.workflow_id

    @property
    def aggregate_type(self) -> str:
        return "workflow"

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "workflow_id": str(self.workflow_id),
            "decision_id": str(self.decision_id),
            "tenant_id": str(self.tenant_id),
            "from_approver_role": self.from_approver_role,
            "delegated_to_user_id": str(self.delegated_to_user_id),
            "reason": self.reason,
            "delegated_at": self.occurred_at.isoformat(),
        }
        if self.acted_by_user_id:
            payload["acted_by_user_id"] = str(self.acted_by_user_id)
        return payload


@dataclass(frozen=True)
class WorkflowEscalated(DomainEvent):
    """
    Event: workflow.escalated
    Source: INFRA-LAY3-002 §4.3 EVENT 6
    """
    workflow_id: UUID = field(default=None)
    decision_id: UUID = field(default=None)
    tenant_id: UUID = field(default=None)
    from_approver_role: str = field(default=None)
    escalated_to_role: str = field(default=None)
    escalation_reason: str = field(default=None)

    @property
    def event_type(self) -> str:
        return "workflow.escalated"

    @property
    def aggregate_id(self) -> UUID:
        return self.workflow_id

    @property
    def aggregate_type(self) -> str:
        return "workflow"

    def to_payload(self) -> Dict[str, Any]:
        return {
            "workflow_id": str(self.workflow_id),
            "decision_id": str(self.decision_id),
            "tenant_id": str(self.tenant_id),
            "from_approver_role": self.from_approver_role,
            "escalated_to_role": self.escalated_to_role,
            "escalation_reason": self.escalation_reason,
            "escalated_at": self.occurred_at.isoformat(),
        }
