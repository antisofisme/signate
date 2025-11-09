# Device Feature Implementation - Quick Start Guide

## Overview

This document provides a quick reference for implementing the Device feature in cms-vite, based on comprehensive analysis of existing patterns.

For detailed analysis, see: `CMS_VITE_ARCHITECTURE_ANALYSIS.md`

## Current Status

✅ **Ready:**
- API endpoints defined in `lib/api/endpoints.ts`
- Device types defined in `features/devices/types/device.ts`
- API client configured
- Router structure ready

❌ **Missing:**
- `features/devices/services/deviceApi.ts`
- `features/devices/hooks/useDevices.ts`
- `features/devices/components/*` (modals, tables)
- `pages/DevicesPage.tsx`
- Route update

## Implementation Order

### 1. Service Layer (deviceApi.ts)

**Use Playlists pattern** - Object-based API with helper functions

```typescript
export const deviceApi = {
  list: async (filters?) => { ... },
  get: async (id) => { ... },
  update: async (id, data) => { ... },
  delete: async (id) => { ... },
  tvRegister: async (data) => { ... },
  monitorRegister: async (data) => { ... },
  activate: async (data) => { ... },
  // ... more methods
}
```

Key points:
- Define response types at top: `ListResponse`, `DetailResponse`
- Include `unwrapResponse<T>()` helper function
- Handle both interceptor-unwrapped AND wrapped responses
- Use `apiClient.get/post/patch/delete<Type>()`

### 2. Hooks Layer (useDevices.ts)

**Use Contents pattern** - Query factory + mutation hooks

```typescript
export const deviceKeys = {
  all: ['devices'] as const,
  lists: () => [...deviceKeys.all, 'list'] as const,
  list: (filters?) => [...deviceKeys.lists(), filters] as const,
  // ... more keys
}

export const useDeviceList = (filters?) => { ... }
export const useDevice = (id, enabled?) => { ... }
export const useUpdateDevice = () => { ... }
export const useDeleteDevice = () => { ... }
// ... more hooks
```

Key points:
- Query factory enables granular cache invalidation
- Mutations use `queryClient.invalidateQueries()`
- Error handling: `error?.response?.data?.detail || 'default message'`
- Toast: Use `toast.success/error/warning/info` from sonner

### 3. Components Layer

Main files needed:
1. `DeviceTable.tsx` - Main list view with action buttons
2. `DeviceDetailModal.tsx` - View device details
3. `DeviceEditModal.tsx` - Edit device info
4. `DeviceActivationModal.tsx` - Register new device
5. `DeviceLogsModal.tsx` - View activity logs
6. `SendCommandModal.tsx` - Send commands

Key points:
- Use Tailwind CSS only (no CSS modules)
- Icons from lucide-react
- Dark mode support: `dark:` prefix
- Modal pattern: `if (!isOpen) return null;`

### 4. Pages & Routes

Create `pages/DevicesPage.tsx`:
```typescript
import { DeviceTable } from '@/features/devices/components/DeviceTable';

export default function DevicesPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Device Management</h1>
      <DeviceTable />
    </div>
  );
}
```

Update `routes/index.tsx`:
```typescript
import DevicesPage from '@/pages/DevicesPage';

// Replace placeholder:
{
  path: 'devices',
  element: <DevicesPage />,
}
```

## Key Patterns to Follow

### API Service
```typescript
// Don't do this (Contents pattern):
export async function getDeviceList(...) { ... }

// Do this (Playlists pattern):
export const deviceApi = {
  list: async (...) => { ... }
}
```

### React Query
```typescript
// Always use query keys factory for cache invalidation
export const deviceKeys = {
  all: ['devices'] as const,
  lists: () => [...deviceKeys.all, 'list'] as const,
  list: (filters?) => [...deviceKeys.lists(), filters] as const,
  detail: (id) => [...deviceKeys.all, 'detail', id] as const,
}

// In mutations:
queryClient.invalidateQueries({ queryKey: deviceKeys.lists() })
```

### Error Handling
```typescript
// Standard pattern
const message = error?.response?.data?.detail || 'Failed to update device';
toast.error(message);

// Not recommended pattern:
const appError = handleAPIError(error);
toast.error(appError.message);
```

### Toast Notifications
```typescript
// Use sonner - already in package.json
import { toast } from 'sonner';

toast.success('Device updated');
toast.error('Failed to update');
toast.warning('Some items failed');
```

### Styling
```typescript
// Use Tailwind CSS
className="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"

// Not: CSS modules, styled-components, or inline styles
// Dark mode: Always include dark: prefix pairs
```

## Common Gotchas

1. **Response Unwrapping**
   - API interceptor intelligently unwraps some responses
   - Include helper function in service: `unwrapResponse<T>(response)`
   - Don't assume response is always unwrapped

2. **Query Keys**
   - Always use factory pattern for consistency
   - Don't hardcode queryKeys: `['devices']` directly in components
   - Invalidate at appropriate levels

3. **Mutations**
   - Include both `onSuccess` and `onError`
   - Invalidate related caches in `onSuccess`
   - Extract error message in `onError`
   - Show user feedback via toast

4. **Dark Mode**
   - Every color class needs dark: variant
   - `bg-white dark:bg-gray-800`
   - `text-gray-900 dark:text-white`

5. **Icons**
   - Use lucide-react ONLY (not react-icons)
   - Import: `import { Plus, Trash2, Edit } from 'lucide-react'`

## Testing Checklist

- [ ] Service: All API calls return correct types
- [ ] Hooks: Query keys uniquely identify cached data
- [ ] Components: Respond to loading/error states
- [ ] Mutations: Invalidate correct cache keys
- [ ] Toasts: Show success/error/warning messages
- [ ] Dark mode: All colors have dark: variants
- [ ] Icons: Only lucide-react used
- [ ] TypeScript: No `any` types in component props
- [ ] Routing: Device page loads correctly
- [ ] Organization: Auto-injected in API headers

## File References

**For comparison, see:**
- `/features/playlists/services/playlistApi.ts` - Best service pattern
- `/features/contents/hooks/useContent.ts` - Best hooks pattern
- `/features/contents/components/ContentTable.tsx` - Best component pattern
- `/features/devices/types/device.ts` - Already defined types
- `/lib/api/endpoints.ts` - Already defined routes

## Next Steps

1. Create `deviceApi.ts` (reference: playlistApi.ts)
2. Create `useDevices.ts` (reference: useContent.ts)
3. Create components (reference: contents components)
4. Create `DevicesPage.tsx`
5. Update routes
6. Test with backend API

Good luck!
