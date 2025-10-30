# Viewer - Smart TV Digital Signage

Static HTML/JS viewer for standard web browsers and monitors. Designed for monitors connected to PCs, Raspberry Pi, or any device with a modern web browser. Also used as source for WebOS TV IPK builds.

## Architecture Role

**Display Client** - Displays content playlists on monitors using:

- **6-digit activation code** for device registration
- **Modern UI/UX** with dark theme and toast notifications
- **IndexedDB caching** for offline playback and bandwidth optimization
- **Direct file access** from Anthias (no proxy)
- **Fullscreen mode** for kiosk-style display
- **Shell/Player separation** for stable core + updateable player

## Tech Stack

- **Frontend**: Plain JavaScript modules (window.ModuleName pattern)
- **UI/UX**: Modern dark theme, Lucide SVG icons, toast notifications, modal dialogs
- **Caching**: IndexedDB for offline media storage
- **Logging**: Real-time console interception & batch sending
- **HTTP Server**: Python `http.server` or nginx (static files only)
- **Port**: 8080

## UI/UX Features

### Modern Design
- **Dark Theme**: Slate gradient background (`#0f172a → #334155`)
- **Glass Morphism**: Backdrop blur effects on cards and modals
- **Smooth Animations**: Slide-in/out transitions for notifications

### Toast Notification System
- **4 Variants**: Success (green), Error (red), Warning (orange), Info (blue)
- **Lucide Icons**: CheckCircle, XCircle, AlertTriangle, Info
- **Auto-dismiss**: 5-8 seconds based on severity
- **Manual Close**: X button on each toast
- **Position**: Bottom-right, stacks vertically

### Interactive Controls
- **WiFi Status Icon**: Top-left, shows online (green) / offline (red)
- **Fullscreen Toggle**: Top-right, hover to show
- **Hard Reset**: Top-right (below fullscreen), password protected via modal
- **Hover Area**: 150×150px top-right corner reveals control buttons

### Password Modal
- **Modern Design**: Backdrop blur, warning icon
- **Keyboard Support**: Enter to confirm, Escape to cancel
- **Security**: Password verification before hard reset

## UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  📶                                    [Hover Area 150×150] │
│  WiFi                                   ⛶ Fullscreen        │
│  (left)                                 ⚡ Hard Reset       │
│                                              (hover show)   │
│                                                             │
│              ┌─────────────────────────┐                    │
│              │  Activation Card        │                    │
│              │  ┌─────────────────┐    │                    │
│              │  │   123456        │    │                    │
│              │  └─────────────────┘    │                    │
│              │  ⏳ Waiting...          │                    │
│              └─────────────────────────┘                    │
│                                                             │
│                                         ┌─────────────────┐ │
│                                         │ 🔔 Toast 1      │ │
│                                         │ Success msg     │ │
│                                         └─────────────────┘ │
│                                         ┌─────────────────┐ │
│                                         │ 🔔 Toast 2      │ │
│                                         │ Error msg       │ │
│                                         └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Z-Index Layers:**
- Modal: 100000 (top-most)
- Control Buttons: 100000
- Toast Container: 99999
- WiFi Icon: 10001
- Shell Info: 9999
- Player Container: 100

## Modular Architecture

### Shell (Stable Core)
```
index.html
js/shell/
├── config.js              - State management & configuration
├── logger.js              - Console interception & log sending
├── registration.js        - Device registration with toast notifications
├── activation-poll.js     - Polling for activation status
├── heartbeat.js           - Keep-alive heartbeat loop
├── ui.js                  - Activation UI & player iframe loading
├── wifi-status.js         - WiFi icon online/offline indicator
├── network-diagnostics.js - Network diagnostics logging
├── display-settings.js    - Display rotation & volume settings
├── commands.js            - Remote command execution
├── device-controls.js     - Device control commands
└── init.js                - Main shell initialization
```

**Shell responsibilities:**
- Device registration (6-digit code)
- Device activation (polling & detection with toast feedback)
- Heartbeat (keep device online)
- Real-time logging (shell context)
- Toast notifications for user feedback
- Password-protected hard reset via modal
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

**Reset activation**:
1. Hover mouse to top-right corner (150×150px area)
2. Click Hard Reset button (⚡ icon)
3. Enter admin password in modal
4. Device will clear all data and re-register with new code

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
- `s` - Toggle shell debug info (device ID, status, heartbeat)
- `r` - Reload player iframe only (without clearing shell)
- `f` - Toggle fullscreen mode
- `Esc` - Exit fullscreen mode

### Player (player.html iframe)
- `p` - Toggle player debug info
- `n` - Skip to next content
- `r` - Reload playlist

**Note:** Player shortcuts only work when focus is inside the iframe.

## Interactive Controls

### Hover-to-Show Buttons (Top-Right Corner)
Move cursor to **150×150px area** at top-right to reveal:

**Normal Mode:**
- ⛶ **Enter Fullscreen** - Expand to fullscreen
- ⚡ **Hard Reset** - Reset device (password required)

**Fullscreen Mode:**
- ✕ **Exit Fullscreen** - Return to normal view
- ⚡ **Hard Reset** - Reset device (password required)

**Button Behavior:**
- Buttons **hidden by default**
- Appear **only on hover** in top-right area
- Disappear when cursor leaves area
- Z-index: 100000 (above toast notifications)

## Notification System

### Toast Messages

The viewer displays toast notifications for various events:

**Success (Green)** ✅
- Device activated successfully
- Connection established

**Error (Red)** ❌
- Connection failed to server
- Player failed to load
- Fullscreen API error
- Incorrect password

**Warning (Orange)** ⚠️
- Connection lost during operation
- Activation code expired
- Device code not found (404)

**Info (Blue)** ℹ️
- General information messages

**Toast Features:**
- Position: Bottom-right corner
- Stack vertically if multiple
- Auto-dismiss: 4-8 seconds
- Manual close: Click X button
- Z-index: 99999 (below control buttons)

## Troubleshooting

### Content not displaying

1. Check console logs (press `s` for shell debug, `p` for player debug)
2. Check WiFi icon (top-left): Green = online, Red = offline
3. Check Anthias CORS: `curl -I http://192.168.5.12:8000/screenly_assets/filename`
4. Hard reset device: Hover top-right → Click ⚡ → Enter password

### Connection errors

**Toast shows: "Connection Failed"**
1. Check backend API is running: `curl http://192.168.5.12:8001/docs`
2. Check network connectivity
3. Wait for auto-retry (10 seconds)

### Video playback error

1. Check MIME type in browser console
2. Hard reset to clear cache and re-download
3. Check Anthias file exists and is accessible

### Fullscreen not working

**Toast shows: "Fullscreen Not Supported"**
- Browser doesn't support Fullscreen API
- Try modern browser (Chrome, Firefox, Edge)

### Hard reset not working

1. Ensure correct password (default: `admin123`)
2. Check browser console for errors
3. Try keyboard shortcut instead: `Ctrl+Shift+R` to reload page

## Sync to Server

```bash
sshpass -p 'Password@2021' scp -r viewer/ gzjbbk@192.168.5.12:/home/gzjbbk/signage/
```

## Important Links

- Root README: `../README.md`
- Backend README: `../backend/README.md`
