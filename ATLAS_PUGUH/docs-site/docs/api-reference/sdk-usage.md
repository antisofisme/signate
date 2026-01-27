---
sidebar_position: 4
---

# SDK Usage

Learn how to use the PUGUH SDK in your applications.

## Installation

### JavaScript/TypeScript

```bash
npm install @atlashub/puguh-sdk
# or
yarn add @atlashub/puguh-sdk
# or
bun add @atlashub/puguh-sdk
```

### Python

```bash
pip install puguh-sdk
```

## Quick Start

### JavaScript/TypeScript

```typescript
import { PuguhClient } from '@atlashub/puguh-sdk';

const client = new PuguhClient({
  apiKey: process.env.PUGUH_API_KEY,
  tenantId: process.env.PUGUH_TENANT_ID,
  projectId: process.env.PUGUH_PROJECT_ID, // optional
});

// Request a decision
const decision = await client.decide({
  type: 'expense_approval',
  context: {
    amount: 15000,
    category: 'equipment',
  },
});

console.log(decision.outcome); // 'REQUIRE_APPROVAL'
console.log(decision.workflowId); // 'wf-uuid'
```

### Python

```python
from puguh import PuguhClient

client = PuguhClient(
    api_key=os.environ['PUGUH_API_KEY'],
    tenant_id=os.environ['PUGUH_TENANT_ID']
)

# Request a decision
decision = client.decide(
    type='expense_approval',
    context={
        'amount': 15000,
        'category': 'equipment'
    }
)

print(decision.outcome)  # 'REQUIRE_APPROVAL'
```

## Configuration

### Client Options

```typescript
const client = new PuguhClient({
  // Required
  apiKey: 'your-api-key',
  tenantId: 'your-tenant-id',

  // Optional
  projectId: 'your-project-id',
  baseUrl: 'https://api-puguh.atlashub.com', // Custom API URL
  timeout: 30000, // Request timeout in ms
  retries: 3, // Retry count for failed requests
  onError: (error) => console.error(error), // Error handler
});
```

### Environment Variables

```bash
PUGUH_API_KEY=your-api-key
PUGUH_TENANT_ID=your-tenant-id
PUGUH_PROJECT_ID=your-project-id
PUGUH_BASE_URL=https://api-puguh.atlashub.com
```

## Decisions

### Basic Decision

```typescript
const decision = await client.decide({
  type: 'expense_approval',
  context: {
    amount: 5000,
    department: 'engineering',
  },
});
```

### Decision with Options

```typescript
const decision = await client.decide({
  type: 'expense_approval',
  context: { amount: 5000 },
  options: {
    dryRun: true, // Don't persist
    includeEvaluation: true, // Include rule trace
    idempotencyKey: 'unique-id', // Prevent duplicates
  },
});
```

### Handling Outcomes

```typescript
switch (decision.outcome) {
  case 'ALLOWED':
    // Proceed with the action
    await processExpense(expense);
    break;

  case 'DENIED':
    // Reject the request
    throw new Error(`Denied: ${decision.reason}`);

  case 'REQUIRE_APPROVAL':
    // Wait for workflow completion
    const workflowId = decision.workflowId;
    await notifyApprovers(workflowId);
    break;

  case 'FLAGGED':
    // Allow but flag for review
    await processExpense(expense);
    await createReviewTask(decision);
    break;
}
```

## Rules

### List Rules

```typescript
const rules = await client.listRules({
  status: 'active',
  decisionType: 'expense_approval',
});
```

### Create Rule

```typescript
const rule = await client.createRule({
  name: 'High Value Approval',
  decisionType: 'expense_approval',
  priority: 100,
  conditions: {
    all: [
      { field: 'amount', operator: 'greater_than', value: 5000 },
    ],
  },
  actions: {
    type: 'REQUIRE_APPROVAL',
    config: { workflowId: 'manager-approval' },
  },
});
```

### Test Rule

```typescript
const result = await client.testRule(rule.id, {
  amount: 7500,
  category: 'equipment',
});

console.log(result.matches); // true
console.log(result.action); // { type: 'REQUIRE_APPROVAL', ... }
```

### Activate Rule

