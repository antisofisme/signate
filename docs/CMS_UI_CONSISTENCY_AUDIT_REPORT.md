# CMS UI & Core Services Consistency Audit Report

**Date**: 2025-12-01
**Scope**: Full analysis of cms-vite frontend and backend-python integration
**Methodology**: Multi-agent parallel analysis using cms-ui-development and core-services-integration skills

---

## Executive Summary

| Category | Score | Status |
|----------|-------|--------|
| Feature Structure | 77% | ⚠️ Needs Improvement |
| API Patterns | 75% | ⚠️ Needs Improvement |
| State Management | 70% | ⚠️ Critical Issues |
| Form Handling | 76% | ⚠️ Needs Improvement |
| RBAC Integration | 85% | ✅ Good |
| Multi-Tenancy | 65% | 🔴 Critical Issues |
| Error/Loading States | 80% | ✅ Good |
| Shared Components | 85% | ✅ Good |

**Overall Grade: B- (75/100)**

---

## Table of Contents

1. [Feature Structure Analysis](#1-feature-structure-analysis)
2. [API Integration Patterns](#2-api-integration-patterns)
3. [State Management Patterns](#3-state-management-patterns)
4. [Form Handling & Validation](#4-form-handling--validation)
5. [RBAC/Permission Integration](#5-rbacpermission-integration)
6. [Multi-Tenancy Security](#6-multi-tenancy-security)
7. [Error Handling & Loading States](#7-error-handling--loading-states)
8. [Shared Components Usage](#8-shared-components-usage)
9. [Prioritized Remediation Plan](#9-prioritized-remediation-plan)

---

## 1. Feature Structure Analysis

### Overview
- **Total Features**: 21 directories
- **Fully Compliant**: 1 (menus - 100%)
- **Mostly Compliant**: 15 (83%)
- **Non-Compliant**: 5 (33-67%)

### Critical Finding: Missing Index Files

**20 out of 21 features are missing root-level `index.ts` barrel exports.**

Only `menus/` has proper exports:
```typescript
// menus/index.ts (REFERENCE IMPLEMENTATION)
export * from './api/menuApi';
export * from './types/menu';
export * from './hooks/useMenus';
export * from './components';
export { default as MenusPage } from './pages/MenusPage';
```

### Feature Compliance Matrix

| Feature | Root Index | Pages | Hooks | API | Types | Components | Score |
|---------|:----------:|:-----:|:-----:|:---:|:-----:|:----------:|:-----:|
| menus | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| analytics | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | 83% |
| organizations | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | 83% |
| playlists | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | 83% |
| schedules | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | 83% |
| users | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | 83% |
| tags | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | 83% |
| auth | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | 67% |
| contents | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | 67% |
| devices | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | 67% |
| rbac | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | 67% |
| uploads | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | 67% |
| **dashboard** | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | **33%** |

### Missing Folders by Feature

| Missing Component | Features Affected |
|-------------------|-------------------|
| `pages/` folder | auth, contents, dashboard, devices, rbac, uploads |
| `hooks/` folder | dashboard |
| `types/` folder | dashboard |
| Root `index.ts` | All except menus |

### Recommendations

1. **Priority 1**: Add root `index.ts` to all 20 features
2. **Priority 2**: Fix dashboard feature (most non-compliant)
3. **Priority 3**: Standardize API file naming (use `[feature]Api.ts` not `index.ts`)

---

## 2. API Integration Patterns

### Overview
- **Files Analyzed**: 28 API files
- **Major Issues**: 7 critical patterns found

### Critical Issue: Duplicate `unwrapResponse()` Function

**Found in 7 files with identical implementation:**

| File | Lines |
|------|-------|
| `features/devices/api/deviceApi.ts` | 65-78 |
| `features/devices/api/deviceAssignmentsApi.ts` | 28-40 |
| `features/devices/api/commands.ts` | 37-50 |
| `features/devices/api/logsApi.ts` | 16-29 |
| `features/menus/api/menuApi.ts` | 45-58 |
| `features/playlists/api/playlistApi.ts` | 64-77 |
| `features/devices/api/health.ts` | 40-53 |

**Impact**: Maintenance burden, potential double-unwrapping bugs

**Fix**: Extract to `@/lib/api/utils.ts`:
```typescript
export function unwrapResponse<T>(response: any): T {
  if (response.data && !('success' in response.data || 'data' in response.data)) {
    return response.data as T;
  }
  if (response.data?.data) {
    return response.data.data as T;
  }
  return response.data as T;
}
```

### Hardcoded Endpoint URLs

**22+ instances** of hardcoded URLs instead of using centralized endpoints:

| File | Count | Examples |
|------|-------|----------|
| `deviceAssignmentsApi.ts` | 9 | `/api/v1/devices/${deviceId}/playlists` |
| `menuApi.ts` | 9 | `/api/v1/menu-media` |
| `scheduleAdvancedApi.ts` | 4 | `/api/v1/schedules/check-conflict` |

**Fix**: Add missing endpoints to `lib/api/endpoints.ts`

### Error Handling Inconsistency

| Pattern | Files | Example |
|---------|-------|---------|
| Return empty defaults | 2 | `return { total: 0, items: [] }` |
| Throw error up | 5 | `throw error` |
| Return null | 3 | `return null` |
| No try-catch | 6 | authApi, contentApi, analyticsApi |

**Recommendation**: Standardize on throw pattern with centralized error handling

### Logging Inconsistency

| Method | Count |
|--------|-------|
| `logger.debug/error()` | 4 files |
| `console.error/warn()` | 10+ files |
| No logging | 5+ files |

**Fix**: Use centralized logger in ALL API files

---

## 3. State Management Patterns

### Zustand Store Issues

#### Critical: Auth Store Not Using Selectors

**File**: `lib/stores/authStore.ts`

```typescript
// WRONG - Current pattern (causes unnecessary re-renders)
const { organizations, selectedOrgId } = useAuthStore();

// CORRECT - Use selectors
const organizations = useAuthStore(state => state.organizations);
const selectedOrgId = useAuthStore(state => state.selectedOrgId);
```

**Impact**: ~96 usages across codebase causing performance issues

### TanStack Query Issues

#### Critical: Missing Organization Context in Query Keys

**Affected Features:**
- `menus/hooks/useMenus.ts` - ALL hooks missing orgId
- `analytics/hooks/index.ts` - 5 hooks missing orgId
- `audit/hooks/useAuditLogs.ts` - 2 hooks missing orgId

```typescript
// WRONG - No organization context (Line 16-24 in useMenus.ts)
export const menuKeys = {
  all: ['menus'] as const,
  list: (params?: MenuListParams) => [...menuKeys.lists(), params] as const,
};

// CORRECT - Include organization ID
export const menuKeys = {
  all: ['menus'] as const,
  list: (orgId: number, params?: MenuListParams) =>
    [...menuKeys.lists(), orgId, params] as const,
};
```

**Security Impact**: Data from previous organization remains cached when switching orgs

#### Missing `enabled` Conditions

Hooks without proper auth guards:
- `useAnalyticsDashboard` - No enabled check
- `useAnalyticsStats` - No enabled check
- `useAuditLogs` - No enabled check

```typescript
// WRONG
return useQuery({
  queryKey: [...],
  queryFn: () => api.get(),
});

// CORRECT
return useQuery({
  queryKey: [...],
  queryFn: () => api.get(),
  enabled: hasHydrated && !!orgId,
});
```

#### Inconsistent staleTime Values

| Value | Usage Count | Example Features |
|-------|-------------|------------------|
| 0 | 2 | contents, menus |
| 30000 (30s) | 6 | devices |
| 60000 (1m) | 2 | content |
| 120000 (2m) | 4 | schedules, tags |
| 300000 (5m) | Many | roles, widgets, users |

**Recommendation**: Document staleTime patterns based on data volatility

---

## 4. Form Handling & Validation

### Overview
- **Total Form Components**: 51
- **Using React Hook Form**: 39 (76.5%)
- **Using Zod Validation**: 39 (76.5%)
- **Non-Compliant**: 12 (23.5%)

### Forms NOT Using React Hook Form

| Component | Feature | Status |
|-----------|---------|--------|
| UploadModal.tsx | contents | ❌ Uses useState |
| BulkEditModal.tsx | contents | ❌ Uses useState |
| EditContentModal.tsx | contents | ❌ Uses useState |
| BulkTagModal.tsx | contents | ❌ Uses useState |
| SendCommandModal.tsx | devices | ❌ Uses useState |
| ActivationCodeModal.tsx | devices | ❌ Uses useState |
| ContentAssignmentModal.tsx | devices | ❌ Uses useState |
| DeviceDetailModal.tsx | devices | ❌ Uses useState |
| DeviceEditModal.tsx | devices | ❌ Uses useState |
| PlaylistAssignmentModal.tsx | devices | ❌ Uses useState |
| TagAssignmentModal.tsx | devices | ❌ Uses useState |
| PMSConnectionForm.tsx | pms | ❌ Uses onChange |

### Zod Schema Location Issue

**ALL 39 compliant forms define schemas inline** instead of in `types/` folder:

```typescript
// CURRENT (LoginForm.tsx)
const loginSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
});

// SHOULD BE (types/auth.ts)
export const loginSchema = z.object({...});
export type LoginFormData = z.infer<typeof loginSchema>;
```

**Impact**:
- Cannot reuse schemas across components
- Cannot unit test schemas independently
- Duplicated validation logic

### Error Display Patterns

| Pattern | Components | Status |
|---------|------------|--------|
| Shared FormInput (automatic) | 23 | ✅ Consistent |
| Manual `{errors.field && <p>...}` | 14 | ⚠️ Inconsistent |
| No error display | 12 | ❌ Missing |

---

## 5. RBAC/Permission Integration

### Overview
- **Total Pages**: 18
- **Fully Compliant**: 15 (85%)
- **Missing Permission Checks**: 3

### Pages WITHOUT Permission Checks

| Page | File | Risk Level |
|------|------|------------|
| WidgetsPage | `widgets/pages/WidgetsPage.tsx` | 🔴 HIGH |
| TemplatesPage | `templates/pages/TemplatesPage.tsx` | 🔴 HIGH |
| TranslationsPage | `translations/pages/TranslationsPage.tsx` | 🔴 HIGH |

**Issues Found:**
- No `useCanPerformAction` hook
- No `AccessDenied` component
- All action buttons shown unconditionally

### Compliant Pages (Reference)

```typescript
// CORRECT PATTERN (from DevicesPage)
function DevicesPage() {
  const { hasPermission: canRead, isLoading } = useCanPerformAction('devices', 'read');

  if (isLoading) return <PageSkeleton />;
  if (!canRead) return <AccessDenied />;

  return (
    <>
      {hasPermission('devices.create') && <CreateButton />}
      {hasPermission('devices.delete') && <DeleteButton />}
    </>
  );
}
```

### Permission Format Validation

✅ **All compliant pages use correct format**: `'read'`, `'create'`, `'edit'`, `'delete'`, `'manage'`

❌ **No incorrect formats found** (e.g., no `'view'` or `'write'`)

---

## 6. Multi-Tenancy Security

### Risk Level: 🔴 CRITICAL

### Critical Security Issues

#### Issue #1: Incorrect Role Check Pattern (CVSS 9.2)

**File**: `backend-python/shared/middleware.py`

```python
# WRONG (Lines 310, 321, 348)
def can_manage_user(current_user: dict, target_user_org_id: Optional[int]) -> bool:
    if current_user["role"] == "admin":  # Missing "super_admin"!
        return True

# CORRECT
def can_manage_user(current_user: dict, target_user_org_id: Optional[int]) -> bool:
    if current_user["role"] in ["super_admin", "admin"]:
        return True
```

**Impact**: Super admins blocked from cross-organization management

#### Issue #2: Missing Organization Filtering (CVSS 9.1)

**Affected Routes:**
- `rbac/routes.py` - list_roles accepts optional org_id
- `template/routes.py` - create_template no org validation
- `menu/routes.py` - Repository doesn't receive org context
- `widget/use_cases` - Hardcoded `organization_id=None`
- `analytics/routes.py` - Inconsistent org filtering

```python
# WRONG (widget/use_cases/assign_widget_to_playlist.py:74)
widget = repo.get_widget_by_id(pw.widget_id, organization_id=None)  # HARDCODED NULL!

# CORRECT
widget = repo.get_widget_by_id(pw.widget_id, organization_id=current_user["organization_id"])
```

#### Issue #3: Role Case Inconsistency (CVSS 6.5)

```python
# Line 140 - lowercase
if user_role != "super_admin":

# Line 559 - UPPERCASE
if current_user["role"] not in ["admin", "super_admin"]:  # Won't match "SUPER_ADMIN"
```

**Fix**: Always normalize to lowercase before comparison

#### Issue #4: Client-Side Organization Filtering (CVSS 7.2)

**File**: `organization/routes.py:133-142`

```python
# WRONG - Backend returns ALL, frontend filters
result = use_case.execute(active_only=active_only)  # Returns all orgs
if user_role != "super_admin":
    result["organizations"] = [org for org in result["organizations"]
                               if org.id == current_user["organization_id"]]

# CORRECT - Filter on backend
if user_role == "super_admin":
    result = use_case.execute()
else:
    result = use_case.execute_for_org(organization_id=current_user["organization_id"])
```

### Security Issues Summary

| Issue | Severity | CVSS | Files Affected |
|-------|----------|------|----------------|
| Incorrect role check | CRITICAL | 9.2 | middleware.py |
| Missing org filtering | CRITICAL | 9.1 | 5+ routes |
| Role case inconsistency | MEDIUM | 6.5 | Multiple |
| Client-side filtering | MEDIUM | 7.2 | organization/routes.py |
| Audit log access | MEDIUM | 6.7 | audit/routes.py |
| Widget org bypass | MEDIUM | 6.5 | widget/use_cases |

---

## 7. Error Handling & Loading States

### Overview
- **Overall Grade**: B+ (Good but with Notable Gaps)

### Critical Issues (2 Pages)

| Page | Issues |
|------|--------|
| PMSConfigPage.tsx | No skeleton, NO error handling |
| WeatherConfigPage.tsx | No skeleton, NO error handling for 4 hooks |

### Statistics

| Metric | Current | Status |
|--------|---------|--------|
| Pages with Loading States | 16/16 (100%) | ✅ |
| Pages with Error Handling | 3/16 (19%) | ❌ Critical Gap |
| Pages with Empty States | 10/16 (63%) | ⚠️ |
| Error Boundaries | 0/16 (0%) | ❌ Missing |
| Toast Notifications | 14/16 (88%) | ✅ |

### Missing Error Boundaries

No pages implement React Error Boundaries. Add global error boundary:

```typescript
// RECOMMENDED: Add to App.tsx
<ErrorBoundary fallback={<ErrorPage />}>
  <Routes>...</Routes>
</ErrorBoundary>
```

### Loading State Patterns

| Pattern | Usage | Status |
|---------|-------|--------|
| PageSkeleton | 12 pages | ✅ Consistent |
| TableSkeleton | 8 components | ✅ Consistent |
| Custom `animate-pulse` | 4 components | ⚠️ Should use shared |
| Plain text "Loading..." | 2 pages | ❌ Non-compliant |

---

## 8. Shared Components Usage

### Overview
- **Coverage**: 87/89 feature files use shared components (98%)
- **Modal Centralization**: ✅ Excellent (30+ modals use shared Modal)
- **Form Components**: ✅ Excellent (all use shared FormInput/Select/etc.)
- **Button Styling**: ✅ Excellent (8 variants consistently used)

### i18n Issues (Hardcoded Strings)

| Component | Location | Hardcoded Text |
|-----------|----------|----------------|
| ContentPerformanceChart.tsx | analytics | "Top Content Performance" |
| PlaybackTimelineChart.tsx | analytics | "Playback Timeline" |
| DeviceTable.tsx | devices | "Loading..." |
| DeleteConfirmModal.tsx | shared | "Cancel", "Delete", "Deleting..." |

### Duplicate Patterns

#### Card Container (15+ files)
```typescript
// Duplicated across analytics feature
className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm"

// SHOULD BE: <CardContainer>{children}</CardContainer>
```

#### Confirmation Dialogs (2 patterns)
- `DeleteConfirmModal` - 5 files
- `ConfirmDialog` - 18 files

**Recommendation**: Standardize on `ConfirmDialog` (more widely used)

### Missing Shared Components

| Needed Component | Files Affected | Current Pattern |
|------------------|----------------|-----------------|
| CardContainer | 15+ | Inline className |
| DataTable | 11 tables | Custom implementations |
| ChartSkeleton | 4 | Custom animate-pulse |

---

## 9. Prioritized Remediation Plan

### Priority 1: Critical Security (Fix Immediately)

| Task | Files | Effort |
|------|-------|--------|
| Fix role check in middleware.py | 1 file | 30 min |
| Add org_id to widget use_case | 1 file | 30 min |
| Fix org filtering in routes | 5 files | 2 hrs |
| Normalize role case comparison | Multiple | 1 hr |

### Priority 2: High Impact (This Sprint)

| Task | Files | Effort |
|------|-------|--------|
| Add permission checks to 3 pages | 3 files | 2 hrs |
| Add orgId to query keys (menus, analytics, audit) | 3 files | 2 hrs |
| Extract unwrapResponse to shared util | 8 files | 1 hr |
| Add error handling to PMS/Weather pages | 2 files | 1 hr |

### Priority 3: Medium Impact (Next Sprint)

| Task | Files | Effort |
|------|-------|--------|
| Add root index.ts to all features | 20 files | 3 hrs |
| Convert 12 forms to React Hook Form | 12 files | 4 hrs |
| Move Zod schemas to types/ folders | 39 files | 3 hrs |
| Add enabled conditions to queries | 5+ hooks | 2 hrs |
| Standardize staleTime values | All hooks | 1 hr |

### Priority 4: Low Impact (Backlog)

| Task | Files | Effort |
|------|-------|--------|
| Add missing endpoints to centralized file | 1 file | 1 hr |
| Add i18n to hardcoded strings | 5 files | 1 hr |
| Create CardContainer shared component | 1 new + 15 updates | 2 hrs |
| Standardize confirmation dialog usage | 23 files | 2 hrs |
| Implement Zustand selectors | 96 usages | 4 hrs |

---

## Appendix A: File Reference

### Critical Files to Review

```
Backend Security:
- backend-python/shared/middleware.py (Lines 310, 321, 348, 576)
- backend-python/services/widget/use_cases/assign_widget_to_playlist.py (Line 74)
- backend-python/services/organization/routes.py (Lines 133-142)

Frontend Permission Gaps:
- cms-vite/src/features/widgets/pages/WidgetsPage.tsx
- cms-vite/src/features/templates/pages/TemplatesPage.tsx
- cms-vite/src/features/translations/pages/TranslationsPage.tsx

State Management:
- cms-vite/src/features/menus/hooks/useMenus.ts (Lines 16-35)
- cms-vite/src/features/analytics/hooks/index.ts (Lines 18-108)
- cms-vite/src/features/audit/hooks/useAuditLogs.ts (Lines 12-34)

API Patterns:
- cms-vite/src/lib/api/client.ts (Response interceptor)
- cms-vite/src/features/devices/api/deviceApi.ts (Duplicate unwrapResponse)

Reference Implementation:
- cms-vite/src/features/menus/ (Best feature structure)
- cms-vite/src/features/devices/hooks/useDevices.ts (Correct query key pattern)
```

---

## Appendix B: Quick Fix Checklist

### Immediate (< 1 hour)

- [ ] Fix `can_manage_user` in middleware.py to include "super_admin"
- [ ] Fix `can_manage_organization` in middleware.py
- [ ] Fix `can_view_audit_logs` in middleware.py
- [ ] Fix widget use_case to require organization_id

### Today

- [ ] Add `useCanPerformAction` to WidgetsPage
- [ ] Add `useCanPerformAction` to TemplatesPage
- [ ] Add `useCanPerformAction` to TranslationsPage
- [ ] Add error handling to PMSConfigPage
- [ ] Add error handling to WeatherConfigPage

### This Week

- [ ] Add orgId to menuKeys in useMenus.ts
- [ ] Add orgId to analytics query keys
- [ ] Add orgId to audit query keys
- [ ] Extract unwrapResponse to shared utility
- [ ] Add hardcoded endpoints to endpoints.ts

---

**Report Generated**: 2025-12-01
**Analysis Method**: Multi-agent parallel analysis
**Skills Used**: cms-ui-development, core-services-integration
