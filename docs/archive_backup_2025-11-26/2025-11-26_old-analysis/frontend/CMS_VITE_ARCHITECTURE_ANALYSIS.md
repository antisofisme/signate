# CMS-Vite Project Architecture Analysis
## Detailed Pattern Report for Device Feature Implementation

**Generated:** 2025-11-07
**Purpose:** Ensure Device feature implementation matches existing patterns exactly

---

## 1. EXISTING FEATURES PATTERN & STRUCTURE

### 1.1 Feature Directory Organization

All features follow a CONSISTENT folder structure:

```
cms-vite/src/features/[feature-name]/
├── components/          # UI components
├── hooks/              # Custom React Query hooks
├── services/           # API service layer (axios calls)
├── types/              # TypeScript interfaces
└── api/               # (Optional) Additional API organization (only playlists uses this)
```

### 1.2 Implemented Features

| Feature | Location | Status | Structure Completeness |
|---------|----------|--------|------------------------|
| auth | `/features/auth` | Complete | components, hooks, services, types |
| contents | `/features/contents` | Complete | components, hooks, services, types |
| playlists | `/features/playlists` | Complete | components, hooks, services, types, api/ |
| tags | `/features/tags` | Complete | components, hooks, services, types |
| organizations | `/features/organizations` | Complete | components, hooks, services, types |
| users | `/features/users` | Complete | components, hooks, services, types |
| audit | `/features/audit` | Complete | components, hooks, services, types |
| **devices** | `/features/devices` | **PARTIAL** | **ONLY types/ exists** |

### 1.3 Current Devices Status

**EXISTING FILE:**
- `/mnt/g/khoirul/signate/cms-vite/src/features/devices/types/device.ts` ✅ Complete

**MISSING FILES (need creation):**
- `/features/devices/services/deviceApi.ts`
- `/features/devices/hooks/useDevices.ts`
- `/features/devices/components/` (multiple modal/table components)

---

## 2. API CLIENT PATTERN

### 2.1 API Client Configuration

**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/lib/api/client.ts`

```typescript
// Key Features:
✅ Axios instance with baseURL: `/api/v1` (dev) or `http://192.168.5.12:8001/api/v1` (prod)
✅ Auto JWT token injection from localStorage ('auth-token')
✅ Auto Organization ID header injection ('X-Organization-Id')
✅ Auto 401 logout redirect
✅ Response unwrapping interceptor
✅ Timeout: 30000ms
✅ Content-Type: application/json
```

**Response Unwrapping Logic:**
```typescript
// Intelligently unwraps backend response format { success, data, ... }
// Checks for important fields (pagination, total, organizations)
// For responses with pagination: keeps whole structure
// For simple responses: unwraps to response.data.data
```

### 2.2 API Endpoints Definition

**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/lib/api/endpoints.ts`

**Pattern:** Single source of truth for all API routes
- Uses object with sections (AUTH, ORGANIZATIONS, DEVICES, CONTENT, TAGS, PLAYLISTS, USERS, AUDIT, ANALYTICS, PREVIEW)
- Parameterized routes: `GET: (id: number) => /path/${id}`
- ALL devices endpoints already defined:

```typescript
DEVICES: {
  LIST: '/devices',
  GET: (id: number) => `/devices/${id}`,
  TV_REGISTER: '/devices/tv/register',
  MONITOR_REGISTER: '/devices/monitor/register',
  ACTIVATE: '/devices/activate',
  UPDATE: (id: number) => `/devices/${id}`,
  DELETE: (id: number) => `/devices/${id}`,
  HEARTBEAT: '/devices/heartbeat',
  CHECK_ACTIVATION: (code: string) => `/devices/check-activation/${code}`,
  LOGS: (id: number) => `/devices/${id}/logs`,
  COMMANDS: (id: number) => `/devices/${id}/commands`,
  SEND_COMMAND: (id: number) => `/devices/${id}/commands`,
}
```

---

## 3. SERVICE LAYER PATTERN

### 3.1 API Service File Structure

