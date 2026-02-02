# MANTRA SDK for TypeScript

TypeScript/JavaScript client library for ARSAKA_MANTRA Decision System.

## Installation

```bash
npm install @atlas/mantra-sdk
# or
bun add @atlas/mantra-sdk
```

## Quick Start

```typescript
import { MantraClient } from '@atlas/mantra-sdk';

// Initialize client
const client = new MantraClient('http://localhost:8000');

// List decisions
const decisions = await client.listDecisions({ domain: 'INT', limit: 10 });
decisions.forEach(d => console.log(`${d.code}: ${d.statement}`));

// Get a specific decision
const decision = await client.getDecision('uuid-here');

// Context-aware retrieval
const result = await client.retrieve({
  query: 'authentication patterns',
  file_path: 'src/auth/login.ts',
  max_results: 5,
});
result.results.forEach(match =>
  console.log(`${match.decision_code} (${Math.round(match.confidence * 100)}%): ${match.statement}`)
);
```

## Proposing Decisions

Per MANTRA-LAW-006, the SDK can only **propose** decisions. All proposals require human approval.

```typescript
import type { DecisionCreate } from '@atlas/mantra-sdk';

// Create a proposal
const proposal: DecisionCreate = {
  code: 'MANTRA-ARCH-042',
  domain_id: 'ARCH',
  aspect_id: 'A05',
  statement: 'Use Repository pattern for data access',
  rationale: 'Provides abstraction and testability',
  scope: ['backend/*'],
  tags: ['pattern', 'data-access'],
  authorship: {
    authored_by: 'john.doe@example.com',
    organization: 'Engineering',
  },
};

// Submit proposal (requires human approval via dashboard)
const result = await client.proposeDecision(proposal);
console.log(`Proposal ID: ${result.decision_id}`);
console.log(`Status: ${result.status}`); // "pending_approval"
```

## Validation

```typescript
// Validate a decision before proposing
const validation = await client.validateDecision(proposal);
console.log(`Status: ${validation.status}`);
validation.violations.forEach(v =>
  console.log(`  [${v.severity}] ${v.rule_id}: ${v.message}`)
);

// Full 3-gate validation
const fullResult = await client.validateFull(proposal, true);
console.log(`Gate 1 (Deterministic): ${fullResult.gate1.passed ? 'PASS' : 'FAIL'}`);
console.log(`Gate 2 (AI): Confidence ${Math.round(fullResult.gate2.confidence * 100)}%`);
console.log(`Gate 3 (Human): ${fullResult.gate3.pending ? 'Pending' : 'Approved'}`);
```

## Document Generation

```typescript
import type { DocumentGenerateRequest } from '@atlas/mantra-sdk';

// List available document types
const types = await client.listDocumentTypes();
types.forEach(t => console.log(`${t.type}: ${t.name} (${t.phase})`));

// Generate a PRD
const request: DocumentGenerateRequest = {
  doc_type: 'prd',
  title: 'My Project PRD',
  company_name: 'Acme Corp',
  domain_filter: 'INT',
  max_decisions: 50,
};

const doc = await client.generateDocument(request);
console.log(`Generated: ${doc.title} (${doc.word_count} words)`);
console.log(doc.content);
```

## Analytics

```typescript
// Get usage summary
const summary = await client.getAnalyticsSummary();
console.log(`Tracked: ${summary.total_decisions_tracked}`);
console.log(`Hot: ${summary.hot_decisions_count}`);
console.log(`Stale: ${summary.stale_decisions_count}`);

// Track usage
await client.trackEvent('decision-id', 'view', { source: 'sdk' });

// Submit feedback
await client.submitFeedback('decision-id', true, 'Very clear');
```

## Error Handling

```typescript
import {
  MantraError,
  AuthorizationError,
  NotFoundError,
} from '@atlas/mantra-sdk';

try {
  const decision = await client.getDecision('invalid-id');
} catch (error) {
  if (error instanceof NotFoundError) {
    console.log(`Not found: ${error.identifier}`);
  } else if (error instanceof AuthorizationError) {
    console.log('Human authorization required');
  } else if (error instanceof MantraError) {
    console.log(`Error [${error.code}]: ${error.message}`);
  }
}
```

## API Key Authentication

```typescript
const client = new MantraClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key',
  timeout: 30000, // ms
});
```

## MANTRA Laws

This SDK enforces MANTRA constitutional laws:

- **LAW-001**: All decisions must be human-authored
- **LAW-006**: AI has ZERO authority for approval/creation/modification

The SDK can:
- Read decisions
- Validate decisions
- Propose decisions (requires human approval)
- Retrieve context-aware results
- Generate documentation
- Track usage analytics

The SDK cannot:
- Directly create approved decisions
- Modify existing decisions
- Approve proposals
