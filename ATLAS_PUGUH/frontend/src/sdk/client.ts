/**
 * ATLAS_PUGUH CMS SDK Client
 *
 * CRITICAL RULES:
 * - ALL API calls go through this client
 * - ALL mutations require idempotency_key
 * - ALL requests require tenant + subject context
 * - NO direct fetch() calls allowed
 *
 * Phase: 4
 */

import { v4 as uuidv4 } from 'uuid';

// =============================================================================
// TYPES
// =============================================================================

export interface RequestContext {
  tenant_id: string;
  subject_id: string;
  subject_type: 'user' | 'service';
  trace_id: string;
  idempotency_key?: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta?: {
    page: number;
    limit: number;
    total: number;
  };
}

// =============================================================================
// CONTEXT VALIDATION
// =============================================================================

function validateContext(context: RequestContext, requireIdempotency: boolean): void {
  if (!context.tenant_id) {
    throw new Error('TENANT_REQUIRED: tenant_id is required in context');
  }
  if (!context.subject_id) {
    throw new Error('SUBJECT_REQUIRED: subject_id is required in context');
  }
  if (!context.trace_id) {
    throw new Error('TRACE_REQUIRED: trace_id is required in context');
  }
  if (requireIdempotency && !context.idempotency_key) {
    throw new Error('IDEMPOTENCY_REQUIRED: idempotency_key is required for mutations');
  }
}

// =============================================================================
// HTTP CLIENT
// =============================================================================

export class SDKClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  /**
   * Set auth token
   */
  setAuthToken(token: string): void {
    this.defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Build headers from context
   */
  private buildHeaders(context: RequestContext): Record<string, string> {
    const headers: Record<string, string> = {
      ...this.defaultHeaders,
      'X-Tenant-ID': context.tenant_id,
      'X-Subject-ID': context.subject_id,
      'X-Subject-Type': context.subject_type,
      'X-Trace-ID': context.trace_id,
    };

    if (context.idempotency_key) {
      headers['X-Idempotency-Key'] = context.idempotency_key;
    }

    return headers;
  }

  /**
   * GET request (read-only)
   */
  async get<T>(
    endpoint: string,
    context: RequestContext,
    params?: Record<string, string | number | undefined>
  ): Promise<ApiResponse<T>> {
    validateContext(context, false);

    const url = new URL(`${this.baseUrl}${endpoint}`, window.location.origin);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.buildHeaders(context),
    });

    return response.json();
  }

  /**
   * POST request (mutation - requires idempotency)
   */
  async post<T>(
    endpoint: string,
    context: RequestContext,
    body: Record<string, unknown>
  ): Promise<ApiResponse<T>> {
    validateContext(context, true); // Idempotency REQUIRED

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: this.buildHeaders(context),
      body: JSON.stringify(body),
    });

    return response.json();
  }

  /**
   * PUT request (mutation - requires idempotency)
   */
  async put<T>(
    endpoint: string,
    context: RequestContext,
    body: Record<string, unknown>
  ): Promise<ApiResponse<T>> {
    validateContext(context, true); // Idempotency REQUIRED

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PUT',
      headers: this.buildHeaders(context),
      body: JSON.stringify(body),
    });

    return response.json();
  }
}

// =============================================================================
// DOMAIN CLIENTS
// =============================================================================

/**
 * IAM Domain Client
 * READ-ONLY toward Core
 */
export class IAMClient {
  constructor(private sdk: SDKClient) {}

  async listUsers(
    context: RequestContext,
    params?: { role_id?: string; search?: string } & PaginationParams
  ) {
    return this.sdk.get('/iam/users', context, params);
  }

  async getUser(context: RequestContext, userId: string) {
    return this.sdk.get(`/iam/users/${userId}`, context);
  }

  async listRoles(context: RequestContext) {
    return this.sdk.get('/iam/roles', context);
  }

  async getRole(context: RequestContext, roleId: string) {
    return this.sdk.get(`/iam/roles/${roleId}`, context);
  }

  async listServiceAccounts(context: RequestContext) {
    return this.sdk.get('/iam/service-accounts', context);
  }