**PATTERN:** Used by Contents, Playlists, Tags, Users, Organizations, Audit

**Example from Contents:**
**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/features/contents/services/contentApi.ts`

```typescript
// Pattern:
1. Import apiClient + API_ENDPOINTS
2. Import types from '../types/content'
3. Export async functions (NOT class/object):
   - getContentList(filters?: ContentFilters): Promise<ContentListResponse>
   - getContent(id: number): Promise<ContentResponse>
   - uploadContent(data, onProgress?): Promise<ContentResponse>
   - updateContent(id, data): Promise<ContentResponse>
   - deleteContent(id): Promise<void>
   - bulkDeleteContent(ids[]): Promise<void>
   - getContentStats(): Promise<...>

4. Helper functions exported:
   - formatFileSize(bytes): string
   - getFileTypeFromMime(mimeType): 'image'|'video'|'audio'|'unknown'

5. Return types:
   - Typed response: apiClient.get<ContentResponse>(...)
   - .data accessor returns unwrapped response
```

**BEST PRACTICE FROM PLAYLISTS:**
**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/features/playlists/services/playlistApi.ts`

```typescript
// Alternative pattern: Object-based API
export const playlistApi = {
  list: async (filters?): Promise<...> => { ... },
  get: async (id): Promise<...> => { ... },
  create: async (data): Promise<...> => { ... },
  // etc
}

// Advantages:
✅ Cleaner organization
✅ Helper functions included in object
✅ Response unwrapping helper: unwrapResponse<T>(response)
✅ Type definitions at top of file
```

**Key Pattern for Response Unwrapping:**
```typescript
// Playlists includes helper to handle both interceptor-unwrapped AND wrapped responses
function unwrapResponse<T>(response: any): T {
  // If already unwrapped by interceptor
  if (response.data && !('success' in response.data || 'data' in response.data)) {
    return response.data as T;
  }
  // If still wrapped
  if (response.data?.data) {
    return response.data.data as T;
  }
  // Fallback
  return response.data as T;
}
```

---

## 4. REACT QUERY HOOKS PATTERN

### 4.1 Query Keys Factory Pattern

**PATTERN USED BY:** Contents, Playlists, Tags

**Example from Contents:**
**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/features/contents/hooks/useContent.ts`

```typescript
// Query Keys Factory - enables cache invalidation
export const contentKeys = {
  all: ['content'] as const,           // Root
  lists: () => [...contentKeys.all, 'list'] as const,  // All list queries
  list: (filters?) => [...contentKeys.lists(), filters],  // Specific list
  details: () => [...contentKeys.all, 'detail'] as const,  // All detail queries
  detail: (id: number) => [...contentKeys.details(), id],  // Specific detail
  stats: () => [...contentKeys.all, 'stats'] as const,  // Stats
};
```

**Benefits:**
- Granular cache invalidation
- Related queries can be invalidated together
- queryKey: contentKeys.list(filters) enables filter-specific caching
- Can invalidate contentKeys.lists() to refresh ALL list variations

### 4.2 Query Hook Pattern

```typescript
// Pattern 1: List with Filters
export const useContentList = (filters?: ContentFilters) => {
  return useQuery({
    queryKey: contentKeys.list(filters),
    queryFn: () => getContentList(filters),
    staleTime: 30000, // 30 seconds
  });
};

// Pattern 2: Detail Query
export const useContent = (id: number, enabled = true) => {
  return useQuery({
    queryKey: contentKeys.detail(id),
    queryFn: () => getContent(id),
    enabled: enabled && id > 0,  // Don't query if id is 0
  });
};

