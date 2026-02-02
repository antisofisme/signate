# Development Standards V3

> Standards #17+ untuk Centralized Registry dan Event-Driven Architecture

**Contents:**
- **#17** - Centralized Registries
- **#18** - Event/Message Schema Standard
- **#19** - File/Media Handling Standard

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
const total = response.data.total || response.data.meta.total_items;  // Confusion!
```

**Solution (standardized per DEVELOPMENT_STANDARDS.md Section 6.3):**

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
  meta: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
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
  ...response.meta,
});
```

```typescript
// Usage
const response = await deviceApi.getDevices(filters);
const { items, total_items, page, has_next } = extractPaginatedData(response);
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

## 18. Event/Message Schema Standard

> Standard untuk inter-module communication (Event-Driven Architecture)

### 18.1 Overview

**Problem:** Module-module berkomunikasi dengan format event yang berbeda-beda:

```python
# ❌ TANPA STANDARD - Format tidak konsisten
# Service A:
{"type": "room_charge", "amount": 100}

# Service B:
{"event_type": "RoomCharge", "total": 100}

# Service C:
{"name": "ROOM_CHARGED", "value": 100}
```

**Solution:** Standardized Event Schema yang selaras dengan Log Standard (#15):

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  EVENT SCHEMA - ALIGNED WITH LOG STANDARD                                  ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Log Standard (#15)           Event Standard (#18)                        ║
║  ─────────────────           ──────────────────────                       ║
║  timestamp (ISO8601)    ←→   timestamp (ISO8601)         ✅ Aligned       ║
║  service                ←→   source_service              ✅ Aligned       ║
║  tenant_id              ←→   tenant_id                   ✅ Aligned       ║
║  user_id                ←→   user_id                     ✅ Aligned       ║
║  correlation_id         ←→   correlation_id              ✅ Aligned       ║
║  data                   ←→   payload                     ✅ Similar       ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 18.2 Event Schema Structure

```typescript
// TypeScript Interface
interface DomainEvent<T = unknown> {
  // === HEADER ===
  event_id: string;              // UUID: "evt-550e8400-e29b-41d4-a716-446655440000"
  event_type: string;            // "{app}.{entity}.{action}.{version}"
  timestamp: string;             // ISO8601 UTC: "2025-12-09T10:30:00.123Z"

  // === SOURCE (aligned with Log Standard) ===
  source_service: string;        // "pms", "pos", "accounting"
  tenant_id: string;             // "org_123" (organization_id)
  user_id: number | null;        // User who triggered (null for system events)

  // === TRACING (aligned with Log Standard) ===
  correlation_id: string;        // Same as request correlation_id
  causation_id: string | null;   // Parent event_id (for event chains)

  // === PAYLOAD ===
  payload: T;                    // Event-specific data

  // === METADATA ===
  version: string;               // Schema version: "1.0"
  published_at: string;          // When published to queue
}
```

```python
# Python Pydantic Model
from pydantic import BaseModel, Field
from datetime import datetime
from typing import TypeVar, Generic, Optional
from uuid import uuid4

T = TypeVar('T')

class DomainEvent(BaseModel, Generic[T]):
    # Header
    event_id: str = Field(default_factory=lambda: f"evt-{uuid4()}")
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Source (aligned with Log Standard)
    source_service: str
    tenant_id: str
    user_id: Optional[int] = None

    # Tracing (aligned with Log Standard)
    correlation_id: str
    causation_id: Optional[str] = None

    # Payload
    payload: T

    # Metadata
    version: str = "1.0"
    published_at: Optional[datetime] = None
