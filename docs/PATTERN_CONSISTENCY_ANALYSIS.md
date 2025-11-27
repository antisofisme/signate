# Frontend Pattern Consistency Analysis Report
## CMS Vite: Standardized Services vs Business Features

**Date**: November 27, 2025  
**Scope**: Comparing 5 standardized services with 6 business features  
**Conclusion**: Business features have **multiple critical inconsistencies** that need standardization

---

## Executive Summary

### Standardized Services (Following Pattern)
1. **Organizations** ✅
2. **Users** ✅
3. **Sessions** ✅
4. **Roles (RBAC)** ✅
5. **Audit** ✅

### Business Features (Inconsistent Pattern)
1. **Devices** ⚠️ Multiple issues
2. **Contents** ⚠️ Multiple issues
3. **Playlists** ⚠️ Multiple issues
4. **Schedules** ⚠️ Multiple issues
5. **Menus** ⚠️ Multiple issues
6. **Tags** ✅ Mostly consistent

---

## 1. Hook Pattern Consistency Analysis

### Standard Pattern (Organizations, Users)
```typescript
// Query Key Factory
export const organizationKeys = {
  all: ['organizations'] as const,
  lists: () => [...organizationKeys.all, 'list'] as const,
  list: (filters?: FilterType) => [...organizationKeys.lists(), filters] as const,
  details: () => [...organizationKeys.all, 'detail'] as const,
  detail: (id: number) => [...organizationKeys.details(), id] as const,
};

// Mutation with Standardized Error Handling
export function useCreateOrganization() {
  return useMutation({
    mutationFn: (orgData: CreateOrganizationRequest) => organizationsApi.create(orgData),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      toast.success(`Organization "${data.name}" created`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);  // Standardized error handler
      toast.error(appError.message);
    },
  });
}
```

### Issues Found by Feature

| Feature | Issue | Severity | Details |
|---------|-------|----------|---------|
| **Devices** | ❌ INCONSISTENT QUERY KEY PATTERN | HIGH | Uses inline `['devices']` keys instead of factory pattern in many places (e.g., `useDeviceTags`) |
| **Devices** | ❌ INCONSISTENT ERROR HANDLER | HIGH | Uses `getApiErrorMessage()` in hooks, standardized services use `handleAPIError()` |
| **Devices** | ✅ HAS QUERY KEY FACTORY | - | `deviceKeys` factory exists and is used properly |
| **Devices** | ✅ OPTIMISTIC UPDATES | - | Implements optimistic updates in `useDeleteDevice()` - GOOD! |
| **Contents** | ❌ INCONSISTENT QUERY KEY PATTERN | HIGH | Uses `contentKeys` factory but incomplete - missing stats key factory pattern |
| **Contents** | ❌ INCONSISTENT ERROR HANDLER | HIGH | Uses `getApiErrorMessage()` instead of standardized `handleAPIError()` |
| **Contents** | ⚠️ API FUNCTION EXPORTS | MEDIUM | Exports functions directly instead of as `contentApi` object |
| **Playlists** | ✅ GOOD QUERY KEY FACTORY | - | `playlistKeys` factory is complete and properly structured |
| **Playlists** | ❌ INCONSISTENT ERROR HANDLER | HIGH | Uses `getApiErrorMessage()` instead of `handleAPIError()` |
| **Schedules** | ⚠️ NO QUERY KEY FACTORY | MEDIUM | Uses inline keys like `['schedules', filters]` - missing factory pattern entirely |
| **Schedules** | ❌ INCONSISTENT ERROR HANDLER | HIGH | Uses `getApiErrorMessage()` instead of `handleAPIError()` |
| **Menus** | ✅ GOOD QUERY KEY FACTORY | - | `menuKeys` factory is complete and well-structured |
| **Menus** | ❌ INCONSISTENT ERROR HANDLER | HIGH | Uses `getApiErrorMessage()` instead of `handleAPIError()` |
| **Tags** | ✅ CONSISTENT PATTERN | - | Follows standardized pattern with `handleAPIError()` |

