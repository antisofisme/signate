# CMS-Vite Pattern Inconsistencies & Recommendations

## Summary

The cms-vite project has a **generally consistent** architecture with **2 minor variations** that could affect Device implementation. This document identifies these inconsistencies and recommends the approach for Device.

---

## 1. API Service Layer Pattern Inconsistency

### Issue

**Two different patterns used:**

#### Pattern A: Function Exports (Contents, Auth)
**File:** `/features/contents/services/contentApi.ts`

```typescript
export const getContentList = async (filters?: ContentFilters): Promise<ContentListResponse> => {
  // implementation
}

export const getContent = async (id: number): Promise<ContentResponse> => {
  // implementation
}

export const uploadContent = async (data: ContentUploadData, onProgress?): Promise<ContentResponse> => {
  // implementation
}

export const formatFileSize = (bytes: number): string => {
  // implementation
}
```

Characteristics:
- Individual async functions exported
- Helper functions exported separately
- No encapsulation
- Easy to tree-shake but harder to organize

#### Pattern B: Object-Based API (Playlists, Tags)
**File:** `/features/playlists/services/playlistApi.ts`

```typescript
export const playlistApi = {
  list: async (filters?): Promise<...> => { ... },
  get: async (id): Promise<...> => { ... },
  create: async (data): Promise<...> => { ... },
  update: async (id, data): Promise<...> => { ... },
  delete: async (id): Promise<...> => { ... },
  // ... more methods
}
```

Characteristics:
- Single exported object with methods
- Helper functions included in object
- Better organization
- Easier to track all API operations
- Includes response unwrapping helper

### Recommendation for Device

**Use Pattern B: Object-Based API (Playlists style)**

**Reasons:**
1. More maintainable as Device feature grows
2. Easier to track all device operations in one place
3. Can include helper functions: `deviceApi.unwrapResponse()` if needed
4. Aligns with Playlists (most complex feature)
5. Better for future expansion (commands, logs, etc.)

```typescript
// features/devices/services/deviceApi.ts
export const deviceApi = {
  list: async (filters?: DeviceFilters) => { ... },
  get: async (id: number) => { ... },
  update: async (id: number, data: Partial<Device>) => { ... },
  delete: async (id: number) => { ... },
  tvRegister: async (data: TVRegisterRequest) => { ... },
  monitorRegister: async (data: MonitorRegisterRequest) => { ... },
  activate: async (data: ActivateDeviceRequest) => { ... },
  // ... more methods
}
```

---

## 2. Error Handling Inconsistency

### Issue

**Two different error handling patterns:**

#### Pattern A: Direct Error Extraction (Contents)

**File:** `/features/contents/hooks/useContent.ts`

```typescript
onError: (error: any) => {
  const message = error?.response?.data?.detail || 'Failed to upload content';
  toast.error(message);
}
```

Characteristics:
- Minimal abstraction
- Directly accesses error response
- Simple and straightforward
- Assumes backend returns `detail` field

#### Pattern B: Error Handler Function (Tags)

**File:** `/features/tags/hooks/useTags.ts`

```typescript
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/lib/notifications/toast';

onError: (error) => {
  const appError = handleAPIError(error);
  toast.error(appError.message);
}
```

Characteristics:
- Uses centralized error handler
- Returns typed AppError object
- More complex but more standardized
- Handles multiple error types

### Recommendation for Device

**Use Pattern A: Direct Error Extraction (Contents style)**

**Reasons:**
1. Simpler and more direct
2. Already used by majority of features (Contents, Playlists)
3. Less abstraction layers
4. Matches the sonner toast pattern (also simpler)
5. Sufficient for Device feature needs

```typescript
// features/devices/hooks/useDevices.ts
onError: (error: any) => {
  const message = error?.response?.data?.detail || 'Failed to update device';
  toast.error(message);
}
```

---

## 3. Toast Notification Inconsistency

### Issue

**Two different toast libraries in use:**

#### Pattern A: Sonner (Contents, Playlists, Organizations)

**File:** `/features/contents/hooks/useContent.ts`

```typescript
import { toast } from 'sonner';

// Direct usage
toast.success('Content uploaded successfully');
toast.error(message);
toast.warning(`${count} items...`);
```

Characteristics:
- Lightweight
- Already in package.json
- Direct function calls
- Handles position, duration automatically

#### Pattern B: Custom Toast System (Tags)

**File:** `/features/tags/hooks/useTags.ts`

```typescript
import { toast } from '@/lib/notifications/toast';

// Custom wrapper
toast.success(`Tag "${data.tag_name}" berhasil dibuat`);
toast.error(appError.message);
```

**File:** `/lib/notifications/toast.ts` (custom implementation)

```typescript
class ToastManager {
  show(options: ToastOptions) { ... }
  success(message: string, title?: string) { ... }
  error(message: string, title?: string) { ... }
}

export const toast = new ToastManager();
```

Characteristics:
- Custom implementation
- Supports title + message
- More control but more code
- Separate notification system

### Recommendation for Device

**Use Pattern A: Sonner (Contents style)**

**Reasons:**
1. Already in package.json dependencies
2. Used by majority of features (Contents, Playlists)
3. Simpler - no custom code needed
4. Better UX with built-in positioning
5. Less maintenance burden

