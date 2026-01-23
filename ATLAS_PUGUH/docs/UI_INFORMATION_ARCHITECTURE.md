# ATLAS_PUGUH CMS - UI Information Architecture

**Phase**: 4
**Status**: IMPLEMENTATION READY
**Date**: 2026-01-24

---

## Overview

The CMS is structured around **5 infrastructure domains** that MUST remain strictly separated.
This document defines the menu structure, routing, and screen organization.

---

## Navigation Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│  ATLAS_PUGUH Control Plane                              [User Menu] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │   IAM   │ │ TENANT  │ │DECISION │ │WORKFLOW │ │ CONTROL │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
│       │           │           │           │           │             │
│       ▼           ▼           ▼           ▼           ▼             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     DOMAIN CONTENT AREA                      │   │
│  │                                                               │   │
│  │   (Only ONE domain visible at a time)                        │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Menu Structure

### Top-Level Navigation (5 Tabs)

| Tab | Icon | Label | Route | Description |
|-----|------|-------|-------|-------------|
| 1 | 👤 | IAM | `/iam` | Identity & Access Management |
| 2 | 🏢 | Tenant | `/tenant` | Tenant Isolation |
| 3 | ⚖️ | Decision | `/decision` | Rules & Policy Decision |
| 4 | ✅ | Workflow | `/workflow` | Approval Workflows |
| 5 | 📊 | Control | `/control` | Audit & Monitoring |

### Visual Separation

- Each domain has a **distinct accent color**
- Domain header clearly shows which domain is active
- No breadcrumbs crossing domain boundaries

