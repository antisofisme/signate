"""
Data Transfer Objects for Use Cases

Input/Output DTOs for use case layer.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from ..domain import DomainEvent


@dataclass(frozen=True)
class CreateDecisionInput:
    """Input for CreateDecisionUseCase"""
    tenant_id: UUID
    decision_type: str
    context: Dict[str, Any]
    idempotency_key: Optional[str] = None
    trace_id: Optional[UUID] = None
    requester_user_id: Optional[UUID] = None


@dataclass(frozen=True)
class CreateDecisionOutput:
    """Output for CreateDecisionUseCase"""
    decision_id: UUID
    outcome: str
    rule_matched_id: Optional[UUID]
    rule_version: Optional[str]
    workflow_id: Optional[UUID]
    created_at: datetime
    events: List[DomainEvent]


@dataclass(frozen=True)
class ApproveWorkflowInput:
    """Input for ApproveWorkflowUseCase"""
    workflow_id: UUID
    tenant_id: UUID
    approver_role: str
    acted_by_user_id: Optional[UUID] = None
    comment: Optional[str] = None


@dataclass(frozen=True)
class ApproveWorkflowOutput:
    """Output for ApproveWorkflowUseCase"""
    workflow_id: UUID
    current_state: str
    completed_at: datetime
    events: List[DomainEvent]


@dataclass(frozen=True)
class RejectWorkflowInput:
    """Input for RejectWorkflowUseCase"""
    workflow_id: UUID
    tenant_id: UUID
    approver_role: str
    acted_by_user_id: Optional[UUID] = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class RejectWorkflowOutput:
    """Output for RejectWorkflowUseCase"""
    workflow_id: UUID
    current_state: str
    completed_at: datetime
    events: List[DomainEvent]


@dataclass(frozen=True)
class DelegateWorkflowInput:
    """Input for DelegateWorkflowUseCase"""
    workflow_id: UUID
    tenant_id: UUID
    approver_role: str
    delegated_to_user_id: UUID
    acted_by_user_id: Optional[UUID] = None
    reason: str = ""


@dataclass(frozen=True)
class DelegateWorkflowOutput:
    """Output for DelegateWorkflowUseCase"""
    workflow_id: UUID
    current_state: str
    delegated_to_user_id: UUID
    events: List[DomainEvent]


@dataclass(frozen=True)
class EscalateWorkflowInput:
    """Input for EscalateWorkflowUseCase"""
    workflow_id: UUID
    tenant_id: UUID
    escalated_to_role: str
    escalation_reason: str


@dataclass(frozen=True)
class EscalateWorkflowOutput:
    """Output for EscalateWorkflowUseCase"""
    workflow_id: UUID
    current_state: str
    escalated_to_role: str
    events: List[DomainEvent]
