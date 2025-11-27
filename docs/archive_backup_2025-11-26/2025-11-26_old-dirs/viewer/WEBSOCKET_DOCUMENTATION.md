# WebSocket Real-Time Updates - Viewer Documentation

## Overview

The Smart TV Digital Signage viewer now supports real-time updates via WebSocket connections. This eliminates the need for constant HTTP polling and provides instant (<1s) updates when playlists change, new content is ready, or admin commands are sent.

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌───────────────┐
│   Viewer    │◄────WS──►│  Backend API │◄───────►│  Redis Pub/Sub│
│  (Browser/  │         │  (FastAPI)   │         │               │
│   WebOS)    │         └──────────────┘         └───────────────┘
└─────────────┘                 ▲                        ▲
                                │                        │
                         ┌──────┴────────┐               │
                         │  Web Admin    │───Publishes───┘
                         │  (React)      │   Events
                         └───────────────┘
```

### Components

1. **SignageWebSocket** (`js/shared/websocket.js`)
   - Core WebSocket client library
   - Auto-reconnect with exponential backoff
   - Heartbeat mechanism (30s ping/pong)
   - Event-driven architecture

2. **PlayerWebSocket** (`js/player/websocket-integration.js`)
   - Player-specific integration
   - Message handlers (playlist_update, content_ready, command)
   - Graceful fallback to HTTP polling

3. **Backend WebSocket Endpoint** (`backend/app/api/websocket.py`)
   - Device-specific WebSocket endpoint: `/ws/device/{device_id}`
   - Redis pub/sub integration
   - Ping/pong keepalive

4. **WebSocket Publisher** (`backend/app/core/websocket_publisher.py`)
   - Helper utility to publish events
   - Used by API endpoints to notify devices

## Features

### ✅ Auto-Reconnect with Exponential Backoff
- Initial retry: 1 second
- Maximum retry delay: 30 seconds
- Maximum attempts: 10
- Automatically falls back to HTTP polling after max retries

### ✅ Heartbeat Mechanism
- Ping sent every 30 seconds
- Detects dead connections (3 missed pongs)
- Automatic reconnection on timeout

### ✅ Event-Driven Architecture
- Subscribe to specific event types
- Clean separation of concerns
- Easy to extend with new event types

### ✅ Graceful Fallback
- Falls back to HTTP polling if WebSocket fails
- Seamless transition - no user impact
- Automatic switch back to WebSocket when reconnected

## WebSocket URL

```
ws://192.168.5.12:8001/ws/device/{device_id}
```

For HTTPS deployments:
```
wss://your-domain.com/ws/device/{device_id}
```

## Message Types

### 1. `connected` (Server → Device)
Sent when WebSocket connection is established.

```json
{
  "type": "connected",
  "device_id": 123,
  "device_name": "TV-Living Room",
  "message": "Connected to device updates stream"
}
```

### 2. `playlist_update` (Server → Device)
Sent when a playlist is assigned or updated.

```json
{
  "type": "playlist_update",
  "playlist_id": 456,
  "playlist_name": "Morning Ads",
  "action": "assigned",
  "timestamp": "2025-10-28T12:34:56.789Z"
}
```

**Device Action**: Reload playlist immediately

### 3. `content_ready` (Server → Device)
Sent when new content has been uploaded and processed.

```json
{
  "type": "content_ready",
  "content_id": 789,
  "content_type": "video",
  "timestamp": "2025-10-28T12:34:56.789Z"
}
```

**Device Action**: Check for playlist updates

### 4. `command` (Server → Device)
Sent by admin to execute commands on device.

```json
{
  "type": "command",
  "command": "reload",
  "params": {},
  "timestamp": "2025-10-28T12:34:56.789Z"
}
```

**Supported Commands**:
- `reload` - Reload entire viewer
- `refresh` - Refresh playlist and cache
- `reset` - Reset device (clear cache and re-register)
- `clear_cache` - Clear media cache only
- `volume` - Set volume (params: `{level: 50}`)

### 5. `ping` (Device → Server)
Heartbeat ping sent by device every 30 seconds.

```json
{
  "type": "ping",
  "timestamp": 1730119896789
}
```

### 6. `pong` (Server → Device)
Response to ping.

```json
{
  "type": "pong",
  "timestamp": 1730119896789
}
```

## Usage

### Frontend (Viewer)

The WebSocket is automatically initialized when the player starts:

```javascript
// Initialization happens in js/player/init.js
if (window.PlayerWebSocket) {
    window.PlayerWebSocket.initialize();
}
```

### Backend (API Endpoints)

Publish events from any endpoint:

```python
from app.core.websocket_publisher import ws_publisher

# Notify specific device
await ws_publisher.notify_device(
    device_id=123,
    event_type='playlist_update',
    data={
        'playlist_id': 456,
        'playlist_name': 'Morning Ads',
        'action': 'assigned'
    }
)

# Broadcast to all devices
await ws_publisher.broadcast_devices(
    event_type='command',
    data={
        'command': 'reload',
        'params': {}
    }
)
```

## Connection States

1. **`disconnected`** - Not connected
2. **`connecting`** - Attempting to connect
3. **`connected`** - Connected and ready
4. **`reconnecting`** - Reconnecting after disconnect
5. **`failed`** - Max retries reached, using HTTP polling fallback

## Monitoring

### Debug Mode

Enable debug logging in browser console:

```javascript
// Enable WebSocket debug logs
enableWSDebug()

