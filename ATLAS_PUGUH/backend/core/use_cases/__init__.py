"""
Use Case Layer - ATLAS_PUGUH Core Service

Orchestration logic for business use cases.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from .interfaces import (
    IUnitOfWork,
    IDecisionRepository,
    IWorkflowRepository,
    IRuleRepository,
    IIdempotencyRepository,
    IRuleEvaluationService,
    Rule,
    RuleEvaluationResult
)

from .exceptions import (
    UseCaseError,
    IdempotencyConflictError,
    WorkflowNotFoundError,
    ApproverRoleMismatchError,
    InvalidWorkflowTransitionError,
    TenantIsolationViolationError
)

from .dtos import (
    CreateDecisionInput,
    CreateDecisionOutput,
    ApproveWorkflowInput,
    ApproveWorkflowOutput,
    RejectWorkflowInput,
    RejectWorkflowOutput,
    DelegateWorkflowInput,
    DelegateWorkflowOutput,
    EscalateWorkflowInput,
    EscalateWorkflowOutput
)

from .create_decision import CreateDecisionUseCase
from .approve_workflow import ApproveWorkflowUseCase
from .reject_workflow import RejectWorkflowUseCase
from .delegate_workflow import DelegateWorkflowUseCase
from .escalate_workflow import EscalateWorkflowUseCase

__all__ = [
    # Interfaces
    "IUnitOfWork",
    "IDecisionRepository",
    "IWorkflowRepository",
    "IRuleRepository",
    "IIdempotencyRepository",
    "IRuleEvaluationService",
    "Rule",
    "RuleEvaluationResult",
    # Exceptions
    "UseCaseError",
    "IdempotencyConflictError",
    "WorkflowNotFoundError",
    "ApproverRoleMismatchError",
    "InvalidWorkflowTransitionError",
    "TenantIsolationViolationError",
    # DTOs
    "CreateDecisionInput",
    "CreateDecisionOutput",
    "ApproveWorkflowInput",
    "ApproveWorkflowOutput",
    "RejectWorkflowInput",
    "RejectWorkflowOutput",
    "DelegateWorkflowInput",
    "DelegateWorkflowOutput",
    "EscalateWorkflowInput",
    "EscalateWorkflowOutput",
    # Use Cases
    "CreateDecisionUseCase",
    "ApproveWorkflowUseCase",
    "RejectWorkflowUseCase",
    "DelegateWorkflowUseCase",
    "EscalateWorkflowUseCase",
]
