# INFRA Layer 2: Architecture & Service Boundaries

**PURPOSE**: This layer defines **how Infra is architected** as a system of services with clear boundaries.

Layer 2 builds on Layer 0 concepts and Layer 1 contracts to define service decomposition, critical paths, data persistence strategies, and observability requirements. This layer answers "how do services collaborate?" without prescribing implementation details (deferred to Layer 3).

---

## Documents

### 1. [INFRA-LAY2-001: Service Boundaries](./INFRA-LAY2-001-service-boundaries.md)

Defines the four Infra services and their exclusive responsibilities.

- **Infra Core**: Decision engine, rule evaluation, workflow state machine
- **Infra CMS**: Configuration & management plane, rule CRUD
- **Infra SDK**: Client libraries, request validation, auth forwarding
- **Application Adapter**: Entity ownership validation, approver resolution

---

### 2. [INFRA-LAY2-002: Critical Path Sequences](./INFRA-LAY2-002-critical-path-sequences.md)

Defines the sequence diagrams for critical operations.

- Decision creation flow
- Workflow approval/rejection flow
- Timeout and escalation handling
- Error propagation patterns

---

### 3. [INFRA-LAY2-003: Data Persistence Model](./INFRA-LAY2-003-data-persistence-model.md)

Defines how data is stored, partitioned, and indexed.

- Decision storage (immutable, append-only)
- Workflow state persistence
- Audit log storage and retention
- Tenant data isolation at storage level

---

### 4. [INFRA-LAY2-004: Monitoring & Observability](./INFRA-LAY2-004-monitoring-observability.md)

Defines metrics, logs, and traces requirements.

- Health check endpoints
- Performance metrics (latency, throughput)
- Structured logging standards
- Distributed tracing requirements

---

## Reading Order

1. **Start with [INFRA-LAY2-001](./INFRA-LAY2-001-service-boundaries.md)** - Understand service decomposition
2. **Then read [INFRA-LAY2-002](./INFRA-LAY2-002-critical-path-sequences.md)** - Understand critical paths
3. **Then read [INFRA-LAY2-003](./INFRA-LAY2-003-data-persistence-model.md)** - Understand data storage
4. **Finally read [INFRA-LAY2-004](./INFRA-LAY2-004-monitoring-observability.md)** - Understand observability

---

## Prerequisites

Before reading Layer 2, ensure familiarity with:

- [Layer 0: Foundation Design](../layer-0/README.md) - Core concepts and decision model
- [Layer 1: SDK Contracts & Events](../layer-1/README.md) - API contracts and events

---

## Next Layer

After Layer 2, proceed to:

- [Layer 3](../layer-3/) - Implementation standards and coding guidelines
