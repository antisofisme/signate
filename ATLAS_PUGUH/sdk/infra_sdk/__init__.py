"""
ATLAS_PUGUH Infra SDK - THIN CLIENT

This SDK is an ADAPTER, not a logic holder.

SDK DOES:
- Validate input structure
- Attach tenant_id, subject_id
- Inject idempotency_key
- Propagate trace_id
- Call Core API

SDK DOES NOT:
- Evaluate rules
- Store state
- Perform smart retry
- Modify decisions
- Provide helper shortcuts
- Use implicit defaults
- Implement fallback behavior

Source: Phase 2 Requirements
"""

from .types import (
    TenantContext,
    SubjectContext,
    RequestContext,
    CreateDecisionRequest,
    CreateDecisionResponse,
    GetDecisionRequest,
    GetDecisionResponse,
    WorkflowActionRequest,
    WorkflowActionResponse,
    WorkflowAction,
)

from .client import InfraClient

from .exceptions import (
    InfraSDKError,
    MissingContextError,
    ValidationError,
    CoreAPIError,
    IdempotencyRequiredError,
)

__version__ = "1.0.0"
__all__ = [
    # Types
    "TenantContext",
    "SubjectContext",
    "RequestContext",
    "CreateDecisionRequest",
    "CreateDecisionResponse",
    "GetDecisionRequest",
    "GetDecisionResponse",
    "WorkflowActionRequest",
    "WorkflowActionResponse",
    "WorkflowAction",
    # Client
    "InfraClient",
    # Exceptions
    "InfraSDKError",
    "MissingContextError",
    "ValidationError",
    "CoreAPIError",
    "IdempotencyRequiredError",
]
