/**
 * ARSAKA_PUGUH Core Service SDK (TypeScript)
 *
 * TypeScript client library for decision engine and workflow orchestration.
 * Source: INFRA-LAY3-002 (Core Service Implementation Standards)
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
 *   context: { room_id: '101', guest_count: 2 },
 *   idempotency_key: 'req-12345'
 * });
 *
 * console.log(`Decision ID: ${response.decision_id}`);
 * console.log(`Outcome: ${response.outcome}`);
 *
 * if (response.workflow_id) {
 *   console.log(`Workflow created: ${response.workflow_id}`);
 * }
 * ```
 */

export { CoreServiceClient } from "./client";
export type { CoreServiceClientConfig } from "./client";

export type {
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

export {
  CoreServiceError,
  IdempotencyConflictError,
  WorkflowNotFoundError,
  ApproverRoleMismatchError,
  InvalidWorkflowTransitionError,
  TenantIsolationViolationError,
  NetworkError,
  ValidationError,
} from "./exceptions";