```typescript
await client.activateRule(rule.id, {
  description: 'Tested and ready for production',
});
```

## Workflows

### Get Pending Workflows

```typescript
const pending = await client.listWorkflows({
  status: 'PENDING',
  assignedTo: 'me',
});
```

### Approve Workflow

```typescript
await client.approveWorkflow(workflowId, {
  comment: 'Looks good, approved',
});
```

### Reject Workflow

```typescript
await client.rejectWorkflow(workflowId, {
  reason: 'Budget not available',
});
```

### Delegate Workflow

```typescript
await client.delegateWorkflow(workflowId, {
  to: 'jane@example.com',
  reason: 'Out of office',
});
```

## Webhooks

### Subscribe to Events

```typescript
// Verify webhook signature
const isValid = client.verifyWebhook(
  requestBody,
  requestHeaders['x-puguh-signature']
);

if (isValid) {
  const event = JSON.parse(requestBody);
  switch (event.type) {
    case 'decision.created':
      handleNewDecision(event.data);
      break;
    case 'workflow.completed':
      handleWorkflowComplete(event.data);
      break;
  }
}
```

## Error Handling

### Error Types

```typescript
import {
  PuguhError,
  ValidationError,
  AuthenticationError,
  PermissionError,
  RateLimitError,
  NotFoundError,
} from '@atlashub/puguh-sdk';

try {
  await client.decide({ ... });
} catch (error) {
  if (error instanceof RateLimitError) {
    // Wait and retry
    await sleep(error.retryAfter * 1000);
    await client.decide({ ... });
  } else if (error instanceof ValidationError) {
    // Fix the input
    console.error('Invalid input:', error.details);
  } else if (error instanceof AuthenticationError) {
    // Check API key
    console.error('Authentication failed');
  }
}
```

### Retry Configuration

```typescript
const client = new PuguhClient({
  apiKey: '...',
  tenantId: '...',
  retries: 3,
  retryDelay: 1000, // Initial delay
  retryBackoff: 2, // Exponential backoff multiplier
  retryCondition: (error) => {
    return error instanceof RateLimitError || error.code === 503;
  },
});
```

## TypeScript Types

### Decision Types

```typescript
import type {
  Decision,
  DecisionOutcome,
  DecisionRequest,
  Rule,
  RuleCondition,
  Workflow,
  WorkflowStatus,
} from '@atlashub/puguh-sdk';

const handleDecision = (decision: Decision): void => {
  const outcome: DecisionOutcome = decision.outcome;
  // ...
};
```

### Generating Types from Schema

```bash
npx puguh-cli types generate \
  --tenant YOUR_TENANT_ID \
  --output ./types/puguh.d.ts
```

## Best Practices

### 1. Use Environment Variables

Never hardcode API keys:

```typescript
// Bad
const client = new PuguhClient({ apiKey: 'sk_live_xxx' });

// Good
const client = new PuguhClient({ apiKey: process.env.PUGUH_API_KEY });
```

### 2. Handle All Outcomes

Always handle every possible outcome:

```typescript
// Bad
if (decision.outcome === 'ALLOWED') {
  proceed();
}

// Good
switch (decision.outcome) {
  case 'ALLOWED':
    proceed();
    break;
  case 'DENIED':
    reject();
    break;
  case 'REQUIRE_APPROVAL':
    waitForApproval();
    break;
  case 'FLAGGED':
    proceedWithFlag();
    break;
  default:
    throw new Error(`Unknown outcome: ${decision.outcome}`);
}
```

### 3. Use Idempotency Keys

Prevent duplicate decisions:

```typescript
const decision = await client.decide({
  type: 'expense_approval',
  context: expense,
  options: {
    idempotencyKey: `expense-${expense.id}-${expense.version}`,
  },
});
```

### 4. Implement Proper Error Handling

```typescript
try {
  const decision = await client.decide({ ... });
  return handleOutcome(decision);
} catch (error) {
  if (error.retryable) {
    return retryWithBackoff(() => client.decide({ ... }));
  }
  throw error;
}
```

## Related

- [Authentication](/docs/api-reference/authentication)
- [Rules API](/docs/api-reference/rules-api)
- [Decisions API](/docs/api-reference/decisions-api)
