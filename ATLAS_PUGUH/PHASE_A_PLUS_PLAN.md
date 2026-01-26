# PHASE A+ (VISIBILITY EXPANSION) - Implementation Plan

**Date**: 2026-01-10
**Phase**: A+ (Post-deployment visibility)
**Objective**: Build visibility into decision & approval flow WITHOUT changing business logic
**Standards**: Follow ATLAS_PANDAWA docs conventions

---

## 🎯 LOCKED OBJECTIVES

### Primary Goal
Make decision flow **visually understandable** to humans without reading code or docs.

### Decision Story to Show
```
1. Decision requested     → Form visible
2. Rule evaluated         → Which rule matched (if any)
3. Outcome determined     → ALLOWED / DENIED / REQUIRE_APPROVAL
4. Approval required?     → Workflow visible in inbox
5. Approval action taken  → Approver + timestamp visible
6. Final outcome recorded → Decision detail shows complete story
7. Audit trail visible    → Read-only timeline of all events
```

---

## 🔒 NON-NEGOTIABLE RULES (LOCKED)

### ❌ FORBIDDEN
- Change CORE domain logic
- Add new backend responsibilities
- Add business logic
- Optimize for performance
- Add scaling, HA, caching, retries
- Enable Redis, RLS, metrics, tracing
- Add tenant, user, or role management
- Add pagination, bulk actions, advanced filters
- Add UX polish beyond clarity

### ✅ ALLOWED
- Frontend visualization screens
- Backend descriptive response fields (labels, summaries)
- Read-only audit endpoints
- Normalize response shapes for frontend readability

---

## 📦 TECH STACK (Following ATLAS_PANDAWA Standards)

### Frontend Stack
```
Technology             Purpose                    Version
─────────────────────────────────────────────────────────
Bun                    Runtime + Package Manager  1.x
Vite                   Build tool                 5.x
React 18+              UI framework               18.x
TypeScript             Type safety                5.x
Tailwind CSS           Utility CSS                3.x
shadcn/ui              Component library          latest
TanStack Query         Server state cache         5.x
Zustand                Client/UI state            4.x
React Hook Form        Form state management      7.x
Zod                    Schema validation          3.x
React Router 6+        SPA routing                6.x
Axios                  HTTP client                1.x
```

**Note**: Menggunakan **Bun** sebagai runtime dan package manager (bukan npm/yarn/pnpm)

### Directory Structure (Following ATLAS_PANDAWA Convention)
```
frontend/
├── src/
│   ├── features/              # Feature modules
│   │   ├── decisions/         # Decision management
│   │   │   ├── api/           # API calls
│   │   │   ├── components/    # UI components
│   │   │   ├── hooks/         # Custom hooks
│   │   │   └── types/         # TypeScript types
│   │   ├── approvals/         # Approval inbox
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── types/
│   │   └── audit/             # Audit trail (read-only)
│   │       ├── api/
│   │       ├── components/
│   │       ├── hooks/
│   │       └── types/
│   ├── shared/                # Shared code
│   │   ├── components/        # Reusable UI components
│   │   ├── layouts/           # Page layouts
│   │   ├── lib/               # Utilities
│   │   └── types/             # Shared types
│   └── stores/                # Zustand stores
│       ├── auth.ts            # Auth state (minimal)
│       └── ui.ts              # UI state (theme, sidebar, etc)
```

---

## 📱 SCREENS TO BUILD

### 1. Decision List Page
**Route**: `/decisions`
**Purpose**: Show all decisions with their current status

**Columns**:
- Decision ID (truncated UUID)
- Decision Type
- Amount (if applicable)
- Outcome (ALLOWED / DENIED / REQUIRE_APPROVAL)
- Created At
- Status (Pending Approval / Completed)

**Actions**:
- Click row → Navigate to detail
- "Create Decision" button → Navigate to form

**No pagination** - Show all (Phase A+ limitation)
**No filters** - Basic only (Phase A+ limitation)

---

### 2. Create Decision Form
**Route**: `/decisions/new`
**Purpose**: Submit a new decision request

**Fields**:
```typescript
{
  decision_type: string        // e.g., "purchase_request"
  context: {
    amount?: number           // For amount-based rules
    description?: string
    [key: string]: any        // Flexible for different decision types
  }
}
```

