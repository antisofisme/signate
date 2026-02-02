/**
 * SDK Exception Classes
 *
 * Client-side exceptions for Core Service API interactions.
 * Source: INFRA-LAY3-002 (Core Service Implementation Standards)
 */

export class CoreServiceError extends Error {
  public readonly errorCode?: string;
  public readonly details: Record<string, any>;
  public readonly statusCode?: number;

  constructor(
    message: string,
    errorCode?: string,
    details: Record<string, any> = {},
    statusCode?: number
  ) {
    super(message);
    this.name = "CoreServiceError";
    this.errorCode = errorCode;
    this.details = details;
    this.statusCode = statusCode;

    // Maintains proper stack trace for where error was thrown (V8 only)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

export class IdempotencyConflictError extends CoreServiceError {
  public readonly existingDecisionId: string;

  constructor(
    message: string,
    existingDecisionId: string,
    details: Record<string, any> = {}
  ) {
    super(
      message,
      "IDEMPOTENCY_CONFLICT",
      { ...details, existing_decision_id: existingDecisionId },
      409
    );
    this.name = "IdempotencyConflictError";
    this.existingDecisionId = existingDecisionId;
  }
}

export class WorkflowNotFoundError extends CoreServiceError {
  public readonly workflowId: string;

  constructor(
    message: string,
    workflowId: string,
    details: Record<string, any> = {}
  ) {
    super(
      message,
      "WORKFLOW_NOT_FOUND",
      { ...details, workflow_id: workflowId },
      404
    );
    this.name = "WorkflowNotFoundError";
    this.workflowId = workflowId;
  }
}

export class ApproverRoleMismatchError extends CoreServiceError {
  public readonly expected: string;
  public readonly actual: string;

  constructor(
    message: string,
    expected: string,
    actual: string,
    details: Record<string, any> = {}
  ) {
    super(
      message,
      "APPROVER_ROLE_MISMATCH",
      { ...details, expected, actual },
      403
    );
    this.name = "ApproverRoleMismatchError";
    this.expected = expected;
    this.actual = actual;
  }
}

export class InvalidWorkflowTransitionError extends CoreServiceError {
  public readonly fromState: string;
  public readonly toState: string;

  constructor(
    message: string,
    fromState: string,
    toState: string,
    details: Record<string, any> = {}
  ) {
    super(
      message,
      "INVALID_WORKFLOW_TRANSITION",
      { ...details, from_state: fromState, to_state: toState },
      400
    );
    this.name = "InvalidWorkflowTransitionError";
    this.fromState = fromState;
    this.toState = toState;
  }
}

export class TenantIsolationViolationError extends CoreServiceError {
  constructor(message: string, details: Record<string, any> = {}) {
    super(message, "TENANT_ISOLATION_VIOLATION", details, 403);
    this.name = "TenantIsolationViolationError";
  }
}

export class NetworkError extends CoreServiceError {
  constructor(message: string, details: Record<string, any> = {}) {
    super(message, "NETWORK_ERROR", details);
    this.name = "NetworkError";
  }
}

export class ValidationError extends CoreServiceError {
  constructor(message: string, details: Record<string, any> = {}) {
    super(message, "VALIDATION_ERROR", details, 422);
    this.name = "ValidationError";
  }
}