```

---

### 18.3 Event Type Naming Convention

**Format:** `{app}.{entity}.{action}.{version}`

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  EVENT TYPE NAMING                                                         ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  {Module}   = PMS, POS, Accounting, HRM, Inventory (PascalCase)          ║
║  {Entity}   = Reservation, Order, Journal, Employee, Stock (PascalCase)  ║
║  {Action}   = Created, Updated, Deleted, Approved, Posted, Voided       ║
║  {version}  = v1, v2 (untuk breaking changes)                             ║
║                                                                            ║
║  FORMAT: {Module}.{Entity}.{Action}.v{N} — ALL PascalCase, NO exceptions  ║
║                                                                            ║
║  Examples:                                                                 ║
║  • PMS.Reservation.Created.v1            (was: pms.reservation.created)   ║
║  • PMS.RoomCharge.Posted.v1              (was: pms.room_charge.posted)    ║
║  • POS.Order.Completed.v1                (was: pos.order.completed)       ║
║  • Accounting.Journal.Approved.v1        (was: accounting.journal.appr)   ║
║  • Accounting.Journal.Voided.v1          (was: accounting.journal.voided) ║
║  • HRM.Employee.Terminated.v1            (was: hrm.employee.terminated)   ║
║  • Inventory.Stock.Adjusted.v1           (was: inventory.stock.adjusted)  ║
║                                                                            ║
║  VALIDATION RULE (MANDATORY):                                             ║
║  ✅ Event name MUST match regex: ^[A-Z][a-z]+\\.[A-Z][a-z]+\\.[A-Z][a-z]+\\.v\\d+$ ║
║  ❌ MUST NOT use lowercase, underscores, hyphens (dots only)              ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

**Standard Actions:**

| Action | Kapan Digunakan |
|--------|-----------------|
| `created` | Entity baru dibuat |
| `updated` | Entity di-update |
| `deleted` | Entity di-soft delete |
| `approved` | Entity di-approve (workflow) |
| `rejected` | Entity di-reject (workflow) |
| `posted` | Transaction di-post ke ledger |
| `voided` | Transaction di-void |
| `completed` | Process selesai |
| `cancelled` | Process dibatalkan |
| `expired` | Entity expired |

---

### 18.4 Event Examples

#### 18.4.1 PMS → Accounting (Room Charge Posted)

```json
{
  "event_id": "evt-550e8400-e29b-41d4-a716-446655440000",
  "event_type": "PMS.RoomCharge.Posted.v1",
  "timestamp": "2025-12-09T10:30:00.123Z",

  "source_service": "pms",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 456,

  "correlation_id": "req-abc-123-def",
  "causation_id": null,

  "payload": {
    "charge_id": 789,
    "reservation_id": 101,
    "room_number": "101",
    "charge_type": "room_rate",
    "amount": 1500000,
    "currency": "IDR",
    "transaction_date": "2025-12-09"
  },

  "version": "1.0",
  "published_at": "2025-12-09T10:30:00.150Z"
}
```

#### 18.4.2 POS → Inventory (Order Completed)

```json
{
  "event_id": "evt-660e8400-e29b-41d4-a716-446655440001",
  "event_type": "pos.order.completed.v1",
  "timestamp": "2025-12-09T12:45:30.500Z",

  "source_service": "pos",
  "tenant_id": "org_123",
  "user_id": 789,

  "correlation_id": "req-xyz-456-ghi",
  "causation_id": null,

  "payload": {
    "order_id": 5001,
    "outlet_id": 10,
    "items": [
      {"product_id": 100, "quantity": 2, "unit_price": 50000},
      {"product_id": 101, "quantity": 1, "unit_price": 75000}
    ],
    "total_amount": 175000,
    "payment_method": "room_charge",
    "room_number": "101"
  },

  "version": "1.0",
  "published_at": "2025-12-09T12:45:30.520Z"
}
```

#### 18.4.3 Event Chain (Causation ID)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EVENT CHAIN EXAMPLE                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Guest checks out                                                         │
│     event_id: evt-001                                                        │
│     event_type: pms.checkout.completed.v1                                    │
│     causation_id: null                                                       │
│                    │                                                         │
│                    ▼                                                         │
│  2. Room charge posted to accounting                                         │
│     event_id: evt-002                                                        │
│     event_type: accounting.journal.posted.v1                                 │
│     causation_id: evt-001  ◄── Links to parent                              │
│                    │                                                         │
│                    ▼                                                         │
│  3. Invoice generated                                                        │
│     event_id: evt-003                                                        │
│     event_type: accounting.invoice.created.v1                                │
│     causation_id: evt-002  ◄── Links to parent                              │
│                                                                              │
│  Tracing: evt-003 → evt-002 → evt-001 (full chain)                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 18.5 Event Registry

Semua event types WAJIB didaftarkan di registry:

```typescript
// shared/constants/events.ts
export const EVENT_TYPES = {
  // PMS Events
  PMS: {
    RESERVATION: {
      CREATED: 'PMS.Reservation.Created.v1',
      UPDATED: 'PMS.Reservation.Updated.v1',
      CANCELLED: 'PMS.Reservation.Cancelled.v1',
      CHECKED_IN: 'PMS.Reservation.CheckedIn.v1',
      CHECKED_OUT: 'PMS.Reservation.CheckedOut.v1',
    },
    ROOM_CHARGE: {
      POSTED: 'PMS.RoomCharge.Posted.v1',
      VOIDED: 'PMS.RoomCharge.Voided.v1',
    },
  },

  // POS Events
  POS: {
    ORDER: {
      CREATED: 'POS.Order.Created.v1',
      COMPLETED: 'POS.Order.Completed.v1',
      CANCELLED: 'POS.Order.Cancelled.v1',
    },
  },

  // Accounting Events
  ACCOUNTING: {
    JOURNAL: {
      CREATED: 'Accounting.Journal.Created.v1',
      POSTED: 'Accounting.Journal.Posted.v1',
      APPROVED: 'Accounting.Journal.Approved.v1',
      VOIDED: 'Accounting.Journal.Voided.v1',
    },
    INVOICE: {
      CREATED: 'Accounting.Invoice.Created.v1',
      PAID: 'Accounting.Invoice.Paid.v1',
    },
  },

  // Inventory Events
  INVENTORY: {
    STOCK: {
      RECEIVED: 'Inventory.Stock.Received.v1',
      ISSUED: 'Inventory.Stock.Issued.v1',
      ADJUSTED: 'Inventory.Stock.Adjusted.v1',
    },
  },
} as const;