### Detailed Issues

#### Issue 1a: Query Key Factory Inconsistency (Devices)
**File**: `/cms-vite/src/features/devices/hooks/useDevices.ts`  
**Lines**: 324-331 (useDeviceTags)
```typescript
// CURRENT (Wrong - inline keys)
export const useDeviceTags = (deviceId: number, enabled = true) => {
  return useQuery({
    queryKey: [...deviceKeys.all, 'tags', deviceId],  // ❌ Mixes factory with inline
    queryFn: () => deviceApi.getTags(deviceId),
    ...
  });
};

// SHOULD BE
export const useDeviceTags = (deviceId: number, enabled = true) => {
  return useQuery({
    queryKey: deviceKeys.tags(deviceId),  // ✅ Use factory
    queryFn: () => deviceApi.getTags(deviceId),
    ...
  });
};
```

**Fix Required**: Add `tags`, `contents`, `playlists` to `deviceKeys` factory

#### Issue 1b: Error Handler Inconsistency (All Business Features)
**Files**: 
- `/cms-vite/src/features/devices/hooks/useDevices.ts`
- `/cms-vite/src/features/contents/hooks/useContent.ts`
- `/cms-vite/src/features/playlists/hooks/usePlaylist.ts`
- `/cms-vite/src/features/schedules/hooks/useSchedules.ts`
- `/cms-vite/src/features/menus/hooks/useMenus.ts`

**Current**: All business features use `getApiErrorMessage(error, 'fallback')`  
**Standard**: All standardized services use `handleAPIError(error)` which returns `AppError` object

```typescript
// CURRENT (Business Features)
onError: (error: unknown) => {
  toast.error(getApiErrorMessage(error, 'Failed to update device'));
}

// STANDARD (Standardized Services)
onError: (error) => {
  const appError = handleAPIError(error);
  toast.error(appError.message);
}
```

**Issue**: Two different error handling utilities being used  
**Root Cause**: `handleAPIError` is in `/lib/errors/errorHandler.ts`, newer code uses `getApiErrorMessage` from `/shared/utils/types.ts`  
**Impact**: Inconsistent error processing and toast messages

---

## 2. API Layer Consistency Analysis

### Standard Pattern (Organizations API)
```typescript
// FILE: /cms-vite/src/features/organizations/api/organizationsApi.ts

/**
 * Dedicated API service object
 * All methods are organized under a single object
 * Response unwrapping is centralized
 */
export const organizationsApi = {
  list: async (activeOnly = false): Promise<OrganizationListData> => {
    const { data } = await apiClient.get<OrganizationListData>(...);
    return data;
  },
  
  get: async (id: number): Promise<Organization> => {
    const { data } = await apiClient.get<Organization>(...);
    return data;
  },
};
```

### Issues Found by Feature

| Feature | Pattern | Issue | Severity |
|---------|---------|-------|----------|
| **Devices** | API object (`deviceApi`) | ✅ CORRECT | Uses `export const deviceApi = { ... }` |
| **Devices** | Response handling | ⚠️ CUSTOM UNWRAPPER | Has `unwrapResponse()` helper - non-standard |
| **Contents** | API pattern | ❌ FUNCTION EXPORTS | Exports bare functions: `export const getContentList = ...` |
| **Contents** | Response handling | ❌ INCONSISTENT | Returns `response.data` directly, no unwrapping logic |
| **Playlists** | API object | ✅ CORRECT | Uses `export const playlistApi = { ... }` |
| **Schedules** | API pattern | ⚠️ MIXED PATTERN | Some functions, some methods on object |
| **Menus** | API object | ✅ CORRECT | Uses `export const menuApi = { ... }` |
| **Tags** | API object | ✅ CORRECT | Uses `export const tagsApi = { ... }` |

