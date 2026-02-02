# INFRA Layer 1: SDK Contracts & Event Model

**PURPOSE**: This layer defines **how applications interact** with Infra through SDK methods and events.

Layer 1 builds on Layer 0 concepts and provides the contract specifications that developers use to integrate with Infra. All method signatures, request/response structures, and event schemas are defined here.

---

## Documents

### 1. [INFRA-LAY1-001: SDK Contracts](./INFRA-LAY1-001-sdk-contracts.md)

Defines SDK method signatures, request/response structures, and API contracts.

- `createDecision()` - Create a new decision
- `getDecision()` - Retrieve an existing decision
- `approveWorkflow()` - Approve a pending workflow
- `rejectWorkflow()` - Reject a pending workflow
- Error handling patterns
- Idempotency contracts

---

### 2. [INFRA-LAY1-002: Event Model](./INFRA-LAY1-002-event-model.md)

Defines event types, payload structures, and delivery guarantees.

- Decision events (`decision.created`, `decision.allowed`, `decision.denied`)
- Workflow events (`workflow.created`, `workflow.approved`, `workflow.rejected`)
- Event schema versioning
- At-least-once delivery semantics

---

## Reading Order

1. **Start with [INFRA-LAY1-001](./INFRA-LAY1-001-sdk-contracts.md)** - Understand how to call SDK methods
2. **Then read [INFRA-LAY1-002](./INFRA-LAY1-002-event-model.md)** - Understand how to consume events

---

## Prerequisites

Before reading Layer 1, ensure familiarity with:

- [Layer 0: Foundation Design](../layer-0/README.md) - Core concepts and decision model

---

## Next Layer

After Layer 1, proceed to:

- [Layer 2](../layer-2/) - Architecture and service boundaries
- [Layer 3](../layer-3/) - Implementation standards
