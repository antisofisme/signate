# EXAMPLE-G1-002: Problem Scope

> **Example Decision**: Copy and adapt for your organization.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `EXAMPLE-G1-002` |
| **group_id** | GROUP-1 (Intent & Direction) |
| **feature_id** | F-02 (Problem Statement) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | HIGH |
| **created_by** | [Your Name] |
| **created_at** | [Date] |
| **supersedes** | null |

---

## Statement

**We solve the production scheduling problem: manufacturers struggle to balance capacity, deadlines, and resource constraints, resulting in 15-30% efficiency loss.**

---

## Rationale

Production scheduling is our focus because:

1. **Quantified Pain**: Customer interviews revealed scheduling consumes 20+ hours/week for production managers and still results in missed deadlines.

2. **High Impact**: Solving scheduling improves delivery times (customer satisfaction), reduces overtime (cost), and optimizes machine utilization (efficiency).

3. **Solvable with Software**: Unlike physical constraints, scheduling is a data problem. Better algorithms and real-time visibility can dramatically improve outcomes.

4. **Differentiation**: Competitors focus on ERP (too broad) or MES (too narrow). Scheduling is the underserved middle layer.

5. **Expansion Platform**: Scheduling touches inventory, workforce, and quality - natural expansion vectors.

---

## Problem Dimensions

### What We Solve

| Problem | Current State | Our Solution |
|---------|---------------|--------------|
| Capacity planning | Spreadsheets, gut feel | Algorithm-driven optimization |
| Deadline management | Reactive firefighting | Predictive alerts |
| Resource allocation | Manual juggling | Automated suggestions |
| Schedule changes | Cascade failures | Impact analysis |

### What We DON'T Solve (Non-Goals)

| Problem | Why Not | Alternative |
|---------|---------|-------------|
| Inventory management | Different domain | Partner integration |
| Quality control | Requires hardware | Phase 2 consideration |
| Workforce HR | Commodity market | Integration with HRIS |
| Financial planning | Outside expertise | Partner with accounting tools |

---

## Constraints

### PROHIBITION
1. **P-001**: Product MUST NOT attempt to solve inventory management in v1
2. **P-002**: Features MUST NOT require hardware deployment at customer site
3. **P-003**: Problem scope MUST NOT expand without explicit decision update

### REQUIREMENT
1. **R-001**: All features MUST directly improve scheduling outcomes
2. **R-002**: Non-scheduling features MUST integrate with scheduling (not standalone)
3. **R-003**: Problem definition MUST be validated with 10+ customer interviews before change

### LIMITATION
1. **L-001**: Hardware integration limited to read-only data ingestion
2. **L-002**: Financial features limited to scheduling cost impact (not accounting)

---

## Invariants

These properties are ALWAYS true:

1. Production scheduling is core problem domain
2. Software-only solution (no hardware required)
3. Mid-market manufacturing is context (from EXAMPLE-G1-001)
4. Measurable efficiency improvement is success criteria

---

## Problem Validation

| Validation Method | Findings |
|-------------------|----------|
| Customer interviews (n=25) | 92% cite scheduling as top-3 pain point |
| Market research | TAM for manufacturing scheduling: $2.3B |
| Competitor analysis | No dominant player in mid-market segment |
| Pilot results | 23% efficiency improvement in 3 pilots |

---

## Related Decisions

- EXAMPLE-G1-001: Product Vision (parent context)
- [Future]: Feature Prioritization Framework (GROUP-3/F-09)
- [Future]: Integration Strategy (GROUP-2/F-08)

---

## Evolution Path

Problem scope may evolve when:
- Core problem is solved (expansion needed)
- Market feedback indicates adjacent problem is more valuable
- Technology enables previously impossible solutions

Example evolution:
```
v1.0.0: "Production scheduling problem"
v1.1.0: "Production scheduling with quality correlation"
v2.0.0: "Production operations optimization (scheduling, quality, maintenance)"
```

---

## Template Notes

**When adapting this example:**

1. Define your specific problem with quantified impact
2. Clearly separate what you DO and DON'T solve
3. Include validation evidence (interviews, research)
4. Link to vision decision for context