// Pattern 3: Related Data
export const useContentStats = () => {
  return useQuery({
    queryKey: contentKeys.stats(),
    queryFn: () => getContentStats(),
    staleTime: 60000, // 1 minute
  });
};
```

### 4.3 Mutation Hook Pattern

**Standard Pattern:**
```typescript
export const useUploadContent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ data, onProgress }: { data: ContentUploadData; onProgress?: (progress: number) => void }) =>
      uploadContent(data, onProgress),
    onSuccess: () => {
      // Invalidate related caches
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contentKeys.stats() });
      
      // Show toast
      toast.success('Content uploaded successfully');
    },
    onError: (error: any) => {
      // Extract error message
      const message = error?.response?.data?.detail || 'Failed to upload content';
      toast.error(message);
    },
  });
};
```

**Cache Invalidation Patterns:**
```typescript
// Invalidate all variations of a query
queryClient.invalidateQueries({ queryKey: contentKeys.lists() });

// Invalidate specific item
queryClient.invalidateQueries({ queryKey: contentKeys.detail(id) });

// Remove query from cache completely
queryClient.removeQueries({ queryKey: contentKeys.detail(id) });
```

**Mutation onSuccess Return:**
```typescript
// Can access:
// - response: return value from mutationFn
// - variables: the data passed to mutation

onSuccess: (response, variables) => {
  queryClient.invalidateQueries({ queryKey: contentKeys.detail(variables.id) });
  toast.success(`${response.title} updated`);
}
```

---

## 5. TYPESCRIPT TYPES PATTERN

### 5.1 Types File Organization

**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/features/contents/types/content.ts`

**Pattern Structure:**
```typescript
// 1. Type unions first
export type ContentType = 'image' | 'video' | 'audio';
export type TranscodingStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type UploadStatus = 'pending' | 'completed' | 'failed';

// 2. Domain entity
export interface Content {
  id: number;
  title: string;
  description?: string;
  content_type: ContentType;
  // ... all properties
  created_at: string;
  updated_at?: string;
}

// 3. Request/Response DTOs
export interface ContentUploadData {
  file: File;
  title: string;
  description?: string;
  duration: number;
  is_active: boolean;
}

export interface ContentFilters {
  skip?: number;
  limit?: number;
  content_type?: ContentType;
  is_active?: boolean;
}

// 4. API Response wrappers
export interface ContentListResponse {
  success: boolean;
  data: Content[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  timestamp: string;
}

export interface ContentResponse {
  success: boolean;
  data: Content;
  message?: string;
  timestamp: string;
}
```

**Naming Conventions:**
- Request DTO: `[Feature]Request` (e.g., `CreatePlaylistRequest`)
- Response DTO: `[Feature]Response` (e.g., `ContentResponse`)
- List Response: `[Feature]ListResponse`
- Filter: `[Feature]Filters`
- Filters params: `[Feature]ListFilters`

**Device Types Already Defined:**
**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/features/devices/types/device.ts`

```typescript
export type DeviceType = 'tv' | 'monitor';
export type DeviceStatus = 'pending' | 'active' | 'inactive';

export interface Device { ... }
export interface DeviceTag { ... }
export interface DevicePlaylist { ... }
export interface DeviceLog { ... }
export interface DeviceCommand { ... }
export interface MonitorRegisterRequest { ... }
export interface TVRegisterRequest { ... }
export interface ActivateDeviceRequest { ... }
```

---

## 6. COMPONENT PATTERN

### 6.1 Component Structure

**PATTERN:** Feature-based modular components

**Contents Feature Components:**
- `ContentTable.tsx` - Main table with CRUD actions
- `UploadModal.tsx` - Single content upload
- `EditContentModal.tsx` - Edit metadata
- `BulkEditModal.tsx` - Bulk edit multiple items
- `BulkTagModal.tsx` - Bulk tag assignment

### 6.2 Modal Component Pattern

**General Pattern (from ContentTable):**
```typescript
interface DeleteConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  itemName: string;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function DeleteConfirmModal({ ... }: DeleteConfirmModalProps) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        {/* modal content with Tailwind classes */}
      </div>
    </div>
  );
}
```

**Styling Pattern:**
- Tailwind CSS classes (NO CSS modules, NO styled-components)
- Dark mode support: `dark:` prefix for dark theme
- Responsive: `sm:`, `md:`, `lg:` prefixes
- Color scheme: `bg-gray-800`, `text-white`, etc.

### 6.3 Icon Usage

**Library:** lucide-react (NOT React Icons!)

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

---

## 7. NOTIFICATION & ERROR HANDLING

### 7.1 Toast Notifications

**Library:** sonner

**Pattern 1: Simple toast from sonner**
```typescript
import { toast } from 'sonner';

