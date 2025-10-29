# Web-Admin Cleanup Tasks

**Based on:** TypeScript Migration Audit (October 28, 2025)
**Full Report:** `/mnt/g/khoirul/signate/docs/audit-reports/web-admin-audit.md`

---

## Quick Summary

**Migration Status:** 98.3% Complete (117/119 files)
**Quality Score:** 92/100 (A-)
**Remaining Work:** 2 JS files, 62 'any' types, no tests

---

## Immediate Tasks (30 minutes)

### 1. Delete Backup File
```bash
cd /mnt/g/khoirul/signate/web-admin
rm src/hooks/useContentGrouping.js.bak
```

### 2. Migrate Constants to TypeScript
```bash
# Migrate constants.js
mv src/utils/constants.js src/utils/constants.ts

# Remove declaration file (no longer needed)
rm src/utils/constants.d.ts

# Optional: Migrate tokens.js
mv src/styles/tokens.js src/styles/tokens.ts
```

### 3. Update ESLint Configuration
```json
// package.json
{
  "scripts": {
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  }
}
```

---

## Short-term Tasks (Week 1-2)

### 4. Create Proper Error Type

**File:** `src/types/api.ts`

Add this interface:
```typescript
/**
 * API Error Structure
 * Used for proper error handling in catch blocks
 */
export interface ApiError {
  response?: {
    status: number
    data?: {
      detail?: string
      code?: string
      field?: string
    }
  }
  message: string
}
```

### 5. Fix Error Handlers (62 occurrences)

**Pattern to Replace:**
```typescript
// ❌ Current (30 occurrences)
catch (error: any) {
  toast.error(error.response?.data?.detail || 'Error')
}

// ✅ Recommended
catch (error: unknown) {
  const apiError = error as ApiError
  toast.error(apiError.response?.data?.detail || 'Error')
}
```

**Files with most occurrences:**
- src/pages/Templates.tsx (4 occurrences)
- src/pages/Contents.tsx (4 occurrences)
- src/pages/Playlists.tsx (4 occurrences)
- src/pages/Tags.tsx (3 occurrences)
- src/components/devices/modals/DeviceDetailModal.tsx (6 occurrences)

### 6. Fix React Query Callbacks (16 occurrences)

**Pattern to Replace:**
```typescript
// ❌ Current
onError: (error: any) => {
  toast.error(error.response?.data?.detail)
}

// ✅ Recommended
onError: (error: unknown) => {
  const apiError = error as ApiError
  toast.error(apiError.response?.data?.detail)
}
```

### 7. Fix Generic Function Type (1 occurrence)

**File:** `src/utils/helpers.ts:67`

```typescript
// ❌ Current
type GenericFunction = (...args: any[]) => any

// ✅ Recommended
type GenericFunction<T = unknown, R = unknown> = (...args: T[]) => R
```

---

## Medium-term Tasks (Weeks 3-4)

### 8. Setup Testing Infrastructure

```bash
# Install testing dependencies
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @vitest/ui
```

**Create:** `vitest.config.ts`
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts'
  }
})
```

### 9. Write Initial Tests

**Priority test files:**
1. `src/utils/formatters.test.ts` - Test date/time formatters
2. `src/utils/helpers.test.ts` - Test helper functions
3. `src/components/shared/Button.test.tsx` - Test Button component
4. `src/components/shared/Modal.test.tsx` - Test Modal component
5. `src/hooks/useContentGrouping.test.ts` - Test custom hook

---

## Long-term Tasks (Months 1-2)

### 10. Add Route Lazy Loading

**File:** `src/App.tsx`

```typescript
import { lazy, Suspense } from 'react'

// ✅ Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Devices = lazy(() => import('./pages/Devices'))
const Contents = lazy(() => import('./pages/Contents'))
// ... etc

// Wrap routes in Suspense
<Suspense fallback={<LoadingSkeleton />}>
  <Routes>
    <Route path="/dashboard" element={<Dashboard />} />
    {/* ... */}
  </Routes>
</Suspense>
```

### 11. Add Celery Task Status UI

**Create:** `src/components/tasks/TaskStatusModal.tsx`

Features:
- Show task progress (pending, running, completed, failed)
- Poll task status endpoint: `GET /api/tasks/{task_id}/status/`
- Or use WebSocket for real-time updates
- Used for: speed tests, content processing, bulk operations

### 12. Improve Accessibility

Checklist:
- [ ] Add aria-label to icon-only buttons
- [ ] Add aria-describedby to form inputs
- [ ] Add aria-live regions for dynamic content
- [ ] Improve keyboard navigation (Tab, Enter, Escape)
- [ ] Add focus indicators for interactive elements
- [ ] Test with screen reader (NVDA/JAWS)
- [ ] Verify color contrast (WCAG AA)

---

## Verification Checklist

After completing cleanup tasks, verify:

### TypeScript Compilation
```bash
npm run build
# Should complete without errors
```

### ESLint Check
```bash
npm run lint
# Should have 0 warnings
```

### Type Coverage
```bash
# Install type coverage tool
npm install --save-dev type-coverage

# Check type coverage
npx type-coverage --detail
# Target: 95%+ coverage
```

### Bundle Size
```bash
npm run build
# Check dist/ folder size
# Target: < 500KB gzipped
```

---

## Maintenance Reminders

### Weekly
- [ ] Check for TypeScript updates: `npm outdated typescript`
- [ ] Review new 'any' types introduced in code reviews
- [ ] Update type definitions if backend API changes

### Monthly
- [ ] Run full audit again: Check for new unused code
- [ ] Review bundle size: Optimize if growing
- [ ] Update dependencies: `npm update`

### Quarterly
- [ ] Review and update this cleanup tasks list
- [ ] Conduct accessibility audit
- [ ] Performance profiling

---

## Quick Commands Reference

```bash
# Check TypeScript files
find src -name "*.tsx" -o -name "*.ts" | wc -l

# Check JavaScript files
find src -name "*.jsx" -o -name "*.js" | wc -l

# Find 'any' types
grep -rn ": any" src/ --include="*.ts" --include="*.tsx" | wc -l

# Find console.log
grep -rn "console\." src/ --include="*.ts" --include="*.tsx"

# Check bundle size
npm run build && du -sh dist/

# Run linter
npm run lint

# Run type check
npx tsc --noEmit
```

---

## Contact & Support

**Audit Report:** `/mnt/g/khoirul/signate/docs/audit-reports/web-admin-audit.md`
**API Documentation:** `/mnt/g/khoirul/signate/docs/API_DOCUMENTATION_INDEX.md`
**Migration Guide:** `/mnt/g/khoirul/signate/web-admin/TYPESCRIPT_MIGRATION_GUIDE.md`

For questions or issues, refer to the full audit report.
