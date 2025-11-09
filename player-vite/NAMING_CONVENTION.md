# Naming Convention Standard

**Project**: Player-Vite (Smart TV Digital Signage Player)
**Created**: 2025-11-08
**Status**: Official Standard

This document defines the official naming conventions for the player-vite codebase to ensure consistency, readability, and maintainability.

---

## 📁 File Naming

### General Rules
- **Format**: `kebab-case` (lowercase with hyphens)
- **Reason**: URL-friendly, case-insensitive filesystem safe, easy to read

| File Type | Convention | Example |
|-----------|------------|---------|
| TypeScript files | `kebab-case.ts` | `device-state.ts` |
| Component files | `kebab-case.tsx` | `activation-modal.tsx` |
| Type definitions | `kebab-case.types.ts` | `device.types.ts` |
| Test files | `kebab-case.test.ts` | `api-client.test.ts` |
| Config files | `kebab-case.ts` | `vite.config.ts` |
| Barrel exports | `index.ts` | `src/shared/api/index.ts` |

### Examples
```
✅ CORRECT:
device-state.ts
activation-modal.tsx
api-client.types.ts
device-state.test.ts

❌ WRONG:
DeviceState.ts        (PascalCase)
deviceState.ts        (camelCase)
device_state.ts       (snake_case)
```

---

## 💻 Code Naming

### 1. Classes & Constructors
- **Format**: `PascalCase`
- **Prefix**: Based on context (Shared/Shell/Player)

```typescript
// ✅ CORRECT
class SharedAPIClient { }
class ShellActivation { }
class PlayerCache { }

// ❌ WRONG
class sharedApiClient { }
class shell_activation { }
```

### 2. Interfaces & Type Aliases
- **Format**: `PascalCase`
- **NO PREFIX** (Modern TypeScript style)

```typescript
// ✅ CORRECT - Modern TypeScript (NO 'I' prefix)
interface Device {
  id: number;
  name: string;
}

interface DeviceConfig {
  apiUrl: string;
  timeout: number;
}

type DeviceStatus = 'pending' | 'active' | 'inactive';

// ❌ WRONG - Old convention
interface IDevice { }
interface IDeviceConfig { }
```

### 3. Functions & Methods
- **Format**: `camelCase`
- **Naming Pattern**: Verb-based, descriptive

```typescript
// ✅ CORRECT
function getDeviceId(): string { }
function setDeviceStatus(status: string): void { }
function isActivated(): boolean { }
function hasDeviceToken(): boolean { }
function handleError(error: Error): void { }
function fetchDeviceData(): Promise<Device> { }

// ❌ WRONG
function GetDeviceId() { }      // PascalCase
function device_id() { }        // snake_case
```

#### Common Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| `get*` | Retrieve value | `getDeviceId()` |
| `set*` | Set value | `setDeviceStatus()` |
| `is*` | Boolean check | `isActivated()` |
| `has*` | Check existence | `hasDeviceToken()` |
| `on*` | Event handler | `onActivated()` |
| `handle*` | Handle event/action | `handleError()` |
| `fetch*` | Async data retrieval | `fetchDeviceData()` |
| `update*` | Modify existing | `updateDeviceStatus()` |
| `create*` | Create new | `createDevice()` |
| `delete*` | Remove | `deleteDevice()` |

### 4. Variables
- **Format**: `camelCase`

```typescript
// ✅ CORRECT
const deviceId = 123;
const isActivated = true;
const deviceConfig = { ... };

// ❌ WRONG
const DeviceId = 123;           // PascalCase
const device_id = 123;          // snake_case
```

### 5. Constants
- **Format**: `UPPER_SNAKE_CASE`
- **Usage**: Truly constant values only

```typescript
// ✅ CORRECT
const MAX_RETRY_COUNT = 20;
const API_BASE_URL = 'http://192.168.5.12:8001';
const HEARTBEAT_INTERVAL = 30000;

// ❌ WRONG
const maxRetryCount = 20;       // camelCase (use for variables)
const Max_Retry_Count = 20;     // Mixed case
```

### 6. Enums
- **Format**: `PascalCase` for enum name, `PascalCase` for members

```typescript
// ✅ CORRECT
enum DeviceStatus {
  Pending = 'pending',
  Active = 'active',
  Inactive = 'inactive'
}

// ❌ WRONG
enum deviceStatus { }           // camelCase
enum DEVICE_STATUS { }          // UPPER_SNAKE_CASE
```

---

## 🏗️ Namespace & Context Prefixes

### Purpose
- Clear separation of concerns
- Easy identification of scope
- Avoid naming conflicts

| Context | Prefix | Usage | Example |
|---------|--------|-------|---------|
| **Shared** | `Shared` | Used in both shell & player | `SharedAPIClient` |
| **Shell** | `Shell` | Activation/registration context | `ShellActivation` |
| **Player** | `Player` | Video playback context | `PlayerCache` |

### Examples

```typescript
// Shared utilities (both contexts)
class SharedAPIClient { }
class SharedDeviceState { }
class SharedLogger { }

// Shell context (activation)
class ShellActivation { }
class ShellRegistration { }
class ShellInit { }

// Player context (playback)
class PlayerHLS { }
class PlayerCache { }
class PlayerSync { }
```

---

## 🌐 API Endpoint Naming

### Pattern
- Mirror backend-python `shared/api_routes.py`
- Centralized in `src/shared/api/routes.ts`
- Use object structure, NOT classes