// In components
toast.success('Content uploaded successfully');
toast.error(message);
toast.warning(`${count} items...`);
toast.info('Some info');
```

**Pattern 2: Custom toast system (alternative)**
**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/lib/notifications/toast.ts`

```typescript
import { toast } from '@/lib/notifications/toast';
// or
import { handleAPIError } from '@/lib/errors/errorHandler';
```

### 7.2 Error Handling

**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/lib/errors/errorHandler.ts`

```typescript
// Used by features like tags:
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/lib/notifications/toast';

// In mutation onError:
onError: (error) => {
  const appError = handleAPIError(error);
  toast.error(appError.message);
}
```

**Standard Pattern:**
```typescript
// Direct error extraction (Contents pattern):
const message = error?.response?.data?.detail || 'Failed to upload content';
toast.error(message);

// OR with error handler (Tags pattern):
const appError = handleAPIError(error);
toast.error(appError.message);
```

---

## 8. STATE MANAGEMENT

### 8.1 Zustand Stores

**Library:** Zustand (NOT Redux!)

**Auth Store:**
**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/lib/stores/authStore.ts`

```typescript
interface AuthStore extends AuthState {
  // Actions
  setAuth: (user: User, token: string, organizations: Organization[]) => void;
  selectOrganization: (orgId: number) => void;
  updateUser: (user: Partial<User>) => void;
  logout: () => void;
  isOrgSelected: () => boolean;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      organizations: [],
      selectedOrgId: null,
      isAuthenticated: false,
      
      // Actions
      setAuth: (user, token, organizations) => { ... },
      selectOrganization: (orgId) => { ... },
      // etc
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({ ... }) // What to persist
    }
  )
);
```

**Usage:**
```typescript
const { user, token, selectedOrgId, setAuth, logout } = useAuthStore();
```

### 8.2 UI Store

**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/lib/stores/uiStore.ts`

```typescript
// Manages:
- sidebarOpen: boolean
- theme: 'light' | 'dark'
- language: 'id' | 'en'
- currentModal: string | null
- modalData: any

// Actions:
- toggleSidebar()
- setTheme(theme)
- toggleTheme()
- setLanguage(language)
- openModal(modalId, data?)
- closeModal()
```

### 8.3 Division of Responsibility

| State Type | Store | Method |
|-----------|-------|--------|
| Auth info | Zustand (authStore) | Global |
| User preferences | Zustand (uiStore) | Global |
| Server data | React Query | Local (per hook) |
| UI temporary state | Local useState | Component |

**Guidelines:**
- React Query: Server data, list/detail/stats (NOT in Zustand!)
- Zustand: Auth state, user prefs, selected org
- useState: Form state, modal toggles, temporary UI

---

## 9. ROUTING PATTERN

**FILE:** `/mnt/g/khoirul/signate/cms-vite/src/routes/index.tsx`

```typescript
// Current structure:
/dashboard                    → DashboardPage
/select-organization          → SelectOrganizationPage
/settings                     → SettingsPage (Organizations & Users)
/devices                      → "Coming Soon" (placeholder)
/contents                     → ContentPage
/playlists                    → PlaylistsPage
/tags                        → TagsPage
/audit-logs                  → AuditLogsPage
/widgets                     → "Coming Soon" (placeholder)