  async getPermissionMatrix(context: RequestContext) {
    return this.sdk.get('/iam/permissions/matrix', context);
  }
}

/**
 * Tenant Domain Client
 * READ-ONLY toward Core
 */
export class TenantClient {
  constructor(private sdk: SDKClient) {}

  async listTenants(context: RequestContext) {
    return this.sdk.get('/tenants', context);
  }

  async getTenant(context: RequestContext, tenantId: string) {
    // CRITICAL: Validate tenant_id matches
    if (context.tenant_id !== tenantId) {
      throw new Error('CROSS_TENANT_DENIED: Cannot access other tenant data');
    }
    return this.sdk.get(`/tenants/${tenantId}`, context);
  }

  async getTenantMembers(context: RequestContext, tenantId: string) {
    if (context.tenant_id !== tenantId) {
      throw new Error('CROSS_TENANT_DENIED: Cannot access other tenant data');
    }
    return this.sdk.get(`/tenants/${tenantId}/members`, context);
  }

  async checkIsolation(context: RequestContext) {
    return this.sdk.get('/tenants/isolation-check', context);
  }
}

/**
 * Decision Domain Client
 * CAN create rules and request activation (via workflow)
 */
export class DecisionClient {
  constructor(private sdk: SDKClient) {}

  async listRules(
    context: RequestContext,
    params?: { status?: string; decision_type?: string } & PaginationParams
  ) {
    return this.sdk.get('/rules', context, params);
  }

  async getRule(context: RequestContext, ruleId: string) {
    return this.sdk.get(`/rules/${ruleId}`, context);
  }

  async getRuleVersions(context: RequestContext, ruleId: string) {
    return this.sdk.get(`/rules/${ruleId}/versions`, context);
  }

  /**
   * Create rule draft
   * MUTATION - requires idempotency_key
   */
  async createRuleDraft(
    context: RequestContext,
    data: {
      rule_name: string;
      decision_type: string;
      conditions: Record<string, unknown>;
      action: Record<string, unknown>;
      description?: string;
    }
  ) {
    return this.sdk.post('/rules', context, {
      ...data,
      status: 'DRAFT', // Always create as DRAFT
    });
  }

  /**
   * Request rule activation (creates workflow)
   * MUTATION - requires idempotency_key
   */
  async requestRuleActivation(context: RequestContext, ruleId: string) {
    return this.sdk.post(`/rules/${ruleId}/activate`, context, {});
  }

  async listDecisionTypes(context: RequestContext) {
    return this.sdk.get('/decision-types', context);
  }

  async listDecisions(
    context: RequestContext,
    params?: { type?: string; outcome?: string } & PaginationParams
  ) {
    return this.sdk.get('/decisions', context, params);
  }

  async getDecision(context: RequestContext, decisionId: string) {
    return this.sdk.get(`/decisions/${decisionId}`, context);
  }

  async getDecisionEvents(context: RequestContext, decisionId: string) {
    return this.sdk.get(`/decisions/${decisionId}/events`, context);
  }
}

/**
 * Workflow Domain Client
 * CAN approve, reject, delegate, escalate
 */
export class WorkflowClient {
  constructor(private sdk: SDKClient) {}

  async listPending(context: RequestContext) {
    return this.sdk.get('/workflows', context, {
      assignee: 'me',
      status: 'pending',
    });
  }

  async listAll(context: RequestContext, params?: { status?: string } & PaginationParams) {
    return this.sdk.get('/workflows', context, params);
  }

  async getWorkflow(context: RequestContext, workflowId: string) {
    return this.sdk.get(`/workflows/${workflowId}`, context);
  }

  async getWorkflowTransitions(context: RequestContext, workflowId: string) {
    return this.sdk.get(`/workflows/${workflowId}/transitions`, context);
  }

  /**
   * Approve workflow
   * MUTATION - requires idempotency_key
   */
  async approve(context: RequestContext, workflowId: string, comment?: string) {
    return this.sdk.post(`/workflows/${workflowId}/approve`, context, {
      comment,
    });
  }