// Check connection status
window.PlayerWebSocket.isActive()

// Get connection stats
window.PlayerWebSocket.getStats()
```

### Connection Stats

```javascript
{
  connectionAttempts: 5,
  messagesReceived: 123,
  messagesSent: 45,
  reconnects: 2,
  errors: 1,
  state: "connected",
  reconnectAttempts: 0,
  lastPongTime: 1730119896789
}
```

## Error Handling

### Network Disconnection
- Automatic reconnection with exponential backoff
- Falls back to HTTP polling after 10 failed attempts
- Network status indicator shows connection state

### Server Restart
- Client automatically reconnects when server is back online
- Buffered events are not lost (handled by Redis)
- Seamless recovery with no manual intervention

### Device Not Found (404)
- WebSocket connection closes immediately
- Error message sent to device before close
- Device can retry registration

## Performance

### Latency
- **WebSocket**: <1 second for real-time updates
- **HTTP Polling (fallback)**: 60 seconds interval

### Bandwidth
- **WebSocket**: Minimal (only event messages + 30s heartbeat)
- **HTTP Polling**: Higher (full playlist fetch every 60s)

### Server Load
- **WebSocket**: 1 persistent connection per device
- **Redis Pub/Sub**: Efficient broadcasting to multiple devices
- **Background Tasks**: Non-blocking event publishing

## Redis Channels

### Device-Specific Channels
```
device:{device_id}:updates
```
Events targeted to a specific device.

### Broadcast Channel
```
devices:broadcast
```
Events sent to all connected devices.

## Testing

### Manual Testing

1. **Test Connection**:
   ```javascript
   // In browser console
   window.PlayerWebSocket.getStats()
   ```

2. **Test Playlist Update**:
   - Assign playlist in web admin
   - Check viewer logs for WebSocket message
   - Verify playlist reloads instantly

3. **Test Reconnection**:
   ```javascript
   // Disconnect manually
   window.PlayerWebSocket.disconnect()

   // Reconnect
   window.PlayerWebSocket.initialize()
   ```

4. **Test Fallback**:
   - Stop backend server
   - Wait for max retries (10 attempts)
   - Verify fallback to HTTP polling
   - Restart server
   - Verify automatic switch back to WebSocket

### Backend Testing

Publish test event via Redis CLI:

```bash
# Connect to Redis
redis-cli -h localhost -p 6379

# Publish playlist update to device 1
PUBLISH "device:1:updates" '{"type":"playlist_update","playlist_id":123,"timestamp":"2025-10-28T12:34:56Z"}'

# Broadcast reload command to all devices
PUBLISH "devices:broadcast" '{"type":"command","command":"reload","timestamp":"2025-10-28T12:34:56Z"}'
```

## Troubleshooting

### WebSocket Not Connecting

1. **Check backend logs**:
   ```bash
   docker logs signage-backend
   ```

2. **Verify Redis is running**:
   ```bash
   docker ps | grep redis
   ```

3. **Check CORS settings** in `backend/app/main.py`:
   ```python
   allow_origins=["http://192.168.5.12:8080", ...]
   ```

4. **Check firewall** - Port 8001 must be accessible

### Messages Not Received

1. **Enable debug mode**:
   ```javascript
   enableWSDebug()
   ```

2. **Check WebSocket state**:
   ```javascript
   window.PlayerWebSocket.getStats()
   ```

3. **Verify Redis pub/sub**:
   ```bash
   redis-cli
   PSUBSCRIBE "device:*"
   ```

### High Reconnection Rate

- Check network stability
- Verify backend server is not overloaded
- Check Redis connection pool settings

## Future Enhancements

### Planned Features
- [ ] Message acknowledgment (ack/nack)
- [ ] Message queue for offline devices
- [ ] WebSocket compression
- [ ] Binary message support for large payloads
- [ ] Multi-server WebSocket support (sticky sessions)
- [ ] WebSocket metrics and monitoring dashboard

### Potential Use Cases
- Live content preview sync
- Real-time analytics updates
- Emergency broadcast messages
- Remote device diagnostics
- Multi-device synchronized playback

## Files Modified

### Frontend (Viewer)
```
viewer/js/shared/websocket.js                    (NEW)
viewer/js/player/websocket-integration.js        (NEW)
viewer/js/player/init.js                         (MODIFIED)
viewer/player.html                               (MODIFIED)
```

### Backend (API)
```
backend/app/api/websocket.py                     (MODIFIED)
backend/app/api/playlists.py                     (MODIFIED)
backend/app/core/websocket_publisher.py          (NEW)
```

## Deployment Checklist

- [ ] Ensure Redis is running and accessible
- [ ] Update CORS settings for WebSocket origin
- [ ] Test WebSocket connection from viewer
- [ ] Verify auto-reconnect behavior
- [ ] Test fallback to HTTP polling
- [ ] Monitor Redis pub/sub channels
- [ ] Check backend logs for WebSocket errors
- [ ] Test with multiple concurrent devices
- [ ] Verify events are published correctly
- [ ] Test all command types (reload, refresh, reset)

## Support

For issues or questions:
- Check browser console for WebSocket logs
- Check backend logs: `docker logs signage-backend`
- Enable debug mode: `enableWSDebug()`
- Verify Redis is running: `docker ps | grep redis`

---

**Version**: 1.0.0
**Last Updated**: 2025-10-28
**Status**: Production Ready ✅
