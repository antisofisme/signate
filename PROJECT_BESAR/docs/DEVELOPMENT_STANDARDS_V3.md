# Development Standards V3 - Centralized Registries

> Standards #17+ untuk pattern Centralized Registry - menghilangkan gap/miss karena nilai hardcoded scattered.

---

## 17. Centralized Registries

### 17.0 Overview

**Problem:** Nilai-nilai yang sama digunakan di banyak tempat (frontend & backend), tapi didefinisikan secara manual/scattered. Ketika ada perubahan, sering miss update di beberapa tempat.

**Solution:** Centralized Registry Pattern - Single Source of Truth untuk setiap kategori nilai.

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  ⚠️  CHECKLIST WAJIB - SEBELUM HARDCODE NILAI APAPUN:                     ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  □ Apakah nilai ini dipakai di lebih dari 1 tempat?                       ║
║  □ Apakah nilai ini mungkin berubah di masa depan?                        ║
║  □ Apakah nilai ini perlu konsisten antara frontend & backend?            ║
║                                                                            ║
║  Jika YA untuk salah satu → WAJIB pakai Centralized Registry!            ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 17.1 Status/Enum Registry

**Problem:**
```typescript
// ❌ Status values hardcoded di banyak tempat
// DeviceTable.tsx
{status === 'online' && <Badge>Online</Badge>}

// DeviceFilter.tsx
<Select options={[{value: 'online'}, {value: 'ofline'}]} />  // TYPO!

// Backend Python
class DeviceStatus(str, Enum):
    ONLINE = "online"
    MAINTENANCE = "maintenance"  // Frontend tidak tahu!
```

**Solution:**

```typescript
// src/lib/constants/statuses.ts - SINGLE SOURCE OF TRUTH

export const DeviceStatus = {
  ONLINE: 'online',
  OFFLINE: 'offline',
  MAINTENANCE: 'maintenance',
  PENDING: 'pending',
} as const;

export type DeviceStatusType = typeof DeviceStatus[keyof typeof DeviceStatus];

// Dengan label untuk UI
export const DeviceStatusConfig = {
  [DeviceStatus.ONLINE]: {
    label: 'Online',
    color: 'green',
    icon: 'check-circle',
  },
  [DeviceStatus.OFFLINE]: {
    label: 'Offline',
    color: 'red',
    icon: 'x-circle',
  },
  [DeviceStatus.MAINTENANCE]: {
    label: 'Maintenance',
    color: 'yellow',
    icon: 'wrench',
  },
  [DeviceStatus.PENDING]: {
    label: 'Pending Activation',
    color: 'gray',
    icon: 'clock',
  },
} as const;

// Helper functions
export const getDeviceStatusLabel = (status: DeviceStatusType) =>
  DeviceStatusConfig[status]?.label ?? status;

export const getDeviceStatusColor = (status: DeviceStatusType) =>
  DeviceStatusConfig[status]?.color ?? 'gray';

export const deviceStatusOptions = Object.entries(DeviceStatusConfig).map(
  ([value, config]) => ({ value, label: config.label })
);
```

```typescript
// Usage - DeviceTable.tsx
import { DeviceStatus, getDeviceStatusColor } from '@/lib/constants/statuses';

<Badge color={getDeviceStatusColor(device.status)}>
  {getDeviceStatusLabel(device.status)}
</Badge>

// Usage - DeviceFilter.tsx
import { deviceStatusOptions } from '@/lib/constants/statuses';

<Select options={deviceStatusOptions} />  // ✅ Auto-sync!
```

```python
# Backend - Sync dengan frontend
# backend-python/shared/constants/statuses.py

from enum import Enum

class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    PENDING = "pending"
```

---

### 17.2 Permission Codes Registry

**Problem:**
```typescript
// ❌ Permission strings hardcoded, typo-prone
{hasPermission('devices.create') && <Button>Add</Button>}
{hasPermission('device.create') && <Button>Add</Button>}  // TYPO!
```

**Solution:**

```typescript
// src/lib/constants/permissions.ts

export const Permissions = {
  // Devices
  DEVICES_VIEW: 'devices.view',
  DEVICES_CREATE: 'devices.create',
  DEVICES_UPDATE: 'devices.update',
  DEVICES_DELETE: 'devices.delete',
  DEVICES_COMMAND: 'devices.command',

  // Contents
  CONTENTS_VIEW: 'contents.view',
  CONTENTS_CREATE: 'contents.create',
  CONTENTS_UPDATE: 'contents.update',
  CONTENTS_DELETE: 'contents.delete',
  CONTENTS_RESTORE: 'contents.restore',

  // Playlists
  PLAYLISTS_VIEW: 'playlists.view',
  PLAYLISTS_CREATE: 'playlists.create',
  PLAYLISTS_UPDATE: 'playlists.update',
  PLAYLISTS_DELETE: 'playlists.delete',

  // Schedules
  SCHEDULES_VIEW: 'schedules.view',
  SCHEDULES_CREATE: 'schedules.create',
  SCHEDULES_UPDATE: 'schedules.update',
  SCHEDULES_DELETE: 'schedules.delete',

  // Settings
  SETTINGS_VIEW: 'settings.view',
  SETTINGS_MANAGE: 'settings.manage',

  // Users
  USERS_VIEW: 'users.view',
  USERS_INVITE: 'users.invite',
  USERS_MANAGE: 'users.manage',
} as const;

export type PermissionCode = typeof Permissions[keyof typeof Permissions];

// Permission groupings untuk UI
export const PermissionGroups = {
  devices: [
    Permissions.DEVICES_VIEW,
    Permissions.DEVICES_CREATE,
    Permissions.DEVICES_UPDATE,
    Permissions.DEVICES_DELETE,
    Permissions.DEVICES_COMMAND,
  ],
  contents: [
    Permissions.CONTENTS_VIEW,
    Permissions.CONTENTS_CREATE,
    Permissions.CONTENTS_UPDATE,
    Permissions.CONTENTS_DELETE,
    Permissions.CONTENTS_RESTORE,
  ],
  // ... etc
} as const;
```