```typescript
// features/devices/hooks/useDevices.ts
import { toast } from 'sonner';

toast.success('Device updated successfully');
toast.error(message);
toast.warning('Some devices failed');
toast.info('Device information');
```

---

## 4. Query Keys Pattern (NO inconsistency)

### Status: CONSISTENT

All features use the same Query Keys Factory pattern:

**File:** `/features/contents/hooks/useContent.ts`
**File:** `/features/playlists/hooks/usePlaylist.ts`
**File:** `/features/tags/hooks/useTags.ts`

```typescript
export const contentKeys = {
  all: ['content'] as const,
  lists: () => [...contentKeys.all, 'list'] as const,
  list: (filters?) => [...contentKeys.lists(), filters] as const,
  details: () => [...contentKeys.all, 'detail'] as const,
  detail: (id) => [...contentKeys.details(), id] as const,
  stats: () => [...contentKeys.all, 'stats'] as const,
}
```

**Recommendation:** Follow same pattern for Device

---

## 5. Component Styling (NO inconsistency)

### Status: CONSISTENT

All features use **Tailwind CSS only** - no variations found.

Examples:
- `/features/contents/components/ContentTable.tsx` - Tailwind only
- `/features/playlists/components/PlaylistContentModal.tsx` - Tailwind only
- `/features/tags/components/TagBadge.tsx` - Tailwind only

**Recommendation:** Use Tailwind CSS only for Device components

---

## 6. TypeScript Types Pattern (NO inconsistency)

### Status: CONSISTENT

All features follow same type organization:

```typescript
// 1. Type unions
export type DeviceType = 'tv' | 'monitor';
export type DeviceStatus = 'pending' | 'active' | 'inactive';

// 2. Domain entity
export interface Device { ... }

// 3. Request DTOs
export interface TVRegisterRequest { ... }
export interface MonitorRegisterRequest { ... }

// 4. Response wrappers
export interface DeviceResponse { ... }
export interface DeviceListResponse { ... }
```

**Recommendation:** Follow same pattern (already done in `features/devices/types/device.ts`)

---

## 7. Icon Library (NO inconsistency)

### Status: CONSISTENT

All features use **lucide-react only** - no variations found.

Examples from `/features/contents/components/ContentTable.tsx`:
```typescript
import {
  Upload,
  Trash2,
  Loader2,
  FileImage,
  FileVideo,
  Eye,
  Download,
  Edit,
  Filter,
  X,
} from 'lucide-react';
```

**Recommendation:** Use lucide-react for Device components

---

## 8. State Management (NO inconsistency)

### Status: CONSISTENT

Clear division of responsibility:

| State Type | Store | Library | Example |
|-----------|-------|---------|---------|
| Auth info | `authStore` | Zustand | User, token, org selection |
| UI prefs | `uiStore` | Zustand | Theme, sidebar, language |
| Server data | React Query hooks | TanStack Query | Device list, detail, logs |
| Form state | useState | React | Modal input, temporary UI |

**Recommendation:** Follow same division for Device

---

## Summary Table

| Aspect | Pattern Used | Features | Recommendation | Status |
|--------|--------------|----------|-----------------|--------|
| API Service | Function Exports | Contents, Auth | **Use Object-Based** | Inconsistent |
| | Object-Based | Playlists, Tags | | |
| Error Handling | Direct Extract | Contents, Playlists | **Use Direct Extract** | Inconsistent |
| | Error Handler | Tags | | |
| Toast | Sonner | Contents, Playlists | **Use Sonner** | Inconsistent |
| | Custom | Tags | | |
| Query Keys | Factory Pattern | All | Use Factory | Consistent |
| Styling | Tailwind CSS | All | Use Tailwind | Consistent |
| Types | Structured DTOs | All | Follow pattern | Consistent |
| Icons | lucide-react | All | Use lucide-react | Consistent |
| State | Zustand + RQ | All | Use both | Consistent |

---

## Implementation Decision

For Device feature, follow:

1. **Service:** Playlists pattern (object-based API)
2. **Hooks:** Contents pattern (direct error extraction + sonner)
3. **Components:** Contents pattern (Tailwind CSS, lucide-react)
4. **Types:** Existing device.ts pattern
5. **State:** Zustand (auth) + React Query (server data)

This creates **maximum consistency** with existing codebase by:
- Using the **best pattern for each concern**
- Combining strengths from multiple features
- Avoiding least-used patterns (custom toast, error handler)
- Maintaining consistency across the project

---

## Files to Reference During Implementation

| File | Purpose | Pattern |
|------|---------|---------|
| `/features/playlists/services/playlistApi.ts` | API Service structure | Object-based API ✅ |
| `/features/contents/hooks/useContent.ts` | Query keys + hooks | Query factory ✅ |
| `/features/contents/components/ContentTable.tsx` | Component structure | Modal + table ✅ |
| `/features/contents/types/content.ts` | Type organization | DTOs ✅ |
| `/lib/api/endpoints.ts` | API routes | Already defined ✅ |
| `/features/devices/types/device.ts` | Device types | Already defined ✅ |

