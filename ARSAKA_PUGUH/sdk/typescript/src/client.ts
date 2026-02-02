/**
 * Core Service SDK Client
 *
 * TypeScript client for ARSAKA_PUGUH Core Service HTTP API.
 * Source: INFRA-LAY3-002 (Core Service Implementation Standards)
 */

import type {
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
} from "./types";

import {
  CoreServiceError,
  IdempotencyConflictError,
  WorkflowNotFoundError,
  ApproverRoleMismatchError,
  InvalidWorkflowTransitionError,
  TenantIsolationViolationError,
  NetworkError,
  ValidationError,
} from "./exceptions";

export interface CoreServiceClientConfig {
  baseUrl: string;
  timeout?: number;
  apiKey?: string;
}

/**
 * HTTP client for Core Service API
 *
 * Provides methods for decision creation and workflow management.
 *
 * @example
 * ```typescript
 * import { CoreServiceClient } from '@arsaka-puguh/core-service-sdk';
 *
 * const client = new CoreServiceClient({
 *   baseUrl: 'http://localhost:8001'
 * });
 *
 * const response = await client.createDecision({
 *   tenant_id: '550e8400-e29b-41d4-a716-446655440000',
 *   decision_type: 'check_in_approval',
 *   context: { room_id: '101', guest_count: 2 }
 * });
 *
 * console.log(`Decision: ${response.outcome}`);
 * ```
 *
 * Source: INFRA-LAY3-002 §5 (SDK Contract)
 */
export class CoreServiceClient {
  private readonly baseUrl: string;
  private readonly timeout: number;
  private readonly apiKey?: string;

  constructor(config: CoreServiceClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.timeout = config.timeout ?? 30000;
    this.apiKey = config.apiKey;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: any
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        await this.handleErrorResponse(response);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof CoreServiceError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === "AbortError") {
          throw new NetworkError(`Request timeout after ${this.timeout}ms`);
        }
        throw new NetworkError(`Network request failed: ${error.message}`);
      }

      throw new NetworkError("Unknown network error");
    }
  }

  private async handleErrorResponse(response: Response): Promise<never> {
    let errorData: ErrorResponse;

    try {
      errorData = await response.json();
    } catch {
      // Fallback if response is not valid JSON
      errorData = {
        error_code: "UNKNOWN_ERROR",
        message: response.statusText || `HTTP ${response.status}`,
      };
    }

    const { error_code, message, details = {} } = errorData;

    // Map error codes to exception classes
    switch (error_code) {
      case "IDEMPOTENCY_CONFLICT":
        throw new IdempotencyConflictError(
          message,
          details.existing_decision_id || "unknown",
          details
        );

      case "WORKFLOW_NOT_FOUND":
        throw new WorkflowNotFoundError(
          message,
          details.workflow_id || "unknown",
          details
        );

      case "APPROVER_ROLE_MISMATCH":
        throw new ApproverRoleMismatchError(
          message,
          details.expected || "unknown",
          details.actual || "unknown",
          details
        );

      case "INVALID_WORKFLOW_TRANSITION":
        throw new InvalidWorkflowTransitionError(
          message,
          details.from_state || "unknown",
          details.to_state || "unknown",
          details
        );

      case "TENANT_ISOLATION_VIOLATION":
        throw new TenantIsolationViolationError(message, details);

      default:
        if (response.status === 422) {
          throw new ValidationError(message, details);
        }
        throw new CoreServiceError(message, error_code, details, response.status);
    }
  }

  /**
   * Create a new decision
   *
   * @param request - Decision creation request
   * @returns Decision creation response
   * @throws {IdempotencyConflictError} If idempotency key conflicts
   * @throws {ValidationError} If request validation fails
   * @throws {NetworkError} If network request fails
   * @throws {CoreServiceError} For other API errors
   *
   * Source: INFRA-LAY3-002 §2.3 (Decision Creation)
   */
  async createDecision(
    request: CreateDecisionRequest
  ): Promise<CreateDecisionResponse> {
    return this.request<CreateDecisionResponse>(
      "POST",
      "/api/v1/decisions",
      request
    );
  }

  /**
   * Approve a workflow
   *
   * @param workflowId - Workflow UUID
   * @param request - Approval request
   * @returns Approval response
   * @throws {WorkflowNotFoundError} If workflow not found
   * @throws {ApproverRoleMismatchError} If approver role mismatches
   * @throws {InvalidWorkflowTransitionError} If transition invalid
   * @throws {NetworkError} If network request fails
   * @throws {CoreServiceError} For other API errors
   *
   * Source: INFRA-LAY3-002 §3.2 (Workflow Approval)
   */
  async approveWorkflow(
    workflowId: string,
    request: ApproveWorkflowRequest
  ): Promise<ApproveWorkflowResponse> {
    return this.request<ApproveWorkflowResponse>(
      "POST",
      `/api/v1/workflows/${workflowId}/approve`,
      request
    );
  }

  /**
   * Reject a workflow
   *
   * @param workflowId - Workflow UUID
   * @param request - Rejection request
   * @returns Rejection response
   * @throws {WorkflowNotFoundError} If workflow not found
   * @throws {ApproverRoleMismatchError} If approver role mismatches
   * @throws {InvalidWorkflowTransitionError} If transition invalid
   * @throws {NetworkError} If network request fails
   * @throws {CoreServiceError} For other API errors
   *
   * Source: INFRA-LAY3-002 §3.2 (Workflow Rejection)
   */
  async rejectWorkflow(
    workflowId: string,
    request: RejectWorkflowRequest
  ): Promise<RejectWorkflowResponse> {
    return this.request<RejectWorkflowResponse>(
      "POST",
      `/api/v1/workflows/${workflowId}/reject`,
      request
    );
  }

  /**
   * Delegate a workflow
   *
   * @param workflowId - Workflow UUID
   * @param request - Delegation request
   * @returns Delegation response
   * @throws {WorkflowNotFoundError} If workflow not found
   * @throws {ApproverRoleMismatchError} If approver role mismatches
   * @throws {InvalidWorkflowTransitionError} If transition invalid
   * @throws {NetworkError} If network request fails
   * @throws {CoreServiceError} For other API errors
   *
   * Source: INFRA-LAY3-002 §3.3 (Workflow Delegation)
   */
  async delegateWorkflow(
    workflowId: string,
    request: DelegateWorkflowRequest
  ): Promise<DelegateWorkflowResponse> {
    return this.request<DelegateWorkflowResponse>(
      "POST",
      `/api/v1/workflows/${workflowId}/delegate`,
      request
    );
  }

  /**
   * Escalate a workflow
   *
   * @param workflowId - Workflow UUID
   * @param request - Escalation request
   * @returns Escalation response
   * @throws {WorkflowNotFoundError} If workflow not found
   * @throws {InvalidWorkflowTransitionError} If transition invalid
   * @throws {NetworkError} If network request fails
   * @throws {CoreServiceError} For other API errors
   *
   * Source: INFRA-LAY3-002 §3.3 (Workflow Escalation)
   */
  async escalateWorkflow(
    workflowId: string,
    request: EscalateWorkflowRequest
  ): Promise<EscalateWorkflowResponse> {
    return this.request<EscalateWorkflowResponse>(
      "POST",
      `/api/v1/workflows/${workflowId}/escalate`,
      request
    );
  }
}