  /**
   * Reject workflow
   * MUTATION - requires idempotency_key
   */
  async reject(context: RequestContext, workflowId: string, reason: string) {
    if (!reason) {
      throw new Error('REASON_REQUIRED: reason is required for rejection');
    }
    return this.sdk.post(`/workflows/${workflowId}/reject`, context, {
      reason,
    });
  }

  /**
   * Delegate workflow
   * MUTATION - requires idempotency_key
   */
  async delegate(
    context: RequestContext,
    workflowId: string,
    delegateToUserId: string,
    reason: string
  ) {
    if (!reason) {
      throw new Error('REASON_REQUIRED: reason is required for delegation');
    }
    return this.sdk.post(`/workflows/${workflowId}/delegate`, context, {
      delegate_to_user_id: delegateToUserId,
      reason,
    });
  }

  /**
   * Escalate workflow
   * MUTATION - requires idempotency_key
   */
  async escalate(
    context: RequestContext,
    workflowId: string,
    escalateToRole: string,
    reason: string
  ) {
    if (!reason) {
      throw new Error('REASON_REQUIRED: reason is required for escalation');
    }
    return this.sdk.post(`/workflows/${workflowId}/escalate`, context, {
      escalate_to_role: escalateToRole,
      reason,
    });
  }

  async listEscalations(context: RequestContext) {
    return this.sdk.get('/workflows', context, { status: 'escalated' });
  }

  async listCompleted(context: RequestContext, params?: PaginationParams) {
    return this.sdk.get('/workflows', context, {
      ...params,
      status: 'completed',
    });
  }
}

/**
 * Control Domain Client
 * 100% READ-ONLY - No mutations
 */
export class ControlClient {
  constructor(private sdk: SDKClient) {}

  async listAudit(
    context: RequestContext,
    params?: {
      resource_type?: string;
      action?: string;
      from_date?: string;
      to_date?: string;
    } & PaginationParams
  ) {
    return this.sdk.get('/audit', context, params);
  }

  async getAuditRecord(context: RequestContext, auditId: string) {
    return this.sdk.get(`/audit/${auditId}`, context);
  }

  async listEvents(
    context: RequestContext,
    params?: {
      event_type?: string;
      aggregate_id?: string;
      from_date?: string;
      to_date?: string;
    } & PaginationParams
  ) {
    return this.sdk.get('/events', context, params);
  }

  async getEvent(context: RequestContext, eventId: string) {
    return this.sdk.get(`/events/${eventId}`, context);
  }

  async listDLQ(context: RequestContext, params?: PaginationParams) {
    return this.sdk.get('/events/dlq', context, params);
  }

  async getDLQEvent(context: RequestContext, eventId: string) {
    return this.sdk.get(`/events/dlq/${eventId}`, context);
  }

  async getMetrics(context: RequestContext) {
    return this.sdk.get('/metrics', context);
  }

  async getDecisionMetrics(context: RequestContext) {
    return this.sdk.get('/metrics/decisions', context);
  }

  async getWorkflowMetrics(context: RequestContext) {
    return this.sdk.get('/metrics/workflows', context);
  }
}

// =============================================================================
// MAIN SDK EXPORT
// =============================================================================

export class AtlasPuguhSDK {
  private client: SDKClient;

  public iam: IAMClient;
  public tenant: TenantClient;
  public decision: DecisionClient;
  public workflow: WorkflowClient;
  public control: ControlClient;

  constructor(baseUrl: string = '/api/v1') {
    this.client = new SDKClient(baseUrl);

    // Initialize domain clients
    this.iam = new IAMClient(this.client);
    this.tenant = new TenantClient(this.client);
    this.decision = new DecisionClient(this.client);
    this.workflow = new WorkflowClient(this.client);
    this.control = new ControlClient(this.client);
  }

  setAuthToken(token: string): void {
    this.client.setAuthToken(token);
  }

  /**
   * Generate idempotency key
   * Use this for all mutation operations
   */
  generateIdempotencyKey(): string {
    return uuidv4();
  }

  /**
   * Generate trace ID
   * Use this for all requests in a user session
   */
  generateTraceId(): string {
    return uuidv4();
  }
}

// Default export
export const sdk = new AtlasPuguhSDK();
