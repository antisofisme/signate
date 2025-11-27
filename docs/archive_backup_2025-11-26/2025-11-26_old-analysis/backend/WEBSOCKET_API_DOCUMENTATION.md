# WebSocket API Documentation

## Overview

The Digital Signage backend provides real-time WebSocket connections for instant communication between the server, devices, and admin dashboard. This replaces HTTP polling with sub-10ms latency updates.

## Performance Specifications

- **Latency**: <10ms for message delivery
- **Concurrent Connections**: 500-1000 per instance
- **Memory Usage**: ~1MB per connection
- **Heartbeat Interval**: 30 seconds
- **Reconnection**: Automatic with exponential backoff
- **Message Size**: Up to 64KB per message

## WebSocket Endpoints

### 1. Device WebSocket

**Endpoint**: `/ws/device/{device_id}`

**Query Parameters**:
- `token` (optional): Device activation code for authentication

**Purpose**: Real-time communication channel for digital signage devices

**Connection Flow**:
1. Device connects with its ID and optional token
2. Server validates device and accepts connection
3. Bidirectional communication established
4. Automatic heartbeat every 30s
5. Graceful disconnect with cleanup

**Message Types (Server → Device)**:

```javascript
// Connected confirmation
{
    "type": "connected",
    "device_id": 123,
    "device_name": "Lobby Display",
    "message": "Connected to signage backend",
    "server_time": "2025-10-28T10:00:00Z"
}

// Playlist update
{
    "type": "playlist_update",
    "playlist_id": 456,
    "playlist_name": "Morning Content",
    "action": "assigned", // assigned|updated|removed
    "timestamp": "2025-10-28T10:00:00Z"
}

// Content ready
{
    "type": "content_ready",
    "content_id": 789,
    "content_title": "Promo Video",
    "content_url": "http://192.168.5.12:8001/data/hls/content_789/playlist.m3u8",
    "content_type": "video",
    "timestamp": "2025-10-28T10:00:00Z"
}

// Command
{
    "type": "command",
    "command": "reload", // reload|screenshot|restart|update_config
    "params": {
        // Command-specific parameters
    },
    "timestamp": "2025-10-28T10:00:00Z"
}

// Heartbeat
{
    "type": "heartbeat",
    "server_time": "2025-10-28T10:00:00Z"
}
```

**Message Types (Device → Server)**:

```javascript
// Heartbeat response
{
    "type": "heartbeat"
}

// Command response
{
    "type": "command_response",
    "command": "screenshot",
    "success": true,
    "result": "Screenshot taken",
    "error": null
}

// Status update
{
    "type": "status",
    "status": "playing", // idle|playing|error
    "details": {
        "current_content": "content_789",
        "playback_position": 45.2,
        "cpu_usage": 25,
        "memory_usage": 512
    }
}
```

### 2. Admin Dashboard WebSocket

**Endpoint**: `/ws/admin`

**Query Parameters**:
- `token` (optional): JWT authentication token

**Purpose**: Real-time updates for admin dashboard

**Message Types (Server → Admin)**:

```javascript
// Connected confirmation
{
    "type": "connected",
    "message": "Connected to admin dashboard",
    "connection_id": "uuid-here",
    "server_time": "2025-10-28T10:00:00Z"
}

// Device events
{
    "type": "dashboard_update",
    "event": "device_connected", // device_connected|device_disconnected
    "device_id": 123,
    "device_name": "Lobby Display"
}

// Transcoding progress
{
    "type": "transcoding_progress",
    "content_id": 789,
    "progress": 45,
    "stage": "transcoding", // analyzing|transcoding|finalizing|completed
    "eta": "2025-10-28T10:05:00Z"
}

// Command response from device
{
    "type": "command_response",
    "device_id": 123,
    "command": "screenshot",
    "success": true,
    "result": "base64_image_data_here"
}

// Connection statistics
{
    "type": "connection_stats",
    "stats": {
        "total_connections": 150,
        "current_device_connections": 45,
        "current_admin_connections": 3,
        "peak_connections": 200,
        "messages_sent": 10000,
        "messages_received": 8500
    }
}
```

**Message Types (Admin → Server)**:

```javascript
// Ping
{
    "type": "ping"
}

// Get statistics
{
    "type": "get_stats"
}

// Send command to device
{
    "type": "send_command",
    "device_id": 123,
    "command": "reload",
    "params": {}
}
```

## HTTP API Endpoints

### WebSocket Statistics

**GET** `/api/websocket/stats`

Get current WebSocket connection statistics.

**Response**:
```json
{
    "success": true,
    "stats": {
        "total_connections": 150,
        "current_device_connections": 45,
        "current_admin_connections": 3,
        "peak_connections": 200,
        "messages_sent": 10000,
        "messages_received": 8500,
        "bytes_sent": 104857600,
        "bytes_received": 52428800,
        "devices": {
            "123": {
                "device_name": "Lobby Display",
                "connected_at": "2025-10-28T09:00:00Z",
                "last_heartbeat": "2025-10-28T10:00:00Z",
                "messages_sent": 100,
                "messages_received": 80
            }
        }
    }
}
```

### Broadcast Message

**POST** `/api/websocket/broadcast`

Broadcast message to devices via WebSocket.

**Request**:
```json
{
    "message_type": "playlist_update",
    "data": {
        "playlist_id": 456,
        "playlist_name": "Updated Playlist",
        "action": "updated"
    },
    "device_ids": [123, 124, 125]  // Optional, omit to broadcast to all
}
```

**Response**:
```json
{
    "success": true,
    "total_devices": 3,
    "successful_sends": 3,
    "failed_sends": 0,
    "results": {
        "123": true,
        "124": true,
        "125": true
    }
}
```

