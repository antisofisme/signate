# WebOS Viewer - Smart TV Digital Signage

Static HTML/JS viewer specifically designed for LG WebOS Smart TVs. Uses UUID-based persistent device identity for seamless activation.

## Architecture Role

**Display Client (WebOS TV)** - Displays content playlists on LG WebOS Smart TVs using:

- **UUID-based persistent identity** (no manual activation needed)
- **IndexedDB caching** for offline playback and bandwidth optimization
- **Direct file access** from Anthias (no proxy)
- **Automatic fullscreen** optimized for TV displays

## Tech Stack

- **Frontend**: Vanilla JavaScript ES6 modules
- **Caching**: IndexedDB for offline media storage
- **HTTP Server**: Python `http.server` or nginx (static files only)
- **Port**: 8081
- **Platform**: LG WebOS Smart TV (via hosted web app or IPK package)

## Differences from Browser Viewer

| Feature | Browser Viewer | WebOS Viewer |
|---------|---------------|--------------|
| **Activation** | 6-digit code | UUID-based automatic |
| **Port** | 8080 | 8081 |
| **Platform** | Any browser | WebOS TV only |
| **Registration** | Manual approval | Auto-registers on first run |
| **Storage** | localStorage | localStorage (persistent on TV) |

## Setup

### Option 1: Hosted Web App (Recommended)

1. Ensure HTTP server is running on port 8081
2. On WebOS TV, open browser
3. Navigate to `http://192.168.5.12:8081`
4. Add to Home Screen for easy access

### Option 2: IPK Package

See `../webos-app/README.md` for packaging and installation.

## UUID-Based Activation

### How It Works

1. **First run**: Viewer generates UUID (e.g., `550e8400-e29b-41d4-a716-446655440000`)
2. **Register**: Calls backend to register device with UUID
   ```javascript
   POST /api/devices/register
   {
     "device_uuid": "550e8400-e29b-41d4-a716-446655440000",
     "device_type": "webos"
   }
   ```
3. **Backend creates** device with status `active` (auto-approved for WebOS)
4. **Viewer stores** device_id in localStorage
5. **Subsequent runs**: Viewer uses stored device_id (no re-registration)

### Storage

```javascript
localStorage.setItem('device_uuid', uuid);
localStorage.setItem('device_id', deviceId);
```

**UUID persists** across TV reboots (unlike browser viewer which may clear localStorage).

## Content Playback

Identical to browser-viewer with cache-first architecture:

1. Backend API returns playlist with direct Anthias URLs
2. Viewer checks IndexedDB cache
3. Cache HIT → Play from cache
4. Cache MISS → Download from Anthias → Cache → Play

## Keyboard Shortcuts

Same as browser-viewer:

- `d` - Toggle debug overlay
- `f` - Toggle fullscreen (or use TV remote)
- `n` - Next content
- `r` - Reload playlist
- `c` - Clear cache

**Note**: Use WebOS TV remote for navigation and selection.

## Configuration

**File**: `js/config.js`

```javascript
export const API_BASE_URL = 'http://192.168.5.12:8001';
export const DB_NAME = 'SignageCache';
export const DB_VERSION = 2;
export const PRELOAD_TIME = 3000;
export const PLAYLIST_REFRESH_INTERVAL = 60000;
export const HEARTBEAT_INTERVAL = 30000;
```

## Development

### Start HTTP Server

```bash
cd webos-viewer
python3 -m http.server 8081
```

### Test on WebOS TV

1. Open WebOS TV browser
2. Navigate to `http://192.168.5.12:8081`
3. Check browser console (if available) or use debug overlay

### Module Cache Busting

When updating JavaScript modules, increment version in `index.html`:

```html
<script type="module">
  import { init } from './js/app.js?v=5';  // Increment this
  init();
</script>
```

## Production Deployment

### Nginx Configuration

```nginx
server {
    listen 8081;
    server_name 192.168.5.12;

    root /home/gzjbbk/signage/webos-viewer;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    add_header Access-Control-Allow-Origin *;
}
```

### WebOS App Package

For native WebOS app deployment, see `../webos-app/README.md`.

## Troubleshooting

### TV not registering

1. Check TV can access backend: Use TV browser to open `http://192.168.5.12:8001/docs`
2. Check network connectivity (same network as server)
3. Open debug overlay on TV (press `d` on keyboard or use remote)
4. Check localStorage: UUID should be present

### Content not displaying

1. Check Anthias CORS headers (same as browser-viewer)
2. Clear cache: Press `c` on keyboard
3. Check TV browser console (if available)

### Cache not working

WebOS TV browsers may have limitations on IndexedDB size. Monitor cache usage and clear periodically if needed.

## Sync to Server

```bash
sshpass -p 'Password@2021' scp -r webos-viewer/ gzjbbk@192.168.5.12:/home/gzjbbk/signage/
```

## Important Links

- Root README: `../README.md`
- Backend README: `../backend/README.md`
- Browser Viewer README: `../browser-viewer/README.md`
- WebOS App README: `../webos-app/README.md` (for IPK packaging)