```typescript
// Usage
import { Permissions } from '@/lib/constants/permissions';

// ✅ Type-safe, autocomplete
{hasPermission(Permissions.DEVICES_CREATE) && <Button>Add</Button>}

// ❌ DILARANG - string manual
{hasPermission('devices.create') && <Button>Add</Button>}
```

```python
# Backend sync
# backend-python/shared/constants/permissions.py

class Permissions:
    # Devices
    DEVICES_VIEW = "devices.view"
    DEVICES_CREATE = "devices.create"
    DEVICES_UPDATE = "devices.update"
    DEVICES_DELETE = "devices.delete"
    DEVICES_COMMAND = "devices.command"

    # Contents
    CONTENTS_VIEW = "contents.view"
    # ... etc

# Usage di decorator
@require_permission(Permissions.DEVICES_CREATE)
async def create_device(...):
    pass
```

---

### 17.3 Route Paths Registry

**Problem:**
```typescript
// ❌ Route paths hardcoded
<Link to="/devices">Devices</Link>
navigate('/device/' + id);  // TYPO: '/device/' vs '/devices/'
```

**Solution:**

```typescript
// src/lib/constants/routes.ts

export const Routes = {
  // Auth
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',

  // Dashboard
  DASHBOARD: '/',

  // Devices
  DEVICES: '/devices',
  DEVICE_DETAIL: (id: number | string) => `/devices/${id}`,
  DEVICE_CREATE: '/devices/new',
  DEVICE_EDIT: (id: number | string) => `/devices/${id}/edit`,

  // Contents
  CONTENTS: '/contents',
  CONTENT_DETAIL: (id: number | string) => `/contents/${id}`,
  CONTENT_CREATE: '/contents/new',
  CONTENTS_DELETED: '/contents/deleted',

  // Playlists
  PLAYLISTS: '/playlists',
  PLAYLIST_DETAIL: (id: number | string) => `/playlists/${id}`,
  PLAYLIST_CREATE: '/playlists/new',
  PLAYLIST_EDIT: (id: number | string) => `/playlists/${id}/edit`,

  // Schedules
  SCHEDULES: '/schedules',
  SCHEDULE_DETAIL: (id: number | string) => `/schedules/${id}`,

  // Settings
  SETTINGS: '/settings',
  SETTINGS_ORGANIZATION: '/settings/organization',
  SETTINGS_USERS: '/settings/users',
  SETTINGS_ROLES: '/settings/roles',
} as const;

// For React Router definitions
export const RoutePatterns = {
  DEVICE_DETAIL: '/devices/:id',
  DEVICE_EDIT: '/devices/:id/edit',
  CONTENT_DETAIL: '/contents/:id',
  PLAYLIST_DETAIL: '/playlists/:id',
  PLAYLIST_EDIT: '/playlists/:id/edit',
  SCHEDULE_DETAIL: '/schedules/:id',
} as const;
```

```typescript
// Usage
import { Routes } from '@/lib/constants/routes';

// Navigation
navigate(Routes.DEVICES);
navigate(Routes.DEVICE_DETAIL(device.id));

// Links
<Link to={Routes.DEVICE_EDIT(id)}>Edit</Link>

// Breadcrumbs
const breadcrumbs = [
  { path: Routes.DEVICES, label: 'Devices' },
  { path: Routes.DEVICE_DETAIL(id), label: device.name },
];
```

---

### 17.4 Form Validation Constants

**Problem:**
```typescript
// ❌ Validation rules berbeda di frontend vs backend
// Frontend: max 100
const schema = z.object({ name: z.string().max(100) });

// Backend: max 200
name: str = Field(..., max_length=200)
```

**Solution:**