export type EventType = typeof EVENT_TYPES;
```

```python
# shared/constants/events.py
class EventTypes:
    class PMS:
        class RESERVATION:
            CREATED = "PMS.Reservation.Created.v1"
            UPDATED = "PMS.Reservation.Updated.v1"
            CANCELLED = "PMS.Reservation.Cancelled.v1"
            CHECKED_IN = "PMS.Reservation.CheckedIn.v1"
            CHECKED_OUT = "PMS.Reservation.CheckedOut.v1"

        class ROOM_CHARGE:
            POSTED = "PMS.RoomCharge.Posted.v1"
            VOIDED = "PMS.RoomCharge.Voided.v1"

    class POS:
        class ORDER:
            CREATED = "POS.Order.Created.v1"
            COMPLETED = "POS.Order.Completed.v1"
            CANCELLED = "POS.Order.Cancelled.v1"

    class ACCOUNTING:
        class JOURNAL:
            CREATED = "Accounting.Journal.Created.v1"
            POSTED = "Accounting.Journal.Posted.v1"
            APPROVED = "Accounting.Journal.Approved.v1"
            VOIDED = "Accounting.Journal.Voided.v1"
```

---

### 18.6 Event Publishing

```python
# shared/events/publisher.py
from shared.constants.events import EventTypes
from shared.events.schema import DomainEvent
import aio_pika
import json

class EventPublisher:
    def __init__(self, connection: aio_pika.Connection):
        self.connection = connection

    async def publish(
        self,
        event_type: str,
        payload: dict,
        tenant_id: str,
        user_id: int | None,
        correlation_id: str,
        causation_id: str | None = None
    ):
        event = DomainEvent(
            event_type=event_type,
            source_service=settings.SERVICE_NAME,
            tenant_id=tenant_id,
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            payload=payload
        )

        channel = await self.connection.channel()
        exchange = await channel.declare_exchange(
            "domain_events",
            aio_pika.ExchangeType.TOPIC
        )

        await exchange.publish(
            aio_pika.Message(
                body=event.json().encode(),
                content_type="application/json",
                headers={"event_type": event_type}
            ),
            routing_key=event_type
        )

