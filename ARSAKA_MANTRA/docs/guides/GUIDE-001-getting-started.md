# Getting Started with MANTRA

> Record your first decision in 5 minutes.

---

## Step 1: Access MANTRA

**URL**: `http://31.97.111.175:3001`

Open in your browser. No installation required.

---

## Step 2: Understand the Dashboard

When you log in, you'll see:

```
┌─────────────────────────────────────────────────────────────┐
│  ARSAKA_MANTRA                           [AI = ZERO]         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   GROUP-1   │  │   GROUP-2   │  │   GROUP-3   │  ...    │
│  │  Intent &   │  │ Architecture│  │  Control &  │         │
│  │  Direction  │  │ & Boundaries│  │   Policy    │         │
│  │             │  │             │  │             │         │
│  │  0 decisions│  │  0 decisions│  │  0 decisions│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  [Validator]  [Audit Log]  [All Decisions]                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 3: Choose a Group

Before recording a decision, determine which GROUP it belongs to:

| If your decision is about... | Use GROUP |
|------------------------------|-----------|
| WHY we're doing something (vision, goals, scope) | **GROUP-1** |
| HOW we build it (architecture, boundaries, data) | **GROUP-2** |
| What's ALLOWED/FORBIDDEN (policies, authority) | **GROUP-3** |
| How things CHANGE (lifecycle, versioning, environments) | **GROUP-4** |

### Quick Examples

```
"We will focus on B2B market" → GROUP-1 (Intent)
"Payment is a separate microservice" → GROUP-2 (Architecture)
"Only managers can approve expenses" → GROUP-3 (Control)
"APIs deprecated after 12 months" → GROUP-4 (Evolution)
```

---

## Step 4: Choose a Feature

Each GROUP has 4 FEATURES. Pick the most specific one:

### GROUP-1 Features (Intent)
| Feature | Use When... |
|---------|-------------|
| F-01: Vision & Outcome | Long-term goals, success criteria |
| F-02: Problem Statement | Defining the problem you're solving |
| F-03: Scope & Non-Goals | What's in/out of scope |
| F-04: Principles & Values | Guiding principles, trade-offs |

### GROUP-2 Features (Architecture)
| Feature | Use When... |
|---------|-------------|
| F-05: Domain & Bounded Context | Business domain boundaries |
| F-06: Service & Module Boundary | Technical component boundaries |
| F-07: Data Ownership & Sovereignty | Who owns what data |
| F-08: Integration & Contract Model | How systems communicate |

### GROUP-3 Features (Control)
| Feature | Use When... |
|---------|-------------|
| F-09: Policy & Rules | Business rules, constraints |
| F-10: Approval & Authority | Who can approve what |
| F-11: Security & Compliance | Security requirements |
| F-12: Risk & Blast Radius | Risk assessment |

### GROUP-4 Features (Evolution)
| Feature | Use When... |
|---------|-------------|
| F-13: Decision Lifecycle | How decisions evolve |
| F-14: Reversibility & Exit | How to undo/exit |
| F-15: Environment & Promotion | Dev→Staging→Prod rules |
| F-16: Anti-Drift & Consistency | Preventing divergence |

---

## Step 5: Record Your Decision

Click on the GROUP, then "New Decision".

### Required Fields

**Statement** (1-2 sentences)
```
What is the decision? Be clear and specific.

Good: "All public APIs MUST use semantic versioning (major.minor.patch)"
Bad: "We should think about API versioning sometime"
```

**Rationale** (required, cannot be empty)
```
WHY this decision? This is the most important field.

Good: "Semantic versioning enables clients to understand breaking vs
      non-breaking changes. It's industry standard and tooling supports it."
Bad: "Because it's good"
```

**Group & Feature**
```
Select from dropdowns. Must match (F-01 to F-04 = GROUP-1, etc.)
```

**Version**
```
Start with 1.0.0 for new decisions.
Use semantic versioning: major.minor.patch
```

### Optional Fields

**Constraints**
```
What MUST or MUST NOT happen?

Example:
- PROHIBITION: API versions MUST NOT be removed without 12-month notice
- REQUIREMENT: All version changes MUST be documented in changelog
- LIMITATION: Breaking changes only in major versions
```

**Invariants**
```
What is ALWAYS true regardless of circumstances?

Example:
- Version number always increases, never decreases
- Changelog always accompanies version bump
```

**Related Decisions**
```
Link to other decisions this relates to (optional).
```

---

## Step 6: Save

Click "Store Decision".

The decision is now:
- ✅ **Permanently stored** (cannot be modified)
- ✅ **Auditable** (who created, when)
- ✅ **Versioned** (can be superseded later)
- ✅ **Classified** (in the taxonomy)

---

## Step 7: Evolving Decisions

Decisions don't change. They **evolve** via supersedes.

### To Update a Decision

1. Open the existing decision
2. Click "Create Superseding Decision"
3. The new decision will have `supersedes: [original-id]`
4. Bump the version (1.0.0 → 1.1.0 or 2.0.0)
5. Explain WHY in the rationale

### Example Evolution

```
v1.0.0: "All APIs use REST"
        Rationale: "REST is simple and well-understood"

v1.1.0: "All APIs use REST, GraphQL for mobile"
        Rationale: "Mobile needs flexible queries, REST still for web"
        supersedes: v1.0.0

v2.0.0: "GraphQL primary, REST deprecated"
        Rationale: "GraphQL adoption successful, REST maintenance burden"
        supersedes: v1.1.0
```

All three versions remain visible in history.

---

## Common Questions

### "What if I make a mistake in the decision?"

You cannot edit it (immutable). Create a new version that supersedes it with corrections.

### "Can I delete a decision?"

No. Decisions are permanent. If it's wrong, supersede it with a corrected version.

### "Who can see my decisions?"

All decisions in your organization are visible to all members. Transparency is intentional.

### "Can AI help me write decisions?"

AI can help DRAFT decisions, but a human must:
- Review the draft
- Make final edits
- Click "Store Decision"

The `created_by` field will show the human who submitted.

### "What's the difference between constraints and invariants?"

- **Constraints**: Rules that must be followed (MUST, MUST NOT, etc.)
- **Invariants**: Properties that are always true, no matter what

---

## Next Steps

1. **Record 3-5 decisions** to get comfortable with the system
2. **Read existing decisions** to understand organizational context
3. **Link related decisions** to build the decision graph
4. **Involve your team** - decisions are better with input

---

## Need Help?

- **Validator**: Use `/validate` to check decision format before storing
- **Audit Log**: See all actions at `/audit`
- **Compare**: Compare two decisions at `/decisions/{id}/compare/{other_id}`
- **History**: See version chain at `/decisions/{id}/history`
