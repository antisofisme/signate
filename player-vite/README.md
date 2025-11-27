# Player Vite - Digital Signage Display Player

Display player untuk menampilkan content digital signage pada berbagai device (monitor, TV, browser).

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Build Tool | Vite | 5.x |
| Language | TypeScript | 5.x |
| Video Player | Video.js + HLS.js | Latest |
| Storage | IndexedDB | Native |
| Caching | Service Worker | Native |
| Real-time | WebSocket | Native |

## Architecture

Player menggunakan **Shell/Player dual-mode architecture**:

```
player-vite/
├── src/
│   ├── shell/                    # Shell Mode (before activation)
│   │   ├── index.ts              # Shell entry point
│   │   ├── components/           # Shell UI components
│   │   │   ├── shell-ui.ts       # Activation code display
│   │   │   ├── clear-cache-handler.ts
│   │   │   ├── hard-reset-handler.ts
│   │   │   ├── fullscreen-manager.ts
│   │   │   └── keyboard-shortcuts.ts
│   │   ├── services/             # Shell services
│   │   │   ├── shell-activation-poll.ts
│   │   │   ├── shell-connection-status.ts
│   │   │   ├── shell-device-controls.ts
│   │   │   └── shell-network-diagnostics.ts
│   │   └── types/
│   ├── player/                   # Player Mode (after activation)
│   │   ├── index.ts              # Player entry point
│   │   ├── components/           # Player UI components
│   │   │   ├── quality-selector.ts
│   │   │   ├── waiting-for-content.ts
│   │   │   ├── device-info-popup.ts
│   │   │   └── connection-log-popup.ts
│   │   ├── services/             # Player services
│   │   │   ├── player-heartbeat.ts
│   │   │   ├── player-media-cache.ts
│   │   │   ├── player-hls-cache.ts
│   │   │   ├── player-schedule-manager.ts
│   │   │   ├── player-playback-logger.ts
│   │   │   ├── player-background-audio.ts
│   │   │   ├── player-health-reporter.ts
│   │   │   └── player-command-executor.ts
│   │   └── types/
│   ├── shared/                   # Shared between Shell & Player
│   │   ├── api/                  # API client
│   │   ├── commands/             # Remote commands
│   │   │   ├── base-command.ts
│   │   │   ├── reboot-command.ts
│   │   │   ├── volume-command.ts
│   │   │   ├── brightness-command.ts
│   │   │   ├── screenshot-command.ts
│   │   │   └── info-command.ts
│   │   ├── config/               # Configuration
│   │   ├── device/               # Device state management
│   │   ├── events/               # Event bus
│   │   ├── logger/               # Logging
│   │   ├── models/               # Data models
│   │   │   ├── content.model.ts
│   │   │   ├── device.model.ts
│   │   │   ├── playlist.model.ts
│   │   │   ├── segment.model.ts
│   │   │   └── widget.model.ts
│   │   ├── services/             # Shared services
│   │   │   ├── device-info/      # Device info collector
│   │   │   ├── network-speed-test.ts
│   │   │   ├── template-processor.ts
│   │   │   ├── widget-renderer.ts
│   │   │   └── service-registry.ts
│   │   ├── state/                # Application state
│   │   ├── storage/              # IndexedDB & caching
│   │   │   ├── indexed-db-manager.ts
│   │   │   ├── device-config-storage.ts
│   │   │   ├── media-cache.types.ts
│   │   │   └── storage-schema.ts
│   │   ├── ui/                   # Shared UI components
│   │   │   ├── shared-toast.ts
│   │   │   ├── shared-modal.ts
│   │   │   └── shared-offline-handler.ts
│   │   ├── utils/                # Utility functions
│   │   │   ├── device-fingerprint.ts
│   │   │   ├── device-info.ts
│   │   │   ├── network-info.ts
│   │   │   ├── performance-info.ts
│   │   │   ├── error-handler.ts
│   │   │   └── command-reporter.ts
│   │   └── websocket/            # WebSocket client
│   │       └── shared-websocket.ts
├── public/                       # Static assets
└── dist/                         # Build output
```

## Operation Modes

### Shell Mode (Pre-Activation)
Ditampilkan saat device belum teraktivasi:
- Menampilkan 6-digit activation code
- Polling ke server untuk status aktivasi
- Connection status indicator
- Network diagnostics
- Clear cache & hard reset options

### Player Mode (Post-Activation)
Ditampilkan setelah device teraktivasi:
- Playback content (image/video)
- Playlist management
- Schedule-based playback
- Heartbeat ke server
- Remote command execution
- Offline mode dengan cached content

## Features

### Device Activation
- 6-digit activation code
- Server polling setiap 5 detik
- Auto-transition ke Player mode setelah aktivasi
- Device fingerprinting untuk identifikasi unik

### Content Playback
- Image display dengan configurable duration
- Video playback dengan Video.js
- HLS streaming support
- Background audio support
- Quality selector untuk video
- Smooth transitions antar content

### Offline Support
```
IndexedDB Storage:
├── playlists          # Cached playlist data
├── contents           # Cached content metadata
├── media-cache        # Cached media files (binary)
├── device-config      # Device configuration
└── playback-logs      # Offline playback logs
```