# Usage
await publisher.publish(
    event_type=EventTypes.PMS.ROOM_CHARGE.POSTED,
    payload={"charge_id": 789, "amount": 1500000},
    tenant_id="org_123",
    user_id=456,
    correlation_id=get_correlation_id()
)
```

---

### 18.7 Event Consuming

```python
# services/accounting/events/handlers.py
from shared.events.schema import DomainEvent
from shared.constants.events import EventTypes

class AccountingEventHandler:
    @subscribe(EventTypes.PMS.ROOM_CHARGE.POSTED)
    async def handle_room_charge_posted(self, event: DomainEvent):
        """Create journal entry when room charge is posted"""

        # Log with same correlation_id for tracing
        logger.info(
            "Processing room charge",
            correlation_id=event.correlation_id,
            event_id=event.event_id
        )

        # Create journal entry
        journal = await self.journal_service.create_from_room_charge(
            charge_id=event.payload["charge_id"],
            amount=event.payload["amount"],
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.event_id  # Link to parent event
        )

        # Publish resulting event
        await self.publisher.publish(
            event_type=EventTypes.ACCOUNTING.JOURNAL.CREATED,
            payload={"journal_id": journal.id},
            tenant_id=event.tenant_id,
            user_id=event.user_id,
            correlation_id=event.correlation_id,
            causation_id=event.event_id
        )
```

---

### 18.8 Event Versioning

**Kapan Bump Version:**

| Change Type | Action | Example |
|-------------|--------|---------|
| Add optional field | No bump | Add `notes` field |
| Add required field | Bump v1 → v2 | Add `currency` required |
| Rename field | Bump v1 → v2 | `amount` → `total_amount` |
| Remove field | Bump v1 → v2 | Remove `legacy_id` |
| Change type | Bump v1 → v2 | `amount: string` → `amount: number` |

**Backward Compatibility:**

```python
# Consumer must handle multiple versions
@subscribe([
    EventTypes.PMS.ROOM_CHARGE.POSTED_V1,
    EventTypes.PMS.ROOM_CHARGE.POSTED_V2
])
async def handle_room_charge(self, event: DomainEvent):
    if event.version == "1.0":
        amount = event.payload["amount"]
    elif event.version == "2.0":
        amount = event.payload["total_amount"]  # Renamed in v2
