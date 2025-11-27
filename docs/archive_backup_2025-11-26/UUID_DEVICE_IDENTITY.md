# UUID-Based Device Identity System

Comprehensive guide to the permanent device identity system using UUID.

## 📋 Table of Contents

- [Overview](#overview)
- [Why UUID?](#why-uuid)
- [Architecture](#architecture)
- [Implementation Details](#implementation-details)
- [Database Schema](#database-schema)
- [API Changes](#api-changes)
- [Frontend Changes](#frontend-changes)
- [Migration Guide](#migration-guide)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The UUID-based device identity system provides **permanent device identification** that survives:
- ✅ IP address changes (DHCP)
- ✅ Network disconnections
- ✅ TV/Monitor restarts
- ✅ Browser cache clearing (uses localStorage)
- ✅ Firmware updates

## 🤔 Why UUID?

### Problem with Previous Approaches

| Method | Problem |
|--------|---------|
| **IP Address** | Changes with DHCP, can't identify device after reconnect |
| **MAC Address** | Not accessible in browser for security reasons |
| **Passphrase** | Can be forgotten, requires user input |
| **Activation Code** | Temporary (10 min expiry), changes on re-registration |

### UUID Solution

UUID (Universally Unique Identifier) v4 provides:
- 🔑 **Permanent**: Generated once, never changes
- 💾 **Persistent**: Stored in localStorage (survives restarts)
- 🌐 **Universal**: 128-bit unique identifier (collision probability ≈ 0)
- 🔒 **Secure**: No personal information, no MAC address exposure
- 📱 **Cross-platform**: Works on browser, WebOS, any platform

**UUID Format**: `550e8400-e29b-41d4-a716-446655440000` (36 characters)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitor/WebOS Device                      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  localStorage                                       │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  device_uuid: "550e8400-..."                 │  │    │
│  │  │  monitor_device_id: 30                       │  │    │
│  │  │  monitor_activation_code: "123456"           │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Viewer JavaScript (index.html)                    │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  getOrCreateDeviceUUID()                     │  │    │
│  │  │  getWebOSDeviceInfo()                        │  │    │
│  │  │  getDeviceInfo()                             │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│                    HTTP Requests                            │
│              (registration, heartbeat)                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  /api/devices/monitor/register                     │    │
│  │  - Accepts: device_uuid, platform, model_name     │    │
│  │  - Saves to database                              │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  /api/devices/heartbeat                            │    │
│  │  - Updates: device_uuid, platform metadata        │    │
│  │  - Tracks last_seen                               │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL Database (devices table)           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  device_uuid (VARCHAR(36), UNIQUE)                 │    │
│  │  platform (VARCHAR(20))                            │    │
│  │  model_name (VARCHAR(100))                         │    │
│  │  firmware_version (VARCHAR(50))                    │    │
│  │  + existing fields (id, name, status, etc.)       │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 💻 Implementation Details

### 1. UUID Generation (Viewer)

**Location**: `/browser-viewer/index.html`

```javascript
// Generate UUID v4 (RFC 4122 compliant)
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
```

**UUID v4 Format**:
- `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- Version: `4` (random UUID)
- Variant: `8`, `9`, `a`, or `b` (RFC 4122)

### 2. UUID Persistence (Viewer)

```javascript
// Get or create UUID (persists in localStorage)
function getOrCreateDeviceUUID() {
    let uuid = localStorage.getItem('device_uuid');
    if (!uuid) {
        uuid = generateUUID();
        localStorage.setItem('device_uuid', uuid);
        console.log('🆕 Generated new device UUID:', uuid);
    } else {
        console.log('✅ Using existing device UUID:', uuid);
    }
    return uuid;
}
```

**localStorage Persistence**:
- ✅ Survives browser restart
- ✅ Survives TV restart
- ✅ Survives app reload
- ⚠️ Cleared if user clears browser data (rare on TV)

### 3. WebOS Device Detection (Viewer)

```javascript
// Detect WebOS platform and get device info
function getWebOSDeviceInfo() {
    const info = {};

    if (typeof window.webOS !== 'undefined') {
        console.log('🖥️  Running on WebOS TV');

        if (window.webOS.deviceInfo) {
            info.platform = 'webOS';
            info.modelName = window.webOS.deviceInfo('modelName') || 'Unknown';
            info.firmwareVersion = window.webOS.deviceInfo('version') || 'Unknown';
            info.sdkVersion = window.webOS.deviceInfo('sdkVersion') || 'Unknown';
        }

        if (window.webOS.platform && window.webOS.platform.tv) {
            info.screenWidth = window.webOS.platform.tv.screenWidth || window.screen.width;
            info.screenHeight = window.webOS.platform.tv.screenHeight || window.screen.height;
        }
    } else {
        info.platform = 'browser';
        info.modelName = 'Browser';
    }

    return info;
}
```

**WebOS Platform API**:
- `window.webOS` - WebOS global object
- `window.webOS.deviceInfo()` - Device information
- `window.webOS.platform.tv` - TV-specific information

### 4. Device Registration (Viewer)

```javascript
async function registerMonitor() {
    const webOSInfo = getWebOSDeviceInfo();

    const response = await fetch(`${API_BASE_URL}/api/devices/monitor/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            activation_code: activationCode,
            device_name: `Monitor-${activationCode}`,
            device_uuid: deviceUUID,              // Permanent UUID
            platform: webOSInfo.platform || 'browser',
            model_name: webOSInfo.modelName || 'Unknown'
        })
    });
}
```

### 5. Heartbeat with UUID (Viewer)

```javascript
function getDeviceInfo() {
    const webOSInfo = getWebOSDeviceInfo();

    return {
        device_uuid: deviceUUID,                   // UUID
        platform: webOSInfo.platform || 'browser',
        model_name: webOSInfo.modelName || 'Unknown',
        firmware_version: webOSInfo.firmwareVersion || 'N/A',
        screen_width: window.screen.width,
        screen_height: window.screen.height,
        viewport_width: window.innerWidth,
        viewport_height: window.innerHeight,
        device_pixel_ratio: window.devicePixelRatio || 1,
        user_agent: navigator.userAgent,
        // ... connection info
    };
}

async function sendHeartbeat() {
    const deviceInfo = getDeviceInfo();

    await fetch(`${API_BASE_URL}/api/devices/heartbeat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            device_id: parseInt(deviceId),
            ...deviceInfo  // Includes UUID and all metadata
        })
    });
}
```

## 🗄️ Database Schema

### New Columns in `devices` Table

```sql
-- UUID and Platform fields
device_uuid          VARCHAR(36)   UNIQUE    -- Permanent device identifier
platform             VARCHAR(20)             -- 'webOS', 'browser', etc.
model_name           VARCHAR(100)            -- Device model (e.g., LG OLED55C1PUB)
firmware_version     VARCHAR(50)             -- WebOS firmware version

-- Indexes for performance
CREATE UNIQUE INDEX idx_devices_device_uuid ON devices(device_uuid) WHERE device_uuid IS NOT NULL;
CREATE INDEX idx_devices_platform ON devices(platform);
```

### Full Device Schema

```sql
CREATE TABLE devices (
    -- Primary identification
    id                    SERIAL PRIMARY KEY,
    device_type           VARCHAR(20) NOT NULL,
    device_name           VARCHAR(100) NOT NULL,

    -- TV devices
    ip_address            VARCHAR(45),
    passphrase            VARCHAR(50),

    -- Monitor devices
    unique_code           VARCHAR(20) UNIQUE,
    code_expires_at       TIMESTAMP,

    -- UUID and platform (NEW)
    device_uuid           VARCHAR(36) UNIQUE,
    platform              VARCHAR(20),
    model_name            VARCHAR(100),
    firmware_version      VARCHAR(50),

    -- Status
    status                VARCHAR(20) NOT NULL DEFAULT 'pending',
    last_seen             TIMESTAMP,

    -- Device information (from viewer)
    screen_width          INTEGER,
    screen_height         INTEGER,
    viewport_width        INTEGER,
    viewport_height       INTEGER,
    device_pixel_ratio    FLOAT,
    user_agent            TEXT,
    connection_type       VARCHAR(50),
    connection_speed      FLOAT,

    -- Timestamps
    created_at            TIMESTAMP DEFAULT NOW(),
    updated_at            TIMESTAMP DEFAULT NOW()
);
```

## 🔌 API Changes

### 1. Monitor Registration Endpoint

**Endpoint**: `POST /api/devices/monitor/register`

**Request Schema** (updated):
```json
{
  "activation_code": "123456",
  "device_name": "Monitor-123456",
  "device_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "webOS",
  "model_name": "LG OLED55C1PUB"
}
```

**Backend Implementation**:
```python
device = Device(
    device_type="monitor",
    device_name=device_data.device_name,
    unique_code=device_data.activation_code,
    code_expires_at=get_code_expiry(),
    device_uuid=device_data.device_uuid,      # NEW
    platform=device_data.platform,            # NEW
    model_name=device_data.model_name,        # NEW
    status="pending"
)
```

### 2. Heartbeat Endpoint

**Endpoint**: `POST /api/devices/heartbeat`

**Request Schema** (updated):
```json
{
  "device_id": 30,
  "device_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "webOS",
  "model_name": "LG OLED55C1PUB",
  "firmware_version": "6.0.0",
  "screen_width": 1920,
  "screen_height": 1080,
  "viewport_width": 1920,
  "viewport_height": 1080,
  "device_pixel_ratio": 1.0,
  "user_agent": "Mozilla/5.0 ...",
  "connection_type": "4g",
  "connection_speed": 10.5
}
```

**Backend Updates**:
```python
# Update UUID and platform info
if heartbeat_data.device_uuid is not None:
    device.device_uuid = heartbeat_data.device_uuid
if heartbeat_data.platform is not None:
    device.platform = heartbeat_data.platform
if heartbeat_data.model_name is not None:
    device.model_name = heartbeat_data.model_name
if heartbeat_data.firmware_version is not None:
    device.firmware_version = heartbeat_data.firmware_version
```

### 3. Device Response Schema

**Response** (updated):
```json
{
  "id": 30,
  "device_type": "monitor",
  "device_name": "Monitor-123456",
  "device_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "webOS",
  "model_name": "LG OLED55C1PUB",
  "firmware_version": "6.0.0",
  "status": "active",
  "last_seen": "2025-10-23T10:30:00",
  "screen_width": 1920,
  "screen_height": 1080,
  ...
}
```

## 🎨 Frontend Changes

### Web Admin Device Info Modal

**Location**: `/web-admin/src/pages/Devices.jsx`

**New Platform Information Section**:
```jsx
<div className="mb-6">
  <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
    🖥️ Platform Information
  </h3>
  <div className="space-y-3 bg-gray-50 rounded-lg p-4">
    <div className="flex items-center">
      <span className="w-48 font-medium text-gray-700">Device UUID:</span>
      <span className="text-gray-900 font-mono text-sm">
        {device.device_uuid || 'N/A'}
      </span>
    </div>
    <div className="flex items-center">
      <span className="w-48 font-medium text-gray-700">Platform:</span>
      <span className="text-gray-900">
        {device.platform ? (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            device.platform === 'webOS' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'
          }`}>
            {device.platform}
          </span>
        ) : 'N/A'}
      </span>
    </div>
    <div className="flex items-center">
      <span className="w-48 font-medium text-gray-700">Model Name:</span>
      <span className="text-gray-900">{device.model_name || 'N/A'}</span>
    </div>
    <div className="flex items-center">
      <span className="w-48 font-medium text-gray-700">Firmware Version:</span>
      <span className="text-gray-900">{device.firmware_version || 'N/A'}</span>
    </div>
  </div>
</div>
```

## 📚 Migration Guide

### Step 1: Apply Database Migration

```bash
# On server
docker exec -i signage-postgres psql -U signage_user -d signage_db < /path/to/add_uuid_and_platform_fields.sql
```

**Migration adds**:
- `device_uuid` column (VARCHAR(36), UNIQUE)
- `platform` column (VARCHAR(20))
- `model_name` column (VARCHAR(100))
- `firmware_version` column (VARCHAR(50))
- Indexes for performance

### Step 2: Deploy Updated Code

```bash
# Sync backend files
scp backend/app/models/device.py server:/path/to/backend/app/models/
scp backend/app/schemas/device.py server:/path/to/backend/app/schemas/
scp backend/app/api/devices.py server:/path/to/backend/app/api/

# Sync monitor viewer
scp browser-viewer/index.html server:/path/to/browser-viewer/

# Restart backend
docker restart signage-backend
```

### Step 3: Verify Migration

```bash
# Check database schema
docker exec signage-postgres psql -U signage_user -d signage_db -c "\d devices"

# Should show new columns:
# device_uuid | character varying(36)
# platform | character varying(20)
# model_name | character varying(100)
# firmware_version | character varying(50)
```

### Step 4: Existing Devices

**Existing devices** (registered before UUID system):
- ✅ Will continue working with `device_id`
- ⚠️ `device_uuid` will be `NULL` initially
- ✅ Will get UUID on next heartbeat (auto-populated)
- ✅ No action required - seamless migration

**New devices** (registered after UUID system):
- ✅ Get UUID immediately on registration
- ✅ UUID stored in localStorage
- ✅ Persistent across restarts

## 🧪 Testing

### 1. Test UUID Generation

**Browser Console**:
```javascript
// Check if UUID is generated
console.log(localStorage.getItem('device_uuid'));
// Expected: "550e8400-e29b-41d4-a716-446655440000"

// Generate new UUID (for testing)
localStorage.removeItem('device_uuid');
location.reload();
// New UUID should be generated
```

### 2. Test UUID Persistence

```bash
# Test 1: Browser restart
1. Open monitor viewer
2. Note UUID in console
3. Close browser
4. Open monitor viewer again
5. Verify same UUID

# Test 2: TV restart
1. Open WebOS app
2. Note UUID in logs
3. Restart TV
4. Launch app again
5. Verify same UUID

# Test 3: Network change
1. Device connected to network A (IP: 192.168.1.100)
2. Note UUID
3. Connect to network B (IP: 192.168.2.100)
4. Verify same UUID, different IP
```

### 3. Test WebOS Detection

**WebOS Device**:
```javascript
// Should detect WebOS
console.log(typeof window.webOS);
// Expected: "object"

// Should get model name
console.log(window.webOS.deviceInfo('modelName'));
// Expected: "LG OLED55C1PUB" (or your TV model)
```

**Browser**:
```javascript
// Should fallback to browser
console.log(typeof window.webOS);
// Expected: "undefined"

// Platform should be "browser"
```

### 4. Test Database Storage

```bash
# Check UUID in database
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "SELECT id, device_name, device_uuid, platform, model_name FROM devices WHERE device_type = 'monitor';"

# Expected output:
# id |    device_name    |              device_uuid              | platform |    model_name
# ----+-------------------+---------------------------------------+----------+-------------------
#  30 | Monitor-123456    | 550e8400-e29b-41d4-a716-446655440000 | webOS    | LG OLED55C1PUB
#  31 | Monitor-789012    | 6ba7b810-9dad-11d1-80b4-00c04fd430c8 | browser  | Browser
```

### 5. Test Web Admin Display

1. Open Web Admin → Devices
2. Click device info icon (ℹ️)
3. Verify "Platform Information" section shows:
   - Device UUID (36 characters)
   - Platform badge (webOS or browser)
   - Model Name
   - Firmware Version

## 🐛 Troubleshooting

### UUID Not Generated

**Symptom**: `device_uuid` is `null` in database

**Causes**:
1. Old viewer code (before UUID implementation)
2. localStorage disabled/blocked
3. JavaScript error preventing UUID generation

**Solution**:
```javascript
// Force UUID regeneration
localStorage.removeItem('device_uuid');
location.reload();
```

### UUID Changes on Restart

**Symptom**: Different UUID after TV restart

**Causes**:
1. localStorage cleared by system
2. Different browser/app instance
3. WebOS factory reset

**Solution**:
- UUIDs should persist unless localStorage is cleared
- If TV was factory reset, new UUID is expected (it's a "new" device)
- Check TV settings → Storage → Don't clear app data

### WebOS Info Not Detected

**Symptom**: `platform: "browser"` instead of `"webOS"`

**Causes**:
1. Running in browser instead of WebOS app
2. WebOS API not available
3. App not packaged as WebOS app

**Solution**:
```bash
# Verify WebOS app package
ares-package webos-app/
ares-install --device mytv build/com.signage.viewer_1.0.0_all.ipk
ares-launch --device mytv com.signage.viewer
```

### Backend Not Accepting UUID

**Symptom**: UUID not saved to database

**Causes**:
1. Backend not updated
2. Schema migration not applied
3. Container not restarted

**Solution**:
```bash
# 1. Verify schema
docker exec signage-postgres psql -U signage_user -d signage_db -c "\d devices"

# 2. Reapply migration
docker exec -i signage-postgres psql -U signage_user -d signage_db < migrations/add_uuid_and_platform_fields.sql

# 3. Restart backend
docker restart signage-backend

# 4. Check logs
docker logs signage-backend --tail 50
```

### UUID Duplicate Error

**Symptom**: `UNIQUE constraint failed: devices.device_uuid`

**Causes**:
1. Same localStorage used on multiple devices (unlikely)
2. UUID collision (extremely rare, probability ≈ 0)

**Solution**:
```javascript
// Force new UUID
localStorage.removeItem('device_uuid');
location.reload();
```

## 📊 Benefits Summary

| Benefit | Description |
|---------|-------------|
| **Persistent Identity** | Device keeps same identity across restarts, IP changes, network switches |
| **No User Input** | Automatic UUID generation, no passphrase or activation code needed |
| **Privacy** | No MAC address exposure, no personal information |
| **Cross-Platform** | Works on browser, WebOS TV, any platform with localStorage |
| **Scalability** | Unique across billions of devices (128-bit UUID) |
| **Debugging** | Easy to identify devices in logs and database |
| **Analytics** | Track device history, uptime, content consumption |

## 🔐 Security Considerations

### UUID Security

- ✅ **No MAC address leak**: UUID is randomly generated, not derived from hardware
- ✅ **No personal info**: UUID contains no user data
- ✅ **Non-guessable**: 128-bit random (2^128 possible values)
- ⚠️ **localStorage**: Accessible to JavaScript on same origin (not a security risk for this use case)

### Privacy

- UUID is device identifier, NOT user identifier
- No tracking across different apps/websites
- Stored only on device and backend database
- Can be cleared by user (localStorage clear)

## 📈 Future Enhancements

1. **UUID-based device lookup**: Allow devices to reconnect using UUID instead of device_id
2. **Device transfer**: Transfer content assignments to new device using UUID
3. **Device history**: Track device lifecycle using UUID
4. **Multi-device sync**: Sync settings across devices with same UUID (future)
5. **QR code pairing**: Generate QR code with UUID for easy pairing

## 🎯 Conclusion

The UUID-based device identity system provides **robust, permanent device identification** that solves the problem of dynamic IPs, network changes, and device restarts. It's:

- ✅ **Automatic** - No user intervention
- ✅ **Persistent** - Survives restarts and network changes
- ✅ **Secure** - No privacy concerns
- ✅ **Scalable** - Works for millions of devices
- ✅ **Cross-platform** - Browser and WebOS compatible

---

**System Status**: ✅ Fully Implemented
**Migration Status**: ✅ Complete
**Testing Status**: ⏳ Pending
**Documentation**: ✅ Complete