// Protected with ProtectedRoute wrapper
// Uses DashboardLayout as main layout
// Toolbar shows organization selector
```

**Device Page Placeholder:**
```typescript
{
  path: 'devices',
  element: <div className="p-8">Devices Page - Coming Soon</div>,
},
```

---

## 10. EXACT PATTERNS TO FOLLOW FOR DEVICES

### 10.1 Files to Create

```
cms-vite/src/features/devices/
├── services/
│   └── deviceApi.ts              (CREATE) - API service layer
├── hooks/
│   └── useDevices.ts             (CREATE) - React Query hooks
└── components/
    ├── DeviceTable.tsx           (CREATE) - Main device list
    ├── DeviceDetailModal.tsx      (CREATE) - View device details
    ├── DeviceEditModal.tsx        (CREATE) - Edit device info
    ├── DeviceActivationModal.tsx  (CREATE) - Activation flow
    ├── AssignPlaylistModal.tsx    (CREATE) - Assign playlist
    ├── SendCommandModal.tsx       (CREATE) - Device commands
    ├── DeviceLogsModal.tsx        (CREATE) - View logs
    └── DeleteConfirmModal.tsx     (CREATE) - Delete confirmation
```

### 10.2 DeviceApi Service Pattern

**Based on:** Playlists API structure (object-based, most maintainable)

```typescript
// /features/devices/services/deviceApi.ts

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type {
  Device,
  DeviceFilters,
  MonitorRegisterRequest,
  TVRegisterRequest,
  ActivateDeviceRequest,
} from '../types/device';

interface ListResponse {
  success: boolean;
  data: {
    total: number;
    items: Device[];
  };
}

interface DetailResponse {
  success: boolean;
  data: Device;
}

function unwrapResponse<T>(response: any): T {
  if (response.data && !('success' in response.data || 'data' in response.data)) {
    return response.data as T;
  }
  if (response.data?.data) {
    return response.data.data as T;
  }
  return response.data as T;
}

export const deviceApi = {
  // CRUD
  list: async (filters?: DeviceFilters): Promise<{ total: number; items: Device[] }> => {
    const params = new URLSearchParams();
    if (filters?.skip !== undefined) params.append('skip', String(filters.skip));
    if (filters?.limit !== undefined) params.append('limit', String(filters.limit));
    if (filters?.status) params.append('status', filters.status);
    
    const response = await apiClient.get<ListResponse>(
      `${API_ENDPOINTS.DEVICES.LIST}${params.toString() ? `?${params.toString()}` : ''}`
    );
    
    if (response.data && 'total' in response.data && 'items' in response.data) {
      return response.data as { total: number; items: Device[] };
    }
    if (response.data?.data) {
      return response.data.data;
    }
    return { total: 0, items: [] };
  },

  get: async (id: number): Promise<Device> => {
    const response = await apiClient.get<DetailResponse>(API_ENDPOINTS.DEVICES.GET(id));
    return unwrapResponse<Device>(response);
  },

  update: async (id: number, data: Partial<Device>): Promise<Device> => {
    const response = await apiClient.patch<DetailResponse>(
      API_ENDPOINTS.DEVICES.UPDATE(id),
      data
    );
    return unwrapResponse<Device>(response);
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.DEVICES.DELETE(id));
  },

  // Device specific operations
  tvRegister: async (data: TVRegisterRequest): Promise<Device> => {
    const response = await apiClient.post<DetailResponse>(
      API_ENDPOINTS.DEVICES.TV_REGISTER,
      data
    );
    return unwrapResponse<Device>(response);
  },

  monitorRegister: async (data: MonitorRegisterRequest): Promise<Device> => {
    const response = await apiClient.post<DetailResponse>(
      API_ENDPOINTS.DEVICES.MONITOR_REGISTER,
      data
    );
    return unwrapResponse<Device>(response);
  },

  activate: async (data: ActivateDeviceRequest): Promise<Device> => {
    const response = await apiClient.post<DetailResponse>(
      API_ENDPOINTS.DEVICES.ACTIVATE,
      data
    );
    return unwrapResponse<Device>(response);
  },

  checkActivation: async (code: string): Promise<{ active: boolean; device?: Device }> => {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.CHECK_ACTIVATION(code));
    return response.data;
  },

  sendHeartbeat: async (data: { unique_code: string }): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.DEVICES.HEARTBEAT, data);
  },

  sendCommand: async (id: number, commandData: any): Promise<any> => {
    const response = await apiClient.post(API_ENDPOINTS.DEVICES.SEND_COMMAND(id), commandData);
    return response.data;
  },

  getLogs: async (id: number, filters?: any): Promise<any> => {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.LOGS(id));
    return response.data;
  },

  getCommands: async (id: number): Promise<any> => {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.COMMANDS(id));
    return response.data;
  },
};
```

### 10.3 DeviceHooks Pattern

**Based on:** Contents + Playlists structure

```typescript
// /features/devices/hooks/useDevices.ts

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { deviceApi } from '../services/deviceApi';
import type { Device, DeviceFilters } from '../types/device';