```

---

### 18.9 Dead Letter & Retry

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  RETRY & DEAD LETTER STRATEGY                                              ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  1. Initial attempt                                                        ║
║     ↓ (fail)                                                               ║
║  2. Retry 1: after 1 second                                                ║
║     ↓ (fail)                                                               ║
║  3. Retry 2: after 5 seconds                                               ║
║     ↓ (fail)                                                               ║
║  4. Retry 3: after 30 seconds                                              ║
║     ↓ (fail)                                                               ║
║  5. Retry 4: after 2 minutes                                               ║
║     ↓ (fail)                                                               ║
║  6. Move to Dead Letter Queue (DLQ)                                        ║
║     → Alert to monitoring                                                  ║
║     → Manual intervention required                                         ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 18.10 Ringkasan Event Standard

| Aspect | Standard |
|--------|----------|
| **Schema** | DomainEvent with header, source, tracing, payload |
| **Naming** | `{app}.{entity}.{action}.{version}` |
| **Timestamp** | ISO8601 UTC (aligned with Log Standard) |
| **Tracing** | `correlation_id` + `causation_id` |
| **Registry** | All events in `shared/constants/events.ts` |
| **Versioning** | Semantic: bump on breaking changes |
| **Retry** | Exponential backoff, max 5 retries |
| **DLQ** | After 5 failed retries |

---

## 19. File/Media Handling Standard

> Standard untuk upload, processing, storage, dan delivery file/media

### 19.1 Overview

**Tech Stack:**
- **Storage**: Cloudflare R2 (S3-compatible)
- **CDN**: Cloudflare CDN
- **Processing**: Sharp (images), FFmpeg (videos)
- **Queue**: Celery untuk async processing

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  FILE HANDLING FLOW                                                        ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Client          Backend           Worker           Storage      CDN      ║
║    │                │                 │                │          │       ║
║    │ 1. Request     │                 │                │          │       ║
║    │   presigned    │                 │                │          │       ║
║    │   URL          │                 │                │          │       ║
║    │───────────────▶│                 │                │          │       ║
║    │                │                 │                │          │       ║
║    │◀───────────────│                 │                │          │       ║
║    │ 2. Presigned   │                 │                │          │       ║
║    │    URL         │                 │                │          │       ║
║    │                │                 │                │          │       ║
║    │ 3. Direct upload to R2          │                │          │       ║
║    │─────────────────────────────────────────────────▶│          │       ║
║    │                │                 │                │          │       ║
║    │ 4. Confirm     │                 │                │          │       ║
║    │   upload       │                 │                │          │       ║
║    │───────────────▶│                 │                │          │       ║
║    │                │ 5. Queue        │                │          │       ║
║    │                │   processing    │                │          │       ║
║    │                │────────────────▶│                │          │       ║
║    │                │                 │ 6. Process     │          │       ║
║    │                │                 │   (resize,     │          │       ║
║    │                │                 │   transcode)   │          │       ║
║    │                │                 │───────────────▶│          │       ║
║    │                │                 │                │          │       ║
║    │◀───────────────│◀────────────────│                │          │       ║
║    │ 7. Ready       │                 │                │          │       ║
║    │   (webhook/ws) │                 │                │          │       ║
║    │                │                 │                │          │       ║
║    │ 8. Access via CDN               │                │          │       ║
║    │◀────────────────────────────────────────────────────────────│       ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 19.2 Upload Flow

#### 19.2.1 Presigned URL (Recommended)

```python
# Backend: Generate presigned URL
from shared.storage import storage_client

@router.post("/upload/presign")
async def get_presigned_url(
    request: PresignRequest,
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    if request.content_type not in ALLOWED_MIME_TYPES[request.context]:
        raise HTTPException(400, "File type not allowed")

    # Validate file size
    max_size = MAX_FILE_SIZES[request.context]
    if request.file_size > max_size:
        raise HTTPException(400, f"File too large. Max: {max_size} bytes")

    # Generate path
    file_path = generate_file_path(
        tenant_id=current_user.organization_id,
        module=request.context,
        filename=request.filename
    )

    # Generate presigned URL (valid 15 minutes)
    presigned = storage_client.generate_presigned_url(
        method="PUT",
        key=file_path,
        content_type=request.content_type,
        expires_in=900
    )

    # Create pending record
    file_record = await file_repo.create(
        path=file_path,
        original_name=request.filename,
        content_type=request.content_type,
        size=request.file_size,
        status="pending",
        uploaded_by_id=current_user.id,
        organization_id=current_user.organization_id
    )

    return {
        "upload_url": presigned.url,
        "file_id": file_record.id,
        "expires_at": presigned.expires_at
    }
```

```typescript
// Frontend: Upload with presigned URL
async function uploadFile(file: File, context: string) {
  // 1. Get presigned URL
  const { upload_url, file_id } = await api.post('/upload/presign', {
    filename: file.name,
    content_type: file.type,
    file_size: file.size,
    context: context  // 'content', 'document', 'avatar'
  });

  // 2. Upload directly to R2
  await fetch(upload_url, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type
    }
  });

  // 3. Confirm upload
  const result = await api.post(`/upload/${file_id}/confirm`);

  return result;
}
```

#### 19.2.2 Chunked Upload (untuk file >50MB)

```typescript
// Frontend: Chunked upload untuk video besar
const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB chunks

