# MANTRA Terminology Mapping

**Purpose**: Map between LAW terminology and implementation code

---

## LAW ↔ Code Mapping

### Groups → Domains

| LAW Term | Code Enum | Full Name |
|----------|-----------|-----------|
| GROUP-1 | `INT` | Intent & Direction |
| GROUP-2 | `ARCH` | Architecture & Boundaries |
| GROUP-3 | `CTL` | Control, Policy & Risk |
| GROUP-4 | `EVO` | Execution & Evolution |

### Features → Aspects

| LAW Term | Code Enum | Name | Domain |
|----------|-----------|------|--------|
| F-01 | `A01` | Vision & Outcome | INT |
| F-02 | `A02` | Problem Statement | INT |
| F-03 | `A03` | Scope & Non-Goals | INT |
| F-04 | `A04` | Principles & Values | INT |
| F-05 | `A05` | Domain & Bounded Context | ARCH |
| F-06 | `A06` | Service & Module Boundary | ARCH |
| F-07 | `A07` | Data Ownership & Sovereignty | ARCH |
| F-08 | `A08` | Integration & Contract Model | ARCH |
| F-09 | `A09` | Policy & Rules | CTL |
| F-10 | `A10` | Approval & Authority Model | CTL |
| F-11 | `A11` | Security & Compliance Posture | CTL |
| F-12 | `A12` | Risk & Blast Radius | CTL |
| F-13 | `A13` | Decision Lifecycle | EVO |
| F-14 | `A14` | Reversibility & Exit Strategy | EVO |
| F-15 | `A15` | Environment & Promotion Rules | EVO |
| F-16 | `A16` | Anti-Drift & Consistency | EVO |

---

## Code Examples

```python
# LAW says: GROUP-3 / F-09
# Code uses:
domain_id = DomainId.CTL   # GROUP-3 → CTL
aspect_id = AspectId.A09   # F-09 → A09
code = "CTL-A09-001"       # Decision code format
```

---

## Why Different Names?

| LAW | Code | Reason |
|-----|------|--------|
| GROUP-1 | INT | Shorter, easier to type in code |
| F-01 | A01 | "Aspect" is more precise than "Feature" |

**Rule**: LAW terminology is authoritative for documentation. Code names are implementation convenience.

---

## Source of Truth

| Item | Location | Authority |
|------|----------|-----------|
| Taxonomy (4×4) | `MANTRA-LAW-001` | Constitutional |
| Enum definitions | `schema_base.py` | Implementation |
| Mapping | This document | Reference |