```typescript
// src/lib/constants/validation.ts

export const ValidationRules = {
  // Common
  NAME_MIN: 2,
  NAME_MAX: 200,
  DESCRIPTION_MAX: 2000,
  CODE_MAX: 50,

  // Device
  DEVICE_NAME_MIN: 2,
  DEVICE_NAME_MAX: 100,
  ACTIVATION_CODE_LENGTH: 6,

  // Content
  CONTENT_NAME_MAX: 200,
  CONTENT_DESCRIPTION_MAX: 5000,

  // File Upload
  FILE_MAX_SIZE_MB: 100,
  FILE_MAX_SIZE_BYTES: 100 * 1024 * 1024,
  IMAGE_MAX_SIZE_MB: 10,
  VIDEO_MAX_SIZE_MB: 500,

  // Playlist
  PLAYLIST_NAME_MAX: 200,
  PLAYLIST_MAX_ITEMS: 100,

  // Pagination
  PAGE_SIZE_DEFAULT: 20,
  PAGE_SIZE_MAX: 100,

  // Password
  PASSWORD_MIN: 8,
  PASSWORD_MAX: 128,
} as const;

// Allowed file types
export const AllowedFileTypes = {
  IMAGE: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  VIDEO: ['video/mp4', 'video/webm', 'video/quicktime'],
  DOCUMENT: ['application/pdf'],
  ALL_CONTENT: [
    ...['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    ...['video/mp4', 'video/webm'],
  ],
} as const;

export const AllowedExtensions = {
  IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
  VIDEO: ['.mp4', '.webm', '.mov'],
  DOCUMENT: ['.pdf'],
} as const;
```

```typescript
// Usage di Zod schema
import { ValidationRules } from '@/lib/constants/validation';

const deviceSchema = z.object({
  name: z.string()
    .min(ValidationRules.DEVICE_NAME_MIN)
    .max(ValidationRules.DEVICE_NAME_MAX),
  description: z.string().max(ValidationRules.DESCRIPTION_MAX).optional(),
});
```

```python
# Backend sync
# backend-python/shared/constants/validation.py

class ValidationRules:
    NAME_MIN = 2
    NAME_MAX = 200
    DESCRIPTION_MAX = 2000

    DEVICE_NAME_MIN = 2
    DEVICE_NAME_MAX = 100
    ACTIVATION_CODE_LENGTH = 6

    FILE_MAX_SIZE_MB = 100
    FILE_MAX_SIZE_BYTES = 100 * 1024 * 1024

    PAGE_SIZE_DEFAULT = 20
    PAGE_SIZE_MAX = 100

# Usage di Pydantic
class CreateDeviceDTO(BaseModel):
    name: str = Field(
        ...,
        min_length=ValidationRules.DEVICE_NAME_MIN,
        max_length=ValidationRules.DEVICE_NAME_MAX
    )
```

---

### 17.5 WebSocket/Realtime Event Registry

**Problem:**
```typescript
// ❌ Event names tidak konsisten
// Frontend
socket.on('device:status_changed', handler);

// Backend
await ws.emit('device:statusChanged', data);  // camelCase vs snake_case!
```

**Solution:**

```typescript
// src/lib/constants/wsEvents.ts

export const WsEvents = {
  // Device events
  DEVICE_STATUS_CHANGED: 'device:status_changed',
  DEVICE_HEARTBEAT: 'device:heartbeat',
  DEVICE_COMMAND: 'device:command',
  DEVICE_COMMAND_RESULT: 'device:command_result',
  DEVICE_CONNECTED: 'device:connected',
  DEVICE_DISCONNECTED: 'device:disconnected',

  // Content events
  CONTENT_UPLOADED: 'content:uploaded',
  CONTENT_PROCESSING: 'content:processing',
  CONTENT_READY: 'content:ready',
  CONTENT_DELETED: 'content:deleted',

  // Playlist events
  PLAYLIST_UPDATED: 'playlist:updated',
  PLAYLIST_ASSIGNED: 'playlist:assigned',

  // Schedule events
  SCHEDULE_ACTIVATED: 'schedule:activated',
  SCHEDULE_DEACTIVATED: 'schedule:deactivated',

  // System events
  NOTIFICATION: 'system:notification',
  FORCE_LOGOUT: 'system:force_logout',
  MAINTENANCE_MODE: 'system:maintenance',
} as const;

export type WsEventType = typeof WsEvents[keyof typeof WsEvents];

// Event payload types
export interface WsEventPayloads {
  [WsEvents.DEVICE_STATUS_CHANGED]: {
    device_id: number;
    status: string;
    last_seen_at: string;
  };
  [WsEvents.DEVICE_COMMAND]: {
    device_id: number;
    command: string;
    params?: Record<string, unknown>;
  };
  [WsEvents.CONTENT_UPLOADED]: {
    content_id: number;
    filename: string;
    status: string;
  };
  // ... etc
}
```

```typescript
// Usage - Frontend
import { WsEvents } from '@/lib/constants/wsEvents';

socket.on(WsEvents.DEVICE_STATUS_CHANGED, (data) => {
  // Type-safe payload
});

socket.emit(WsEvents.DEVICE_COMMAND, { device_id: 1, command: 'restart' });
```