// Query Keys Factory
export const deviceKeys = {
  all: ['devices'] as const,
  lists: () => [...deviceKeys.all, 'list'] as const,
  list: (filters?: DeviceFilters) => [...deviceKeys.lists(), filters] as const,
  details: () => [...deviceKeys.all, 'detail'] as const,
  detail: (id: number) => [...deviceKeys.details(), id] as const,
  logs: (id: number) => [...deviceKeys.detail(id), 'logs'] as const,
  commands: (id: number) => [...deviceKeys.detail(id), 'commands'] as const,
};

// Queries
export const useDeviceList = (filters?: DeviceFilters) => {
  return useQuery({
    queryKey: deviceKeys.list(filters),
    queryFn: () => deviceApi.list(filters),
    staleTime: 30000,
  });
};

export const useDevice = (id: number, enabled = true) => {
  return useQuery({
    queryKey: deviceKeys.detail(id),
    queryFn: () => deviceApi.get(id),
    enabled: enabled && id > 0,
  });
};

export const useDeviceLogs = (id: number, enabled = true) => {
  return useQuery({
    queryKey: deviceKeys.logs(id),
    queryFn: () => deviceApi.getLogs(id),
    enabled: enabled && id > 0,
  });
};

export const useDeviceCommands = (id: number, enabled = true) => {
  return useQuery({
    queryKey: deviceKeys.commands(id),
    queryFn: () => deviceApi.getCommands(id),
    enabled: enabled && id > 0,
  });
};

// Mutations
export const useUpdateDevice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Device> }) =>
      deviceApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: deviceKeys.list() });
      queryClient.invalidateQueries({ queryKey: deviceKeys.detail(variables.id) });
      toast.success('Device updated successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to update device';
      toast.error(message);
    },
  });
};

export const useDeleteDevice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deviceApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });
      toast.success('Device deleted successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to delete device';
      toast.error(message);
    },
  });
};

export const useTVRegister = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => deviceApi.tvRegister(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });
      toast.success('TV registered successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to register TV';
      toast.error(message);
    },
  });
};

export const useMonitorRegister = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => deviceApi.monitorRegister(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });
      toast.success('Monitor registered successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to register monitor';
      toast.error(message);
    },
  });
};

export const useActivateDevice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => deviceApi.activate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });
      toast.success('Device activated successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to activate device';
      toast.error(message);
    },
  });
};

export const useSendCommand = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, commandData }: { id: number; commandData: any }) =>
      deviceApi.sendCommand(id, commandData),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: deviceKeys.commands(variables.id) });
      toast.success('Command sent successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to send command';
      toast.error(message);
    },
  });
};
```

### 10.4 DeviceTable Component Pattern

```typescript
// /features/devices/components/DeviceTable.tsx

import { useState } from 'react';
import { Plus, Trash2, Edit, Loader2, Eye, Send } from 'lucide-react';
import { useDeviceList, useDeleteDevice } from '../hooks/useDevices';
import type { Device } from '../types/device';
import { DeviceDetailModal } from './DeviceDetailModal';
import { DeviceEditModal } from './DeviceEditModal';
import { DeviceActivationModal } from './DeviceActivationModal';
import { SendCommandModal } from './SendCommandModal';
import { DeviceLogsModal } from './DeviceLogsModal';
import { DeleteConfirmModal } from './DeleteConfirmModal';

