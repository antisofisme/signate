# Frontend Pattern Consistency Analysis - Complete Index

## Generated Reports

This analysis compares code patterns between 5 standardized services and 6 business features in the cms-vite frontend application.

### Report Documents (Read in This Order)

#### 1. **Quick Summary** (Start Here) ⭐
**File**: `PATTERN_CONSISTENCY_QUICK_SUMMARY.md`  
**Length**: ~5 minutes  
**What**: High-level overview of all inconsistencies  
**Includes**:
- 7 key findings
- Impact by feature
- Quick fix checklist (3 phases)
- Files to modify
- Standard patterns reference

#### 2. **Visual Matrix** (Quick Reference)
**File**: `PATTERN_INCONSISTENCY_MATRIX.md`  
**Length**: ~3 minutes  
**What**: Side-by-side comparison of all patterns  
**Includes**:
- ASCII table comparing all features
- Scoring summary
- Severity levels
- Impact assessment

#### 3. **Detailed Analysis** (Complete Reference)
**File**: `PATTERN_CONSISTENCY_ANALYSIS.md`  
**Length**: ~15 minutes  
**What**: Comprehensive analysis with code examples  
**Includes**:
- Hook pattern consistency (Issue 1a, 1b)
- API layer consistency (Issue 2a, 2b)
- Component patterns
- Query key factory status
- Translation coverage
- Toast library inconsistency
- File structure analysis
- Comparison tables
- Priority fixes checklist
- Implementation plan

---

## Key Findings Summary

### 🔴 CRITICAL Issues (2-3 hours to fix)
1. **Error Handler Inconsistency**: 2 different error handler utilities
   - Standardized: `handleAPIError()`
   - Business Features: `getApiErrorMessage()`
   
2. **Toast Library Inconsistency**: 2 different toast imports
   - Standardized: `@/lib/notifications/toast`
   - Business Features: direct `sonner`

3. **Contents API Pattern Violation**: Function exports instead of API object
   - Current: `import { getContentList, getContent } from '../api/contentApi'`
   - Should be: `import { contentApi } from '../api/contentApi'`

### 🟠 HIGH Issues (2-3 hours to fix)
4. **Schedules Missing Query Key Factory**: No factory pattern, uses inline keys
5. **Devices Mixed Query Keys**: Hybrid of factory and inline keys

### 🟡 MEDIUM Issues (4-5 hours to fix)
6. **Devices Over-Split Architecture**: 6 API files, 5 hooks files, 7 types files
7. **Translation Coverage**: Inconsistent use of i18n across features

---

## Affected Features Status

| Feature | Issues | Priority | Effort |
|---------|--------|----------|--------|
| **Devices** | Error handler, Mixed query keys, Over-split | HIGH | 3-4 hrs |
| **Contents** | Error handler, API pattern | HIGH | 2 hrs |
| **Playlists** | Error handler | MEDIUM | 1 hr |
| **Schedules** | Error handler, No factory, Split files | HIGH | 3-4 hrs |
| **Menus** | Error handler, Split hooks | MEDIUM | 2 hrs |
| **Tags** | None | GREEN | - |
| **Organizations** | None (Reference) | GREEN | - |

---

## Implementation Phases

### Phase 1: Critical Fixes (2-3 hours)
- [ ] Replace `getApiErrorMessage()` → `handleAPIError()` (5 features)
- [ ] Replace `import { toast } from 'sonner'` → custom wrapper (5 features)
- [ ] Convert Contents API to API object pattern
- [ ] Create Schedules query key factory

**Impact**: Establishes consistency baseline

### Phase 2: Structural Consistency (4-5 hours)
- [ ] Fix Devices query key inconsistencies
- [ ] Consolidate Devices feature files (optional)
- [ ] Consolidate Schedules advanced (optional)
- [ ] Add missing translation keys

**Impact**: Improves maintainability

### Phase 3: Polish (2-3 hours)
- [ ] Consolidate Menus hooks
- [ ] Update documentation
- [ ] Add examples to contributing guide

**Impact**: Complete consistency

---

## Files to Modify by Priority

