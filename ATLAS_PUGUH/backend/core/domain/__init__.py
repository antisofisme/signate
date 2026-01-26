"""
Domain Layer - ATLAS_PUGUH Core Service

Pure domain logic with no external dependencies.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from .value_objects import (
    Outcome,
    WorkflowState,
    WorkflowAction,
    Context,
    TenantId,
    DecisionId,
    WorkflowId,
    RuleId,
    IdempotencyKey,
    RuleVersion,
    Metadata
)

from .events import (
    DomainEvent,
    DecisionCreated,
    WorkflowPendingApproval,
    WorkflowApproved,
    WorkflowRejected,
    WorkflowDelegated,
    WorkflowEscalated
)

from .aggregates import (
    Decision,
    Workflow
)

__all__ = [
    # Value Objects
    "Outcome",
    "WorkflowState",
    "WorkflowAction",
    "Context",
    "TenantId",
    "DecisionId",
    "WorkflowId",
    "RuleId",
    "IdempotencyKey",
    "RuleVersion",
    "Metadata",
    # Events
    "DomainEvent",
    "DecisionCreated",
    "WorkflowPendingApproval",
    "WorkflowApproved",
    "WorkflowRejected",
    "WorkflowDelegated",
    "WorkflowEscalated",
    # Aggregates
    "Decision",
    "Workflow",
]
