---
name: player-integration
description: Ensure consistent development patterns for player-vite (digital signage player/viewer). Use when implementing player features, fixing player bugs, or integrating with backend APIs. Covers Shell-Player separation, state management, caching, WebSocket, and device lifecycle.
---

# Player-Vite Integration Guide

## Overview

This skill ensures consistent development in the player-vite codebase - a fullscreen kiosk application for digital signage displays. The player runs on browsers, WebOS TVs, and other embedded devices.

## When to Use This Skill

- Implementing new player features
- Fixing player bugs or issues
- Integrating with backend APIs
- Working with device lifecycle (registration, activation)
- Implementing offline/caching features
- Adding WebSocket functionality
- Creating widget renderers

---

## 1. Architecture Principles

### Shell-Player Separation Pattern

The player uses a **two-context architecture**:

| Context | Purpose | When Active |
|---------|---------|-------------|
| **Shell** | Device registration & activation | Before device is activated |
| **Player** | Media playback & monitoring | After device is activated |

```
src/
├── shell/           # Registration & activation context
│   ├── components/  # Activation UI, keyboard shortcuts
│   ├── services/    # Bootstrap, registration, polling
│   └── ui/          # Activation screen
├── player/          # Playback context
│   ├── components/  # Player UI, popups
│   └── services/    # Playback, heartbeat, commands
└── shared/          # Shared between both contexts
    ├── api/         # HTTP client
    ├── device/      # Device state
    ├── events/      # Event bus
    ├── state/       # Player state
    ├── storage/     # IndexedDB, caching
    ├── websocket/   # Real-time communication
    └── ui/          # Toast, Modal
```

### State Management (Singleton + EventBus)

Player does NOT use Redux/Zustand. Uses lightweight patterns:

| Pattern | File | Purpose |
|---------|------|---------|
| `SharedDeviceState` | `shared/device/SharedDeviceState.ts` | Persistent device data (localStorage) |
| `PlayerState` | `shared/state/PlayerState.ts` | Reactive playback state |
| `SharedEventBus` | `shared/events/SharedEventBus.ts` | Pub/Sub for component communication |

**Key Events:**
- `device:activated` - Device successfully activated
- `playlist:loaded` - Playlist data received
- `player:next` - Move to next content
- `player:content-ended` - Content finished playing
- `connection:online` / `connection:offline` - Network status

### Initialization Order (Critical!)

```
1. Console interceptor (FIRST - before SharedLogger import)
2. SharedLogger initialization
3. UI components (Toast first - others depend on it)
4. Version checker (auto-reload on new builds)
5. Connection logging
6. ShellBootstrap (device state loading)
7. Configure console interceptor with device ID
```

---

## 2. API Integration

### SharedAPIClient Usage

```typescript
// Location: shared/api/SharedAPIClient.ts
import { sharedApiClient } from '@shared/api/SharedAPIClient';

// GET request
const response = await sharedApiClient.get<PlaylistData>(`/api/v1/client/playlist/${deviceId}`);

// POST request
await sharedApiClient.post('/api/v1/devices/logs', { logs: logBuffer });
```

**Features:**
- Auto token injection from `localStorage.getItem('device_token')`
- Response envelope unwrapping (`{success, data, message}` -> `data`)
- Request timeout (configurable)
- Enhanced error handling

### Device Token vs User JWT

| Aspect | CMS (User) | Player (Device) |
|--------|------------|-----------------|
| Token Key | `auth-token` | `device_token` |
| Token Type | User JWT | Device JWT |
| Org Header | `X-Organization-Id` | Not needed (implicit) |
| Refresh | Via refresh token | Re-registration |

### WebSocket Patterns

```typescript
// Location: shared/websocket/SharedWebSocket.ts

// Connect
websocket.connect(deviceId);

// Listen for messages
websocket.on('COMMAND', (data) => {
  handleCommand(data);
});

// Send message
websocket.send({ type: 'PLAYER_STATE', data: { status: 'playing' } });
```

**Message Types:**
- `PING` / `PONG` - Connection health
- `AUTH` - Authentication
- `COMMAND` - Remote control commands
- `PLAYLIST_UPDATE` - Playlist changed
- `DEVICE_STATUS` - Status update

**Reliability Features:**
- Auto-reconnect with exponential backoff (max 10 attempts)
- Message queue for offline buffering (max 100)
- Ping-pong heartbeat (30s interval)

---

## 3. Caching & Offline

### Multi-Level Caching Strategy

