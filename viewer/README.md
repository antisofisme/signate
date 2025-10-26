# Viewer - Smart TV Digital Signage

Static HTML/JS viewer for standard web browsers and monitors. Designed for monitors connected to PCs, Raspberry Pi, or any device with a modern web browser. Also used as source for WebOS TV IPK builds.

## Architecture Role

**Display Client** - Displays content playlists on monitors using:

- **6-digit activation code** for device registration
- **IndexedDB caching** for offline playback and bandwidth optimization
- **Direct file access** from Anthias (no proxy)
- **Fullscreen mode** for kiosk-style display
- **Shell/Player separation** for stable core + updateable player

## Tech Stack

- **Frontend**: Plain JavaScript modules (window.ModuleName pattern)
- **Caching**: IndexedDB for offline media storage
- **Logging**: Real-time console interception & batch sending
- **HTTP Server**: Python `http.server` or nginx (static files only)
- **Port**: 8080

## Modular Architecture

### Shell (Stable Core)
```
index.html
js/shell/
├── config.js       - State management & configuration
├── logger.js       - Console interception & log sending
├── registration.js - Device registration & activation polling
├── heartbeat.js    - Keep-alive heartbeat loop
├── ui.js          - Activation UI & player iframe loading
└── init.js        - Main shell initialization
```

**Shell responsibilities:**
- Device registration (6-digit code)
- Device activation (polling & detection)
- Heartbeat (keep device online)
- Real-time logging (shell context)
- Load player in iframe

### Player (Updateable)
```
player.html
js/player/
├── config.js      - Player state management
├── logger.js      - Console interception (player context)
├── cache.js       - IndexedDB cache management
├── api.js         - Playlist fetching & updates
├── playback.js    - Image/video playback logic
├── ui.js          - Loading states & keyboard shortcuts
└── init.js        - Player initialization
```

**Player responsibilities:**
- Fetch playlist from backend
- Auto-sync cache (download new, delete old)
- Play content (image/video)
- Playlist refresh (every 60s)
- Real-time logging (player context)

**Benefits of separation:**
- Shell = stable, rarely updated
- Player = frequently updated without re-registration
- Isolated contexts prevent conflicts
- Easy debugging (separate logs)

## Setup

### 1. Ensure Backend API is Running

Backend must be accessible at `http://192.168.5.12:8001`.

Check: `curl http://192.168.5.12:8001/docs`

### 2. Start HTTP Server

```bash
cd viewer
python3 -m http.server 8080
```

### 3. Access Viewer

Open browser: **http://192.168.5.12:8080**

## Activation Flow

### 6-Digit Code Activation

1. Viewer generates random 6-digit code (e.g., `123456`)
2. Viewer calls backend to register device
3. Backend creates device with status `pending`
4. Viewer polls backend every 5 seconds
5. Admin approves device in web admin dashboard
6. Viewer detects activation and stores `device_id` in localStorage
7. Viewer starts playing content from playlist

**Reset activation**: Press `x` key to clear localStorage and get new code.

## Content Playback

### Cache-First Playback

**Architecture: Control Plane / Data Plane Separation**

1. Backend API returns playlist with direct Anthias URLs
2. Browser Viewer checks IndexedDB cache for each content item
3. Cache HIT: Play from blob URL (instant, no network)
4. Cache MISS: Download from Anthias + Save to IndexedDB + Play

**Benefits:**

- ✅ Fast playback after first download
- ✅ Offline mode support
- ✅ Bandwidth savings
- ✅ Smooth transitions

## Keyboard Shortcuts

### Shell (index.html)
- `s` - Toggle shell debug info
- `r` - Reload player iframe
- `c` - Clear device registration & reset

### Player (player.html iframe)
- `p` - Toggle player debug info
- `n` - Skip to next content
- `r` - Reload playlist

**Note:** Player shortcuts only work when focus is inside the iframe.

## Troubleshooting

### Content not displaying

1. Check console logs
2. Check Anthias CORS: `curl -I http://192.168.5.12:8000/screenly_assets/filename`
3. Clear cache: Press `c`

### Video playback error

MIME type issue. Press `c` to clear cache and re-download.

## Sync to Server

```bash
sshpass -p 'Password@2021' scp -r viewer/ gzjbbk@192.168.5.12:/home/gzjbbk/signage/
```

## Important Links

- Root README: `../README.md`
- Backend README: `../backend/README.md`
