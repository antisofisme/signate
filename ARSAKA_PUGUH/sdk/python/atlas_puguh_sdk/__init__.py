"""
ARSAKA_PUGUH Core Service SDK

Python client library for decision engine and workflow orchestration.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)

Example usage:
    ```python
    from uuid import uuid4
    from arsaka_puguh_sdk import CoreServiceClient, CreateDecisionRequest

    async def main():
        async with CoreServiceClient(base_url="http://localhost:8001") as client:
            request = CreateDecisionRequest(
                tenant_id=uuid4(),
                decision_type="check_in_approval",
                context={"room_id": "101", "guest_count": 2},
                idempotency_key="req-12345"
            )

            response = await client.create_decision(request)
            print(f"Decision ID: {response.decision_id}")
            print(f"Outcome: {response.outcome}")

            if response.workflow_id:
                print(f"Workflow created: {response.workflow_id}")
    ```
"""

from .client import CoreServiceClient
from .types import (
    CreateDecisionRequest,
    CreateDecisionResponse,
    ApproveWorkflowRequest,
    ApproveWorkflowResponse,
    RejectWorkflowRequest,
    RejectWorkflowResponse,
    DelegateWorkflowRequest,
    DelegateWorkflowResponse,
    EscalateWorkflowRequest,
    EscalateWorkflowResponse,
    ErrorResponse,
)
from .exceptions import (
    CoreServiceError,
    IdempotencyConflictError,
    WorkflowNotFoundError,
    ApproverRoleMismatchError,
    InvalidWorkflowTransitionError,
    TenantIsolationViolationError,
    NetworkError,
    ValidationError,
)

__version__ = "1.0.0"

__all__ = [
    # Client
    "CoreServiceClient",
    # Request Types
    "CreateDecisionRequest",
    "ApproveWorkflowRequest",
    "RejectWorkflowRequest",
    "DelegateWorkflowRequest",
    "EscalateWorkflowRequest",
    # Response Types
    "CreateDecisionResponse",
    "ApproveWorkflowResponse",
    "RejectWorkflowResponse",
    "DelegateWorkflowResponse",
    "EscalateWorkflowResponse",
    "ErrorResponse",
    # Exceptions
    "CoreServiceError",
    "IdempotencyConflictError",
    "WorkflowNotFoundError",
    "ApproverRoleMismatchError",
    "InvalidWorkflowTransitionError",
    "TenantIsolationViolationError",
    "NetworkError",
    "ValidationError",
]
