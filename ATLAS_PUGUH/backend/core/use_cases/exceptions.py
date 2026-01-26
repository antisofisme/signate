"""
Use Case Exceptions

Application-level exceptions for use case layer.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from typing import Optional
from uuid import UUID


class UseCaseError(Exception):
    """Base exception for use case errors"""
    pass


class IdempotencyConflictError(UseCaseError):
    """
    Raised when idempotency key is reused with different context
    Source: INFRA-LAY3-002 §2.2
    HTTP: 409 Conflict
    """
    def __init__(self, existing_decision_id: UUID, message: str = "Idempotency key used with different context"):
        self.existing_decision_id = existing_decision_id
        super().__init__(message)


class WorkflowNotFoundError(UseCaseError):
    """
    Raised when workflow is not found
    HTTP: 404 Not Found
    """
    def __init__(self, workflow_id: UUID):
        self.workflow_id = workflow_id
        super().__init__(f"Workflow not found: {workflow_id}")


class ApproverRoleMismatchError(UseCaseError):
    """
    Raised when approver role does not match workflow approver role
    Source: INFRA-LAY3-002 §3.2
    HTTP: 403 Forbidden
    """
    def __init__(self, expected: str, actual: str):
        self.expected = expected
        self.actual = actual
        super().__init__(f"Approver role mismatch: expected {expected}, got {actual}")


class InvalidWorkflowTransitionError(UseCaseError):
    """
    Raised when workflow state transition is invalid
    Source: INFRA-LAY3-002 §3.1
    HTTP: 400 Bad Request
    """
    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Invalid workflow transition: {from_state} -> {to_state}")


class TenantIsolationViolationError(UseCaseError):
    """
    Raised when cross-tenant access is attempted
    Source: INFRA-LAY3-002 §5
    HTTP: 403 Forbidden
    """
    def __init__(self, message: str = "Cross-tenant access denied"):
        super().__init__(message)
