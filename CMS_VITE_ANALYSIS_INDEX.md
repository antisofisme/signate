# CMS-Vite Project Analysis - Complete Index

**Generated:** 2025-11-07
**Purpose:** Quick reference for cms-vite architecture analysis and Device feature implementation

---

## Documents Created

### 1. **CMS_VITE_ARCHITECTURE_ANALYSIS.md** (35KB)
**Comprehensive detailed analysis of the entire cms-vite codebase**

Contains:
- Exact structure of all 8 features
- Complete API client patterns
- API endpoints definitions
- Service layer patterns (with code examples)
- React Query hooks patterns
- TypeScript types organization
- Component patterns & styling
- Notification and error handling
- State management (Zustand + React Query)
- Routing structure
- Exact patterns to follow for Device (with full code examples)
- Critical inconsistencies found
- Implementation checklist
- File references

**When to use:** Need detailed understanding of how to implement Device feature with exact code examples

---

### 2. **PATTERN_INCONSISTENCIES_FOUND.md** (11KB)
**Identifies and recommends solutions for architectural inconsistencies**

Contains:
- API Service Layer Pattern (Function exports vs Object-based)
  - Pattern A: Contents style
  - Pattern B: Playlists style (recommended for Device)
- Error Handling Inconsistency
  - Direct extraction (recommended for Device)
  - Error handler function
- Toast Notification Inconsistency
  - Sonner (recommended for Device)
  - Custom toast system
- Consistent patterns (Query Keys, Styling, Types, Icons, State)
- Summary table of recommendations
- Implementation decision framework

**When to use:** Need to understand WHICH pattern to use for Device and WHY

---

### 3. **DEVICE_IMPLEMENTATION_QUICK_START.md** (6.4KB)
**Quick reference guide for implementing Device feature**

Contains:
- Current status (what's ready, what's missing)
- Implementation order (Service → Hooks → Components → Pages)
- Key patterns to follow with code snippets
- Common gotchas to avoid
- Testing checklist
- File references for comparison
- Next steps

**When to use:** Quick reference while actually implementing, or to remind yourself of the order

---

## Architecture Overview

### Existing Features (All Complete)
1. **Auth** - Login/Register, password reset, token management
2. **Contents** - File upload, metadata, transcoding
3. **Playlists** - CRUD, content management, assignments
4. **Tags** - Tag management, bulk assignment
5. **Organizations** - Multi-org support
6. **Users** - User management
7. **Audit** - Activity logging
8. **Devices** - **PARTIAL** (types only, needs: services, hooks, components)

### Technology Stack
- Frontend: React 18 + Vite + TypeScript
- API Client: Axios
- State Management: Zustand (auth/ui) + React Query (server data)
- Form: React Hook Form
- UI Library: Custom Tailwind CSS
- Icons: lucide-react
- Toast: sonner
- Dark Mode: Supported

---

## Recommended Patterns for Device Feature

| Layer | Pattern | Source | Recommendation |
|-------|---------|--------|-----------------|
| **Service** | Object-based API | Playlists | Use this pattern |
| **Hooks** | Query factory + mutations | Contents | Use this pattern |
| **Error** | Direct extraction | Contents | Use this pattern |
| **Toast** | sonner library | Contents | Use this pattern |
| **Components** | Tailwind CSS | All | Use this pattern |
| **Icons** | lucide-react | All | Use this pattern |
| **Types** | Structured DTOs | All | Already defined |
| **State** | Zustand + RQ | All | Already integrated |

---

## Quick Facts

### API Client
- Base URL: `/api/v1` (dev) or `http://192.168.5.12:8001/api/v1` (prod)
- Auto JWT token injection from localStorage
- Auto Organization ID header injection
- Response unwrapping interceptor
- Auto 401 logout redirect

### API Endpoints (Device)
Already defined in `/lib/api/endpoints.ts`:
```typescript
DEVICES: {
  LIST: '/devices',
  GET: (id) => `/devices/${id}`,
  TV_REGISTER: '/devices/tv/register',
  MONITOR_REGISTER: '/devices/monitor/register',
  ACTIVATE: '/devices/activate',
  UPDATE: (id) => `/devices/${id}`,
  DELETE: (id) => `/devices/${id}`,
  HEARTBEAT: '/devices/heartbeat',
  CHECK_ACTIVATION: (code) => `/devices/check-activation/${code}`,
  LOGS: (id) => `/devices/${id}/logs`,
  COMMANDS: (id) => `/devices/${id}/commands`,
  SEND_COMMAND: (id) => `/devices/${id}/commands`,
}
```

### Device Types (Already Defined)
File: `/features/devices/types/device.ts`
- Device interface (complete)
- DeviceType, DeviceStatus enums
- DeviceLog, DeviceCommand interfaces
- Register/Activate request DTOs

---

## Files Currently Missing for Device

```
features/devices/
├── services/
│   └── deviceApi.ts              ❌ MISSING
├── hooks/
│   └── useDevices.ts             ❌ MISSING
└── components/
    ├── DeviceTable.tsx           ❌ MISSING
    ├── DeviceDetailModal.tsx      ❌ MISSING
    ├── DeviceEditModal.tsx        ❌ MISSING
    ├── DeviceActivationModal.tsx  ❌ MISSING
    ├── AssignPlaylistModal.tsx    ❌ MISSING
    ├── SendCommandModal.tsx       ❌ MISSING
    ├── DeviceLogsModal.tsx        ❌ MISSING
    └── DeleteConfirmModal.tsx     ❌ MISSING

pages/
└── DevicesPage.tsx               ❌ MISSING
```

Route placeholder exists in `/routes/index.tsx` but shows "Coming Soon".