```
Layer 1: API Response Cache (TTL-based, in-memory)
    ↓
Layer 2: IndexedDB (8 object stores)
    ↓
Layer 3: HLS Segment Cache (video chunks)
    ↓
Layer 4: Blob URL Generation (offline playback)
```

### IndexedDB Stores

| Store | Purpose | Key |
|-------|---------|-----|
| `devices` | Device info cache | device_id |
| `playlists` | Playlist data | playlist_id |
| `contents` | Content metadata | content_id |
| `media` | Downloaded media files | url |
| `hls-segments` | HLS video chunks | segment_url |
| `analytics` | Buffered analytics events | timestamp |
| `logs` | Buffered console logs | timestamp |
| `settings` | User preferences | key |

### Sync Strategy (Offline → Online)

Priority order when coming back online:
1. Send buffered analytics events
2. Send buffered logs
3. Check for playlist updates
4. Check for pending commands
5. Resume normal heartbeat

---

## 4. Device Lifecycle

### Registration Flow

```
1. Device opens player URL
2. ShellBootstrap checks localStorage for device_id
3. If no device_id → Request 6-digit code from backend
4. Display code on activation screen
5. User enters code in CMS to activate
6. Player polls /check-activation/{code} every 5 seconds
7. On activation → Store device_token, switch to Player context
```

### Activation Polling

```typescript
// Location: shell/services/activation-polling.ts
const pollInterval = 5000; // 5 seconds
const maxAttempts = 720;   // 1 hour max
```

### Hard Reset Flow

```
1. User presses Ctrl+Shift+R (or command from CMS)
2. Prompt for Organization PIN
3. Verify PIN with backend
4. Clear ALL localStorage
5. Clear ALL IndexedDB stores
6. Reload page → Back to registration
```

### Token Expiry Handling

When device token expires:
1. API returns 401 Unauthorized
2. Player shows "Session Expired" message
3. Clear device token from localStorage
4. Reload page → Re-registration flow

---

## 5. Widget System

### Widget Types

| Type | Renderer | Data Source |
|------|----------|-------------|
| `CLOCK` | ClockRenderer | System time |
| `WEATHER` | WeatherRenderer | Weather API |
| `CALENDAR` | CalendarRenderer | Calendar API |
| `TEXT` | TextRenderer | Static/scrolling text |
| `HTML` | HTMLRenderer | Custom HTML |

### Widget Configuration

```typescript
interface WidgetConfig {
  id: string;
  type: 'CLOCK' | 'WEATHER' | 'CALENDAR' | 'TEXT' | 'HTML';
  position: { x: number; y: number; width: number; height: number };
  zIndex: number;
  animation?: 'fade' | 'slide';
  config: Record<string, any>;  // Type-specific config
}
```

### Z-Index Management

- Content layer: z-index 0
- Widget base: z-index 100
- Each widget: 100 + position in array
- Toast: z-index 200000 (always on top)

---

## 6. Backend Integration Contracts

### Response Envelope Format

Backend returns standardized format:
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

Player's `SharedAPIClient` auto-unwraps to just `data`.

### Error Codes to Handle

| Code | Meaning | Player Action |
|------|---------|---------------|
| `DEVICE_NOT_FOUND` | Device deleted | Re-register |
| `DEVICE_NOT_ACTIVATED` | Pending activation | Show activation screen |
| `TOKEN_EXPIRED` | Session expired | Re-register |
| `ORGANIZATION_INACTIVE` | Org disabled | Show error message |
| `QUOTA_EXCEEDED` | Storage limit | Show warning |

### Heartbeat Response

Backend may include commands in heartbeat response:
```json
{
  "status": "ok",
  "server_time": "2025-01-01T00:00:00Z",
  "commands": [
    { "id": 1, "type": "REFRESH", "params": {} }
  ]
}
```

Player MUST process `commands` array if present.

### Content URL Resolution

All content URLs from backend use `PUBLIC_BASE_URL`:
- Videos: `https://api.domain.com/content/videos/{id}`
- HLS: `https://api.domain.com/content/hls/{path}/master.m3u8`
- Images: `https://api.domain.com/content/images/{id}`

Player should NOT hardcode URLs.

---

## 7. Analytics & Telemetry

### Required Event Types

| Event | When | Data |
|-------|------|------|
| `CONTENT_PLAYED` | Content starts | content_id, playlist_id |
| `CONTENT_COMPLETED` | Content ends | content_id, duration, actual_duration |
| `CONTENT_SKIPPED` | Content skipped | content_id, skipped_at_seconds |
| `PLAYLIST_LOADED` | Playlist received | playlist_id, content_count |
| `DEVICE_ONLINE` | Connection restored | - |
| `DEVICE_OFFLINE` | Connection lost | - |
| `COMMAND_EXECUTED` | Command processed | command_type, success, error? |

