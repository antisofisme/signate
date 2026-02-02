"""
Exception Handlers

Maps use case exceptions to HTTP responses.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from ..use_cases.exceptions import (
    IdempotencyConflictError,
    WorkflowNotFoundError,
    ApproverRoleMismatchError,
    InvalidWorkflowTransitionError,
    TenantIsolationViolationError
)
from .schemas import ErrorResponse


async def idempotency_conflict_handler(request: Request, exc: IdempotencyConflictError) -> JSONResponse:
    """Handle idempotency conflict (409)"""
    return JSONResponse(
        status_code=409,
        content=ErrorResponse(
            error_code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
            details={"existing_decision_id": str(exc.existing_decision_id)}
        ).dict()
    )


async def workflow_not_found_handler(request: Request, exc: WorkflowNotFoundError) -> JSONResponse:
    """Handle workflow not found (404)"""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error_code="WORKFLOW_NOT_FOUND",
            message=str(exc),
            details={"workflow_id": str(exc.workflow_id)}
        ).dict()
    )


async def approver_role_mismatch_handler(request: Request, exc: ApproverRoleMismatchError) -> JSONResponse:
    """Handle approver role mismatch (403)"""
    return JSONResponse(
        status_code=403,
        content=ErrorResponse(
            error_code="APPROVER_ROLE_MISMATCH",
            message=str(exc),
            details={"expected": exc.expected, "actual": exc.actual}
        ).dict()
    )


async def invalid_workflow_transition_handler(request: Request, exc: InvalidWorkflowTransitionError) -> JSONResponse:
    """Handle invalid workflow transition (400)"""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error_code="INVALID_WORKFLOW_TRANSITION",
            message=str(exc),
            details={"from_state": exc.from_state, "to_state": exc.to_state}
        ).dict()
    )


async def tenant_isolation_violation_handler(request: Request, exc: TenantIsolationViolationError) -> JSONResponse:
    """Handle tenant isolation violation (403)"""
    return JSONResponse(
        status_code=403,
        content=ErrorResponse(
            error_code="TENANT_ISOLATION_VIOLATION",
            message=str(exc)
        ).dict()
    )


EXCEPTION_HANDLERS = {
    IdempotencyConflictError: idempotency_conflict_handler,
    WorkflowNotFoundError: workflow_not_found_handler,
    ApproverRoleMismatchError: approver_role_mismatch_handler,
    InvalidWorkflowTransitionError: invalid_workflow_transition_handler,
    TenantIsolationViolationError: tenant_isolation_violation_handler,
}