| Domain | Accent Color | Background |
|--------|--------------|------------|
| IAM | Blue (#3B82F6) | Blue-50 |
| Tenant | Purple (#8B5CF6) | Purple-50 |
| Decision | Amber (#F59E0B) | Amber-50 |
| Workflow | Green (#10B981) | Green-50 |
| Control | Slate (#64748B) | Slate-50 |

---

## Route Structure

### 1. IAM Domain (`/iam/*`)

```
/iam
├── /users                    # User list
│   └── /:userId              # User detail
├── /roles                    # Role list
│   └── /:roleId              # Role detail & permissions
├── /service-accounts         # Service account list
│   └── /:accountId           # Service account detail
└── /permissions              # Permission matrix view
```

### 2. Tenant Domain (`/tenant/*`)

```
/tenant
├── /list                     # Tenant list
│   └── /:tenantId            # Tenant detail
├── /members                  # Tenant membership
│   └── /:tenantId/members    # Members of specific tenant
└── /isolation-check          # Isolation validation tool
```

### 3. Decision Domain (`/decision/*`)

```
/decision
├── /rules                    # Rule list
│   ├── /new                  # Create rule draft
│   └── /:ruleId              # Rule detail
│       ├── /versions         # Rule version history
│       └── /activate         # Activation flow
├── /types                    # Decision types
│   └── /:decisionType        # Type configuration
├── /history                  # Decision history
│   └── /:decisionId          # Decision detail (read-only)
└── /simulation               # Rule simulation tool
```

### 4. Workflow Domain (`/workflow/*`)

```
/workflow
├── /pending                  # Pending approvals (my queue)
├── /all                      # All workflows (admin view)
│   └── /:workflowId          # Workflow detail
│       ├── /approve          # Approval action
│       ├── /reject           # Rejection action
│       ├── /delegate         # Delegation action
│       └── /escalate         # Escalation action
├── /escalations              # Escalated items
└── /completed                # Completed workflows
```

### 5. Control Domain (`/control/*`)

```
/control
├── /audit                    # Audit trail
│   └── /:auditId             # Audit record detail
├── /events                   # Event timeline
│   └── /:eventId             # Event detail
├── /dlq                      # Dead-letter queue (read-only)
│   └── /:eventId             # DLQ event detail
├── /metrics                  # System metrics dashboard
└── /enforcement              # Enforcement status
```

---

## Screen Inventory

### 1. IAM Domain (6 screens)

| Screen | Route | Purpose | API Calls |
|--------|-------|---------|-----------|
| User List | `/iam/users` | List all users in tenant | `GET /api/v1/iam/users` |
| User Detail | `/iam/users/:id` | View user info & roles | `GET /api/v1/iam/users/:id` |
| Role List | `/iam/roles` | List all roles | `GET /api/v1/iam/roles` |
| Role Detail | `/iam/roles/:id` | View role permissions | `GET /api/v1/iam/roles/:id` |
| Service Accounts | `/iam/service-accounts` | List service accounts | `GET /api/v1/iam/service-accounts` |
| Permission Matrix | `/iam/permissions` | View permission mapping | `GET /api/v1/iam/permissions` |

### 2. Tenant Domain (4 screens)

| Screen | Route | Purpose | API Calls |
|--------|-------|---------|-----------|
| Tenant List | `/tenant/list` | List all tenants | `GET /api/v1/tenants` |
| Tenant Detail | `/tenant/:id` | View tenant info | `GET /api/v1/tenants/:id` |
| Tenant Members | `/tenant/:id/members` | View tenant membership | `GET /api/v1/tenants/:id/members` |
| Isolation Check | `/tenant/isolation-check` | Validate data isolation | `GET /api/v1/tenants/isolation-check` |

### 3. Decision Domain (8 screens)

| Screen | Route | Purpose | API Calls |
|--------|-------|---------|-----------|
| Rule List | `/decision/rules` | List all rules | `GET /api/v1/rules` |
| Create Rule | `/decision/rules/new` | Create rule draft | `POST /api/v1/rules` |
| Rule Detail | `/decision/rules/:id` | View rule | `GET /api/v1/rules/:id` |
| Rule Versions | `/decision/rules/:id/versions` | Version history | `GET /api/v1/rules/:id/versions` |
| Activate Rule | `/decision/rules/:id/activate` | Activation flow | `POST /api/v1/rules/:id/activate` |
| Decision Types | `/decision/types` | List decision types | `GET /api/v1/decision-types` |
| Decision History | `/decision/history` | View past decisions | `GET /api/v1/decisions` |
| Decision Detail | `/decision/history/:id` | Decision detail | `GET /api/v1/decisions/:id` |

### 4. Workflow Domain (6 screens)

| Screen | Route | Purpose | API Calls |
|--------|-------|---------|-----------|
| My Pending | `/workflow/pending` | My approval queue | `GET /api/v1/workflows?assignee=me&status=pending` |
| All Workflows | `/workflow/all` | Admin view | `GET /api/v1/workflows` |
| Workflow Detail | `/workflow/:id` | View workflow | `GET /api/v1/workflows/:id` |
| Approve | `/workflow/:id/approve` | Approve action | `POST /api/v1/workflows/:id/approve` |
| Reject | `/workflow/:id/reject` | Reject action | `POST /api/v1/workflows/:id/reject` |
| Escalations | `/workflow/escalations` | Escalated items | `GET /api/v1/workflows?status=escalated` |

### 5. Control Domain (6 screens)

| Screen | Route | Purpose | API Calls |
|--------|-------|---------|-----------|
| Audit Trail | `/control/audit` | View audit log | `GET /api/v1/audit` |
| Audit Detail | `/control/audit/:id` | Audit record | `GET /api/v1/audit/:id` |
| Event Timeline | `/control/events` | View events | `GET /api/v1/events` |
| Event Detail | `/control/events/:id` | Event detail | `GET /api/v1/events/:id` |
| DLQ View | `/control/dlq` | Dead-letter queue | `GET /api/v1/events/dlq` |
| Metrics | `/control/metrics` | System metrics | `GET /api/v1/metrics` |

---

## Total Screen Count: 30 screens

| Domain | Screens |
|--------|---------|
| IAM | 6 |
| Tenant | 4 |
| Decision | 8 |
| Workflow | 6 |
| Control | 6 |
| **Total** | **30** |

---

## Page Templates

### List Page Template
```
┌────────────────────────────────────────────────────┐
│ [Domain] > [Resource] List                         │
├────────────────────────────────────────────────────┤
│ [Search] [Filter ▼] [Sort ▼]         [+ Create]   │
├────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────┐ │
│ │ Item 1                              [Actions] │ │
│ ├────────────────────────────────────────────────┤ │
│ │ Item 2                              [Actions] │ │
│ ├────────────────────────────────────────────────┤ │
│ │ Item 3                              [Actions] │ │
│ └────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────┤
│ Showing 1-10 of 100                [< 1 2 3 ... >] │
└────────────────────────────────────────────────────┘
```

### Detail Page Template
```
┌────────────────────────────────────────────────────┐
│ [Domain] > [Resource] > [Name]         [Actions ▼] │
├────────────────────────────────────────────────────┤
│                                                    │
│ ┌─────────────────┐  ┌─────────────────────────┐  │
│ │   Metadata      │  │      Main Content       │  │
│ │                 │  │                         │  │
│ │ ID: xxx         │  │  [Tab 1] [Tab 2] [Tab3] │  │
│ │ Created: xxx    │  │  ┌───────────────────┐  │  │
│ │ Status: xxx     │  │  │                   │  │  │
│ │                 │  │  │   Tab Content     │  │  │
│ └─────────────────┘  │  │                   │  │  │
│                      │  └───────────────────┘  │  │
│                      └─────────────────────────┘  │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Action Confirmation Template
```
┌────────────────────────────────────────────────────┐
│                    ⚠️ Confirm Action                │
├────────────────────────────────────────────────────┤
│                                                    │
│  You are about to: [ACTION DESCRIPTION]            │
│                                                    │
│  This will:                                        │
│  ✓ Create a decision record                        │
│  ✓ Generate an audit trail entry                   │
│  ✓ Emit an event to subscribers                    │
│                                                    │
│  This action CANNOT be undone.                     │
│                                                    │
├────────────────────────────────────────────────────┤
│              [Cancel]        [Confirm]             │
└────────────────────────────────────────────────────┘
```

---

## Navigation Rules

### Allowed Navigation
- Within same domain: ✅ Always allowed
- To different domain: ✅ Via top navigation only
- Deep link to any screen: ✅ Allowed (with auth)

### Forbidden Navigation
- Cross-domain action buttons: ❌ NEVER
- Combined domain views: ❌ NEVER
- Embedded cross-domain widgets: ❌ NEVER

### Example: Forbidden Patterns

```
❌ FORBIDDEN: Decision page with embedded Workflow approval
❌ FORBIDDEN: IAM page with "Force Allow" button
❌ FORBIDDEN: Audit page with "Replay Event" button
❌ FORBIDDEN: Rule page with "Direct Activate" (bypassing workflow)
```

---

## Responsive Behavior

| Breakpoint | Navigation | Content |
|------------|------------|---------|
| Desktop (≥1024px) | Top tabs | Full layout |
| Tablet (768-1023px) | Top tabs | Condensed |
| Mobile (<768px) | Hamburger menu | Single column |

---

## Accessibility Requirements

- All interactive elements keyboard-navigable
- ARIA labels on all buttons
- Color not sole indicator of state
- Minimum contrast ratio 4.5:1
- Screen reader compatible
