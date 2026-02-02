/**
 * PHASE 4 BYPASS TESTS - NON-NEGOTIABLE GATE
 *
 * These tests verify that the CMS UI cannot bypass enforcement.
 *
 * CRITICAL: ALL tests MUST pass before Phase 4 is complete.
 *
 * Phase: 4
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  SDKClient,
  IAMClient,
  TenantClient,
  DecisionClient,
  WorkflowClient,
  ControlClient,
  AtlasPuguhSDK,
  RequestContext,
} from '../client';

// =============================================================================
// TEST FIXTURES
// =============================================================================

const validContext: RequestContext = {
  tenant_id: '11111111-1111-1111-1111-111111111111',
  subject_id: '22222222-2222-2222-2222-222222222222',
  subject_type: 'user',
  trace_id: '33333333-3333-3333-3333-333333333333',
};

const validContextWithIdempotency: RequestContext = {
  ...validContext,
  idempotency_key: '44444444-4444-4444-4444-444444444444',
};

const differentTenantId = '99999999-9999-9999-9999-999999999999';

// =============================================================================
// BYPASS TEST 1: UI ACTION WITHOUT TENANT → DENY
// =============================================================================

describe('Bypass Test 1: UI action without tenant must DENY', () => {
  let sdk: AtlasPuguhSDK;

  beforeEach(() => {
    sdk = new AtlasPuguhSDK();
    global.fetch = vi.fn();
  });

  it('GET request without tenant_id throws error', async () => {
    const contextWithoutTenant = {
      ...validContext,
      tenant_id: '', // Empty
    };

    await expect(
      sdk.iam.listUsers(contextWithoutTenant as RequestContext)
    ).rejects.toThrow('TENANT_REQUIRED');
  });

  it('GET request with null tenant_id throws error', async () => {
    const contextWithNullTenant = {
      ...validContext,
      tenant_id: null,
    };

    await expect(
      sdk.decision.listRules(contextWithNullTenant as unknown as RequestContext)
    ).rejects.toThrow('TENANT_REQUIRED');
  });

  it('POST request without tenant_id throws error', async () => {
    const contextWithoutTenant = {
      ...validContextWithIdempotency,
      tenant_id: '',
    };

    await expect(
      sdk.decision.createRuleDraft(contextWithoutTenant as RequestContext, {
        rule_name: 'test',
        decision_type: 'test.type',
        conditions: {},
        action: {},
      })
    ).rejects.toThrow('TENANT_REQUIRED');
  });
});

// =============================================================================
// BYPASS TEST 2: CROSS-DOMAIN ACTION → DENY
// =============================================================================

describe('Bypass Test 2: Cross-domain actions must be prevented', () => {
  let sdk: AtlasPuguhSDK;

  beforeEach(() => {
    sdk = new AtlasPuguhSDK();
    global.fetch = vi.fn();
  });

  it('TenantClient cannot access different tenant', async () => {
    // Context says tenant A, but requesting tenant B
    await expect(
      sdk.tenant.getTenant(validContext, differentTenantId)
    ).rejects.toThrow('CROSS_TENANT_DENIED');
  });

  it('TenantClient cannot get members of different tenant', async () => {
    await expect(
      sdk.tenant.getTenantMembers(validContext, differentTenantId)
    ).rejects.toThrow('CROSS_TENANT_DENIED');
  });

  it('IAM client has no decision mutation methods', () => {
    const iamClient = sdk.iam;

    // IAM should NOT have these methods
    expect((iamClient as any).createDecision).toBeUndefined();
    expect((iamClient as any).approveWorkflow).toBeUndefined();
    expect((iamClient as any).createRule).toBeUndefined();
    expect((iamClient as any).forceAllow).toBeUndefined();
  });

  it('Control client has no mutation methods', () => {
    const controlClient = sdk.control;

    // Control should be 100% read-only
    expect((controlClient as any).createAudit).toBeUndefined();
    expect((controlClient as any).deleteAudit).toBeUndefined();
    expect((controlClient as any).replayEvent).toBeUndefined();
    expect((controlClient as any).deleteEvent).toBeUndefined();
    expect((controlClient as any).mutate).toBeUndefined();
  });
});

// =============================================================================
// BYPASS TEST 3: BYPASS WORKFLOW → DENY
// =============================================================================

describe('Bypass Test 3: Cannot bypass workflow', () => {
  let sdk: AtlasPuguhSDK;

  beforeEach(() => {
    sdk = new AtlasPuguhSDK();
    global.fetch = vi.fn();
  });

  it('Decision client cannot directly activate rule (must go through workflow)', async () => {
    // requestRuleActivation creates a WORKFLOW, not direct activation
    const decisionClient = sdk.decision;

    // Should NOT have directActivate method
    expect((decisionClient as any).directActivate).toBeUndefined();
    expect((decisionClient as any).forceActivate).toBeUndefined();
    expect((decisionClient as any).bypassActivate).toBeUndefined();
  });

  it('Workflow reject requires reason', async () => {
    await expect(
      sdk.workflow.reject(validContextWithIdempotency, 'workflow-id', '')
    ).rejects.toThrow('REASON_REQUIRED');
  });

  it('Workflow delegate requires reason', async () => {
    await expect(
      sdk.workflow.delegate(validContextWithIdempotency, 'workflow-id', 'user-id', '')
    ).rejects.toThrow('REASON_REQUIRED');
  });

  it('Workflow escalate requires reason', async () => {
    await expect(
      sdk.workflow.escalate(validContextWithIdempotency, 'workflow-id', 'role', '')
    ).rejects.toThrow('REASON_REQUIRED');
  });
});

// =============================================================================
// BYPASS TEST 4: UI CANNOT MUTATE AUDIT/EVENT
// =============================================================================

describe('Bypass Test 4: UI cannot mutate audit or events', () => {
  let sdk: AtlasPuguhSDK;

  beforeEach(() => {
    sdk = new AtlasPuguhSDK();
  });

  it('Control client has NO POST methods', () => {
    const controlClient = sdk.control;
    const methods = Object.getOwnPropertyNames(Object.getPrototypeOf(controlClient));

    // All methods should be read-only (list*, get*)
    const mutationMethods = methods.filter(
      (m) =>
        m.startsWith('create') ||
        m.startsWith('update') ||
        m.startsWith('delete') ||
        m.startsWith('post') ||
        m.startsWith('put') ||
        m.startsWith('patch')
    );

    expect(mutationMethods).toHaveLength(0);
  });

  it('Control client methods are all GET operations', () => {
    const controlClient = sdk.control;
    const methods = Object.getOwnPropertyNames(Object.getPrototypeOf(controlClient)).filter(
      (m) => m !== 'constructor'
    );

    // All methods should start with list or get
    methods.forEach((method) => {
      expect(method).toMatch(/^(list|get)/);
    });
  });

  it('SDK does not expose raw database access', () => {
    expect((sdk as any).database).toBeUndefined();
    expect((sdk as any).db).toBeUndefined();
    expect((sdk as any).sql).toBeUndefined();
    expect((sdk as any).query).toBeUndefined();
    expect((sdk as any).execute).toBeUndefined();
  });
});

// =============================================================================
// BYPASS TEST 5: UI RETRY → IDEMPOTENT
// =============================================================================

describe('Bypass Test 5: UI mutations require idempotency', () => {
  let sdk: AtlasPuguhSDK;

  beforeEach(() => {
    sdk = new AtlasPuguhSDK();
    global.fetch = vi.fn();
  });

  it('createRuleDraft without idempotency_key throws error', async () => {
    const contextWithoutIdempotency = { ...validContext }; // No idempotency_key

    await expect(
      sdk.decision.createRuleDraft(contextWithoutIdempotency, {
        rule_name: 'test',
        decision_type: 'test.type',
        conditions: {},
        action: {},
      })
    ).rejects.toThrow('IDEMPOTENCY_REQUIRED');
  });

  it('requestRuleActivation without idempotency_key throws error', async () => {
    await expect(
      sdk.decision.requestRuleActivation(validContext, 'rule-id')
    ).rejects.toThrow('IDEMPOTENCY_REQUIRED');
  });

  it('workflow approve without idempotency_key throws error', async () => {
    await expect(
      sdk.workflow.approve(validContext, 'workflow-id')
    ).rejects.toThrow('IDEMPOTENCY_REQUIRED');
  });

  it('workflow reject without idempotency_key throws error', async () => {
    await expect(
      sdk.workflow.reject(validContext, 'workflow-id', 'reason')
    ).rejects.toThrow('IDEMPOTENCY_REQUIRED');
  });

  it('workflow delegate without idempotency_key throws error', async () => {
    await expect(
      sdk.workflow.delegate(validContext, 'workflow-id', 'user-id', 'reason')
    ).rejects.toThrow('IDEMPOTENCY_REQUIRED');
  });

  it('workflow escalate without idempotency_key throws error', async () => {
    await expect(
      sdk.workflow.escalate(validContext, 'workflow-id', 'role', 'reason')
    ).rejects.toThrow('IDEMPOTENCY_REQUIRED');
  });
});

// =============================================================================
// BYPASS TEST 6: CONTEXT PROPAGATION
// =============================================================================

describe('Bypass Test 6: Context is properly propagated', () => {
  let sdk: AtlasPuguhSDK;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    sdk = new AtlasPuguhSDK();
    fetchMock = vi.fn().mockResolvedValue({
      json: () => Promise.resolve({ success: true, data: [] }),
    });
    global.fetch = fetchMock;
  });

  it('GET request includes all context headers', async () => {
    await sdk.iam.listUsers(validContext);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-Tenant-ID': validContext.tenant_id,
          'X-Subject-ID': validContext.subject_id,
          'X-Subject-Type': validContext.subject_type,
          'X-Trace-ID': validContext.trace_id,
        }),
      })
    );
  });

  it('POST request includes idempotency header', async () => {
    await sdk.decision.createRuleDraft(validContextWithIdempotency, {
      rule_name: 'test',
      decision_type: 'test.type',
      conditions: {},
      action: {},
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-Idempotency-Key': validContextWithIdempotency.idempotency_key,
        }),
      })
    );
  });
});

// =============================================================================
// BYPASS TEST 7: SUBJECT CONTEXT REQUIRED
// =============================================================================

describe('Bypass Test 7: Subject context is required', () => {
  let sdk: AtlasPuguhSDK;

  beforeEach(() => {
    sdk = new AtlasPuguhSDK();
    global.fetch = vi.fn();
  });

  it('GET request without subject_id throws error', async () => {
    const contextWithoutSubject = {
      ...validContext,
      subject_id: '',
    };

    await expect(
      sdk.decision.listRules(contextWithoutSubject as RequestContext)
    ).rejects.toThrow('SUBJECT_REQUIRED');
  });

  it('POST request without subject_id throws error', async () => {
    const contextWithoutSubject = {
      ...validContextWithIdempotency,
      subject_id: '',
    };

    await expect(
      sdk.workflow.approve(contextWithoutSubject as RequestContext, 'workflow-id')
    ).rejects.toThrow('SUBJECT_REQUIRED');
  });
});

// =============================================================================
// BYPASS TEST 8: TRACE ID REQUIRED
// =============================================================================

describe('Bypass Test 8: Trace ID is required', () => {
  let sdk: AtlasPuguhSDK;

  beforeEach(() => {
    sdk = new AtlasPuguhSDK();
    global.fetch = vi.fn();
  });

  it('GET request without trace_id throws error', async () => {
    const contextWithoutTrace = {
      ...validContext,
      trace_id: '',
    };

    await expect(
      sdk.control.listAudit(contextWithoutTrace as RequestContext)
    ).rejects.toThrow('TRACE_REQUIRED');
  });

  it('POST request without trace_id throws error', async () => {
    const contextWithoutTrace = {
      ...validContextWithIdempotency,
      trace_id: '',
    };

    await expect(
      sdk.decision.createRuleDraft(contextWithoutTrace as RequestContext, {
        rule_name: 'test',
        decision_type: 'test.type',
        conditions: {},
        action: {},
      })
    ).rejects.toThrow('TRACE_REQUIRED');
  });
});

// =============================================================================
// BYPASS TEST 9: NO SUPERUSER MODE
// =============================================================================

describe('Bypass Test 9: No superuser or bypass mode', () => {
  let sdk: AtlasPuguhSDK;

  beforeEach(() => {
    sdk = new AtlasPuguhSDK();
  });

  it('SDK does not have superuser mode', () => {
    expect((sdk as any).superuser).toBeUndefined();
    expect((sdk as any).admin).toBeUndefined();
    expect((sdk as any).bypass).toBeUndefined();
    expect((sdk as any).override).toBeUndefined();
    expect((sdk as any).setSuperuser).toBeUndefined();
    expect((sdk as any).enableBypass).toBeUndefined();
  });

  it('SDK client does not have bypass methods', () => {
    const client = (sdk as any).client;

    expect(client.bypassAuth).toBeUndefined();
    expect(client.setBypassMode).toBeUndefined();
    expect(client.directQuery).toBeUndefined();
  });
});

// =============================================================================
// BYPASS TEST 10: DOMAIN SEPARATION
// =============================================================================

describe('Bypass Test 10: Domain separation enforced', () => {
  let sdk: AtlasPuguhSDK;

  beforeEach(() => {
    sdk = new AtlasPuguhSDK();
  });

  it('Each domain client is separate', () => {
    expect(sdk.iam).toBeDefined();
    expect(sdk.tenant).toBeDefined();
    expect(sdk.decision).toBeDefined();
    expect(sdk.workflow).toBeDefined();
    expect(sdk.control).toBeDefined();

    // Each should be a different instance
    expect(sdk.iam).not.toBe(sdk.tenant);
    expect(sdk.iam).not.toBe(sdk.decision);
    expect(sdk.iam).not.toBe(sdk.workflow);
    expect(sdk.iam).not.toBe(sdk.control);
  });

  it('Domain clients do not have cross-domain methods', () => {
    // IAM should not have workflow methods
    expect((sdk.iam as any).approve).toBeUndefined();
    expect((sdk.iam as any).createRule).toBeUndefined();

    // Decision should not have IAM methods
    expect((sdk.decision as any).listUsers).toBeUndefined();
    expect((sdk.decision as any).listRoles).toBeUndefined();

    // Workflow should not have decision methods
    expect((sdk.workflow as any).createRuleDraft).toBeUndefined();
    expect((sdk.workflow as any).listDecisions).toBeUndefined();

    // Control should not have any mutation methods
    expect((sdk.control as any).approve).toBeUndefined();
    expect((sdk.control as any).createRule).toBeUndefined();
  });
});
