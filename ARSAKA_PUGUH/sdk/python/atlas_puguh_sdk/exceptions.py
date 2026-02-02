"""
SDK Exception Classes

Client-side exceptions for Core Service API interactions.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from typing import Optional, Dict, Any


class CoreServiceError(Exception):
    """Base exception for Core Service SDK errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code


class IdempotencyConflictError(CoreServiceError):
    """Raised when idempotency key conflicts with different context (HTTP 409)"""

    def __init__(self, message: str, existing_decision_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="IDEMPOTENCY_CONFLICT",
            details=details or {"existing_decision_id": existing_decision_id},
            status_code=409
        )
        self.existing_decision_id = existing_decision_id


class WorkflowNotFoundError(CoreServiceError):
    """Raised when workflow is not found (HTTP 404)"""

    def __init__(self, message: str, workflow_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="WORKFLOW_NOT_FOUND",
            details=details or {"workflow_id": workflow_id},
            status_code=404
        )
        self.workflow_id = workflow_id


class ApproverRoleMismatchError(CoreServiceError):
    """Raised when approver role does not match expected role (HTTP 403)"""

    def __init__(self, message: str, expected: str, actual: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="APPROVER_ROLE_MISMATCH",
            details=details or {"expected": expected, "actual": actual},
            status_code=403
        )
        self.expected = expected
        self.actual = actual


class InvalidWorkflowTransitionError(CoreServiceError):
    """Raised when workflow transition is invalid (HTTP 400)"""

    def __init__(self, message: str, from_state: str, to_state: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_WORKFLOW_TRANSITION",
            details=details or {"from_state": from_state, "to_state": to_state},
            status_code=400
        )
        self.from_state = from_state
        self.to_state = to_state


class TenantIsolationViolationError(CoreServiceError):
    """Raised when tenant isolation is violated (HTTP 403)"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TENANT_ISOLATION_VIOLATION",
            details=details,
            status_code=403
        )


class NetworkError(CoreServiceError):
    """Raised when network request fails"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            details=details
        )


class ValidationError(CoreServiceError):
    """Raised when request validation fails (HTTP 422)"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=422
        )