export function DeviceTable() {
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [activeModal, setActiveModal] = useState<string | null>(null);
  const [filters, setFilters] = useState({});
  
  const { data, isLoading } = useDeviceList(filters);
  const deleteDevice = useDeleteDevice();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Devices</h2>
        <button
          onClick={() => setActiveModal('activate')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          <Plus size={18} /> Add Device
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left p-4">Name</th>
              <th className="text-left p-4">Type</th>
              <th className="text-left p-4">Status</th>
              <th className="text-left p-4">Last Seen</th>
              <th className="text-left p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((device: Device) => (
              <tr key={device.id} className="border-b border-gray-100 dark:border-gray-800">
                <td className="p-4">{device.device_name}</td>
                <td className="p-4">{device.device_type}</td>
                <td className="p-4">{device.status}</td>
                <td className="p-4">{device.last_seen || 'Never'}</td>
                <td className="p-4 flex gap-2">
                  <button onClick={() => { setSelectedDevice(device); setActiveModal('detail'); }}>
                    <Eye size={18} />
                  </button>
                  <button onClick={() => { setSelectedDevice(device); setActiveModal('edit'); }}>
                    <Edit size={18} />
                  </button>
                  <button onClick={() => { setSelectedDevice(device); setActiveModal('delete'); }}>
                    <Trash2 size={18} className="text-red-600" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {selectedDevice && activeModal === 'detail' && (
        <DeviceDetailModal
          device={selectedDevice}
          onClose={() => { setActiveModal(null); setSelectedDevice(null); }}
        />
      )}
      {/* ... other modals ... */}
    </div>
  );
}
```

### 10.5 Main DevicesPage Creation

Create: `/pages/DevicesPage.tsx`

```typescript
import { DeviceTable } from '@/features/devices/components/DeviceTable';

export default function DevicesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Device Management</h1>
        <p className="text-gray-500">Manage and monitor all devices</p>
      </div>
      <DeviceTable />
    </div>
  );
}
```

Update route in `/routes/index.tsx`:
```typescript
import DevicesPage from '@/pages/DevicesPage';

// In routes array:
{
  path: 'devices',
  element: <DevicesPage />,
},
```

---

## 11. CRITICAL INCONSISTENCIES FOUND

### 11.1 Toast Notification Inconsistency

**ISSUE:** Two different toast systems in use:
1. **sonner** - Used by Contents, Playlists
2. **Custom toast** - Used by Tags, defined in `/lib/notifications/toast.ts`

**RECOMMENDATION FOR DEVICES:**
✅ **Use sonner** (simpler, already used by majority)
```typescript
import { toast } from 'sonner';

