/**
 * ATLAS_PUGUH CMS SDK
 *
 * This SDK enforces:
 * - Tenant context on all requests
 * - Subject context on all requests
 * - Idempotency keys on all mutations
 * - Domain separation
 *
 * Phase: 4
 */

export {
  // Main SDK
  AtlasPuguhSDK,
  sdk,

  // Domain Clients
  IAMClient,
  TenantClient,
  DecisionClient,
  WorkflowClient,
  ControlClient,

  // Types
  type RequestContext,
  type PaginationParams,
  type ApiResponse,
} from './client';