```python
# Backend sync
# backend-python/shared/constants/ws_events.py

class WsEvents:
    DEVICE_STATUS_CHANGED = "device:status_changed"
    DEVICE_HEARTBEAT = "device:heartbeat"
    DEVICE_COMMAND = "device:command"
    DEVICE_COMMAND_RESULT = "device:command_result"
    CONTENT_UPLOADED = "content:uploaded"
    # ... etc

# Usage
await websocket.send_json({
    "event": WsEvents.DEVICE_STATUS_CHANGED,
    "data": {"device_id": 1, "status": "online"}
})
```

---

### 17.6 Table Column Registry

**Problem:**
```typescript
// ❌ Column config copy-paste, sering out of sync
// DeviceTable.tsx
{ key: 'name', header: 'Name', sortable: true }

// DeviceExport.tsx
{ key: 'name', header: 'Device Name' }  // Header beda!
```

**Solution:**

```typescript
// src/lib/constants/tableColumns.ts

export interface ColumnConfig {
  key: string;
  header: string;
  sortable?: boolean;
  filterable?: boolean;
  exportable?: boolean;
  width?: number | string;
  align?: 'left' | 'center' | 'right';
  format?: 'text' | 'date' | 'datetime' | 'number' | 'currency' | 'boolean' | 'status';
}

export const DeviceColumns: Record<string, ColumnConfig> = {
  id: { key: 'id', header: 'ID', sortable: true, width: 80, align: 'center' },
  name: { key: 'name', header: 'Device Name', sortable: true, filterable: true, exportable: true },
  status: { key: 'status', header: 'Status', sortable: true, filterable: true, format: 'status' },
  location: { key: 'location', header: 'Location', sortable: true, filterable: true, exportable: true },
  last_seen_at: { key: 'last_seen_at', header: 'Last Seen', sortable: true, format: 'datetime' },
  created_at: { key: 'created_at', header: 'Created', sortable: true, format: 'datetime', exportable: true },
  is_active: { key: 'is_active', header: 'Active', format: 'boolean', align: 'center' },
};

export const ContentColumns: Record<string, ColumnConfig> = {
  id: { key: 'id', header: 'ID', sortable: true, width: 80 },
  name: { key: 'name', header: 'Content Name', sortable: true, filterable: true, exportable: true },
  content_type: { key: 'content_type', header: 'Type', sortable: true, filterable: true },
  file_size: { key: 'file_size', header: 'Size', sortable: true, format: 'number' },
  duration: { key: 'duration', header: 'Duration', sortable: true },
  created_at: { key: 'created_at', header: 'Uploaded', sortable: true, format: 'datetime' },
};

// Helper: Get columns for table display
export const getTableColumns = (columns: Record<string, ColumnConfig>, keys: string[]) =>
  keys.map(key => columns[key]).filter(Boolean);

// Helper: Get columns for export
export const getExportColumns = (columns: Record<string, ColumnConfig>) =>
  Object.values(columns).filter(col => col.exportable);

// Helper: Get sortable columns
export const getSortableColumns = (columns: Record<string, ColumnConfig>) =>
  Object.values(columns).filter(col => col.sortable);
```

```typescript
// Usage - DeviceTable.tsx
import { DeviceColumns, getTableColumns } from '@/lib/constants/tableColumns';

const columns = getTableColumns(DeviceColumns, ['name', 'status', 'location', 'last_seen_at']);

// Usage - DeviceExport.tsx (same config!)
const exportColumns = getExportColumns(DeviceColumns);
```

---

### 17.7 Toast/Notification Messages

**Problem:**
```typescript
// ❌ Toast messages scattered & inconsistent
toast.success('Device created successfully');
toast.success('Device has been created');  // Beda wording
toast.success('Berhasil membuat device');  // Mix language
```

**Solution:**

```typescript
// src/lib/constants/messages.ts

export const Messages = {
  // Success messages
  success: {
    // Generic CRUD
    created: (entity: string) => `${entity} created successfully`,
    updated: (entity: string) => `${entity} updated successfully`,
    deleted: (entity: string) => `${entity} deleted successfully`,
    restored: (entity: string) => `${entity} restored successfully`,

    // Specific actions
    DEVICE_ACTIVATED: 'Device activated successfully',
    DEVICE_COMMAND_SENT: 'Command sent to device',
    CONTENT_UPLOADED: 'Content uploaded successfully',
    PLAYLIST_ASSIGNED: 'Playlist assigned to device',
    SCHEDULE_ACTIVATED: 'Schedule activated',
    PASSWORD_CHANGED: 'Password changed successfully',
    SETTINGS_SAVED: 'Settings saved',
  },

  // Error messages
  error: {
    // Generic
    GENERIC: 'Something went wrong. Please try again.',
    NETWORK: 'Network error. Please check your connection.',
    UNAUTHORIZED: 'Your session has expired. Please login again.',
    FORBIDDEN: 'You do not have permission to perform this action.',
    NOT_FOUND: (entity: string) => `${entity} not found`,

    // Validation
    REQUIRED_FIELD: (field: string) => `${field} is required`,
    INVALID_FORMAT: (field: string) => `Invalid ${field} format`,

    // Specific
    DEVICE_OFFLINE: 'Device is offline. Command cannot be sent.',
    FILE_TOO_LARGE: 'File size exceeds maximum limit',
    INVALID_FILE_TYPE: 'File type not supported',
    DUPLICATE_NAME: (entity: string) => `${entity} with this name already exists`,
  },

  // Confirmation messages
  confirm: {
    delete: (entity: string) => `Are you sure you want to delete this ${entity}?`,
    deleteMultiple: (count: number, entity: string) =>
      `Are you sure you want to delete ${count} ${entity}s?`,
    restore: (entity: string) => `Are you sure you want to restore this ${entity}?`,
    deactivate: (entity: string) => `Are you sure you want to deactivate this ${entity}?`,
    logout: 'Are you sure you want to logout?',
    unsavedChanges: 'You have unsaved changes. Are you sure you want to leave?',
  },

  // Info messages
  info: {
    PROCESSING: 'Processing...',
    UPLOADING: 'Uploading...',
    LOADING: 'Loading...',
    NO_DATA: 'No data available',
    NO_RESULTS: 'No results found',
  },
} as const;
```