async function uploadLargeFile(file: File, context: string) {
  // 1. Initialize multipart upload
  const { upload_id, file_id } = await api.post('/upload/multipart/init', {
    filename: file.name,
    content_type: file.type,
    file_size: file.size,
    context: context
  });

  // 2. Upload chunks
  const chunks = Math.ceil(file.size / CHUNK_SIZE);
  const parts: UploadPart[] = [];

  for (let i = 0; i < chunks; i++) {
    const start = i * CHUNK_SIZE;
    const end = Math.min(start + CHUNK_SIZE, file.size);
    const chunk = file.slice(start, end);

    // Get presigned URL for this part
    const { url } = await api.post('/upload/multipart/presign', {
      upload_id,
      part_number: i + 1
    });

    // Upload chunk
    const response = await fetch(url, {
      method: 'PUT',
      body: chunk
    });

    parts.push({
      part_number: i + 1,
      etag: response.headers.get('ETag')
    });

    // Report progress
    onProgress?.((i + 1) / chunks * 100);
  }

  // 3. Complete multipart upload
  await api.post('/upload/multipart/complete', {
    upload_id,
    file_id,
    parts
  });

  return { file_id };
}
```

---

### 19.3 File Validation

#### 19.3.1 MIME Type Registry

```typescript
// shared/constants/fileTypes.ts
export const ALLOWED_MIME_TYPES = {
  // Digital Signage Content
  content: [
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
    'video/mp4',
    'video/webm',
    'application/pdf',
  ],

  // User Avatar
  avatar: [
    'image/jpeg',
    'image/png',
    'image/webp',
  ],

  // Documents (invoices, reports)
  document: [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // xlsx
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // docx
  ],

  // Guest ID/Passport scan
  guest_document: [
    'image/jpeg',
    'image/png',
    'application/pdf',
  ],
} as const;

export const MAX_FILE_SIZES = {
  content: 500 * 1024 * 1024,      // 500MB (video)
  avatar: 5 * 1024 * 1024,          // 5MB
  document: 25 * 1024 * 1024,       // 25MB
  guest_document: 10 * 1024 * 1024, // 10MB
} as const;
```

```python
# shared/constants/file_types.py
ALLOWED_MIME_TYPES = {
    "content": [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "video/mp4",
        "video/webm",
        "application/pdf",
    ],
    "avatar": ["image/jpeg", "image/png", "image/webp"],
    "document": [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ],
    "guest_document": ["image/jpeg", "image/png", "application/pdf"],
}

MAX_FILE_SIZES = {
    "content": 500 * 1024 * 1024,       # 500MB
    "avatar": 5 * 1024 * 1024,           # 5MB
    "document": 25 * 1024 * 1024,        # 25MB
    "guest_document": 10 * 1024 * 1024,  # 10MB
}
```

#### 19.3.2 Validation Rules

```python
# shared/files/validator.py
import magic
from PIL import Image

class FileValidator:
    @staticmethod
    def validate_mime_type(file_path: str, expected_type: str) -> bool:
        """Validate actual MIME type (not just extension)"""
        actual_type = magic.from_file(file_path, mime=True)
        return actual_type == expected_type

    @staticmethod
    def validate_image_dimensions(
        file_path: str,
        min_width: int = 100,
        min_height: int = 100,
        max_width: int = 8000,
        max_height: int = 8000
    ) -> tuple[bool, str]:
        """Validate image dimensions"""
        with Image.open(file_path) as img:
            width, height = img.size

            if width < min_width or height < min_height:
                return False, f"Image too small. Min: {min_width}x{min_height}"

            if width > max_width or height > max_height:
                return False, f"Image too large. Max: {max_width}x{max_height}"

            return True, "OK"

    @staticmethod
    def validate_video_duration(
        file_path: str,
        max_duration_seconds: int = 300  # 5 minutes
    ) -> tuple[bool, str]:
        """Validate video duration"""
        import ffmpeg

        probe = ffmpeg.probe(file_path)
        duration = float(probe['format']['duration'])

        if duration > max_duration_seconds:
            return False, f"Video too long. Max: {max_duration_seconds}s"

        return True, "OK"