```typescript
// ✅ CORRECT - Mirror backend-python structure
export const ApiRoutes = {
  Auth: {
    BASE: '/api/v1/auth',
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
    REGISTER: '/api/v1/auth/register',
  },

  Device: {
    BASE: '/api/v1/devices',
    REQUEST_CODE: '/api/devices/request-code',
    CHECK_ACTIVATION: (code: string) => `/api/devices/check-activation/${code}`,
    HEARTBEAT: (id: number) => `/api/v1/devices/${id}/heartbeat`,
    COMMANDS: (id: number) => `/api/v1/devices/${id}/commands`,
  },

  Content: {
    BASE: '/api/v1/contents',
    LIST: '/api/v1/contents',
    GET: (id: number) => `/api/v1/contents/${id}`,
  }
} as const;

// Usage
const url = ApiRoutes.Device.HEARTBEAT(123);
// Result: '/api/v1/devices/123/heartbeat'
```

---

## 📦 Import/Export Patterns

### Path Aliases
Use Vite path aliases for clean imports:

```typescript
// ✅ CORRECT - Using aliases
import { SharedAPIClient } from '@shared/api/client';
import { ShellActivation } from '@shell/services/activation-poll';
import { PlayerHLS } from '@player/services/hls-player';

// ❌ WRONG - Relative paths
import { SharedAPIClient } from '../../shared/api/client';
```

### Barrel Exports
Use `index.ts` for cleaner imports:

```typescript
// src/shared/api/index.ts
export { SharedAPIClient } from './client';
export { ApiRoutes } from './routes';
export type { ApiResponse, ApiError } from './client.types';

// Usage
import { SharedAPIClient, ApiRoutes } from '@shared/api';
```

---

## 📂 Directory Naming

### Rules
- **Format**: `kebab-case` (lowercase with hyphens)
- **Plural for collections**: Use plural for directories containing multiple items

```
✅ CORRECT:
src/
├── shared/
│   ├── api/
│   ├── components/      (plural - multiple components)
│   └── types/           (plural - multiple type files)
├── shell/
│   └── services/        (plural - multiple services)
└── player/
    └── components/      (plural - multiple components)

❌ WRONG:
src/
├── Shared/              (PascalCase)
├── shell_context/       (snake_case)
└── playerServices/      (camelCase)
```

---

## 🎨 Component Naming (TSX)

### File Naming
- **Format**: `kebab-case.tsx`

### Component Naming
- **Format**: `PascalCase`
- **Match file name** (converted to PascalCase)

```typescript
// File: activation-modal.tsx

// ✅ CORRECT
export function ActivationModal() {
  return <div>...</div>;
}

// ❌ WRONG
export function activationModal() { }   // camelCase
export function Activation_Modal() { }  // snake_case
```

---

## 🧪 Test File Naming

### Pattern
- Same name as file being tested
- Add `.test.ts` or `.spec.ts` suffix

```
device-state.ts
device-state.test.ts     ✅ CORRECT

deviceState.test.ts      ❌ WRONG (file is kebab-case)
device-state.spec.ts     ✅ ALSO OK
```

---

## 📝 Comments & Documentation

### JSDoc for Public APIs

```typescript
/**
 * Retrieve device ID from local storage
 *
 * @returns Device ID string or null if not found
 * @example
 * const id = getDeviceId();
 * if (id) console.log('Device ID:', id);
 */
export function getDeviceId(): string | null {
  return localStorage.getItem('device_id');
}
```

---

## ⚠️ Anti-Patterns to Avoid

### ❌ DON'T

```typescript
// Mixed naming styles
class deviceState { }              // Should be: DeviceState
function SetDeviceId() { }         // Should be: setDeviceId()
const Device_Id = 123;             // Should be: deviceId

// Hungarian notation
const strDeviceName = 'TV1';       // Should be: deviceName
const arrDevices = [];             // Should be: devices

// Ambiguous names
function doStuff() { }             // Too vague
const data = { ... };              // Too generic
const temp = 123;                  // Unclear purpose

// Abbreviations (unless very common)
function procDev() { }             // Should be: processDevice()
const usrCfg = { };                // Should be: userConfig
```

### ✅ DO

```typescript
// Clear, descriptive names
function processDevice(device: Device): void { }
const userConfiguration = { ... };

// Common abbreviations are OK
const apiClient = new APIClient();
const urlPath = '/api/devices';
const htmlElement = document.getElementById('root');
```

---

## 🎯 Quick Reference

| What | Format | Example |
|------|--------|---------|
| **Files** | kebab-case | `device-state.ts` |
| **Classes** | PascalCase | `DeviceState` |
| **Interfaces** | PascalCase (no prefix) | `Device` |
| **Functions** | camelCase | `getDeviceId()` |
| **Variables** | camelCase | `deviceId` |
| **Constants** | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| **Directories** | kebab-case | `src/shared/api` |
| **Prefixes** | Shared/Shell/Player | `SharedAPIClient` |

---

## 🔄 Migration from Old Code

When migrating from `player-vanillajs`:

1. **Rename files**: `deviceState.js` → `device-state.ts`
2. **Keep class names**: `SharedDeviceState` stays the same
3. **Add types**: Convert to TypeScript with proper interfaces
4. **Update imports**: Use path aliases

---

## 📚 References

- [TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Backend-Python API Routes: `backend-python/shared/api_routes.py`

---

**Last Updated**: 2025-11-08
**Status**: ✅ Official Standard
**Applies To**: player-vite project