```typescript
// Usage
import { Messages } from '@/lib/constants/messages';

// Success
toast.success(Messages.success.created('Device'));
toast.success(Messages.success.DEVICE_ACTIVATED);

// Error
toast.error(Messages.error.DEVICE_OFFLINE);
toast.error(Messages.error.NOT_FOUND('Content'));

// Confirm dialog
confirm(Messages.confirm.delete('device'));
```

---

### 17.8 API Error Codes Registry

**Problem:**
```typescript
// ❌ Error codes scattered, handling inconsistent
if (error.code === 'DEVICE_OFFLINE') { ... }
if (error.code === 'device_offline') { ... }  // Case mismatch!
```

**Solution:**

```typescript
// src/lib/constants/errorCodes.ts

export const ErrorCodes = {
  // Auth errors (1xxx)
  AUTH_INVALID_CREDENTIALS: 'AUTH_1001',
  AUTH_TOKEN_EXPIRED: 'AUTH_1002',
  AUTH_TOKEN_INVALID: 'AUTH_1003',
  AUTH_INSUFFICIENT_PERMISSIONS: 'AUTH_1004',
  AUTH_ACCOUNT_DISABLED: 'AUTH_1005',

  // Validation errors (2xxx)
  VALIDATION_REQUIRED: 'VAL_2001',
  VALIDATION_FORMAT: 'VAL_2002',
  VALIDATION_DUPLICATE: 'VAL_2003',
  VALIDATION_REFERENCE: 'VAL_2004',

  // Device errors (3xxx)
  DEVICE_NOT_FOUND: 'DEV_3001',
  DEVICE_OFFLINE: 'DEV_3002',
  DEVICE_ALREADY_ACTIVATED: 'DEV_3003',
  DEVICE_INVALID_CODE: 'DEV_3004',
  DEVICE_COMMAND_FAILED: 'DEV_3005',

  // Content errors (4xxx)
  CONTENT_NOT_FOUND: 'CON_4001',
  CONTENT_UPLOAD_FAILED: 'CON_4002',
  CONTENT_INVALID_TYPE: 'CON_4003',
  CONTENT_TOO_LARGE: 'CON_4004',
  CONTENT_IN_USE: 'CON_4005',

  // Playlist errors (5xxx)
  PLAYLIST_NOT_FOUND: 'PL_5001',
  PLAYLIST_EMPTY: 'PL_5002',
  PLAYLIST_MAX_ITEMS: 'PL_5003',

  // Generic errors (9xxx)
  INTERNAL_ERROR: 'SYS_9001',
  SERVICE_UNAVAILABLE: 'SYS_9002',
  RATE_LIMITED: 'SYS_9003',
} as const;

export type ErrorCode = typeof ErrorCodes[keyof typeof ErrorCodes];

// Error code to message mapping
export const ErrorMessages: Record<ErrorCode, string> = {
  [ErrorCodes.AUTH_INVALID_CREDENTIALS]: 'Invalid username or password',
  [ErrorCodes.AUTH_TOKEN_EXPIRED]: 'Your session has expired',
  [ErrorCodes.DEVICE_OFFLINE]: 'Device is currently offline',
  [ErrorCodes.CONTENT_TOO_LARGE]: 'File size exceeds the maximum limit',
  // ... etc
};

// Helper
export const getErrorMessage = (code: ErrorCode): string =>
  ErrorMessages[code] ?? Messages.error.GENERIC;
```

```typescript
// Usage - Error handling
import { ErrorCodes, getErrorMessage } from '@/lib/constants/errorCodes';

try {
  await deviceApi.sendCommand(id, command);
} catch (error) {
  if (error.code === ErrorCodes.DEVICE_OFFLINE) {
    toast.error(getErrorMessage(ErrorCodes.DEVICE_OFFLINE));
  }
}
```