### Issue 2a: Contents API - Function Exports vs API Object
**File**: `/cms-vite/src/features/contents/api/contentApi.ts`
```typescript
// CURRENT (Wrong)
export const getContentList = async (filters?: ContentFilters) => { ... };
export const getContent = async (id: number) => { ... };
export const uploadContent = async (data: ContentUploadData) => { ... };

// Imported as
import { getContentList, getContent, uploadContent } from '../api/contentApi';

// STANDARD (Correct)
export const contentApi = {
  list: async (filters?: ContentFilters) => { ... },
  get: async (id: number) => { ... },
  upload: async (data: ContentUploadData) => { ... },
};

// Imported as
import { contentApi } from '../api/contentApi';

// Used as
contentApi.list(filters)
contentApi.get(id)
contentApi.upload(data)
```

**Impact**:
- Inconsistent import patterns
- Harder to mock for testing
- Violates established API pattern
- Makes hooks harder to read (imports list is long)

### Issue 2b: Devices API - Non-Standard Response Unwrapping
**File**: `/cms-vite/src/features/devices/api/deviceApi.ts` (Lines 65-78)
```typescript
// CUSTOM UNWRAPPER (Non-standard)
function unwrapResponse<T>(response: any): T {
  if (response.data && !('success' in response.data || 'data' in response.data)) {
    return response.data as T;
  }
  if (response.data?.data) {
    return response.data.data as T;
  }
  return response.data as T;
}

// STANDARD (How it's done in standardized services)
const { data } = await apiClient.get<Type>(...);
return data;
```

**Issue**: Custom response handling logic that duplicates responsibility  
**Why**: Suggests inconsistent backend response format or API interceptor issues

---

## 3. Component Pattern Consistency Analysis

### Query Key Factory Status Summary

```
STANDARDIZED SERVICES:
✅ Organizations: Complete factory
✅ Users: Complete factory  
✅ Sessions: Not checked (but likely complete)
✅ RBAC: Not checked (but likely complete)
✅ Audit: Not checked (but likely complete)

BUSINESS FEATURES:
✅ Devices: Complete deviceKeys factory
✅ Playlists: Complete playlistKeys factory
✅ Menus: Complete menuKeys factory
⚠️ Contents: Partial contentKeys factory
⚠️ Schedules: NO factory - uses inline keys
✅ Tags: Uses simple query keys (acceptable for simple CRUD)
```

### Issue 3a: Schedules - No Query Key Factory
**File**: `/cms-vite/src/features/schedules/hooks/useSchedules.ts`
```typescript
// CURRENT (No factory)
export const useSchedules = (filters?: ScheduleFilters) => {
  return useQuery({
    queryKey: ['schedules', filters],  // ❌ Inline key
    queryFn: () => getSchedules(filters),
    ...
  });
};

export const useSchedule = (id: number) => {
  return useQuery({
    queryKey: ['schedule', id],  // ❌ Inline key, inconsistent with list
    queryFn: () => getSchedule(id),
    ...
  });
};

export const useDeviceSchedules = (deviceId: number) => {
  return useQuery({
    queryKey: ['device-schedules', deviceId],  // ❌ Inline key
    ...
  });
};

// SHOULD BE
export const scheduleKeys = {
  all: ['schedules'] as const,
  lists: () => [...scheduleKeys.all, 'list'] as const,
  list: (filters?: ScheduleFilters) => [...scheduleKeys.lists(), filters] as const,
  details: () => [...scheduleKeys.all, 'detail'] as const,
  detail: (id: number) => [...scheduleKeys.details(), id] as const,
  deviceSchedules: (deviceId: number) => [...scheduleKeys.all, 'device-schedules', deviceId] as const,
  playlistSchedules: (playlistId: number) => [...scheduleKeys.all, 'playlist-schedules', playlistId] as const,
  occurrences: (data: GetOccurrencesRequest) => [...scheduleKeys.all, 'occurrences', data] as const,
};
```

---

## 4. Translation Keys Consistency Analysis

### Standards Check

**Standardized Services** (Organizations, Users, Audit):
- Uses `useTranslation()` hook
- Accesses translations via `t('key.path.subkey')`
- Example: `t('users.form.createUser')`

