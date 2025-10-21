# Smart TV Monitor Viewer

Browser-based digital signage content viewer for Smart TV monitors.

## Features

- **Activation System**: Generates 6-digit activation code for pairing with Web Admin
- **Auto-polling**: Checks activation status every 5 seconds
- **Content Display**: Supports both images and videos
- **Smooth Transitions**: 1-second fade between content items
- **Preloading**: Loads next content 3 seconds before current ends
- **Fullscreen Mode**: Automatically enters fullscreen on activation
- **Playlist Looping**: Continuously loops through assigned content

## Usage

### 1. Open Monitor Viewer

Simply open `index.html` in any modern browser:

```bash
# Option 1: Direct file open
firefox /mnt/g/khoirul/signate/monitor-viewer/index.html

# Option 2: Using file:// URL
file:///mnt/g/khoirul/signate/monitor-viewer/index.html

# Option 3: Serve with simple HTTP server (recommended)
cd /mnt/g/khoirul/signate/monitor-viewer
python3 -m http.server 8080
# Then open: http://localhost:8080
```

### 2. Activation Process

1. Monitor viewer will display a 6-digit activation code
2. Go to Web Admin → Devices
3. Find the monitor in the list (status: "pending")
4. Click "Activate" and the monitor will immediately start playing content

### 3. Content Assignment

Content is assigned to monitors through:
- **Direct assignment**: Assign content directly to specific monitor
- **Tag assignment**: Assign monitor to a tag, then assign content to that tag

### 4. Keyboard Shortcuts

- `d` - Toggle debug info overlay
- `f` - Toggle fullscreen mode
- `n` - Skip to next content (when activated)
- `r` - Reload playlist (when activated)

## API Endpoints Used

### Registration
```
POST /api/devices/monitor
Body: {
  "activation_code": "123456",
  "device_name": "Monitor-123456"
}
```

### Status Check
```
GET /api/devices/{device_id}
Returns: {
  "id": 1,
  "status": "pending" | "active",
  ...
}
```

### Playlist
```
GET /api/client/playlist?device_id={device_id}
Returns: [
  {
    "id": 1,
    "content_type": "image",
    "duration": 10,
    ...
  }
]
```

### Content Serving
```
GET /api/content/{content_id}/image
Returns: Image/video file with correct Content-Type
```

## Configuration

Edit `index.html` to change settings:

```javascript
const API_BASE_URL = 'http://192.168.5.12:8001';  // Backend API URL
const POLL_INTERVAL = 5000;   // Polling interval (ms)
const PRELOAD_TIME = 3000;    // Preload time before content ends (ms)
```

## Troubleshooting

### Monitor doesn't register
- Check if backend API is accessible at `http://192.168.5.12:8001`
- Check browser console for errors (F12 → Console)
- Ensure CORS is enabled on backend

### Content doesn't display
- Check if monitor is activated (status: "active")
- Verify content is assigned to monitor or its tag
- Check content URLs in debug mode (press `d`)
- Verify backend content proxy endpoint is working

### Playlist doesn't loop
- Check if playlist has content assigned
- Refresh playlist with `r` key
- Check backend playlist endpoint response

## Debug Mode

Press `d` to toggle debug overlay showing:
- Device ID
- Current status
- Playlist item count
- Current content index
- Next content change time

## Browser Compatibility

Tested on:
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- WebOS Browser (for LG TVs)

## Next Steps

After testing this browser viewer:
1. Create WebOS TV App (Phase 6) using Enyo framework
2. Package as IPK for installation on LG TVs
3. Deploy to production monitors