```python
# Backend sync
# backend-python/shared/constants/error_codes.py

class ErrorCodes:
    AUTH_INVALID_CREDENTIALS = "AUTH_1001"
    AUTH_TOKEN_EXPIRED = "AUTH_1002"
    DEVICE_OFFLINE = "DEV_3002"
    # ... etc

# Usage
raise HTTPException(
    status_code=400,
    detail={"code": ErrorCodes.DEVICE_OFFLINE, "message": "Device is offline"}
)
```

---

### 17.9 Feature Flags Registry

**Problem:**
```typescript
// ❌ Feature flags scattered
if (localStorage.getItem('feature_new_ui') === 'true') { ... }
if (config.features.newUI) { ... }  // Different approach!
```

**Solution:**

```typescript
// src/lib/constants/featureFlags.ts

export const FeatureFlags = {
  // UI Features
  NEW_DASHBOARD: 'new_dashboard',
  DARK_MODE: 'dark_mode',
  COMPACT_TABLE: 'compact_table',

  // Functionality
  BULK_OPERATIONS: 'bulk_operations',
  ADVANCED_SCHEDULING: 'advanced_scheduling',
  CONTENT_PREVIEW: 'content_preview',
  DEVICE_GROUPING: 'device_grouping',

  // Experimental
  AI_RECOMMENDATIONS: 'ai_recommendations',
  REAL_TIME_ANALYTICS: 'real_time_analytics',

  // Beta
  MULTI_LANGUAGE: 'multi_language',
} as const;

export type FeatureFlag = typeof FeatureFlags[keyof typeof FeatureFlags];

// Default values (can be overridden by backend/config)
export const FeatureFlagDefaults: Record<FeatureFlag, boolean> = {
  [FeatureFlags.NEW_DASHBOARD]: false,
  [FeatureFlags.DARK_MODE]: true,
  [FeatureFlags.COMPACT_TABLE]: false,
  [FeatureFlags.BULK_OPERATIONS]: true,
  [FeatureFlags.ADVANCED_SCHEDULING]: false,
  [FeatureFlags.CONTENT_PREVIEW]: true,
  [FeatureFlags.DEVICE_GROUPING]: false,
  [FeatureFlags.AI_RECOMMENDATIONS]: false,
  [FeatureFlags.REAL_TIME_ANALYTICS]: false,
  [FeatureFlags.MULTI_LANGUAGE]: false,
};
```

```typescript
// src/hooks/useFeatureFlag.ts
import { FeatureFlags, FeatureFlag, FeatureFlagDefaults } from '@/lib/constants/featureFlags';

export function useFeatureFlag(flag: FeatureFlag): boolean {
  // Could check from backend config, localStorage, or user settings
  const orgSettings = useOrgSettings();
  return orgSettings?.features?.[flag] ?? FeatureFlagDefaults[flag];
}

// Usage
const showBulkOps = useFeatureFlag(FeatureFlags.BULK_OPERATIONS);

{showBulkOps && <BulkActionsToolbar />}
```

---

### 17.10 Pagination & List Defaults

**Problem:**
```typescript
// ❌ Page size berbeda di setiap halaman
// DevicesPage.tsx
const [pageSize, setPageSize] = useState(20);

// ContentsPage.tsx
const [pageSize, setPageSize] = useState(10);  // Beda!

// PlaylistsPage.tsx
const [pageSize, setPageSize] = useState(25);  // Beda lagi!
```

**Solution:**

```typescript
// src/lib/constants/pagination.ts

export const PaginationConfig = {
  // Default values
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 20,

  // Page size options
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100] as const,

  // Limits
  MAX_PAGE_SIZE: 100,
  MIN_PAGE_SIZE: 10,

  // Infinite scroll
  INFINITE_SCROLL_THRESHOLD: 200,  // px from bottom
  INFINITE_SCROLL_PAGE_SIZE: 20,
} as const;

// Default sort configs per entity
export const DefaultSortConfig = {
  devices: { field: 'name', order: 'asc' },
  contents: { field: 'created_at', order: 'desc' },
  playlists: { field: 'name', order: 'asc' },
  schedules: { field: 'start_date', order: 'asc' },
  users: { field: 'username', order: 'asc' },
} as const;
```

```typescript
// Usage
import { PaginationConfig, DefaultSortConfig } from '@/lib/constants/pagination';

const [pagination, setPagination] = useState({
  page: PaginationConfig.DEFAULT_PAGE,
  pageSize: PaginationConfig.DEFAULT_PAGE_SIZE,
  ...DefaultSortConfig.devices,
});

<Select options={PaginationConfig.PAGE_SIZE_OPTIONS.map(n => ({ value: n, label: `${n} / page` }))} />
```

---

### 17.11 Date/Time Format Constants

**Problem:**
```typescript
// ❌ Date format berbeda di setiap tempat
format(date, 'yyyy-MM-dd');
format(date, 'dd/MM/yyyy');  // Format beda!
format(date, 'MMMM d, yyyy');  // Beda lagi!
```

**Solution:**