- Content di-cache ke IndexedDB
- Media files di-cache untuk offline playback
- Automatic sync saat online kembali
- Service Worker untuk HLS segment caching

### Media Cache
| Content Type | Storage | Format |
|--------------|---------|--------|
| Images | IndexedDB Blob | PNG, JPG, WebP |
| Videos | IndexedDB Blob | MP4, WebM |
| HLS Segments | Service Worker | .ts, .m3u8 |

### WebSocket Connection
Real-time communication dengan server:
- Device status updates
- Playlist changes
- Emergency alerts
- Remote commands
- Connection status monitoring

### Remote Commands
Commands yang dapat dikirim dari CMS:
| Command | Description |
|---------|-------------|
| `refresh` | Refresh content/playlist |
| `restart` | Restart player |
| `reboot` | Reboot device (if supported) |
| `clear-cache` | Clear all cached data |
| `volume` | Adjust volume |
| `brightness` | Adjust brightness |
| `screenshot` | Take screenshot |
| `info` | Get device info |

### Schedule Management
- Time-based content scheduling
- Weekly recurring schedules
- Priority-based content selection
- Default playlist fallback

### Health Reporting
Device health metrics sent to server:
- CPU usage
- Memory usage
- Storage usage
- Network status
- Playback status
- Error logs

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+F` | Toggle fullscreen |
| `Ctrl+Shift+D` | Show device info |
| `Ctrl+Shift+L` | Show connection log |
| `Ctrl+Shift+C` | Clear cache |
| `Ctrl+Shift+R` | Hard reset |

## Widget Support

Embedded widgets dalam content:
| Widget | Description |
|--------|-------------|
| `text` | Text overlay |
| `calendar` | Calendar/date display |
| `weather` | Weather information |
| `html` | Custom HTML embed |

## Heartbeat System

```
Device → Server (every 30 seconds):
{
  device_id: string,
  status: "playing" | "idle" | "error",
  current_content_id: number | null,
  playlist_id: number | null,
  network_status: "online" | "offline",
  metrics: {
    cpu_usage: number,
    memory_usage: number,
    storage_free: number
  }
}
```

## API Endpoints Used

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/devices/code/{code}` | Get device by activation code |
| POST | `/api/v1/devices/activate` | Activate device |
| POST | `/api/v1/devices/{id}/heartbeat` | Send heartbeat |
| GET | `/api/v1/devices/{id}/playlist` | Get assigned playlist |
| GET | `/api/v1/devices/{id}/schedule` | Get device schedule |
| POST | `/api/v1/devices/{id}/command/ack` | Acknowledge command |
| POST | `/api/v1/playback-logs` | Submit playback logs |

## Environment Variables

```env
# Backend API
VITE_API_URL=https://api.zhmhotels.online
VITE_API_VERSION=v1

# WebSocket
VITE_WS_URL=wss://api.zhmhotels.online

# Player Configuration
VITE_HEARTBEAT_INTERVAL=30000
VITE_POLL_INTERVAL=5000
VITE_DEFAULT_IMAGE_DURATION=10000
```

## Docker Deployment

```yaml
player:
  container_name: signage-player
  image: nginx:alpine
  ports:
    - 8080:80
  volumes:
    - ./player-vite/dist:/usr/share/nginx/html:ro
    - ./player-vite/nginx-full.conf:/etc/nginx/nginx.conf:ro
```

## Nginx Configuration

```nginx
server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;

  # SPA fallback
  location / {
    try_files $uri $uri/ /index.html;
  }

  # Cache static assets
  location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }

  # WebSocket proxy
  location /ws {
    proxy_pass http://signage-backend-python:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }

  # API proxy
  location /api {
    proxy_pass http://signage-backend-python:8000;
  }
}
```

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Build Output

```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js       # Main bundle
│   ├── index-[hash].css      # Styles
│   └── vendor-[hash].js      # Vendor chunks
├── sw.js                     # Service Worker
└── ...
```

## Platform Support

| Platform | Support | Notes |
|----------|---------|-------|
| Chrome/Edge | Full | Recommended |
| Firefox | Full | - |
| Safari | Partial | No Service Worker |
| WebOS TV | Full | Via IPK package |
| Android TV | Full | Via browser |
| Raspberry Pi | Full | Via Chromium |

## WebOS TV Packaging

WebOS TV menggunakan IPK package dari `webos-app/` folder:
```bash
# Build player
npm run build

# Package for WebOS
cd ../webos-app
./package.sh
```

Output: `signage-player_1.0.0_all.ipk`

## URLs

| Environment | URL |
|-------------|-----|
| Production | https://player.zhmhotels.online |
| Local | http://localhost:8080 |

## Offline Behavior

1. **Network disconnected**:
   - Continue playing cached content
   - Show offline indicator
   - Queue playback logs

2. **Network reconnected**:
   - Sync playback logs
   - Check for playlist updates
   - Download new content
   - Resume heartbeat

3. **No cached content**:
   - Show "Waiting for Content" screen
   - Retry connection periodically
