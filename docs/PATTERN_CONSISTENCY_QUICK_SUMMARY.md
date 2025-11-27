# Pattern Consistency Analysis - Quick Summary

## Key Findings

### 1. Error Handler Inconsistency (CRITICAL)
- **Standardized services**: Use `handleAPIError()` from `/lib/errors/errorHandler.ts`
- **Business features**: Use `getApiErrorMessage()` from `/shared/utils/types.ts`
- **Affected**: Devices, Contents, Playlists, Schedules, Menus (5 features)
- **Fix**: Replace all instances of `getApiErrorMessage()` → `handleAPIError()`

### 2. Toast Library Inconsistency (CRITICAL)
- **Standardized services**: Import from `@/lib/notifications/toast`
- **Business features**: Import directly from `sonner`
- **Affected**: Devices, Contents, Playlists, Schedules, Menus (5 features)
- **Fix**: Change `import { toast } from 'sonner'` → `import { toast } from '@/lib/notifications/toast'`

### 3. Contents API Pattern (HIGH)
- **Issue**: Exports individual functions instead of API object
- **Current**: `import { getContentList, getContent, uploadContent } from '../api/contentApi'`
- **Should Be**: `import { contentApi } from '../api/contentApi'` then use `contentApi.list()`
- **Fix**: Refactor to API object pattern like other features

### 4. Schedules Query Key Factory (HIGH)
- **Issue**: No query key factory - uses inline keys like `['schedules', filters]`
- **Missing**: Complete factory like other features have
- **Fix**: Create `scheduleKeys` factory with all necessary keys

### 5. Devices Query Key Inconsistencies (MEDIUM)
- **Issue**: Some assignment hooks use inline keys instead of factory
- **Example**: `useDeviceTags` uses `[...deviceKeys.all, 'tags', deviceId]` instead of `deviceKeys.tags(deviceId)`
- **Fix**: Add missing factory keys: `tags()`, `contents()`, `playlists()`

### 6. File Structure (MEDIUM)
- **Devices**: Over-split across 6 API files, 5 hooks files, 7 types files
- **Schedules**: Split into basic and advanced (2 API files, 2 hooks files)
- **Menus**: Split menu items and import into separate files
- **Impact**: Harder to navigate, harder to maintain
- **Recommendation**: Consolidate (low priority, can do in phases)

### 7. Translation Coverage (LOW)
- **Issue**: Inconsistent use of translation keys in hooks
- **Status**: Some features have it, some use hardcoded English strings
- **Examples**:
  - Devices: 46 components use `useTranslation()`
  - Contents: Some hardcoded "Content uploaded successfully"
  - Playlists: Some hardcoded "Playlist created successfully"

---

## Impact by Feature

| Feature | High Issues | Medium Issues | Status |
|---------|------------|---------------|--------|
| Devices | Error handler, Query keys | File structure | ⚠️ Multiple issues |
| Contents | Error handler, API pattern | - | ⚠️ API pattern critical |
| Playlists | Error handler | - | ⚠️ Fixable |
| Schedules | Error handler, No factory | File structure | ⚠️ Missing factory |
| Menus | Error handler | File structure | ⚠️ Fixable |
| Tags | None | None | ✅ Consistent |

---

## Quick Fix Checklist

### Phase 1: Critical (2-3 hours)
1. [ ] Replace `getApiErrorMessage()` with `handleAPIError()` in 5 features
2. [ ] Replace `import { toast } from 'sonner'` with custom wrapper in 5 features
3. [ ] Convert Contents API from functions to API object
4. [ ] Create Schedules query key factory

### Phase 2: Improvements (4-5 hours)
5. [ ] Fix Devices query key inconsistencies
6. [ ] Consolidate Devices feature files (optional)
7. [ ] Consolidate Schedules advanced (optional)
8. [ ] Add missing translation keys

### Phase 3: Polish (2-3 hours)
9. [ ] Consolidate Menus hooks
10. [ ] Update documentation
11. [ ] Add examples to contributing guide

---

## Files to Modify

### Error Handler Changes (Replace getApiErrorMessage → handleAPIError)
- `/cms-vite/src/features/devices/hooks/useDevices.ts` (15+ instances)
- `/cms-vite/src/features/contents/hooks/useContent.ts` (8+ instances)
- `/cms-vite/src/features/playlists/hooks/usePlaylist.ts` (10+ instances)
- `/cms-vite/src/features/schedules/hooks/useSchedules.ts` (8+ instances)
- `/cms-vite/src/features/menus/hooks/useMenus.ts` (5+ instances)

### Toast Library Changes (Replace 'sonner' → '@/lib/notifications/toast')
- `/cms-vite/src/features/devices/hooks/useDevices.ts` (line 6)
- `/cms-vite/src/features/contents/hooks/useContent.ts` (line 6)
- `/cms-vite/src/features/playlists/hooks/usePlaylist.ts` (line 6)
- `/cms-vite/src/features/schedules/hooks/useSchedules.ts` (line 7)
- `/cms-vite/src/features/menus/hooks/useMenus.ts` (line 5)

### Contents API Refactor
- `/cms-vite/src/features/contents/api/contentApi.ts` (entire file)
- `/cms-vite/src/features/contents/hooks/useContent.ts` (update imports)

### Schedules Query Key Factory
- `/cms-vite/src/features/schedules/hooks/useSchedules.ts` (add factory, update all hooks)

---

## Standard Patterns to Follow

### Error Handling
```typescript
import { handleAPIError } from '@/lib/errors/errorHandler';

onError: (error) => {
  const appError = handleAPIError(error);
  toast.error(appError.message);
}
```

### Toast Notifications
```typescript
import { toast } from '@/lib/notifications/toast';

onSuccess: () => {
  toast.success('Operation successful');
}
```

### Query Key Factory
```typescript
export const featureKeys = {
  all: ['feature'] as const,
  lists: () => [...featureKeys.all, 'list'] as const,
  list: (filters?: F) => [...featureKeys.lists(), filters] as const,
  details: () => [...featureKeys.all, 'detail'] as const,
  detail: (id: number) => [...featureKeys.details(), id] as const,
};
```

### API Organization
```typescript
export const featureApi = {
  list: async (filters) => { const { data } = await apiClient.get(...); return data; },
  get: async (id) => { const { data } = await apiClient.get(...); return data; },
  create: async (data) => { const res = await apiClient.post(...); return res.data; },
};
```

---

## Full Report Location
See: `/mnt/g/khoirul/signate/docs/PATTERN_CONSISTENCY_ANALYSIS.md` for detailed analysis with code examples.