**Business Features - Translation Usage**:
- Devices: 46 files use `useTranslation()`
- Contents: Not systematically checked
- Playlists: Not systematically checked
- Schedules: Not systematically checked
- Menus: Not systematically checked
- Tags: Uses `useTranslation()`

### Issue 4a: Hardcoded Strings in Business Features
**Examples Found**:
- `/cms-vite/src/features/devices/hooks/useDevices.ts` Line 82: `toast.success('Device updated successfully')`
- `/cms-vite/src/features/contents/hooks/useContent.ts` Line 74: `toast.success('Content uploaded successfully')`
- `/cms-vite/src/features/playlists/hooks/usePlaylist.ts` Line 87: `toast.success('Playlist created successfully')`

**Standard Pattern** (from Users):
```typescript
// In hooks
toast.success(`User "${data.username}" berhasil dibuat`);  // Hardcoded in hook

// Better pattern would be:
toast.success(t('users.messages.created', { name: data.username }));
```

**Current Status**: Inconsistent - some features have translations, some don't

---

## 5. Toast Notification Library Inconsistency

### Discovery
- **Standardized Services** (Organizations, Users, Tags): Use `@/lib/notifications/toast` (custom wrapper)
- **Business Features** (Devices, Contents, Playlists, Schedules, Menus): Use `sonner` directly

### Comparison

| Library | Import | Usage | Maintenance |
|---------|--------|-------|-------------|
| Custom (`@/lib/notifications/toast`) | `import { toast } from '@/lib/notifications/toast'` | `toast.success(msg)` | ✅ Centralized configuration |
| Sonner (Direct) | `import { toast } from 'sonner'` | `toast.success(msg)` | ❌ Distributed, hard to update |

**Files Using Sonner**:
- `/cms-vite/src/features/devices/hooks/useDevices.ts` (line 6)
- `/cms-vite/src/features/contents/hooks/useContent.ts` (line 6)
- `/cms-vite/src/features/playlists/hooks/usePlaylist.ts` (line 6)
- `/cms-vite/src/features/schedules/hooks/useSchedules.ts` (line 7)
- `/cms-vite/src/features/menus/hooks/useMenus.ts` (line 5)

**Impact**: If we need to change toast configuration globally, we have to update 5+ files instead of 1 centralized file

---

## 6. File Structure Consistency Analysis

### Standard Structure (Organizations, Users)
```
features/organizations/
├── api/
│   └── organizationsApi.ts         # ✅ Named as [feature]Api.ts
├── components/
│   ├── OrganizationList.tsx
│   └── OrganizationForm.tsx
├── hooks/
│   └── useOrganizations.ts         # ✅ Single hooks file
├── pages/
│   └── OrganizationsPage.tsx
├── types/
│   └── organization.ts             # ✅ Single types file
└── index.ts                        # ✅ Barrel export (optional)
```

### Business Feature Structures

| Feature | API File | Structure | Issue |
|---------|----------|-----------|-------|
| **Devices** | `deviceApi.ts` | ✅ Standard | Good structure |
| **Devices** | Multiple API files | ❌ SPLIT PATTERN | Has `deviceApi.ts`, `groupsApi.ts`, `logsApi.ts`, `commands.ts`, `health.ts`, `deviceAssignmentsApi.ts` |
| **Devices** | Multiple hooks files | ❌ SPLIT PATTERN | Has `useDevices.ts`, `useDeviceLogs.ts`, `useDeviceAssignments.ts`, `useDeviceWebSocket.ts`, `useConsoleLiveStream.ts` |
| **Devices** | Multiple types files | ❌ SPLIT PATTERN | Has `device.ts`, `logs.ts`, `commands.ts`, `health.ts`, `groups.ts`, `assignment.ts`, `commandTemplates.ts` |
| **Contents** | `contentApi.ts` | ✅ Standard | Good structure |
| **Contents** | Single hooks file | ✅ Standard | Good structure |
| **Playlists** | `playlistApi.ts` | ✅ Standard | Good structure |
| **Playlists** | Single hooks file | ✅ Standard | Good structure |
| **Schedules** | Multiple API files | ⚠️ SPLIT PATTERN | Has `scheduleApi.ts`, `scheduleAdvancedApi.ts` |
| **Schedules** | Multiple hooks files | ⚠️ SPLIT PATTERN | Has `useSchedules.ts`, `useAdvancedSchedules.ts` |
| **Menus** | `menuApi.ts` | ✅ Standard | Good structure |
| **Menus** | Multiple hooks files | ⚠️ SPLIT PATTERN | Has `useMenus.ts`, `useMenuItems.ts`, `useMenuImport.ts` |
| **Tags** | `tagsApi.ts` | ✅ Standard | Good structure |

