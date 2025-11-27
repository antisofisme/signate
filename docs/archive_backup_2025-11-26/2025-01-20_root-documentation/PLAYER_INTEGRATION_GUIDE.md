# Player Integration Guide - Release Flows

**Target**: `player-vite/` codebase
**Backend**: ✅ Ready (all endpoints tested)
**Estimated Time**: 2-3 hours

---

## 🎯 Overview

Implement **TWO distinct release flows** in the player:

1. **CMS Release (Soft)**: Clear tokens, keep org_id → re-register to same org
2. **Hard Reset (Factory)**: Clear ALL data → re-register to global pending

---

## 📋 Implementation Checklist

### Phase 1: IndexedDB Device Config Store (1 hour)

- [ ] Create `deviceConfigStorage.ts` utility
- [ ] Implement `getDeviceConfig()` method
- [ ] Implement `setDeviceConfig()` method
- [ ] Implement `clearTokens()` method (CMS release)
- [ ] Implement `hardReset()` method (factory reset)
- [ ] Migrate existing device storage to new structure

### Phase 2: Heartbeat 403 Handler (30 min)

- [ ] Update heartbeat error handler
- [ ] Detect 403 status code
- [ ] Call `clearTokens()` (keep org_id)
- [ ] Trigger re-registration flow
- [ ] Show activation screen

### Phase 3: Hard Reset Dialog (1 hour)

- [ ] Create password input dialog component
- [ ] Implement password validation API call
- [ ] Call `/devices/{id}/hard-reset` endpoint
- [ ] Call `hardReset()` to clear ALL IndexedDB
- [ ] Reload application
- [ ] Show activation screen (no org_id)

### Phase 4: Update Request Code Logic (30 min)

- [ ] Check for org_id in device config
- [ ] Include org_id parameter if exists
- [ ] Omit org_id parameter if not exists

### Phase 5: Testing (1 hour)

- [ ] Test CMS release flow end-to-end
- [ ] Test hard reset flow end-to-end
- [ ] Verify IndexedDB state after each flow
- [ ] Test re-registration with/without org_id

---

## 🔧 Code Implementation

### 1. Device Config Storage (`player-vite/src/utils/deviceConfigStorage.ts`)

```typescript
/**
 * Device Configuration Storage
 * Manages persistent device configuration in IndexedDB
 */

interface DeviceConfig {
  organization_id: number | null;
  access_token: string | null;
  refresh_token: string | null;
  device_id: number | null;
  unique_code: string | null;
  token_expires_at: number | null;
}

const DB_NAME = 'signage_player';
const STORE_NAME = 'device_config';
const CONFIG_KEY = 'config';

class DeviceConfigStorage {
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME);
        }
      };
    });
  }

  async getDeviceConfig(): Promise<DeviceConfig> {
    await this.ensureDB();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(CONFIG_KEY);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const config = request.result || {
          organization_id: null,
          access_token: null,
          refresh_token: null,
          device_id: null,
          unique_code: null,
          token_expires_at: null,
        };
        resolve(config);
      };
    });
  }

  async setDeviceConfig(config: Partial<DeviceConfig>): Promise<void> {
    await this.ensureDB();

    const currentConfig = await this.getDeviceConfig();
    const updatedConfig = { ...currentConfig, ...config };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.put(updatedConfig, CONFIG_KEY);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  /**
   * Clear tokens but KEEP org_id
   * Used for CMS release (soft release)
   */
  async clearTokens(): Promise<void> {
    await this.setDeviceConfig({
      access_token: null,
      refresh_token: null,
      device_id: null,
      token_expires_at: null,
      // Note: organization_id is NOT cleared
    });

    console.log('[DeviceConfig] Tokens cleared, org_id preserved (CMS release)');
  }

  /**
   * Clear ALL device configuration
   * Used for hard reset (factory reset)
   */
  async hardReset(): Promise<void> {
    await this.setDeviceConfig({
      organization_id: null,
      access_token: null,
      refresh_token: null,
      device_id: null,
      unique_code: null,
      token_expires_at: null,
    });

    console.log('[DeviceConfig] ALL data cleared (hard reset)');
  }

  /**
   * Clear media cache
   */
  async clearMediaCache(): Promise<void> {
    await this.ensureDB();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['media_cache'], 'readwrite');
      const store = transaction.objectStore('media_cache');
      const request = store.clear();

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        console.log('[DeviceConfig] Media cache cleared');
        resolve();
      };
    });
  }

  private async ensureDB(): Promise<void> {
    if (!this.db) {
      await this.init();
    }
  }
}

export const deviceConfigStorage = new DeviceConfigStorage();
```

