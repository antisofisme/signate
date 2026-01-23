"""
SDK Type Definitions

Data transfer objects matching Core Service API contracts.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from dataclasses import dataclass


@dataclass
class CreateDecisionRequest:
    """Request for creating a decision"""
    tenant_id: UUID
    decision_type: str
    context: Dict[str, Any]
    idempotency_key: Optional[str] = None
    trace_id: Optional[UUID] = None
    requester_user_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            "tenant_id": str(self.tenant_id),
            "decision_type": self.decision_type,
            "context": self.context,
        }
        if self.idempotency_key:
            data["idempotency_key"] = self.idempotency_key
        if self.trace_id:
            data["trace_id"] = str(self.trace_id)
        if self.requester_user_id:
            data["requester_user_id"] = str(self.requester_user_id)
        return data


@dataclass
class CreateDecisionResponse:
    """Response from decision creation"""
    decision_id: UUID
    outcome: str
    rule_matched_id: Optional[UUID]
    rule_version: Optional[str]
    workflow_id: Optional[UUID]
    created_at: datetime


@dataclass
class ApproveWorkflowRequest:
    """Request for approving a workflow"""
    tenant_id: UUID
    approver_role: str
    acted_by_user_id: Optional[UUID] = None
    comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            "tenant_id": str(self.tenant_id),
            "approver_role": self.approver_role,
        }
        if self.acted_by_user_id:
            data["acted_by_user_id"] = str(self.acted_by_user_id)
        if self.comment:
            data["comment"] = self.comment
        return data


@dataclass
class ApproveWorkflowResponse:
    """Response from workflow approval"""
    workflow_id: UUID
    current_state: str
    completed_at: datetime


@dataclass
class RejectWorkflowRequest:
    """Request for rejecting a workflow"""
    tenant_id: UUID
    approver_role: str
    acted_by_user_id: Optional[UUID] = None
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            "tenant_id": str(self.tenant_id),
            "approver_role": self.approver_role,
        }
        if self.acted_by_user_id:
            data["acted_by_user_id"] = str(self.acted_by_user_id)
        if self.reason:
            data["reason"] = self.reason
        return data


@dataclass
class RejectWorkflowResponse:
    """Response from workflow rejection"""
    workflow_id: UUID
    current_state: str
    completed_at: datetime


@dataclass
class DelegateWorkflowRequest:
    """Request for delegating a workflow"""
    tenant_id: UUID
    approver_role: str
    delegated_to_user_id: UUID
    acted_by_user_id: Optional[UUID] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            "tenant_id": str(self.tenant_id),
            "approver_role": self.approver_role,
            "delegated_to_user_id": str(self.delegated_to_user_id),
            "reason": self.reason,
        }
        if self.acted_by_user_id:
            data["acted_by_user_id"] = str(self.acted_by_user_id)
        return data


@dataclass
class DelegateWorkflowResponse:
    """Response from workflow delegation"""
    workflow_id: UUID
    current_state: str
    delegated_to_user_id: UUID


@dataclass
class EscalateWorkflowRequest:
    """Request for escalating a workflow"""
    tenant_id: UUID
    escalated_to_role: str
    escalation_reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "tenant_id": str(self.tenant_id),
            "escalated_to_role": self.escalated_to_role,
            "escalation_reason": self.escalation_reason,
        }


@dataclass
class EscalateWorkflowResponse:
    """Response from workflow escalation"""
    workflow_id: UUID
    current_state: str
    escalated_to_role: str


@dataclass
class ErrorResponse:
    """Standard error response"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
