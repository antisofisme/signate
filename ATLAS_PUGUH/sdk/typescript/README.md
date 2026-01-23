# ATLAS_PUGUH Core Service SDK (TypeScript)

TypeScript client library for ATLAS_PUGUH Core Service decision engine and workflow orchestration.

## Installation

```bash
npm install @atlas-puguh/core-service-sdk
```

Or with yarn:

```bash
yarn add @atlas-puguh/core-service-sdk
```

## Quick Start

```typescript
import { CoreServiceClient } from '@atlas-puguh/core-service-sdk';

const client = new CoreServiceClient({
  baseUrl: 'http://localhost:8001'
});

// Create a decision
const response = await client.createDecision({
  tenant_id: '550e8400-e29b-41d4-a716-446655440000',
  decision_type: 'check_in_approval',
  context: { room_id: '101', guest_count: 2 },
  idempotency_key: 'req-12345'
});

console.log(`Decision: ${response.outcome}`);

// If workflow created, approve it
if (response.workflow_id) {
  const approveResp = await client.approveWorkflow(
    response.workflow_id,
    {
      tenant_id: '550e8400-e29b-41d4-a716-446655440000',
      approver_role: 'front_desk_manager'
    }
  );

  console.log(`Workflow state: ${approveResp.current_state}`);
}
```

## API Reference

### Client

#### `new CoreServiceClient(config)`

Main client for Core Service API.

**Parameters:**
```typescript
interface CoreServiceClientConfig {
  baseUrl: string;       // Base URL of Core Service API
  timeout?: number;      // Request timeout in ms (default: 30000)
  apiKey?: string;       // Optional API key (future use)
}
```

**Methods:**
- `createDecision(request: CreateDecisionRequest): Promise<CreateDecisionResponse>`
- `approveWorkflow(workflowId: string, request: ApproveWorkflowRequest): Promise<ApproveWorkflowResponse>`
- `rejectWorkflow(workflowId: string, request: RejectWorkflowRequest): Promise<RejectWorkflowResponse>`
- `delegateWorkflow(workflowId: string, request: DelegateWorkflowRequest): Promise<DelegateWorkflowResponse>`
- `escalateWorkflow(workflowId: string, request: EscalateWorkflowRequest): Promise<EscalateWorkflowResponse>`

### Types

#### `CreateDecisionRequest`

```typescript
interface CreateDecisionRequest {
  tenant_id: string;
  decision_type: string;
  context: Record<string, any>;
  idempotency_key?: string;
  trace_id?: string;
  requester_user_id?: string;
}
```

#### `CreateDecisionResponse`

```typescript
interface CreateDecisionResponse {
  decision_id: string;
  outcome: "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL";
  rule_matched_id?: string;
  rule_version?: string;
  workflow_id?: string;
  created_at: string;
}
```

#### `ApproveWorkflowRequest`

```typescript
interface ApproveWorkflowRequest {
  tenant_id: string;
  approver_role: string;
  acted_by_user_id?: string;
  comment?: string;
}
```

### Exceptions

All exceptions extend `CoreServiceError`.

```typescript
class CoreServiceError extends Error {
  readonly errorCode?: string;
  readonly details: Record<string, any>;
  readonly statusCode?: number;
}
```

**Exception Classes:**
- `IdempotencyConflictError` (HTTP 409): Idempotency key conflicts with different context
- `WorkflowNotFoundError` (HTTP 404): Workflow not found
- `ApproverRoleMismatchError` (HTTP 403): Approver role mismatch
- `InvalidWorkflowTransitionError` (HTTP 400): Invalid workflow state transition
- `TenantIsolationViolationError` (HTTP 403): Tenant isolation violated
- `ValidationError` (HTTP 422): Request validation failed
- `NetworkError`: Network request failed

## Error Handling

```typescript
import {
  CoreServiceClient,
  IdempotencyConflictError,
  NetworkError,
  CoreServiceError
} from '@atlas-puguh/core-service-sdk';

async function safeCreateDecision() {
  const client = new CoreServiceClient({
    baseUrl: 'http://localhost:8001'
  });

  try {
    const response = await client.createDecision({
      tenant_id: '550e8400-e29b-41d4-a716-446655440000',
      decision_type: 'test',
      context: { key: 'value' },
      idempotency_key: 'unique-key'
    });

    return response;

  } catch (error) {
    if (error instanceof IdempotencyConflictError) {
      console.error(`Conflict: ${error.message}`);
      console.error(`Existing decision: ${error.existingDecisionId}`);
    } else if (error instanceof NetworkError) {
      console.error(`Network error: ${error.message}`);
    } else if (error instanceof CoreServiceError) {
      console.error(`API error: ${error.errorCode} - ${error.message}`);
    } else {
      throw error;
    }
  }
}
```

## Idempotency

Use `idempotency_key` to ensure exactly-once processing:

```typescript
const request = {
  tenant_id: tenantId,
  decision_type: 'payment_approval',
  context: { amount: 1000, currency: 'USD' },
  idempotency_key: `payment-${paymentId}`  // Unique per payment
};

// Same key + same context = same decision (cached)
const response1 = await client.createDecision(request);
const response2 = await client.createDecision(request);
console.assert(response1.decision_id === response2.decision_id);

// Same key + different context = conflict error
request.context.amount = 2000;
try {
  await client.createDecision(request);  // Throws IdempotencyConflictError
} catch (error) {
  if (error instanceof IdempotencyConflictError) {
    console.log('Idempotency conflict detected');
  }
}
```

## TypeScript Support

This library is written in TypeScript and includes full type definitions out of the box.

```typescript
import type {
  CreateDecisionRequest,
  CreateDecisionResponse
} from '@atlas-puguh/core-service-sdk';

// Full IntelliSense support
const request: CreateDecisionRequest = {
  tenant_id: '550e8400-e29b-41d4-a716-446655440000',
  decision_type: 'check_in_approval',
  context: { room_id: '101' }
};
```

## Requirements

- Node.js 18.0.0 or higher
- TypeScript 5.3.0 or higher (for development)

## License

MIT License - See LICENSE file for details.
