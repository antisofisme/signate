# EXAMPLE-G2-002: Data Ownership

> **Example Decision**: Copy and adapt for your organization.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `EXAMPLE-G2-002` |
| **group_id** | GROUP-2 (Architecture & Boundaries) |
| **feature_id** | F-07 (Data Ownership & Sovereignty) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | CRITICAL |
| **created_by** | [Your Name] |
| **created_at** | [Date] |
| **supersedes** | null |

---

## Statement

**Customer data is owned by the CRM domain and MUST NOT be directly accessed by other services. All customer data access goes through the CRM API.**

---

## Rationale

CRM owns customer data because:

1. **Single Source of Truth**: Customer data scattered across services leads to inconsistency. CRM is the canonical source.

2. **Privacy Compliance**: GDPR, CCPA require knowing where PII lives. Single owner simplifies compliance.

3. **Data Quality**: One team responsible for customer data quality. No conflicting updates from multiple services.

4. **Access Control**: Centralized access control for sensitive customer information. Audit trail in one place.

5. **Schema Evolution**: Customer schema can evolve without coordinating with every consuming service.

---

## Data Ownership Matrix

| Data Domain | Owner Service | Access Pattern |
|-------------|---------------|----------------|
| Customer Profile | CRM | API read/write |
| Customer Preferences | CRM | API read/write |
| Contact Information | CRM | API read/write |
| Orders | Orders Service | API read/write |
| Payments | Payment Service | API read/write |
| Support Tickets | Support Service | API read/write |
| Analytics Events | Analytics Service | Event ingestion |

### Customer Data Scope

**CRM Owns (authoritative source):**
- Customer ID (UUID)
- Name, email, phone
- Billing address
- Shipping addresses
- Communication preferences
- Account status
- Customer segment

**CRM Does NOT Own:**
- Order history (Orders Service owns, references customer_id)
- Payment methods (Payment Service owns, references customer_id)
- Support history (Support Service owns, references customer_id)

---

## Access Patterns

### Allowed

```python
# Other services get customer data via CRM API
customer = crm_client.get_customer(customer_id)
customer_email = crm_client.get_customer_email(customer_id)
customers = crm_client.search_customers(query)
```

### Forbidden

```python
# Direct database access is FORBIDDEN
# ❌ WRONG
cursor.execute("SELECT * FROM customers WHERE id = ?", [customer_id])

# ❌ WRONG - Cross-database join
SELECT o.*, c.email
FROM orders o
JOIN crm_db.customers c ON o.customer_id = c.id
```

---

## Constraints

### PROHIBITION
1. **P-001**: Services MUST NOT directly query CRM database
2. **P-002**: Customer PII MUST NOT be copied to other service databases
3. **P-003**: Customer data MUST NOT be cached longer than 24 hours in other services
4. **P-004**: Customer data MUST NOT be logged in plain text

### REQUIREMENT
1. **R-001**: All customer data access MUST go through CRM API
2. **R-002**: Services MUST store only customer_id reference, not full customer data
3. **R-003**: CRM API MUST support data export for GDPR requests
4. **R-004**: CRM MUST emit events when customer data changes

### LIMITATION
1. **L-001**: CRM API rate limits: 1000 requests/minute per service
2. **L-002**: Bulk operations limited to 100 customers per request

---

## Invariants

These properties are ALWAYS true:

1. CRM is single source of truth for customer data
2. Other services store customer_id reference only
3. All customer PII access goes through CRM API
4. Customer data changes emit events

---

## Implementation Reference

### CRM API Contract

```yaml
# Customer API
GET    /api/v1/customers/{id}
POST   /api/v1/customers
PATCH  /api/v1/customers/{id}
DELETE /api/v1/customers/{id}    # Soft delete (GDPR)
GET    /api/v1/customers/search?q={query}
POST   /api/v1/customers/export  # GDPR export

# Batch operations
POST   /api/v1/customers/batch/get
POST   /api/v1/customers/batch/validate
```

### Event Contract

```json
{
  "event_type": "customer.updated",
  "customer_id": "cust_123",
  "changed_fields": ["email", "phone"],
  "timestamp": "2025-01-24T10:00:00Z"
}
```

### Reference Pattern in Other Services

```python
# Orders Service - stores reference only
class Order:
    id: str
    customer_id: str  # Reference to CRM
    # NO customer_name, customer_email here!

# When display needed, call CRM API
def get_order_with_customer(order_id):
    order = order_repo.get(order_id)
    customer = crm_client.get_customer(order.customer_id)
    return {**order, "customer": customer}
```

---

## Data Flow Diagram

```
┌─────────────┐
│   Orders    │──── customer_id ────┐
│   Service   │                     │
└─────────────┘                     │
                                    ▼
┌─────────────┐              ┌─────────────┐
│   Payment   │──── API ────►│     CRM     │
│   Service   │              │   Service   │
└─────────────┘              └─────────────┘
                                    │
┌─────────────┐                     │
│   Support   │──── customer_id ────┘
│   Service   │
└─────────────┘

Legend:
────► API call to get customer data
──── Reference (customer_id stored locally)
```

---

## Related Decisions

- EXAMPLE-G2-001: Service Boundary (defines service isolation)
- [Future]: Data Retention Policy (GROUP-3/F-11)
- [Future]: GDPR Compliance Strategy (GROUP-3/F-11)

---

## Evolution Path

Data ownership may evolve when:
- New data domains emerge
- Compliance requirements change
- Performance requires caching strategies

Example evolution:
```
v1.0.0: "CRM owns all customer data"
v1.1.0: "CRM owns customer data, read replicas allowed with 1-hour sync"
v2.0.0: "CRM owns customer data, Customer Data Platform for analytics"
```

---

## Template Notes

**When adapting this example:**

1. Create data ownership matrix for your domains
2. Define clear allowed/forbidden patterns
3. Specify API and event contracts
4. Include compliance considerations (GDPR, etc.)
5. Document caching and consistency rules