## Task Management API

### Get Task Status

**GET** `/api/tasks/{task_id}`

Check status of a Celery background task (e.g., video transcoding).

**Response**:
```json
{
    "task_id": "abc-123-def",
    "state": "PROGRESS",
    "progress": 45,
    "stage": "transcoding",
    "current": "Processing segment 5/10",
    "message": "Transcoding video: 45%",
    "metadata": {
        "file_name": "video.mp4",
        "resolution": "1920x1080",
        "duration": 300
    },
    "eta_seconds": 120
}
```

### Cancel Task

**POST** `/api/tasks/{task_id}/cancel`

Cancel a running background task.

**Response**:
```json
{
    "success": true,
    "task_id": "abc-123-def",
    "message": "Task cancellation requested",
    "state": "REVOKED"
}
```

### Get Active Tasks

**GET** `/api/tasks/active`

List all currently active tasks.

**Response**:
```json
{
    "success": true,
    "active_tasks": [
        {
            "task_id": "abc-123",
            "name": "transcode_video",
            "worker": "worker-1",
            "started": "2025-10-28T10:00:00Z"
        }
    ],
    "total": 1,
    "workers": ["worker-1"]
}
```

## JavaScript Client Usage

```javascript
// Initialize WebSocket client
const wsClient = new WebSocketClient({
    deviceId: 123,
    token: 'activation_code',
    serverUrl: 'ws://192.168.5.12:8001',
    debug: true
});

// Handle playlist updates
wsClient.on('playlist_update', (message) => {
    console.log('Playlist updated:', message);
    // Reload playlist content
    loadPlaylist(message.playlist_id);
});

// Handle content ready notifications
wsClient.on('content_ready', (message) => {
    console.log('Content ready:', message);
    // Preload content for smooth playback
    preloadContent(message.content_url);
});

// Handle commands from admin
wsClient.on('command', (message) => {
    switch (message.command) {
        case 'reload':
            location.reload();
            break;
        case 'screenshot':
            takeScreenshot().then(data => {
                wsClient.send('command_response', {
                    command: 'screenshot',
                    success: true,
                    result: data
                });
            });
            break;
    }
});

// Monitor connection state
wsClient.onConnectionChange((connected) => {
    updateConnectionIndicator(connected);
});

// Connect to server
wsClient.connect();
```

## Python Client Usage (Backend Service)

```python
from app.services.websocket_service import websocket_service

# Notify devices about playlist update
await websocket_service.notify_playlist_update(
    device_ids=[123, 124, 125],
    playlist_id=456,
    playlist_name="Morning Content",
    action="assigned"
)

# Send command to specific device
await websocket_service.send_command_to_device(
    device_id=123,
    command="reload",
    params={}
)

# Broadcast command to all devices
results = await websocket_service.broadcast_command(
    command="update_config",
    params={"setting": "value"}
)

# Check if device is connected
is_connected = await websocket_service.is_device_connected(123)

# Get list of connected devices
connected_devices = await websocket_service.get_connected_devices()
```

## Integration with Existing Features

### 1. Content Upload & Transcoding

When content is uploaded and transcoded:
1. Task created with Celery
2. Progress updates sent via WebSocket to admin dashboard
3. When complete, `content_ready` sent to assigned devices
4. Devices preload content for smooth playback

### 2. Playlist Assignment

When playlist is assigned to devices:
1. Database updated
2. `playlist_update` sent immediately via WebSocket
3. Devices receive update in <10ms
4. Devices reload playlist without polling

### 3. Device Commands

Admin can send commands to devices:
1. Admin sends command via dashboard
2. Command routed through WebSocket to device
3. Device executes command
4. Response sent back to admin in real-time

## Migration from HTTP Polling

### Before (HTTP Polling - 30s delay):
```javascript
// Old polling approach
setInterval(() => {
    fetch('/api/client/heartbeat')
        .then(res => res.json())
        .then(data => {
            if (data.playlist_updated) {
                reloadPlaylist();
            }
        });
}, 30000);
```

### After (WebSocket - <10ms):
```javascript
// New WebSocket approach
wsClient.on('playlist_update', (message) => {
    reloadPlaylist(message.playlist_id);
});
```

## Benefits

1. **Instant Updates**: <10ms vs 30s polling delay
2. **Lower Bandwidth**: No constant polling requests
3. **Bidirectional**: Server can push updates immediately
4. **Scalable**: 500-1000 connections per instance
5. **Reliable**: Automatic reconnection with exponential backoff
6. **Efficient**: ~1MB memory per connection

## Troubleshooting

### Connection Issues

1. **Check WebSocket URL**: Ensure using correct protocol (ws:// or wss://)
2. **Verify Device ID**: Device must exist in database
3. **Authentication**: Token must match device activation code
4. **Firewall**: Ensure WebSocket port (8001) is open
5. **Proxy Settings**: Some proxies may block WebSocket upgrade

### Debugging

Enable debug mode in client:
```javascript
const wsClient = new WebSocketClient({
    debug: true  // Enables console logging
});
```

Check server logs:
```bash
docker logs signage-backend 2>&1 | grep WebSocket
```

Monitor connections:
```bash
curl http://192.168.5.12:8001/api/websocket/stats
```

## Security Considerations

1. **Authentication**: Devices use activation codes, admins use JWT
2. **Rate Limiting**: Connection attempts are rate-limited
3. **Input Validation**: All messages validated before processing
4. **Connection Limits**: Max connections per device enforced
5. **Secure Transport**: Use WSS (WebSocket Secure) in production