```typescript
// src/lib/constants/dateFormats.ts

export const DateFormats = {
  // Display formats
  DATE_SHORT: 'dd/MM/yyyy',           // 07/12/2025
  DATE_MEDIUM: 'd MMM yyyy',          // 7 Dec 2025
  DATE_LONG: 'd MMMM yyyy',           // 7 December 2025

  TIME_SHORT: 'HH:mm',                // 14:30
  TIME_MEDIUM: 'HH:mm:ss',            // 14:30:45
  TIME_12H: 'h:mm a',                 // 2:30 PM

  DATETIME_SHORT: 'dd/MM/yyyy HH:mm', // 07/12/2025 14:30
  DATETIME_MEDIUM: 'd MMM yyyy HH:mm', // 7 Dec 2025 14:30
  DATETIME_LONG: 'd MMMM yyyy HH:mm:ss', // 7 December 2025 14:30:45

  // API/ISO formats
  API_DATE: 'yyyy-MM-dd',             // 2025-12-07
  API_DATETIME: "yyyy-MM-dd'T'HH:mm:ss", // 2025-12-07T14:30:00

  // Relative (for display)
  RELATIVE: 'relative',               // "2 hours ago", "yesterday"
} as const;

export type DateFormatType = typeof DateFormats[keyof typeof DateFormats];

// Helper dengan locale support
import { format as fnsFormat, formatDistanceToNow } from 'date-fns';
import { id } from 'date-fns/locale';

export const formatDate = (
  date: Date | string,
  formatStr: DateFormatType = DateFormats.DATE_MEDIUM,
  locale = id
): string => {
  const d = typeof date === 'string' ? new Date(date) : date;

  if (formatStr === DateFormats.RELATIVE) {
    return formatDistanceToNow(d, { addSuffix: true, locale });
  }

  return fnsFormat(d, formatStr, { locale });
};
```

```typescript
// Usage
import { formatDate, DateFormats } from '@/lib/constants/dateFormats';

formatDate(device.last_seen_at, DateFormats.DATETIME_SHORT);  // "07/12/2025 14:30"
formatDate(device.last_seen_at, DateFormats.RELATIVE);        // "2 hours ago"
formatDate(content.created_at, DateFormats.DATE_MEDIUM);      // "7 Dec 2025"
```

---

### 17.12 Design Tokens (Colors, Spacing)

**Problem:**
```typescript
// ❌ Colors hardcoded
<div className="bg-blue-500">  // Magic color
<Badge style={{ backgroundColor: '#22c55e' }}>  // Hex hardcoded
```

**Solution:**

```typescript
// src/lib/constants/designTokens.ts

export const Colors = {
  // Brand
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
  },

  // Semantic
  success: {
    light: '#dcfce7',
    DEFAULT: '#22c55e',
    dark: '#15803d',
  },
  warning: {
    light: '#fef3c7',
    DEFAULT: '#f59e0b',
    dark: '#b45309',
  },
  error: {
    light: '#fee2e2',
    DEFAULT: '#ef4444',
    dark: '#b91c1c',
  },

  // Status colors (linked to StatusConfig)
  status: {
    online: '#22c55e',
    offline: '#ef4444',
    pending: '#f59e0b',
    maintenance: '#3b82f6',
  },
} as const;

export const Spacing = {
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  '2xl': '3rem',   // 48px
} as const;

export const Breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

export const ZIndex = {
  dropdown: 1000,
  sticky: 1020,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
  toast: 1080,
} as const;
```

```typescript
// Usage with Tailwind (tailwind.config.js)
module.exports = {
  theme: {
    extend: {
      colors: Colors,
      spacing: Spacing,
      screens: Breakpoints,
      zIndex: ZIndex,
    },
  },
};

// Usage in components
<Badge className="bg-status-online">Online</Badge>
<div className="p-md mb-lg">...</div>
```

---

### 17.13 Keyboard Shortcuts Registry

**Problem:**
```typescript
// ❌ Keyboard shortcuts hardcoded scattered
useHotkey('ctrl+s', handleSave);
useHotkey('Ctrl+S', handleSave);  // Inconsistent casing
useHotkey('mod+s', handleSave);   // Different library format
```

**Solution:**

```typescript
// src/lib/constants/shortcuts.ts

export const Shortcuts = {
  // Global
  SAVE: 'mod+s',
  SEARCH: 'mod+k',
  NEW: 'mod+n',
  HELP: 'mod+/',

  // Navigation
  GO_DASHBOARD: 'g d',
  GO_DEVICES: 'g v',
  GO_CONTENTS: 'g c',
  GO_PLAYLISTS: 'g p',
  GO_SCHEDULES: 'g s',
  GO_SETTINGS: 'g ,',

  // Table
  SELECT_ALL: 'mod+a',
  DELETE_SELECTED: 'del',
  REFRESH: 'r',
  ESCAPE: 'esc',

  // Modal
  CLOSE_MODAL: 'esc',
  CONFIRM: 'enter',
} as const;

export type ShortcutKey = typeof Shortcuts[keyof typeof Shortcuts];

// Shortcut descriptions untuk help modal
export const ShortcutDescriptions: Record<ShortcutKey, string> = {
  [Shortcuts.SAVE]: 'Save changes',
  [Shortcuts.SEARCH]: 'Open search',
  [Shortcuts.NEW]: 'Create new item',
  [Shortcuts.GO_DASHBOARD]: 'Go to Dashboard',
  [Shortcuts.GO_DEVICES]: 'Go to Devices',
  // ... etc
};
```