**Behavior**:
- Submit → POST /api/decisions
- Response shows:
  - Outcome (ALLOWED / DENIED / REQUIRE_APPROVAL)
  - If REQUIRE_APPROVAL → Show workflow created
  - Which rule matched (if any)
- Auto-redirect to decision detail on success

**Validation**: Zod schema (minimal)

---

### 3. Approval Inbox Page
**Route**: `/approvals`
**Purpose**: Show pending approvals for current user

**Columns**:
- Decision ID
- Decision Type
- Amount
- Requested At
- Requester (if available)

**Actions**:
- Click row → Navigate to approval detail
- Approve button → PUT /api/workflows/{id}/approve
- Reject button → PUT /api/workflows/{id}/reject

**Filter**: Show only PENDING_APPROVAL status

---

### 4. Decision Detail Page
**Route**: `/decisions/:id`
**Purpose**: Show complete decision story

**Sections**:

**A. Decision Info**
- Decision ID
- Decision Type
- Created At
- Context (JSON formatted)

**B. Evaluation Result**
- Outcome (with badge color)
- Rule Matched (ID + version)
- Latency (ms)

**C. Approval Workflow (if exists)**
- Workflow ID
- Current State
- Approver Role
- Delegated To (if any)
- Escalated To (if any)
- Created At
- Completed At (if terminal)

**D. Workflow Actions (if exists)**
- List of all actions taken
- Each action shows:
  - Action type (APPROVE / REJECT / DELEGATE / ESCALATE)
  - Actor (user ID - Phase A+ limitation: no user lookup)
  - Timestamp
  - Comment (if any)

**E. Audit Trail Link**
- Button → Navigate to `/audit?decision_id={id}`

---

### 5. Audit Trail Page
**Route**: `/audit`
**Purpose**: Read-only timeline of all events

**Query Params**:
- `decision_id` (optional) - Filter by decision

**Display**:
- Timeline view (newest first)
- Each event shows:
  - Event ID
  - Event Type
  - Aggregate Type
  - Aggregate ID
  - Timestamp
  - Metadata (JSON formatted)
  - Source

**No actions** - Read-only only

---

## 🔌 BACKEND CHANGES (Minimal - Visibility Only)

### Current Endpoints (From Phase A)
```
POST   /api/decisions                    # Create decision
GET    /api/decisions/{id}               # Get decision detail
PUT    /api/workflows/{id}/approve       # Approve workflow
PUT    /api/workflows/{id}/reject        # Reject workflow
```

### New Endpoints (Read-Only for Visibility)
```
GET    /api/decisions                    # List all decisions
GET    /api/workflows                    # List workflows (for approval inbox)
GET    /api/workflows/{id}               # Get workflow detail
GET    /api/audit                        # Get audit events (with filters)
```

### Response Shape Improvements (Allowed)

**Before (cryptic)**:
```json
{
  "decision_id": "550e8400-e29b-41d4-a716-446655440000",
  "outcome": "REQUIRE_APPROVAL",
  "rule_matched_id": "abc-def-123"
}
```

**After (descriptive)**:
```json
{
  "decision_id": "550e8400-e29b-41d4-a716-446655440000",
  "outcome": "REQUIRE_APPROVAL",
  "outcome_label": "Requires Approval",        // NEW - Human readable
  "outcome_description": "Amount exceeds threshold for auto-approval", // NEW
  "rule_matched": {                            // NEW - Denormalized
    "rule_id": "abc-def-123",
    "rule_name": "Expense > $100 requires approval",
    "version": "v1"
  }
}
```

**Principle**: Add labels/descriptions WITHOUT changing business logic.

---

## 📝 IMPLEMENTATION CHECKLIST

### Phase 1: Frontend Scaffold (1 hour)
- [ ] Create Vite + React + TypeScript project with Bun
- [ ] Install dependencies with Bun (TanStack Query, Zustand, shadcn/ui, etc)
- [ ] Setup Tailwind CSS
- [ ] Setup React Router
- [ ] Create directory structure (features/, shared/, stores/)
- [ ] Setup Axios client with base URL

**Commands**:
```bash
bun create vite@latest frontend -- --template react-ts
cd frontend
bun install
bun add @tanstack/react-query @tanstack/react-table zustand react-hook-form zod @hookform/resolvers axios date-fns clsx tailwind-merge react-router-dom
bun add -d tailwindcss postcss autoprefixer
```