```

---

### 19.4 Image Processing

```python
# shared/files/image_processor.py
from PIL import Image
import io

class ImageProcessor:
    # Standard sizes for thumbnails
    SIZES = {
        "thumbnail": (150, 150),
        "small": (300, 300),
        "medium": (600, 600),
        "large": (1200, 1200),
        "original": None,  # Keep original
    }

    @staticmethod
    async def process_image(
        file_path: str,
        output_format: str = "webp",
        generate_sizes: list[str] = ["thumbnail", "medium", "original"]
    ) -> dict[str, str]:
        """Process image and generate variants"""

        results = {}

        with Image.open(file_path) as img:
            # Strip EXIF data (privacy)
            img_no_exif = Image.new(img.mode, img.size)
            img_no_exif.putdata(list(img.getdata()))

            for size_name in generate_sizes:
                size = ImageProcessor.SIZES[size_name]

                if size is None:
                    # Original size, just convert format
                    output = img_no_exif.copy()
                else:
                    # Resize with aspect ratio
                    output = img_no_exif.copy()
                    output.thumbnail(size, Image.Resampling.LANCZOS)

                # Save to buffer
                buffer = io.BytesIO()
                output.save(
                    buffer,
                    format=output_format.upper(),
                    quality=85,
                    optimize=True
                )
                buffer.seek(0)

                # Upload to storage
                output_path = f"{file_path.rsplit('.', 1)[0]}_{size_name}.{output_format}"
                await storage_client.upload(output_path, buffer)

                results[size_name] = output_path

        return results
```

---

### 19.5 Storage Structure

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  STORAGE PATH CONVENTION                                                   ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Pattern: /{tenant_id}/{module}/{year}/{month}/{uuid}.{ext}               ║
║                                                                            ║
║  Examples:                                                                 ║
║  • /org_123/content/2025/12/550e8400-e29b-41d4.webp                       ║
║  • /org_123/content/2025/12/550e8400-e29b-41d4_thumbnail.webp             ║
║  • /org_123/avatar/2025/12/660e8400-e29b-41d4.webp                        ║
║  • /org_123/document/2025/12/770e8400-e29b-41d4.pdf                       ║
║                                                                            ║
║  Public assets (shared across tenants):                                   ║
║  • /public/defaults/avatar.png                                            ║
║  • /public/templates/invoice.pdf                                          ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

```python
# shared/files/path_generator.py
from uuid import uuid4
from datetime import datetime

def generate_file_path(
    tenant_id: str,
    module: str,
    filename: str,
    variant: str | None = None
) -> str:
    """Generate storage path for file"""

    now = datetime.utcnow()
    file_id = str(uuid4())
    ext = filename.rsplit('.', 1)[-1].lower()

    # Convert to webp for images
    if ext in ['jpg', 'jpeg', 'png']:
        ext = 'webp'

    if variant:
        return f"{tenant_id}/{module}/{now.year}/{now.month:02d}/{file_id}_{variant}.{ext}"
    else:
        return f"{tenant_id}/{module}/{now.year}/{now.month:02d}/{file_id}.{ext}"
```

---

### 19.6 CDN & Caching

#### 19.6.1 Cache Headers

```python
# Cache-Control headers based on content type
CACHE_CONTROL = {
    # Static assets - long cache
    "image": "public, max-age=31536000, immutable",  # 1 year
    "video": "public, max-age=31536000, immutable",  # 1 year

    # Documents - shorter cache (might be updated)
    "document": "public, max-age=86400",  # 1 day

    # Private content - no cache
    "private": "private, no-cache, no-store",
}
```

#### 19.6.2 Signed URLs for Private Content

```python
# shared/files/url_generator.py
from datetime import datetime, timedelta
import hmac
import hashlib