toast.success('Device updated');
toast.error('Failed to update');
toast.warning('Some items failed');
toast.info('Information');
```

### 11.2 Error Handling Inconsistency

**ISSUE:** Two patterns found:
1. **Direct extraction** (Contents): `error?.response?.data?.detail || 'Failed...'`
2. **Error handler** (Tags): `handleAPIError(error)` then `appError.message`

**RECOMMENDATION FOR DEVICES:**
✅ **Use direct extraction** (simpler, matches Contents pattern)
```typescript
const message = error?.response?.data?.detail || 'Failed to update device';
toast.error(message);
```

### 11.3 API Service Pattern Inconsistency

**ISSUE:** Two patterns found:
1. **Function exports** (Contents, Auth): Multiple exported functions
2. **Object-based** (Playlists, Tags): Single exported `api` object with methods

**RECOMMENDATION FOR DEVICES:**
✅ **Use object-based pattern** (Playlists style)
- More maintainable
- Cleaner organization
- Includes helper functions in object
- Better for response unwrapping logic

---

## 12. IMPLEMENTATION CHECKLIST

### Phase 1: Service Layer
- [ ] Create `/features/devices/services/deviceApi.ts`
  - [ ] List with filters
  - [ ] Get single device
  - [ ] Update device
  - [ ] Delete device
  - [ ] TV register
  - [ ] Monitor register
  - [ ] Activate device
  - [ ] Check activation
  - [ ] Send heartbeat
  - [ ] Send command
  - [ ] Get logs
  - [ ] Get commands

### Phase 2: Hooks Layer
- [ ] Create `/features/devices/hooks/useDevices.ts`
  - [ ] Query keys factory
  - [ ] useDeviceList (with filters)
  - [ ] useDevice (detail)
  - [ ] useDeviceLogs
  - [ ] useDeviceCommands
  - [ ] useUpdateDevice mutation
  - [ ] useDeleteDevice mutation
  - [ ] useTVRegister mutation
  - [ ] useMonitorRegister mutation
  - [ ] useActivateDevice mutation
  - [ ] useSendCommand mutation

### Phase 3: Components Layer
- [ ] Create device components:
  - [ ] `DeviceTable.tsx` - Main list view
  - [ ] `DeviceDetailModal.tsx` - View details
  - [ ] `DeviceEditModal.tsx` - Edit info
  - [ ] `DeviceActivationModal.tsx` - Activate new device
  - [ ] `AssignPlaylistModal.tsx` - Assign playlist
  - [ ] `SendCommandModal.tsx` - Send device command
  - [ ] `DeviceLogsModal.tsx` - View activity logs
  - [ ] `DeleteConfirmModal.tsx` - Delete confirmation

### Phase 4: Integration
- [ ] Create `/pages/DevicesPage.tsx`
- [ ] Update `/routes/index.tsx`
- [ ] Add Devices to sidebar navigation
- [ ] Test all features end-to-end

---

## 13. FILE REFERENCES

### Existing Patterns to Reference

| File | Pattern | Use Case |
|------|---------|----------|
| `/features/contents/services/contentApi.ts` | Function exports | Single feature API calls |
| `/features/playlists/services/playlistApi.ts` | Object-based API | Complex multi-operation features |
| `/features/contents/hooks/useContent.ts` | Query factory + mutations | Standard React Query patterns |
| `/features/playlists/hooks/usePlaylist.ts` | Extended hooks | Complex relationships |
| `/lib/api/client.ts` | Axios config | Auto token/org injection |
| `/lib/api/endpoints.ts` | Route definitions | Centralized API routes |
| `/features/contents/types/content.ts` | Type organization | DTOs + domain entities |
| `/features/contents/components/ContentTable.tsx` | Table structure | Main feature UI |
| `/features/devices/types/device.ts` | Already exists | Base types available |

---

## SUMMARY

### What's Ready
✅ API endpoints defined in `lib/api/endpoints.ts`
✅ Device types fully defined in `features/devices/types/device.ts`
✅ API client configured with auth/org injection
✅ Router structure ready (placeholder exists)
✅ Zustand auth + UI store ready
✅ React Query TanStack setup ready

### What Needs Creation
1. **deviceApi.ts** - Object-based service layer (Playlists pattern)
2. **useDevices.ts** - Query factory + 6+ hooks
3. **5-8 Components** - Modals + main table
4. **DevicesPage.tsx** - Main page component
5. **Route update** - Replace placeholder with real page

### Critical Patterns to Match
- **Service:** Object-based API (like playlists, NOT like contents)
- **Hooks:** Query keys factory + mutation patterns (like contents)
- **Errors:** Direct extraction (like contents)
- **Toast:** sonner library (like contents)
- **Types:** DTOs + domain entities (like contents)
- **Styling:** Tailwind CSS only (like all features)

---

## CONCLUSION

The cms-vite project has a CONSISTENT architecture with minor variations. For Device feature:

1. **Services:** Use Playlists pattern (object-based API)
2. **Hooks:** Use Contents pattern (query factory)
3. **Components:** Follow Contents structure
4. **Types:** Extend existing device.ts
5. **Error/Toast:** Use sonner + direct extraction

This will ensure seamless integration with existing codebase.