---

### 2. Heartbeat Service Update (`player-vite/src/services/HeartbeatService.ts`)

```typescript
import { SharedAPIClient } from './SharedAPIClient';
import { deviceConfigStorage } from '../utils/deviceConfigStorage';
import { registrationService } from './RegistrationService';

class HeartbeatService {
  private intervalId: number | null = null;

  async start() {
    // Send heartbeat every 30 seconds
    this.intervalId = window.setInterval(() => {
      this.sendHeartbeat();
    }, 30000);

    // Send first heartbeat immediately
    await this.sendHeartbeat();
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  async sendHeartbeat() {
    try {
      const config = await deviceConfigStorage.getDeviceConfig();

      if (!config.device_id) {
        console.warn('[Heartbeat] No device_id, skipping');
        return;
      }

      const response = await SharedAPIClient.post(
        `/api/v1/devices/${config.device_id}/heartbeat`,
        {
          unique_code: config.unique_code,
          screen_width: window.screen.width,
          screen_height: window.screen.height,
          viewport_width: window.innerWidth,
          viewport_height: window.innerHeight,
          device_pixel_ratio: window.devicePixelRatio,
          user_agent: navigator.userAgent,
        }
      );

      console.log('[Heartbeat] Success');
    } catch (error: any) {
      // Check if device has been released (403 error)
      if (error.response?.status === 403) {
        console.log('[Heartbeat] Device released (403) - triggering re-registration');
        await this.handleDeviceReleased();
      } else {
        console.error('[Heartbeat] Error:', error.message);
      }
    }
  }

  /**
   * Handle device released by CMS admin
   * Clear tokens but KEEP org_id
   */
  async handleDeviceReleased() {
    try {
      // Stop heartbeat
      this.stop();

      // Clear tokens but keep org_id (soft release)
      await deviceConfigStorage.clearTokens();

      // Clear media cache
      await deviceConfigStorage.clearMediaCache();

      // Request new activation code (will use org_id from IndexedDB)
      const activationCode = await registrationService.requestActivationCode();

      console.log(`[Heartbeat] Re-registration initiated - Code: ${activationCode}`);

      // Reload to show activation screen
      window.location.reload();
    } catch (error) {
      console.error('[Heartbeat] Failed to handle device released:', error);
    }
  }
}

export const heartbeatService = new HeartbeatService();
```

---

### 3. Hard Reset Dialog Component (`player-vite/src/components/HardResetDialog.tsx`)

```typescript
import React, { useState } from 'react';
import { SharedAPIClient } from '../services/SharedAPIClient';
import { deviceConfigStorage } from '../utils/deviceConfigStorage';

interface HardResetDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HardResetDialog: React.FC<HardResetDialogProps> = ({
  isOpen,
  onClose,
}) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleHardReset = async () => {
    try {
      setIsLoading(true);
      setError('');

      const config = await deviceConfigStorage.getDeviceConfig();

      if (!config.device_id) {
        setError('No device ID found');
        return;
      }

      // Step 1: Validate password with backend
      const validation = await SharedAPIClient.post(
        '/api/v1/devices/validate-reset-password',
        {
          password,
          device_id: config.device_id,
        }
      );

      if (!validation.valid) {
        setError('Incorrect password');
        return;
      }

      // Step 2: Call hard reset endpoint
      await SharedAPIClient.post(
        `/api/v1/devices/${config.device_id}/hard-reset`
      );

      // Step 3: Clear ALL IndexedDB (including org_id)
      await deviceConfigStorage.hardReset();

      // Step 4: Clear media cache
      await deviceConfigStorage.clearMediaCache();

      // Step 5: Reload (will request code WITHOUT org_id → global pending)
      console.log('[HardReset] Factory reset completed - reloading...');
      window.location.reload();
    } catch (error: any) {
      console.error('[HardReset] Error:', error);
      setError('Failed to reset device. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">Factory Reset</h2>

        <p className="text-gray-600 mb-4">
          This will completely reset the device and remove it from the current
          organization. Enter the reset password to continue.
        </p>

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter reset password"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-2"
          disabled={isLoading}
        />

        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

        <div className="flex gap-2">
          <button
            onClick={handleHardReset}
            disabled={isLoading || !password}
            className="flex-1 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 disabled:opacity-50"
          >
            {isLoading ? 'Resetting...' : 'Factory Reset'}
          </button>

          <button
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
```

