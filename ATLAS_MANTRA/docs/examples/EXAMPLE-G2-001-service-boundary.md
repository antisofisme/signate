# EXAMPLE-G2-001: Service Boundary

> **Example Decision**: Copy and adapt for your organization.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `EXAMPLE-G2-001` |
| **group_id** | GROUP-2 (Architecture & Boundaries) |
| **feature_id** | F-06 (Service & Module Boundary) |
| **version** | 1.0.0 |
| **scope** | TEAM |
| **blast_radius** | HIGH |
| **created_by** | [Your Name] |
| **created_at** | [Date] |
| **supersedes** | null |

---

## Statement

**Payment processing is a standalone microservice with its own database, deployable independently from the main application.**

---

## Rationale

Payment as separate service because:

1. **Compliance Isolation**: PCI-DSS compliance is easier when payment scope is isolated. Audit surface is reduced.

2. **Deployment Independence**: Payment changes (new provider, rate changes) shouldn't require full app deployment.

3. **Scaling Independence**: Payment load patterns differ from main app. Black Friday requires payment scaling, not necessarily app scaling.

4. **Team Ownership**: Clear ownership boundary. Payment team owns everything in payment service.

5. **Failure Isolation**: Payment outages shouldn't crash the main application. Graceful degradation possible.

---

## Service Definition

### Payment Service Scope

**Includes:**
- Payment intent creation
- Payment provider integration (Stripe, PayPal)
- Transaction recording
- Refund processing
- Payment webhook handling
- PCI-compliant card storage (via provider)

**Excludes:**
- Order management (belongs to Orders service)
- Invoice generation (belongs to Billing service)
- Subscription management (belongs to Subscription service)
- Customer management (belongs to Customer service)

### Service Interface

```
Payment Service API:
├── POST /payments/intents          # Create payment intent
├── POST /payments/capture          # Capture authorized payment
├── POST /payments/refund           # Process refund
├── GET  /payments/{id}             # Get payment status
├── POST /payments/webhooks/{provider}  # Provider webhooks
└── GET  /payments/methods/{customer}   # List saved methods
```

### Data Ownership

| Data | Owner | Access Pattern |
|------|-------|----------------|
| Transactions | Payment Service | Read/Write |
| Payment Methods | Payment Service | Read/Write |
| Customer ID | Customer Service | Read-only reference |
| Order ID | Orders Service | Read-only reference |

---

## Constraints

### PROHIBITION
1. **P-001**: Other services MUST NOT directly access payment database
2. **P-002**: Payment service MUST NOT store full card numbers (use tokenization)
3. **P-003**: Synchronous calls to payment service MUST NOT block order creation

### REQUIREMENT
1. **R-001**: All payment operations MUST go through Payment Service API
2. **R-002**: Payment service MUST emit events for transaction state changes
3. **R-003**: Payment service MUST be deployable without other services
4. **R-004**: Payment service MUST have its own CI/CD pipeline

### LIMITATION
1. **L-001**: Maximum 3 payment provider integrations initially
2. **L-002**: Refunds limited to original payment method

---

## Invariants

These properties are ALWAYS true:

1. Payment service has its own database
2. No direct database access from other services
3. All inter-service communication via API or events
4. Payment service can be deployed independently

---

## Implementation Reference

```
payment-service/
├── src/
│   ├── api/
│   │   ├── routes.py           # API endpoints
│   │   └── webhooks.py         # Provider webhooks
│   ├── domain/
│   │   ├── payment.py          # Payment entity
│   │   └── transaction.py      # Transaction entity
│   ├── providers/
│   │   ├── stripe.py           # Stripe integration
│   │   └── paypal.py           # PayPal integration
│   └── events/
│       └── publisher.py        # Event publishing
├── database/
│   └── migrations/             # Payment-specific migrations
├── Dockerfile                  # Independent container
└── docker-compose.yml          # Local development
```

---

## Inter-Service Communication

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Orders    │────────►│   Payment   │────────►│   Billing   │
│   Service   │  API    │   Service   │  Event  │   Service   │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              │ Event: PaymentCompleted
                              ▼
                        ┌─────────────┐
                        │   Message   │
                        │    Queue    │
                        └─────────────┘
```

---

## Related Decisions

- EXAMPLE-G2-002: Data Ownership (defines data boundaries)
- [Future]: Event Schema Standards (GROUP-2/F-08)
- [Future]: Service Deployment Strategy (GROUP-4/F-15)

---

## Evolution Path

Service boundary may evolve when:
- New payment capabilities require scope expansion
- Performance requires further decomposition
- Business model changes (e.g., marketplace payments)

Example evolution:
```
v1.0.0: "Payment as single microservice"
v1.1.0: "Payment + Payout services (marketplace support)"
v2.0.0: "Payment platform (payments, payouts, treasury)"
```

---

## Template Notes

**When adapting this example:**

1. Define clear scope (what's in/out)
2. Specify data ownership explicitly
3. Document API contract at high level
4. Show inter-service communication pattern
5. Include infrastructure requirements (separate DB, deployment)
