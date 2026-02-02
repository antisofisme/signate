# EXAMPLE-G1-001: Product Vision

> **Example Decision**: Copy and adapt for your organization.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `EXAMPLE-G1-001` |
| **group_id** | GROUP-1 (Intent & Direction) |
| **feature_id** | F-01 (Vision & Outcome) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | CRITICAL |
| **created_by** | [Your Name] |
| **created_at** | [Date] |
| **supersedes** | null |

---

## Statement

**Our product focuses on the B2B SaaS market, specifically mid-market companies (100-1000 employees) in the manufacturing sector.**

---

## Rationale

We chose B2B SaaS for mid-market manufacturing because:

1. **Market Gap**: Enterprise solutions are too expensive and complex for mid-market. Consumer solutions lack industry-specific features.

2. **Revenue Model**: B2B SaaS provides predictable recurring revenue with higher contract values than B2C.

3. **Domain Expertise**: Our founding team has 15+ years combined experience in manufacturing operations.

4. **Competitive Landscape**: Few purpose-built solutions exist for this segment. Most competitors are horizontal tools retrofitted for manufacturing.

5. **Growth Trajectory**: Mid-market manufacturing is underserved and growing at 8% annually.

---

## Constraints

### PROHIBITION
1. **P-001**: Product features MUST NOT target consumer (B2C) use cases
2. **P-002**: Product MUST NOT be marketed to enterprises (>1000 employees) without explicit vision update
3. **P-003**: Non-manufacturing verticals MUST NOT be prioritized over manufacturing features

### REQUIREMENT
1. **R-001**: All major features MUST serve at least one manufacturing workflow
2. **R-002**: Pricing MUST be structured for mid-market budget constraints
3. **R-003**: Sales motion MUST be self-serve or low-touch (not enterprise sales cycle)

### LIMITATION
1. **L-001**: Enterprise features (SSO, audit logs, etc.) are optional, not core
2. **L-002**: International expansion limited to English-speaking markets initially

---

## Invariants

These properties are ALWAYS true:

1. Product serves B2B customers, never B2C
2. Mid-market (100-1000 employees) is primary target segment
3. Manufacturing is primary vertical focus
4. SaaS is delivery model (not on-premise or hybrid)

---

## Success Criteria

| Metric | Target | Timeline |
|--------|--------|----------|
| Target customer segment | >80% mid-market | Year 1 |
| Manufacturing vertical | >70% of customers | Year 1 |
| ARR per customer | $10K-$100K range | Year 2 |
| Customer acquisition cost | <$5K | Year 2 |

---

## Related Decisions

- EXAMPLE-G1-002: Problem Scope (defines specific problem within this vision)
- [Future]: Pricing Strategy (GROUP-3/F-09)
- [Future]: Geographic Expansion (GROUP-4/F-15)

---

## Evolution Path

This decision may evolve via supersedes when:
- Market research indicates segment shift needed
- Vertical expansion becomes strategic priority
- Enterprise demand justifies upmarket move

Example evolution:
```
v1.0.0: "B2B SaaS for mid-market manufacturing"
v1.1.0: "B2B SaaS for mid-market manufacturing and logistics"
v2.0.0: "B2B SaaS for mid-market industrial operations (manufacturing, logistics, warehousing)"
```

---

## Template Notes

**When adapting this example:**

1. Replace market segment with your target
2. Update rationale with your specific reasons
3. Define your success criteria
4. List actual related decisions from your organization