---

### 4. Update Registration Service (`player-vite/src/services/RegistrationService.ts`)

```typescript
import { SharedAPIClient } from './SharedAPIClient';
import { deviceConfigStorage } from '../utils/deviceConfigStorage';

class RegistrationService {
  /**
   * Request activation code
   * If org_id exists in config, device will be assigned to that organization
   * If no org_id, device will go to global pending list
   */
  async requestActivationCode(): Promise<string> {
    try {
      // Check if we have org_id in IndexedDB
      const config = await deviceConfigStorage.getDeviceConfig();

      const params: any = {
        device_type: 'tv', // or 'monitor' - detect from device
      };

      // If org_id exists, include it (CMS release scenario)
      if (config.organization_id) {
        params.organization_id = config.organization_id;
        console.log(
          `[Registration] Requesting code WITH org_id: ${config.organization_id}`
        );
      } else {
        console.log('[Registration] Requesting code WITHOUT org_id (global pending)');
      }

      const response = await SharedAPIClient.post(
        '/api/v1/devices/request-code',
        params
      );

      const uniqueCode = response.unique_code;

      // Save unique_code to config
      await deviceConfigStorage.setDeviceConfig({
        unique_code: uniqueCode,
      });

      return uniqueCode;
    } catch (error) {
      console.error('[Registration] Failed to request code:', error);
      throw error;
    }
  }

  /**
   * Poll for activation status
   */
  async checkActivation(uniqueCode: string): Promise<any> {
    try {
      const response = await SharedAPIClient.get(
        `/api/v1/devices/check-activation/${uniqueCode}`
      );

      if (response.status === 'active') {
        // Save device config
        await deviceConfigStorage.setDeviceConfig({
          device_id: response.device_id,
          organization_id: response.organization_id,
          access_token: response.access_token,
          refresh_token: response.refresh_token,
          token_expires_at: response.token_expires_at,
        });

        console.log('[Registration] Device activated successfully');
      }

      return response;
    } catch (error) {
      console.error('[Registration] Check activation failed:', error);
      throw error;
    }
  }
}

export const registrationService = new RegistrationService();
```

---

### 5. Settings Page Integration (`player-vite/src/pages/SettingsPage.tsx`)

```typescript
import React, { useState } from 'react';
import { HardResetDialog } from '../components/HardResetDialog';

export const SettingsPage: React.FC = () => {
  const [showHardResetDialog, setShowHardResetDialog] = useState(false);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="space-y-4">
        {/* Other settings... */}

        <div className="border-t pt-4">
          <h2 className="text-lg font-semibold mb-2 text-red-600">
            Danger Zone
          </h2>

          <button
            onClick={() => setShowHardResetDialog(true)}
            className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600"
          >
            Factory Reset
          </button>

          <p className="text-sm text-gray-600 mt-2">
            This will completely reset the device and remove it from the
            current organization.
          </p>
        </div>
      </div>

      <HardResetDialog
        isOpen={showHardResetDialog}
        onClose={() => setShowHardResetDialog(false)}
      />
    </div>
  );
};
```

---

## 🧪 Testing Scenarios

### Scenario 1: CMS Release (Soft)

**Setup**:
1. Device is active in organization X
2. Player is running normally with heartbeat

**Test Steps**:
1. Admin clicks "Release" button in CMS
2. Wait for next heartbeat (max 30 seconds)
3. Player should detect 403 error
4. Player should show activation screen
5. Check IndexedDB - org_id should still exist