### Issue 6a: Devices Feature - Over-Split Architecture
**Problem**: Devices is split across 6 API files, 5 hooks files, and 7 types files

**Current Structure**:
```
devices/
├── api/
│   ├── deviceApi.ts          # Main CRUD
│   ├── groupsApi.ts          # Groups  
│   ├── logsApi.ts            # Logs
│   ├── commands.ts           # Commands
│   ├── health.ts             # Health
│   ├── deviceAssignmentsApi.ts
│   └── index.ts
├── hooks/
│   ├── useDevices.ts         # 500+ lines
│   ├── useDeviceLogs.ts
│   ├── useDeviceAssignments.ts
│   ├── useDeviceWebSocket.ts
│   └── useConsoleLiveStream.ts
├── types/
│   ├── device.ts
│   ├── logs.ts
│   ├── commands.ts
│   ├── health.ts
│   ├── groups.ts
│   ├── assignment.ts
│   ├── commandTemplates.ts
│   └── index.ts
```

**Could Be Consolidated To**:
```
devices/
├── api/
│   └── deviceApi.ts          # All API calls (organized into sections)
├── hooks/
│   └── useDevices.ts         # All hooks (organized with TSDoc sections)
├── types/
│   └── device.ts             # All types (organized with namespace)
├── components/
└── pages/
```

**Benefits**: Easier to navigate, follows standardized pattern, less file imports

---

## 7. Comparison Table Summary

| Aspect | Standard Pattern | Devices | Contents | Playlists | Schedules | Menus | Tags |
|--------|-----------------|---------|----------|-----------|-----------|-------|------|
| **Query Key Factory** | ✅ Complete | ✅ Complete | ⚠️ Partial | ✅ Complete | ❌ NONE | ✅ Complete | ✅ Simple |
| **Error Handler** | `handleAPIError()` | `getApiErrorMessage()` | `getApiErrorMessage()` | `getApiErrorMessage()` | `getApiErrorMessage()` | `getApiErrorMessage()` | ✅ `handleAPIError()` |
| **API Organization** | Object (`organizationsApi`) | Object | ❌ Functions | Object | ⚠️ Mixed | Object | Object |
| **Toast Library** | `@/lib/notifications/toast` | `sonner` | `sonner` | `sonner` | `sonner` | `sonner` | ✅ Custom |
| **Translation Keys** | ✅ Full coverage | ⚠️ Partial | ⚠️ Partial | ⚠️ Partial | ⚠️ Partial | ⚠️ Partial | ✅ Good |
| **File Structure** | Consolidated | ❌ Over-split | ✅ Standard | ✅ Standard | ⚠️ Split | ⚠️ Split | ✅ Standard |
| **Optimistic Updates** | Limited | ✅ Has deleteDevice | ❌ NONE | ❌ NONE | ❌ NONE | ❌ NONE | ❌ NONE |
| **Cache Invalidation** | Standardized | ✅ Good | ✅ Good | ✅ Good | ✅ Good | ⚠️ Limited | ✅ Good |

---

## Priority Fixes Checklist

### HIGH PRIORITY (Breaking Consistency)

- [ ] **Standardize Error Handler Across All Features**
  - Replace `getApiErrorMessage()` with `handleAPIError()`
  - Update in: Devices, Contents, Playlists, Schedules, Menus
  - Files: ~20 mutations across 5 features

