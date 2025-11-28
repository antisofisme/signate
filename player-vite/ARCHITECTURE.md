# Player-Vite Architecture

## Overview

Player-vite adalah aplikasi digital signage player yang berjalan sebagai fullscreen kiosk. Didesain untuk:
- Browser desktop/mobile
- WebOS Smart TV (LG)
- Embedded displays

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Vite | Build tool & dev server |
| TypeScript | Type safety |
| video.js | Media playback (HLS support) |
| IndexedDB | Offline storage |
| WebSocket | Real-time communication |

## Directory Structure

```
player-vite/
├── src/
│   ├── main.ts              # Entry point
│   ├── shell/               # Registration & activation
│   │   ├── components/      # UI handlers
│   │   ├── services/        # Bootstrap, registration
│   │   └── ui/              # Activation screen
│   ├── player/              # Media playback
│   │   ├── components/      # Player UI, popups
│   │   └── services/        # Playback, heartbeat
│   └── shared/              # Shared utilities
│       ├── api/             # HTTP client
│       ├── commands/        # Remote control
│       ├── config/          # Configuration
│       ├── device/          # Device state
│       ├── events/          # Event bus
│       ├── logger/          # Structured logging
│       ├── models/          # Data types
│       ├── services/        # Cross-cutting services
│       ├── state/           # Player state
│       ├── storage/         # IndexedDB
│       ├── types/           # TypeScript types
│       ├── ui/              # Toast, Modal
│       ├── utils/           # Helpers
│       └── websocket/       # WebSocket client
├── public/                  # Static assets
├── index.html               # HTML entry
├── vite.config.ts           # Vite configuration
└── tsconfig.json            # TypeScript config
```

## Core Concepts

### 1. Shell-Player Separation

Dua context terpisah dengan concern berbeda:

**Shell Context** (sebelum aktivasi):
- Device registration
- 6-digit code display
- Activation polling
- Hard reset handling

**Player Context** (setelah aktivasi):
- Media playback
- Playlist management
- Heartbeat reporting
- Command processing
- Widget rendering

### 2. State Management

Menggunakan Singleton + EventBus (bukan Redux/Zustand):

```
SharedDeviceState ──► localStorage (persistent)
        │
        ▼
    PlayerState ──► Event-driven updates
        │
        ▼
   SharedEventBus ──► Component communication
```

**Alasan:**
- Lebih ringan untuk embedded devices
- Event-driven cocok untuk media player
- Minimal boilerplate

### 3. Offline-First Design

```
Online                    Offline
   │                         │
   ▼                         ▼
API Request ──────────► IndexedDB Cache
   │                         │
   ▼                         ▼
Fresh Data ◄──────────── Cached Data
   │                         │
   ▼                         ▼
Update Cache              Use Cache
```

### 4. Device Lifecycle

```
┌─────────────┐
│   Start     │
└──────┬──────┘
       ▼
┌─────────────┐    No device_id    ┌─────────────┐
│ Check State │ ─────────────────► │ Request Code│
└──────┬──────┘                    └──────┬──────┘
       │ Has device_id                    │
       ▼                                  ▼
┌─────────────┐                    ┌─────────────┐
│ Verify Token│                    │ Show Code   │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       ▼ Valid                            ▼ Poll
┌─────────────┐                    ┌─────────────┐
│   Player    │ ◄─────────────────│  Activated  │
└─────────────┘                    └─────────────┘
```

