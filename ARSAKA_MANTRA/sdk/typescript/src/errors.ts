/**
 * MANTRA SDK Errors
 */

export class MantraError extends Error {
  public readonly code?: string;
  public readonly details?: Record<string, unknown>;

  constructor(message: string, code?: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'MantraError';
    this.code = code;
    this.details = details;
  }
}

export class ValidationError extends MantraError {
  public readonly violations: Array<{
    rule_id: string;
    severity: string;
    message: string;
  }>;

  constructor(message: string, violations: Array<{ rule_id: string; severity: string; message: string }> = []) {
    super(message, 'VALIDATION_FAILED');
    this.name = 'ValidationError';
    this.violations = violations;
  }
}

export class AuthorizationError extends MantraError {
  constructor(message: string = 'This operation requires human authorization') {
    super(message, 'AUTHORIZATION_REQUIRED');
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends MantraError {
  public readonly resource: string;
  public readonly identifier: string;

  constructor(resource: string, identifier: string) {
    super(`${resource} not found: ${identifier}`, 'NOT_FOUND');
    this.name = 'NotFoundError';
    this.resource = resource;
    this.identifier = identifier;
  }
}

export class ConnectionError extends MantraError {
  constructor(message: string = 'Failed to connect to MANTRA backend') {
    super(message, 'CONNECTION_ERROR');
    this.name = 'ConnectionError';
  }
}

export class RateLimitError extends MantraError {
  public readonly retryAfter?: number;

  constructor(retryAfter?: number) {
    let message = 'Rate limit exceeded';
    if (retryAfter) {
      message += `. Retry after ${retryAfter} seconds`;
    }
    super(message, 'RATE_LIMIT_EXCEEDED');
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}