class URLGenerator:
    @staticmethod
    def generate_signed_url(
        path: str,
        expires_in: int = 3600,  # 1 hour default
        tenant_id: str | None = None
    ) -> str:
        """Generate signed URL for private content"""

        expires_at = int((datetime.utcnow() + timedelta(seconds=expires_in)).timestamp())

        # Create signature
        message = f"{path}:{expires_at}:{tenant_id or ''}"
        signature = hmac.new(
            settings.CDN_SIGNING_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{settings.CDN_URL}/{path}?expires={expires_at}&sig={signature}"

    @staticmethod
    def generate_public_url(path: str) -> str:
        """Generate public CDN URL"""
        return f"{settings.CDN_URL}/{path}"
```

---

### 19.7 Database Schema

```sql
-- Files table
CREATE TABLE files (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,

    -- Organization
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- File info
    original_name VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,

    -- Variants (for images)
    variants JSONB DEFAULT '{}',
    -- Example: {"thumbnail": "path/thumb.webp", "medium": "path/medium.webp"}

    -- Processing
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    -- pending, processing, ready, failed
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    -- Example: {"width": 1920, "height": 1080, "duration": 120}

    -- Context (which module uses this)
    context VARCHAR(50) NOT NULL,
    -- content, avatar, document, guest_document

    -- Reference to parent entity (polymorphic)
    entity_type VARCHAR(50),
    entity_id INTEGER,

    -- Audit
    uploaded_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT chk_file_status CHECK (status IN ('pending', 'processing', 'ready', 'failed')),
    CONSTRAINT chk_file_context CHECK (context IN ('content', 'avatar', 'document', 'guest_document'))
);

-- Indexes
CREATE INDEX idx_files_organization ON files(organization_id);
CREATE INDEX idx_files_entity ON files(entity_type, entity_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_files_status ON files(status) WHERE status != 'ready';
CREATE UNIQUE INDEX idx_files_storage_path ON files(storage_path);
```

---

### 19.8 Cleanup & Orphan Detection

```python
# tasks/file_cleanup.py
from celery import shared_task

@shared_task
def cleanup_orphaned_files():
    """
    Find and mark files that are no longer referenced.
    Run daily via cron.
    """

    # Find files not referenced by any entity
    orphaned = await db.execute("""
        SELECT f.id, f.storage_path
        FROM files f
        WHERE f.entity_id IS NULL
          AND f.is_deleted = FALSE
          AND f.created_at < NOW() - INTERVAL '24 hours'
          AND f.status = 'ready'
    """)

    for file in orphaned:
        logger.info(f"Marking orphaned file: {file.storage_path}")
        await file_repo.soft_delete(file.id, system_user_id)

@shared_task
def purge_deleted_files():
    """
    Permanently delete files that were soft-deleted > 30 days ago.
    Run weekly via cron.
    """

    old_deleted = await db.execute("""
        SELECT id, storage_path
        FROM files
        WHERE is_deleted = TRUE
          AND deleted_at < NOW() - INTERVAL '30 days'
    """)

    for file in old_deleted:
        # Delete from storage
        await storage_client.delete(file.storage_path)

        # Delete variants
        for variant_path in file.variants.values():
            await storage_client.delete(variant_path)

        # Hard delete from database
        await db.execute("DELETE FROM files WHERE id = :id", {"id": file.id})

        logger.info(f"Purged file: {file.storage_path}")
```

---

### 19.9 Ringkasan File/Media Standard

| Aspect | Standard |
|--------|----------|
| **Upload Method** | Presigned URL (direct to R2) |
| **Large Files** | Chunked multipart (>50MB) |
| **Validation** | MIME type + size + dimensions |
| **Image Format** | Convert to WebP |
| **Image Variants** | thumbnail, medium, original |
| **Storage Path** | `/{tenant}/{module}/{year}/{month}/{uuid}.{ext}` |
| **CDN Cache** | 1 year for media, 1 day for docs |
| **Private Access** | Signed URLs (1 hour expiry) |
| **Cleanup** | Daily orphan check, 30-day purge |

---

*Last Updated: 2025-12-09*