## API Integration

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/devices/request-code` | POST | Get registration code |
| `/api/v1/devices/check-activation/{code}` | GET | Poll activation status |
| `/api/v1/devices/{id}/heartbeat` | POST | Health check |
| `/api/v1/client/playlist/{id}` | GET | Get active playlist |
| `/api/v1/devices/{id}/commands` | GET | Fetch pending commands |
| `/api/v1/devices/{id}/logs` | POST | Send console logs |
| `/ws/device/{id}` | WS | Real-time channel |

### Authentication

Device menggunakan device token (bukan user JWT):
```
Authorization: Bearer <device_token>
```

Token disimpan di `localStorage.getItem('device_token')`.

## Caching Strategy

### IndexedDB Stores

| Store | Key | Purpose |
|-------|-----|---------|
| devices | device_id | Device info |
| playlists | playlist_id | Playlist data |
| contents | content_id | Content metadata |
| media | url | Downloaded files |
| hls-segments | segment_url | Video chunks |
| analytics | timestamp | Buffered events |
| logs | timestamp | Console logs |
| settings | key | Preferences |

### Cache TTL

| Data Type | TTL |
|-----------|-----|
| API responses | 5 minutes |
| Playlist data | 1 hour |
| Media files | 24 hours |
| HLS segments | 24 hours |

## Build & Deploy

### Development

```bash
npm install
npm run dev
```

### Production Build

```bash
npm run build
```

Output: `dist/` folder

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | API URL or "auto" | auto |
| `VITE_WS_BASE_URL` | WebSocket URL | auto-detected |
| `VITE_HEARTBEAT_INTERVAL` | Heartbeat ms | 30000 |
| `VITE_LOG_SEND_INTERVAL` | Log flush ms | 30000 |
| `VITE_DEBUG_MODE` | Enable debug | false |

### WebOS Deployment

1. Build: `npm run build`
2. Copy `dist/` to `webos-app/`
3. Package: `ares-package webos-app/`
4. Install: `ares-install *.ipk`

## Performance Considerations

### Memory Management

- Cleanup Blob URLs after use: `URL.revokeObjectURL()`
- Remove event listeners on component unmount
- Limit IndexedDB store sizes
- HLS segment cleanup (24-hour policy)

### WebOS Constraints

- Target ES2015 (no ES2020+ features)
- Memory limit: ~256MB
- No native DevTools
- Limited IntersectionObserver support

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Blank screen | Token expired | Check localStorage, re-register |
| No playback | HLS not loaded | Check network, verify URLs |
| High memory | Blob leak | Ensure cleanup |
| WebSocket disconnect | Network issue | Auto-reconnect handles this |

### Debug Mode

Enable dengan:
```
localStorage.setItem('debug_mode', 'true');
```

Atau set `VITE_DEBUG_MODE=true` saat build.

## Design Decisions

Keputusan arsitektur kunci untuk menghindari konflik:

### 1. State Management: Singleton Emits Events

```
Component → Singleton.setState() → localStorage → EventBus.emit() → Listeners
```

- Singleton adalah **single source of truth**
- Components **CALL** Singleton methods untuk change state
- Components **LISTEN** to EventBus untuk receive notifications
- Components **NEVER** emit state events directly

### 2. Communication: Both HTTP & WebSocket (Complementary)

| Channel | Purpose |
|---------|---------|
| WebSocket | Commands, notifications, lightweight ping |
| HTTP Heartbeat | Detailed metrics, fallback health check |

Keduanya **complementary**, bukan redundant.

### 3. Context Transition: Hard Transition + Explicit Cleanup

```
Shell.cleanup() → [stop polling, remove listeners, clear timers]
          ↓
SharedResources → [WebSocket, DeviceState, EventBus persist]
          ↓
Player.init() → [start services, load playlist]
```

### 4. Storage: Split + Unified Clear

| Storage | Data |
|---------|------|
| localStorage | device_id, token, preferences |
| IndexedDB | playlists, contents, media, segments |

Hard reset HARUS clear keduanya dengan `clearAllStorage()`.

### 5. Cache: Version-Based Keys

```
Cache Key: {contentId}_{version}_{segmentIndex}

Content update → new version → old cache auto-ignored
```

### 6. Analytics: Client + Server Deduplication

- **Client**: UUID per event, status tracking, max 3 retries
- **Server**: Idempotent insert dengan event_id as unique key

## Related Documentation

- Claude Skill: `.claude/skills/player-integration/SKILL.md`
- Backend API: `backend-python/shared/api_routes.py`
- CMS Integration: `.claude/skills/core-services-integration/`