### Buffering Strategy

```typescript
// Buffer analytics when offline
const analyticsBuffer: AnalyticsEvent[] = [];
const MAX_BUFFER_SIZE = 1000;
const FLUSH_INTERVAL = 30000; // 30 seconds

// On flush
await sharedApiClient.post('/api/v1/analytics/batch', { events: analyticsBuffer });
```

---

## 8. Anti-Patterns

### DO NOT:

| Anti-Pattern | Risk | Correct Approach |
|--------------|------|------------------|
| Hardcode API URLs | Deploy failure | Use `getSmartApiUrl()` |
| Store tokens in memory only | Lost on refresh | Use localStorage |
| Skip error handling in async | Silent failures | Always try-catch |
| Create Blob URLs without cleanup | Memory leak | Call `URL.revokeObjectURL()` |
| Add event listeners without cleanup | Memory leak | Store and remove in cleanup |
| Use modern JS features (ES2020+) | WebOS failure | Target ES2015 |
| Ignore IndexedDB errors | Data loss | Handle quota exceeded |
| Poll without backoff | Server overload | Exponential backoff |

### Common Mistakes

1. **Forgetting to handle offline state**
   - Always check `navigator.onLine` before API calls
   - Queue actions for later if offline

2. **Not updating device state atomically**
   - Use `SharedDeviceState.markAsActivated()` not individual sets

3. **Mixing Shell and Player concerns**
   - Registration logic stays in Shell
   - Playback logic stays in Player

---

## 9. Key File References

### Core Files to Understand

| File | Purpose |
|------|---------|
| `shared/device/SharedDeviceState.ts` | Device state management |
| `shared/state/PlayerState.ts` | Playback state |
| `shared/events/SharedEventBus.ts` | Event pub/sub |
| `shared/api/SharedAPIClient.ts` | HTTP client |
| `shared/websocket/SharedWebSocket.ts` | WebSocket client |
| `shared/storage/SharedStorage.ts` | IndexedDB wrapper |
| `shell/services/ShellBootstrap.ts` | App initialization |
| `player/services/PlaybackService.ts` | Media playback |
| `player/services/HeartbeatService.ts` | Health reporting |

### Configuration Files

| File | Purpose |
|------|---------|
| `shared/config/AppConfig.ts` | Runtime configuration |
| `.env` | Environment variables |
| `vite.config.ts` | Build configuration |

---

## 10. Conflict Resolution Patterns

Keputusan arsitektur untuk menghindari konflik:

### State Management: Singleton Emits Events

```
Component → Singleton.setState() → localStorage → EventBus.emit() → Listeners
```

- Singleton adalah **single source of truth**
- Components **CALL** Singleton methods untuk change state
- Components **LISTEN** to EventBus untuk receive notifications
- Components **NEVER** emit state events directly

### Communication: Keep Both HTTP & WebSocket

| Channel | Purpose |
|---------|---------|
| WebSocket | Commands, notifications, lightweight ping |
| HTTP Heartbeat | Detailed metrics, fallback health check |

Ini **complementary**, bukan redundant.

### Context Transition: Hard Transition + Explicit Cleanup

```
Shell.cleanup() → [stop polling, remove listeners, clear timers]
          ↓
SharedResources → [WebSocket, DeviceState, EventBus persist]
          ↓
Player.init() → [start services, load playlist]
```

### Storage: Split + Unified Clear

| Storage | Data |
|---------|------|
| localStorage | device_id, token, preferences |
| IndexedDB | playlists, contents, media, segments |

Hard reset HARUS clear keduanya dengan `clearAllStorage()`.

### Cache: Version-Based Keys

```
Cache Key: {contentId}_{version}_{segmentIndex}
```

Content update → new version → old cache auto-ignored.

### Analytics: Client + Server Deduplication

- Client: UUID per event, status tracking, max 3 retries
- Server: Idempotent insert dengan event_id

---

## Quick Checklist

Before submitting player changes:

- [ ] Shell/Player separation maintained?
- [ ] Using SharedDeviceState for device data?
- [ ] Using SharedEventBus for events?
- [ ] API calls use SharedAPIClient?
- [ ] Errors properly handled?
- [ ] Offline scenario considered?
- [ ] Memory cleanup for Blobs/listeners?
- [ ] ES2015 compatible (for WebOS)?
- [ ] Analytics events tracked?
- [ ] No hardcoded URLs?