---

## Reference Files for Copy-Paste Patterns

### Service Layer Pattern
**Reference:** `/features/playlists/services/playlistApi.ts`
- Object-based API structure
- Response type definitions
- unwrapResponse() helper
- All CRUD operations
- Special operations (assign, unassign, etc.)

### Hooks Layer Pattern
**Reference:** `/features/contents/hooks/useContent.ts`
- Query keys factory
- useList hook with filters
- useDetail hook
- useMutation hooks for CRUD
- Error handling with direct extraction
- Toast notifications with sonner

### Component Pattern
**Reference:** `/features/contents/components/ContentTable.tsx`
- Table structure with Tailwind
- Modal integration
- Icon usage from lucide-react
- Dark mode support
- Loading/error states

### Type Pattern
**Reference:** `/features/contents/types/content.ts`
- Type unions
- Domain entity interface
- Request/Response DTOs
- Filter interface
- List response with pagination

---

## Implementation Steps

### Step 1: Create Service Layer
File: `/features/devices/services/deviceApi.ts`
- Follow Playlists pattern (object-based)
- Include all methods from API_ENDPOINTS
- Add response types at top
- Include unwrapResponse() helper

### Step 2: Create Hooks Layer
File: `/features/devices/hooks/useDevices.ts`
- Define deviceKeys factory
- Create query hooks (list, detail, logs, commands)
- Create mutation hooks (update, delete, register, activate, sendCommand)
- Use sonner for toast
- Use direct error extraction

### Step 3: Create Components
Files in `/features/devices/components/`:
1. DeviceTable.tsx - Main list and toolbar
2. DeviceDetailModal.tsx - View details
3. DeviceEditModal.tsx - Edit properties
4. DeviceActivationModal.tsx - Register new
5. DeviceLogsModal.tsx - View activity
6. SendCommandModal.tsx - Control device
7. AssignPlaylistModal.tsx - Assign playlist
8. DeleteConfirmModal.tsx - Confirm deletion

### Step 4: Create Page & Route
- Create `/pages/DevicesPage.tsx`
- Update `/routes/index.tsx`
- Remove "Coming Soon" placeholder
- Add Devices to sidebar navigation

---

## Common Patterns

### Query Factory Pattern
```typescript
export const deviceKeys = {
  all: ['devices'] as const,
  lists: () => [...deviceKeys.all, 'list'] as const,
  list: (filters?) => [...deviceKeys.lists(), filters] as const,
  details: () => [...deviceKeys.all, 'detail'] as const,
  detail: (id) => [...deviceKeys.details(), id] as const,
}
```

### Mutation Pattern
```typescript
export const useUpdateDevice = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }) => deviceApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });
      queryClient.invalidateQueries({ queryKey: deviceKeys.detail(variables.id) });
      toast.success('Device updated successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to update device';
      toast.error(message);
    },
  });
};
```

### Modal Component Pattern
```typescript
interface DeviceDetailModalProps {
  device: Device;
  onClose: () => void;
}

export function DeviceDetailModal({ device, onClose }: DeviceDetailModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl">
        {/* Modal content */}
      </div>
    </div>
  );
}
```

---

## Testing Checklist

- [ ] Service methods return correct types
- [ ] Hooks query keys are unique and consistent
- [ ] Mutations invalidate correct cache keys
- [ ] Error messages display in toasts
- [ ] Loading states show spinners
- [ ] Dark mode works for all colors
- [ ] Icons are from lucide-react only
- [ ] No TypeScript errors
- [ ] Organization ID auto-injected
- [ ] Auth token auto-injected
- [ ] Page accessible from sidebar
- [ ] All modals open/close correctly

---

## Document Navigation

1. **Need implementation code examples?**
   → Read: `CMS_VITE_ARCHITECTURE_ANALYSIS.md` (Section 10)

2. **Need to decide which pattern to use?**
   → Read: `PATTERN_INCONSISTENCIES_FOUND.md`

3. **Need quick reference while coding?**
   → Read: `DEVICE_IMPLEMENTATION_QUICK_START.md`

4. **Need file paths for reference?**
   → Check: Architecture overview section above

---

## Key Takeaways

1. **Most important:** Use Playlists service pattern (object-based API)
2. **Consistent:** Use Contents hooks pattern (query factory + sonner)
3. **Always:** Use Tailwind CSS + lucide-react + Zustand + React Query
4. **Remember:** Don't use custom toast or error handler (use sonner + direct extraction)
5. **Already ready:** Types, endpoints, API client, routing

---

## Quick Command Reference

### View Device Types
```bash
cat /mnt/g/khoirul/signate/cms-vite/src/features/devices/types/device.ts
```

### View API Endpoints
```bash
grep -A 20 "DEVICES:" /mnt/g/khoirul/signate/cms-vite/src/lib/api/endpoints.ts
```

### Reference Service Pattern
```bash
cat /mnt/g/khoirul/signate/cms-vite/src/features/playlists/services/playlistApi.ts
```

### Reference Hooks Pattern
```bash
cat /mnt/g/khoirul/signate/cms-vite/src/features/contents/hooks/useContent.ts
```

---

## Contact & Support

For questions about:
- **Architecture:** See `CMS_VITE_ARCHITECTURE_ANALYSIS.md`
- **Patterns:** See `PATTERN_INCONSISTENCIES_FOUND.md`
- **Implementation:** See `DEVICE_IMPLEMENTATION_QUICK_START.md`
- **Code examples:** See all three documents

---

**Status:** Analysis complete, ready for implementation
**Last Updated:** 2025-11-07
**Next Step:** Create `deviceApi.ts` using Playlists pattern
