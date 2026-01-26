# INFRA Layer 3: Implementation Standards

**PURPOSE**: This layer defines **how Infra components are implemented** with specific coding standards and patterns.

Layer 3 provides the implementation-level details for SDK, Core Service, CMS, Data Layer, Event/Logging, and Testing. This is the "HOW to code" layer - all earlier layers define "WHAT" and "WHY", this layer defines the technical execution standards.

---

## Documents

### 1. [INFRA-LAY3-001: SDK Implementation Standards](./INFRA-LAY3-001-sdk-implementation-standards.md)

Defines implementation standards for all SDK language bindings.

- HTTP request/response patterns
- Request validation and sanitization
- Auth context forwarding
- Idempotency implementation
- Error handling and retry logic

---

### 2. [INFRA-LAY3-002: Core Service Implementation Standards](./INFRA-LAY3-002-core-service-implementation-standards.md)

Defines implementation standards for Infra Core service.

- Rule evaluation engine implementation
- Decision creation pipeline
- Workflow state machine implementation
- Tenant isolation enforcement in code

---

### 3. [INFRA-LAY3-003: CMS Implementation Standards](./INFRA-LAY3-003-cms-implementation-standards.md)

Defines implementation standards for Infra CMS.

- Rule CRUD API implementation
- Rule versioning and rollback
- Audit query API
- Admin UI patterns

---

### 4. [INFRA-LAY3-004: Data Layer Implementation Standards](./INFRA-LAY3-004-data-layer-implementation-standards.md)

Defines implementation standards for data persistence.

- Database schema patterns
- Query optimization
- Indexing strategies
- Tenant partitioning implementation

---

### 5. [INFRA-LAY3-005: Event & Logging Implementation Standards](./INFRA-LAY3-005-event-logging-implementation-standards.md)

Defines implementation standards for events and logging.

- Event emission implementation
- Structured logging format
- Audit log recording
- Event delivery guarantees

---

### 6. [INFRA-LAY3-006: Testing & Verification Standards](./INFRA-LAY3-006-testing-verification-standards.md)

Defines testing standards and verification requirements.

- Unit testing patterns
- Integration testing requirements
- Contract testing
- Security testing checklist

---

## Reading Order

1. **Start with [INFRA-LAY3-001](./INFRA-LAY3-001-sdk-implementation-standards.md)** - SDK is entry point
2. **Then read [INFRA-LAY3-002](./INFRA-LAY3-002-core-service-implementation-standards.md)** - Core is decision engine
3. **Then read [INFRA-LAY3-003](./INFRA-LAY3-003-cms-implementation-standards.md)** - CMS is config plane
4. **Then read [INFRA-LAY3-004](./INFRA-LAY3-004-data-layer-implementation-standards.md)** - Data layer patterns
5. **Then read [INFRA-LAY3-005](./INFRA-LAY3-005-event-logging-implementation-standards.md)** - Event & logging
6. **Finally read [INFRA-LAY3-006](./INFRA-LAY3-006-testing-verification-standards.md)** - Testing standards

---

## Prerequisites

Before reading Layer 3, ensure familiarity with:

- [Layer 0: Foundation Design](../layer-0/README.md) - Core concepts
- [Layer 1: SDK Contracts & Events](../layer-1/README.md) - API contracts
- [Layer 2: Architecture & Service Boundaries](../layer-2/README.md) - System architecture

---

## Implementation Note

Layer 3 documents are **implementation guides**, not laws. Deviations are permitted with documented rationale, but the spirit of the standards (security, immutability, tenant isolation) is non-negotiable.
