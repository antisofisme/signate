"""
SDK Types - Strict Typed Request/Response Objects

NO implicit defaults. NO optional fields that should be required.
Every field is explicitly typed and validated.

Source: Phase 2 Requirements
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from uuid import UUID


# =============================================================================
# CONTEXT TYPES (REQUIRED - NO DEFAULTS)
# =============================================================================

@dataclass(frozen=True)
class TenantContext:
    """
    Tenant context - REQUIRED for all operations.
    NO defaults. Must be explicitly provided.
    """
    tenant_id: UUID

    def __post_init__(self):
        if self.tenant_id is None:
            raise ValueError("tenant_id is REQUIRED")


@dataclass(frozen=True)
class SubjectContext:
    """
    Subject (user/service) context - REQUIRED for all operations.
    NO defaults. Must be explicitly provided.
    """
    subject_id: UUID
    subject_type: str  # "user" or "service"

    def __post_init__(self):
        if self.subject_id is None:
            raise ValueError("subject_id is REQUIRED")
        if self.subject_type not in ("user", "service"):
            raise ValueError("subject_type must be 'user' or 'service'")


@dataclass(frozen=True)
class RequestContext:
    """
    Full request context - REQUIRED for all operations.
    Combines tenant, subject, and trace information.

    NO implicit defaults. All fields must be explicitly provided.
    """
    tenant: TenantContext
    subject: SubjectContext
    trace_id: UUID
    idempotency_key: str  # REQUIRED for create operations

    def __post_init__(self):
        if self.tenant is None:
            raise ValueError("tenant context is REQUIRED")
        if self.subject is None:
            raise ValueError("subject context is REQUIRED")
        if self.trace_id is None:
            raise ValueError("trace_id is REQUIRED")
        # idempotency_key validation is done per-operation


# =============================================================================
# CREATE DECISION TYPES
# =============================================================================

@dataclass(frozen=True)
class CreateDecisionRequest:
    """
    Request to create a decision.

    SDK validates structure only. Core evaluates rules.
    """
    context: RequestContext
    decision_type: str
    decision_context: Dict[str, Any]

    def __post_init__(self):
        if self.context is None:
            raise ValueError("context is REQUIRED")
        if not self.decision_type:
            raise ValueError("decision_type is REQUIRED and cannot be empty")
        if self.decision_context is None:
            raise ValueError("decision_context is REQUIRED")
        # Idempotency key is REQUIRED for create operations
        if not self.context.idempotency_key:
            raise ValueError("idempotency_key is REQUIRED for create_decision")


@dataclass(frozen=True)
class CreateDecisionResponse:
    """
    Response from create_decision.

    Immutable - represents the decision as returned by Core.
    """
    decision_id: UUID
    outcome: str  # "ALLOWED", "DENIED", "REQUIRE_APPROVAL"
    rule_matched_id: Optional[UUID]
    rule_version: Optional[str]
    workflow_id: Optional[UUID]  # Present if outcome is REQUIRE_APPROVAL
    created_at: datetime
    trace_id: UUID


# =============================================================================
# GET DECISION TYPES
# =============================================================================

@dataclass(frozen=True)
class GetDecisionRequest:
    """
    Request to get an existing decision.

    Note: idempotency_key is NOT required for read operations.
    """
    context: RequestContext
    decision_id: UUID

    def __post_init__(self):
        if self.context is None:
            raise ValueError("context is REQUIRED")
        if self.decision_id is None:
            raise ValueError("decision_id is REQUIRED")


@dataclass(frozen=True)
class GetDecisionResponse:
    """
    Response from get_decision.

    Immutable - represents the decision as returned by Core.
    """
    decision_id: UUID
    tenant_id: UUID
    decision_type: str
    decision_context: Dict[str, Any]
    outcome: str
    rule_matched_id: Optional[UUID]
    rule_version: Optional[str]
    workflow_id: Optional[UUID]
    created_at: datetime


# =============================================================================
# WORKFLOW ACTION TYPES
# =============================================================================

class WorkflowAction(Enum):
    """
    Allowed workflow actions.

    NO shortcuts. NO aliases. Explicit action names only.
    """
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    DELEGATE = "DELEGATE"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class WorkflowActionRequest:
    """
    Request to perform a workflow action.

    Idempotency key is REQUIRED.
    """
    context: RequestContext
    workflow_id: UUID
    action: WorkflowAction
    comment: Optional[str] = None
    delegate_to_user_id: Optional[UUID] = None  # Required for DELEGATE
    escalate_to_role: Optional[str] = None  # Required for ESCALATE

    def __post_init__(self):
        if self.context is None:
            raise ValueError("context is REQUIRED")
        if self.workflow_id is None:
            raise ValueError("workflow_id is REQUIRED")
        if self.action is None:
            raise ValueError("action is REQUIRED")
        # Idempotency key is REQUIRED for workflow actions
        if not self.context.idempotency_key:
            raise ValueError("idempotency_key is REQUIRED for workflow actions")
        # Validate action-specific requirements
        if self.action == WorkflowAction.DELEGATE and not self.delegate_to_user_id:
            raise ValueError("delegate_to_user_id is REQUIRED for DELEGATE action")
        if self.action == WorkflowAction.ESCALATE and not self.escalate_to_role:
            raise ValueError("escalate_to_role is REQUIRED for ESCALATE action")


@dataclass(frozen=True)
class WorkflowActionResponse:
    """
    Response from workflow action.

    Represents the workflow state after the action.
    """
    workflow_id: UUID
    decision_id: UUID
    current_state: str
    completed_at: Optional[datetime]
    trace_id: UUID