### Phase 2: Backend Read Endpoints (30 minutes)
- [ ] Add GET /api/decisions endpoint (list all)
- [ ] Add GET /api/workflows endpoint (list pending)
- [ ] Add GET /api/workflows/{id} endpoint
- [ ] Add GET /api/audit endpoint
- [ ] Add descriptive fields to existing responses (labels, summaries)

### Phase 3: Shared Components (1 hour)
- [ ] Create Layout component (sidebar + header)
- [ ] Create Badge component (for statuses)
- [ ] Create Card component
- [ ] Create Button component (from shadcn/ui)
- [ ] Create Table component wrapper (TanStack Table)
- [ ] Create JsonViewer component (for context/metadata)

### Phase 4: Decision List Screen (1 hour)
- [ ] Create decisions/api/getDecisions.ts
- [ ] Create decisions/types/Decision.ts
- [ ] Create decisions/components/DecisionList.tsx
- [ ] Create decisions/hooks/useDecisions.ts
- [ ] Setup TanStack Query for data fetching
- [ ] Add basic sorting (by created_at)
- [ ] Add "Create Decision" button

### Phase 5: Create Decision Form (1.5 hours)
- [ ] Create decisions/api/createDecision.ts
- [ ] Create decisions/components/CreateDecisionForm.tsx
- [ ] Setup React Hook Form + Zod validation
- [ ] Add form fields (decision_type, amount, description)
- [ ] Handle submit + show result
- [ ] Auto-redirect to detail on success

### Phase 6: Decision Detail Screen (1.5 hours)
- [ ] Create decisions/api/getDecision.ts
- [ ] Create decisions/components/DecisionDetail.tsx
- [ ] Display decision info section
- [ ] Display evaluation result section
- [ ] Display workflow section (if exists)
- [ ] Display workflow actions (if exists)
- [ ] Add link to audit trail

### Phase 7: Approval Inbox Screen (1 hour)
- [ ] Create approvals/api/getWorkflows.ts
- [ ] Create approvals/api/approveWorkflow.ts
- [ ] Create approvals/api/rejectWorkflow.ts
- [ ] Create approvals/components/ApprovalInbox.tsx
- [ ] Add approve/reject buttons
- [ ] Show confirmation dialog before action
- [ ] Refetch list after action

### Phase 8: Audit Trail Screen (1 hour)
- [ ] Create audit/api/getAuditEvents.ts
- [ ] Create audit/components/AuditTrail.tsx
- [ ] Create audit/components/EventTimeline.tsx
- [ ] Add query param filtering (decision_id)
- [ ] Format timestamps nicely
- [ ] Format JSON metadata

### Phase 9: Basic Auth Store (30 minutes)
- [ ] Create stores/auth.ts (Zustand)
- [ ] Add mock login (hardcoded user for Phase A+)
- [ ] Add auth token to Axios headers
- [ ] Add logout function

### Phase 10: Testing & Observations (1 hour)
- [ ] Manual E2E test of complete flow
- [ ] Document UX confusion points
- [ ] Document missing visibility
- [ ] Document ambiguous concepts
- [ ] Create PHASE_A_PLUS_OBSERVATIONS.md

**Total Estimated Time**: ~10-12 hours

---

## 🚫 EXPLICITLY OUT OF SCOPE (Phase B+)

### User Management
- ❌ User CRUD
- ❌ User profile pages
- ❌ User authentication (use mock)

### Tenant Management
- ❌ Tenant CRUD
- ❌ Tenant switching
- ❌ Multi-tenant UI

### Role Management
- ❌ Role editors
- ❌ Permission builders

### Business Flow
- ❌ Rule builders
- ❌ Workflow designers
- ❌ Decision type configuration

### Advanced UX
- ❌ Notifications
- ❌ Email/SMS
- ❌ Advanced filters
- ❌ Bulk actions
- ❌ Pagination
- ❌ Export features
- ❌ Responsive mobile design

### Performance
- ❌ Virtualization
- ❌ Code splitting
- ❌ Lazy loading
- ❌ Bundle optimization

### Infrastructure
- ❌ Production build optimization
- ❌ CI/CD pipeline
- ❌ Environment configs

---

## 📊 SUCCESS CRITERIA (LOCKED)

Phase A+ is complete when a human can **visually understand**:

1. ✅ Why a decision was ALLOWED
2. ✅ Why a decision was DENIED
3. ✅ Why approval was REQUIRED
4. ✅ Who approved/rejected
5. ✅ What the final outcome was
6. ✅ Complete timeline of events

