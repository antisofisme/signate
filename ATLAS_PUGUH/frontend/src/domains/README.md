# ATLAS_PUGUH CMS - Domain Architecture

## CRITICAL: 5 Separated Infrastructure Domains

This CMS is organized into **5 STRICTLY SEPARATED domains**.
Each domain corresponds to ONE infrastructure function.

**MIXING DOMAINS IS FORBIDDEN.**

---

## Domain Structure

```
src/domains/
├── iam/              # 1. Identity & Access Management
├── tenant/           # 2. Tenant Isolation
├── decision/         # 3. Decision (PDP) - Rules & Policies
├── workflow/         # 4. Workflow (Approval)
└── control/          # 5. Control & Audit
```

---

## Domain Boundaries (NON-NEGOTIABLE)

| Domain | CAN DO | CANNOT DO |
|--------|--------|-----------|
| **IAM** | View users, roles, permissions | Override decisions, grant direct access |
| **Tenant** | View tenant boundaries | Cross-tenant data access |
| **Decision** | Manage rules, view history | Edit past decisions, force outcomes |
| **Workflow** | Approve/reject pending items | Create decisions, change rules |
| **Control** | View audit trail, events | Mutate audit, replay events |

---

## Routing Convention

Each domain has its own route prefix:

| Domain | Route Prefix | Example |
|--------|--------------|---------|
| IAM | `/iam/*` | `/iam/users`, `/iam/roles` |
| Tenant | `/tenant/*` | `/tenant/list`, `/tenant/:id` |
| Decision | `/decision/*` | `/decision/rules`, `/decision/history` |
| Workflow | `/workflow/*` | `/workflow/pending`, `/workflow/:id` |
| Control | `/control/*` | `/control/audit`, `/control/events` |

---

## API Call Rules

1. **ALL API calls MUST go through SDK client**
2. **ALL mutations MUST include idempotency_key**
3. **ALL requests MUST include tenant context**
4. **ALL requests MUST include subject context**

```typescript
// CORRECT
await sdk.decision.createRuleDraft({
  context: { tenant_id, subject_id, trace_id, idempotency_key },
  rule_name: "...",
});

// FORBIDDEN - Direct API call
await fetch("/api/rules", { method: "POST", ... });
```

---

## Cross-Domain Navigation

Users MAY navigate between domains, but:
- Each domain loads fresh context
- No state sharing between domains
- No combined actions across domains

---

## File Structure per Domain

```
src/domains/{domain}/
├── index.ts              # Domain exports
├── routes.tsx            # Domain routes
├── pages/                # Page components
│   ├── ListPage.tsx
│   └── DetailPage.tsx
├── components/           # Domain-specific components
├── hooks/                # Domain-specific hooks
├── api/                  # API calls (via SDK)
└── types/                # Domain types
```