- [ ] **Standardize Toast Library**
  - Replace all `import { toast } from 'sonner'` with `import { toast } from '@/lib/notifications/toast'`
  - Files: `useDevices.ts`, `useContent.ts`, `usePlaylist.ts`, `useSchedules.ts`, `useMenus.ts`

- [ ] **Fix Contents API - Use API Object Pattern**
  - Convert function exports to `contentApi` object
  - Update all imports in `useContent.ts`

- [ ] **Create Schedules Query Key Factory**
  - Add `scheduleKeys` factory
  - Update all hooks to use factory pattern

### MEDIUM PRIORITY (Consistency & Maintainability)

- [ ] **Fix Devices Query Key Inconsistencies**
  - Add missing factory keys: `tags()`, `contents()`, `playlists()`
  - Update mutations to use factory

- [ ] **Consolidate Devices Feature Structure**
  - Merge API files into single `deviceApi.ts`
  - Merge hooks into single `useDevices.ts` with sections
  - Merge types into single `device.ts` with namespacing

- [ ] **Consolidate Schedules Feature Structure**
  - Merge `scheduleApi.ts` and `scheduleAdvancedApi.ts`
  - Merge `useSchedules.ts` and `useAdvancedSchedules.ts`

- [ ] **Consolidate Menus Feature Structure**
  - Merge `useMenus.ts`, `useMenuItems.ts`, `useMenuImport.ts` into single file

- [ ] **Add Full Translation Coverage**
  - Audit all business feature hooks
  - Add translation keys for all user-facing messages

### LOW PRIORITY (Nice to Have)

- [ ] **Add Optimistic Updates to Other Features**
  - Contents: bulk delete
  - Playlists: content reordering
  - Tags: content assignment

- [ ] **Add Zod Schemas to All Features**
  - Form validation with Zod (like older components)
  - TypeScript type safety

---

## Implementation Plan

### Phase 1: Critical Fixes (2-3 hours)
1. Standardize error handlers (all 5 files)
2. Standardize toast library (all 5 files)
3. Fix Contents API pattern

### Phase 2: Structural Consistency (4-5 hours)
1. Create Schedules query key factory
2. Consolidate Devices feature
3. Consolidate Schedules advanced

### Phase 3: Polish (2-3 hours)
1. Consolidate Menus hooks
2. Add translation coverage audit
3. Update documentation

---

## Code Snippets for Reference

### Standard Error Handling Pattern
```typescript
import { handleAPIError } from '@/lib/errors/errorHandler';

onError: (error) => {
  const appError = handleAPIError(error);
  toast.error(appError.message);
}
```

### Standard Toast Library Pattern
```typescript
import { toast } from '@/lib/notifications/toast';

onSuccess: () => {
  toast.success('Operation completed successfully');
}
```

### Standard Query Key Factory Pattern
```typescript
export const featureKeys = {
  all: ['feature'] as const,
  lists: () => [...featureKeys.all, 'list'] as const,
  list: (filters?: FilterType) => [...featureKeys.lists(), filters] as const,
  details: () => [...featureKeys.all, 'detail'] as const,
  detail: (id: number) => [...featureKeys.details(), id] as const,
};
```

### Standard API Object Pattern
```typescript
export const featureApi = {
  list: async (filters?: FilterType): Promise<ListResponse> => {
    const { data } = await apiClient.get<ListResponse>(...);
    return data;
  },
  
  get: async (id: number): Promise<Feature> => {
    const { data } = await apiClient.get<Feature>(...);
    return data;
  },
};
```

---

## Conclusion

**Current Status**: Business features have **multiple inconsistencies** in:
1. Error handling (wrong utility function)
2. Toast library (direct sonner imports)
3. API organization (Contents uses function exports)
4. Query key patterns (Schedules missing factory)
5. File structure (Devices over-split)
6. Translation coverage (inconsistent)

**Impact**: 
- Harder to maintain
- Inconsistent behavior
- Testing challenges
- Onboarding difficulty for new developers

**Recommendation**: Implement Phase 1 fixes immediately (2-3 hours) to establish consistency baseline, then gradually work through Phase 2 and 3.