**Without**:
- ❌ Reading backend code
- ❌ Reading documentation
- ❌ Asking questions
- ❌ Database queries

---

## 📝 OBSERVATION DOCUMENT TEMPLATE

```markdown
# Phase A+ Observations

## UX Confusion Points
1. [Thing that was confusing]
   - What user expected
   - What actually happened
   - Severity: High / Medium / Low

## Missing Visibility
1. [Information not shown]
   - Where it was needed
   - Why it matters
   - Workaround used

## Ambiguous Concepts
1. [Unclear terminology]
   - Current term
   - User interpretation
   - Suggested alternative

## Human Misunderstandings
1. [Mental model mismatch]
   - User assumption
   - Actual behavior
   - How to clarify

## Recommendations for Phase B
(Observation only - not implemented)
```

---

## 🎨 UI DESIGN PRINCIPLES (Phase A+)

### Clarity > Elegance
```
✅ GOOD (Clear but ugly):
┌─────────────────────────────────────┐
│ Decision ID: 550e8400-e29b...       │
│ Outcome: REQUIRE_APPROVAL           │
│ (Requires manager approval)         │
└─────────────────────────────────────┘

❌ BAD (Beautiful but unclear):
┌─────────────────────────────────────┐
│ 🔔 Pending                          │
│ #550e8400                           │
└─────────────────────────────────────┘
```

### Show Raw Data When Needed
```
✅ GOOD:
Context: { "amount": 500, "department": "IT" }
(Expandable JSON viewer)

❌ BAD:
Context: [Object]
```

### Use Color for Status (Allowed)
```
ALLOWED          → Green badge
DENIED           → Red badge
REQUIRE_APPROVAL → Yellow badge
APPROVED         → Blue badge
REJECTED         → Gray badge
```

### Timestamps Always Visible
```
✅ GOOD:
Created: 2026-01-10 10:32:09 UTC
(2 hours ago)

❌ BAD:
Created: 2 hours ago
```

---

## 🔐 MOCK AUTH (Phase A+ Only)

```typescript
// stores/auth.ts
import { create } from 'zustand'

interface AuthState {
  user: {
    user_id: string
    username: string
    role: string
  } | null
  token: string | null
  login: (username: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,

  login: (username: string) => {
    // MOCK LOGIN - Phase A+ only
    const mockUsers = {
      'admin': {
        user_id: '550e8400-e29b-41d4-a716-446655440000',
        username: 'admin',
        role: 'ADMIN'
      },
      'manager': {
        user_id: '550e8400-e29b-41d4-a716-446655440001',
        username: 'manager',
        role: 'MANAGER'
      }
    }

    const user = mockUsers[username]
    if (user) {
      set({
        user,
        token: 'mock-jwt-token-phase-a-plus'
      })
    }
  },

  logout: () => {
    set({ user: null, token: null })
  }
}))
```

---

## 📦 DEPENDENCIES (package.json)

```json
{
  "name": "atlas-puguh-frontend",
  "version": "1.0.0-phase-a-plus",
  "scripts": {
    "dev": "bunx --bun vite",
    "build": "bunx --bun vite build",
    "preview": "bunx --bun vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.14.0",
    "@tanstack/react-table": "^8.10.0",
    "zustand": "^4.4.7",
    "react-hook-form": "^7.48.2",
    "zod": "^3.22.4",
    "@hookform/resolvers": "^3.3.2",
    "axios": "^1.6.2",
    "date-fns": "^3.0.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.8",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

**Note**:
- Package manager: **Bun** (not npm/yarn/pnpm)
- Install: `bun install`
- Run dev: `bun dev`
- Build: `bun build`

---

## 🚀 NEXT STEPS

1. **Create frontend scaffold** - Setup Vite project with all dependencies
2. **Build backend read endpoints** - Minimal visibility-only endpoints
3. **Build UI screens** - Following ATLAS_PANDAWA patterns
4. **Manual E2E testing** - Test complete decision flow
5. **Document observations** - Create PHASE_A_PLUS_OBSERVATIONS.md

**No Phase B work** - Only visibility, no improvements.

---

**Plan Version**: 1.0
**Date**: 2026-01-10
**Phase**: A+ (Visibility Expansion)
**Locked**: Yes - Do not change scope