```typescript
// Usage
import { Shortcuts } from '@/lib/constants/shortcuts';

useHotkeys(Shortcuts.SAVE, handleSave);
useHotkeys(Shortcuts.GO_DEVICES, () => navigate(Routes.DEVICES));
```

---

### 17.14 API Response Shapes

**Problem:**
```typescript
// ❌ Response shape handling scattered & inconsistent
const data = response.data.data;  // Sometimes
const data = response.data;       // Other times
const total = response.data.total || response.data.meta.total;  // Confusion!
```

**Solution:**

```typescript
// src/lib/constants/apiShapes.ts

// Standard response shapes
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

// Response extractors
export const extractData = <T>(response: ApiResponse<T>): T => response.data;

export const extractPaginatedData = <T>(response: PaginatedResponse<T>) => ({
  items: response.data,
  ...response.pagination,
});
```

```typescript
// Usage
const response = await deviceApi.getDevices(filters);
const { items, total, page } = extractPaginatedData(response);
```

---

## 18. File Structure Summary

```
src/lib/constants/
├── index.ts                 # Re-export semua
├── statuses.ts              # 17.1 - Status/Enum registry
├── permissions.ts           # 17.2 - Permission codes
├── routes.ts                # 17.3 - Route paths
├── validation.ts            # 17.4 - Validation rules & file types
├── wsEvents.ts              # 17.5 - WebSocket events
├── tableColumns.ts          # 17.6 - Table column configs
├── messages.ts              # 17.7 - Toast/notification messages
├── errorCodes.ts            # 17.8 - API error codes
├── featureFlags.ts          # 17.9 - Feature flags
├── pagination.ts            # 17.10 - Pagination defaults
├── dateFormats.ts           # 17.11 - Date/time formats
├── designTokens.ts          # 17.12 - Colors, spacing, breakpoints
├── shortcuts.ts             # 17.13 - Keyboard shortcuts
└── apiShapes.ts             # 17.14 - API response shapes
```

```typescript
// src/lib/constants/index.ts
export * from './statuses';
export * from './permissions';
export * from './routes';
export * from './validation';
export * from './wsEvents';
export * from './tableColumns';
export * from './messages';
export * from './errorCodes';
export * from './featureFlags';
export * from './pagination';
export * from './dateFormats';
export * from './designTokens';
export * from './shortcuts';
export * from './apiShapes';
```

---

## 19. Backend Sync Structure

```
backend-python/shared/constants/
├── __init__.py
├── statuses.py              # DeviceStatus, ContentStatus, etc
├── permissions.py           # Permission codes
├── validation.py            # ValidationRules
├── ws_events.py             # WebSocket event names
├── error_codes.py           # Error codes
└── feature_flags.py         # Feature flags
```

---

## 20. Ringkasan Centralized Registries

| # | Registry | Frontend | Backend | Sync |
|---|----------|----------|---------|------|
| 17.1 | Status/Enum | `statuses.ts` | `statuses.py` | ✅ WAJIB |
| 17.2 | Permissions | `permissions.ts` | `permissions.py` | ✅ WAJIB |
| 17.3 | Routes | `routes.ts` | - | Frontend only |
| 17.4 | Validation | `validation.ts` | `validation.py` | ✅ WAJIB |
| 17.5 | WS Events | `wsEvents.ts` | `ws_events.py` | ✅ WAJIB |
| 17.6 | Table Columns | `tableColumns.ts` | - | Frontend only |
| 17.7 | Messages | `messages.ts` | - | Frontend only |
| 17.8 | Error Codes | `errorCodes.ts` | `error_codes.py` | ✅ WAJIB |
| 17.9 | Feature Flags | `featureFlags.ts` | `feature_flags.py` | ✅ WAJIB |
| 17.10 | Pagination | `pagination.ts` | `validation.py` | ✅ WAJIB |
| 17.11 | Date Formats | `dateFormats.ts` | - | Frontend only |
| 17.12 | Design Tokens | `designTokens.ts` | - | Frontend only |
| 17.13 | Shortcuts | `shortcuts.ts` | - | Frontend only |
| 17.14 | API Shapes | `apiShapes.ts` | - | Frontend only |

---

## 21. Rules

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  RULES CENTRALIZED REGISTRIES                                              ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  1. ❌ DILARANG hardcode nilai yang ada di registry                       ║
║  2. ✅ WAJIB import dari @/lib/constants                                  ║
║  3. ✅ WAJIB sync backend-frontend untuk registry yang shared             ║
║  4. ✅ WAJIB update registry saat ada perubahan, bukan file individual    ║
║  5. ✅ WAJIB tambahkan type untuk autocomplete & type-safety              ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

*Last Updated: 2025-12-08*