**Expected Result**:
- ✅ Activation screen shows
- ✅ Device in "pending" status
- ✅ Device appears in organization X pending list (not global)

---

### Scenario 2: Hard Reset (Factory)

**Setup**:
1. Device is active in organization X
2. Player is running normally

**Test Steps**:
1. User clicks "Factory Reset" in player settings
2. Enter reset password (correct: "admin123")
3. Confirm reset
4. Wait for reload
5. Check IndexedDB - ALL data should be cleared

**Expected Result**:
- ✅ Password validation works
- ✅ Device resets successfully
- ✅ Activation screen shows
- ✅ Device in "pending" status
- ✅ Device appears in GLOBAL pending list (not org X)
- ✅ IndexedDB completely empty

---

### Scenario 3: Wrong Password

**Setup**:
1. Device is active
2. User clicks "Factory Reset"

**Test Steps**:
1. Enter wrong password
2. Click "Factory Reset"

**Expected Result**:
- ✅ Error message: "Incorrect password"
- ✅ Device NOT reset
- ✅ Dialog stays open
- ✅ Player continues running normally

---

## 📊 IndexedDB State Comparison

### Before Implementation

```
IndexedDB: signage_player
  └── media_cache
      ├── token
      ├── device_id
      ├── unique_code
      ├── ...media files...
```

### After Implementation

```
IndexedDB: signage_player
  ├── device_config (NEW!)
  │   └── config: {
  │       organization_id: number | null,
  │       access_token: string | null,
  │       refresh_token: string | null,
  │       device_id: number | null,
  │       unique_code: string | null,
  │       token_expires_at: number | null
  │   }
  └── media_cache
      └── ...media files...
```

### After CMS Release (Soft)

```
device_config.config: {
  organization_id: 4,           // ✅ KEPT
  access_token: null,           // ❌ CLEARED
  refresh_token: null,          // ❌ CLEARED
  device_id: null,              // ❌ CLEARED
  unique_code: null,            // ❌ CLEARED
  token_expires_at: null        // ❌ CLEARED
}
```

### After Hard Reset (Factory)

```
device_config.config: {
  organization_id: null,        // ❌ CLEARED
  access_token: null,           // ❌ CLEARED
  refresh_token: null,          // ❌ CLEARED
  device_id: null,              // ❌ CLEARED
  unique_code: null,            // ❌ CLEARED
  token_expires_at: null        // ❌ CLEARED
}
```

---

## ⚠️ Important Notes

### Security Considerations

1. **Password Validation**: ALWAYS validate password on backend, NEVER client-side only
2. **Public Endpoints**: Hard reset endpoint is public (no auth) because device is being reset anyway
3. **Token Clearing**: Both flows clear tokens immediately

### UX Considerations

1. **Loading States**: Show loading indicator during reset process
2. **Error Handling**: Display clear error messages
3. **Confirmation Dialog**: Require user confirmation before hard reset
4. **Auto-reload**: Automatically reload after reset to show activation screen

### Performance

1. **IndexedDB**: Fast local storage, no performance impact
2. **Heartbeat**: Minimal overhead (30 second interval)
3. **Cache Clearing**: Clear media cache to free up space

---

## 🚀 Deployment Checklist

- [ ] Implement device config storage
- [ ] Update heartbeat service
- [ ] Create hard reset dialog
- [ ] Update registration service
- [ ] Add settings page button
- [ ] Test CMS release flow
- [ ] Test hard reset flow
- [ ] Verify IndexedDB state
- [ ] Test with WebOS device
- [ ] Test with monitor/browser
- [ ] Document player changes
- [ ] Commit and deploy

---

## 📚 References

- Backend API: `http://192.168.5.12:8001/docs`
- Implementation Complete: `RELEASE_FLOWS_IMPLEMENTATION_COMPLETE.md`
- Device Flow Documentation: `DEVICE_FLOW_DOCUMENTATION.md` (v2.0)
- Impact Analysis: `IMPACT_ANALYSIS_RELEASE_FLOWS.md`

---

**Ready to implement!** All backend endpoints are tested and working. 🎉