### Phase 1 Files (Error Handler & Toast)
```
devices/hooks/useDevices.ts
devices/hooks/useDeviceLogs.ts
devices/hooks/useDeviceAssignments.ts

contents/hooks/useContent.ts

playlists/hooks/usePlaylist.ts

schedules/hooks/useSchedules.ts
schedules/hooks/useAdvancedSchedules.ts

menus/hooks/useMenus.ts
menus/hooks/useMenuItems.ts
menus/hooks/useMenuImport.ts
```

### Phase 1 Files (API Pattern & Query Keys)
```
contents/api/contentApi.ts
contents/hooks/useContent.ts

schedules/hooks/useSchedules.ts
schedules/hooks/useAdvancedSchedules.ts
```

---

## Standard Patterns (Copy These)

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

toast.success('Operation successful');
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
  list: async (filters) => { 
    const { data } = await apiClient.get(...); 
    return data; 
  },
  get: async (id) => { 
    const { data } = await apiClient.get(...); 
    return data; 
  },
};
```

---

## Quick Reference

### Statistics
- **Total Features Analyzed**: 11 (5 standardized + 6 business)
- **Total Inconsistencies Found**: 7 major patterns
- **Features with Issues**: 6 out of 6 business features
- **Estimated Fix Time**: 10-14 hours total (3 phases)

### By Numbers
- Error handler inconsistency: 5 features, 46+ mutations
- Toast library inconsistency: 5 features, 5 hook files
- API pattern violation: 1 feature (Contents)
- Query key factory missing: 1 feature (Schedules)
- Query key inconsistency: 1 feature (Devices)
- File structure issues: 3 features
- Translation coverage gaps: 5 features

---

## How to Use These Reports

### For Quick Overview
→ Start with `PATTERN_CONSISTENCY_QUICK_SUMMARY.md`

### For Visual Comparison
→ Reference `PATTERN_INCONSISTENCY_MATRIX.md`

### For Implementation
→ Use `PATTERN_CONSISTENCY_ANALYSIS.md` with:
- Detailed Issue sections (1a, 1b, 2a, 2b, 3a, 6a)
- Code examples showing current vs. correct patterns
- Priority fixes checklist
- Implementation plan

### For Code Review
→ Use standard patterns section in any document

---

## Next Steps

1. **Read** `PATTERN_CONSISTENCY_QUICK_SUMMARY.md` (5 mins)
2. **Reference** `PATTERN_INCONSISTENCY_MATRIX.md` during review (ongoing)
3. **Study** relevant sections of `PATTERN_CONSISTENCY_ANALYSIS.md` before each fix
4. **Follow** the 3-phase implementation plan
5. **Update** contributing guide with standard patterns

---

## Questions & Clarification

### Why Two Different Error Handlers?
- Historical: Earlier code used `handleAPIError()` (older approach)
- Newer code: Introduced `getApiErrorMessage()` (simpler but inconsistent)
- Solution: Standardize on `handleAPIError()` which provides more structure

### Why Two Different Toast Imports?
- Historical: Custom wrapper at `@/lib/notifications/toast`
- Newer code: Direct imports from `sonner` (easier but scattered)
- Solution: Use custom wrapper for centralized configuration

### Why is Contents API Different?
- Historical: Started with function exports
- Other features: Migrated to API object pattern
- Solution: Refactor Contents to match pattern

### Why are Files Split?
- Devices: Feature became very large, split for organization
- Result: 18 files instead of 3, harder to navigate
- Solution: Optional consolidation with clear sections

---

## Document Maintenance

**Last Updated**: November 27, 2025  
**Version**: 1.0  
**Scope**: CMS Vite frontend patterns only  
**Total Analysis Time**: ~4 hours  
**Report Generation**: Automated code analysis + manual review

---

## Related Documentation

- Contributing Guidelines: `docs/CONTRIBUTING.md` (see "Code Patterns" section)
- Architecture Overview: `docs/ARCHITECTURE.md`
- Component Guidelines: `docs/COMPONENT_GUIDELINES.md`
- API Integration: `docs/API_INTEGRATION.md`

