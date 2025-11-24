# WebSocket Manager API Reference

Quick reference for updated `websocket_manager.py` methods supporting Hybrid Console Streaming.

---

## Player Control Methods

### `register_player_control(device_id, websocket)`

Register a player's control WebSocket connection for bidirectional communication.

**Parameters**:
- `device_id` (int): Device ID
- `websocket` (WebSocket): WebSocket connection from player

**Returns**: None

**Example**:
```python
from shared.websocket_manager import websocket_manager

@router.websocket("/devices/{device_id}/console/control")
async def console_control(websocket: WebSocket, device_id: int):
    await websocket.accept()
    await websocket_manager.register_player_control(device_id, websocket)
    # ... handle connection
```

**Thread-Safe**: Yes (uses lock)

---

### `unregister_player_control(device_id)`

Unregister a player's control WebSocket connection.

**Parameters**:
- `device_id` (int): Device ID

**Returns**: None

**Example**:
```python
try:
    # ... WebSocket communication
    pass
except WebSocketDisconnect:
    await websocket_manager.unregister_player_control(device_id)
```

**Thread-Safe**: Yes (uses lock)

---

### `send_command_to_player(device_id, command, data=None)`

Send control command to player via WebSocket or Redis pub/sub.

**Parameters**:
- `device_id` (int): Target device ID
- `command` (str): Command name (`"start_streaming"`, `"stop_streaming"`)
- `data` (dict, optional): Additional command data

**Returns**: `bool` - `True` if sent successfully

**Example**:
```python
# Start streaming
success = await websocket_manager.send_command_to_player(
    device_id=123,
    command="start_streaming",
    data={"organization_id": 1}
)

# Stop streaming
success = await websocket_manager.send_command_to_player(
    device_id=123,
    command="stop_streaming",
    data={"organization_id": 1}
)
```

**Delivery Path**:
1. Try direct WebSocket (if player connected locally)
2. Fallback to Redis pub/sub (multi-instance support)

**Message Format**:
```json
{
  "command": "start_streaming",
  "data": {"organization_id": 1},
  "timestamp": "2025-11-24T10:30:00Z"
}
```

**Thread-Safe**: Partially (WebSocket send is not locked)

---

### `get_console_subscriber_count(device_id, organization_id)`

Get number of admins currently subscribed to device console logs.

**Parameters**:
- `device_id` (int): Device ID
- `organization_id` (int): Organization ID

**Returns**: `int` - Number of subscribed admins

**Example**:
```python
count = await websocket_manager.get_console_subscriber_count(
    device_id=123,
    organization_id=1
)

if count > 0:
    print(f"{count} admins are watching console")
```

**Thread-Safe**: Yes (uses lock)

---

## Console Subscription Methods (UPDATED)

### `subscribe_to_console(device_id, admin_user_id, organization_id, websocket)`

Subscribe admin to device console logs. Sends `start_streaming` if first subscriber.

**Parameters**:
- `device_id` (int): Device ID to subscribe to
- `admin_user_id` (int): Admin user ID
- `organization_id` (int): Organization ID (**NEW - REQUIRED**)
- `websocket` (WebSocket): WebSocket connection for console streaming

**Returns**: `bool` - `True` if subscribed successfully

**Example**:
```python
from shared.websocket_manager import websocket_manager

@router.websocket("/devices/{device_id}/console/stream")
async def console_stream(
    websocket: WebSocket,
    device_id: int,
    current_user: User = Depends(get_current_user)
):
    await websocket.accept()

    # Subscribe to console logs
    await websocket_manager.subscribe_to_console(
        device_id=device_id,
        admin_user_id=current_user.id,
        organization_id=current_user.organization_id,  # MUST PROVIDE
        websocket=websocket
    )

    # ... handle streaming
```

**Behavior**:
- Stores WebSocket connection
- Increments subscriber count for organization
- If FIRST subscriber → Sends `start_streaming` command to player
- Logs subscription with organization context

**Thread-Safe**: Yes (uses lock)

**BREAKING CHANGE**: Now requires `organization_id` parameter

---

### `unsubscribe_from_console(device_id, admin_user_id, organization_id)`

Unsubscribe admin from device console logs. Sends `stop_streaming` if last subscriber.

**Parameters**:
- `device_id` (int): Device ID to unsubscribe from
- `admin_user_id` (int): Admin user ID
- `organization_id` (int): Organization ID (**NEW - REQUIRED**)

**Returns**: None

**Example**:
```python
try:
    # ... WebSocket streaming
    pass
except WebSocketDisconnect:
    await websocket_manager.unsubscribe_from_console(
        device_id=device_id,
        admin_user_id=current_user.id,
        organization_id=current_user.organization_id  # MUST PROVIDE
    )
```

**Behavior**:
- Removes WebSocket connection
- Decrements subscriber count for organization
- If LAST subscriber → Sends `stop_streaming` command to player
- Cleans up empty tracking structures

**Thread-Safe**: Yes (uses lock)

**BREAKING CHANGE**: Now requires `organization_id` parameter

---

### `broadcast_console_log(device_id, organization_id, logs)`

Broadcast console logs to subscribed admins via Redis pub/sub.

**Parameters**:
- `device_id` (int): Source device ID
- `organization_id` (int): Organization ID for multi-tenant routing
- `logs` (list): List of console log entries

**Returns**: None

**Example**:
```python
logs = [
    {
        "level": "log",
        "message": "Application started",
        "timestamp": "2025-11-24T10:30:00Z",
        "source": "app.js:10",
        "stack_trace": None
    }
]

await websocket_manager.broadcast_console_log(
    device_id=123,
    organization_id=1,
    logs=logs
)
```

**Message Format**:
```json
{
  "event": "device.console_log",
  "data": {
    "device_id": 123,
    "logs": [...]
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

**Delivery**:
- Uses Redis pub/sub channel `console:{device_id}:{org_id}`
- Fallback to in-memory if Redis unavailable

**Thread-Safe**: Partially (Redis publish is not locked)

---

## Connection Statistics (UPDATED)

### `get_connection_stats()`

Get comprehensive connection statistics including player controls.

**Parameters**: None

**Returns**: `dict` - Connection statistics

**Example**:
```python
stats = websocket_manager.get_connection_stats()
print(stats)
```

**Response**:
```json
{
  "total_devices": 10,
  "total_admins": 5,
  "total_player_controls": 8,
  "organizations": 2,
  "devices_by_org": {
    "1": 6,
    "2": 4
  },
  "admins_by_org": {
    "1": 3,
    "2": 2
  },
  "console_subscriptions": {
    "123": 2,
    "456": 1
  }
}
```

**New Fields**:
- `total_player_controls` - Number of registered player control WebSockets
- `console_subscriptions` - Map of device_id to subscriber count

**Thread-Safe**: No (read-only snapshot)

---

## Background Tasks (UPDATED)

### `start_redis_listener()`

Start Redis pub/sub listener tasks (logs + commands).

**Parameters**: None

**Returns**: None

**Example**:
```python
# In main.py startup
@app.on_event("startup")
async def startup():
    await websocket_manager.start_redis_listener()
```

**Starts**:
1. `_redis_listener()` - Console log broadcasting
2. `_command_listener()` - Command forwarding (**NEW**)

**Thread-Safe**: Yes (creates tasks)

---

### `stop_redis_listener()`

Stop Redis pub/sub listener tasks gracefully.

**Parameters**: None

**Returns**: None

**Example**:
```python
# In main.py shutdown
@app.on_event("shutdown")
async def shutdown():
    await websocket_manager.stop_redis_listener()
```

**Stops**:
1. `_redis_listener()` - Console log broadcasting
2. `_command_listener()` - Command forwarding (**NEW**)

**Thread-Safe**: Yes (cancels tasks)

---

## Migration Guide

### Old Code (Before Update)

```python
# Subscribe
await websocket_manager.subscribe_to_console(
    device_id=123,
    admin_user_id=456,
    websocket=ws
)

# Unsubscribe
await websocket_manager.unsubscribe_from_console(
    device_id=123,
    admin_user_id=456
)
```

### New Code (After Update)

```python
# Subscribe - ADD organization_id parameter
await websocket_manager.subscribe_to_console(
    device_id=123,
    admin_user_id=456,
    organization_id=1,  # NEW - REQUIRED
    websocket=ws
)

# Unsubscribe - ADD organization_id parameter
await websocket_manager.unsubscribe_from_console(
    device_id=123,
    admin_user_id=456,
    organization_id=1  # NEW - REQUIRED
)
```

### Getting organization_id

**From current_user**:
```python
organization_id = current_user.organization_id
```

**From device**:
```python
device = await device_repo.get_by_id(device_id)
organization_id = device.organization_id
```

---

## Error Handling

### WebSocket Send Failures

```python
try:
    success = await websocket_manager.send_command_to_player(
        device_id=123,
        command="start_streaming"
    )
    if not success:
        logger.error(f"Failed to send command to device {device_id}")
except Exception as e:
    logger.error(f"Error sending command: {e}")
```

### Redis Failures

```python
# Graceful degradation - falls back to in-memory
await websocket_manager.broadcast_console_log(
    device_id=123,
    organization_id=1,
    logs=logs
)
# No exception raised - logs warning instead
```

### WebSocket Disconnects

```python
try:
    while True:
        data = await websocket.receive_json()
except WebSocketDisconnect:
    # Cleanup automatically
    await websocket_manager.unregister_player_control(device_id)
    await websocket_manager.unsubscribe_from_console(
        device_id,
        user_id,
        organization_id
    )
```

---

## Complete Example: Console Streaming Route

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from shared.websocket_manager import websocket_manager
from services.auth.dependencies import get_current_user

router = APIRouter()

@router.websocket("/devices/{device_id}/console/stream")
async def console_stream(
    websocket: WebSocket,
    device_id: int,
    current_user: User = Depends(get_current_user)
):
    """Admin console streaming endpoint"""
    await websocket.accept()

    try:
        # Subscribe to console logs
        await websocket_manager.subscribe_to_console(
            device_id=device_id,
            admin_user_id=current_user.id,
            organization_id=current_user.organization_id,
            websocket=websocket
        )

        # Keep connection alive
        while True:
            # Receive heartbeat or commands from admin
            data = await websocket.receive_json()

            # Handle admin commands (optional)
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"Admin {current_user.id} disconnected from device {device_id} console")

    finally:
        # Cleanup on disconnect
        await websocket_manager.unsubscribe_from_console(
            device_id=device_id,
            admin_user_id=current_user.id,
            organization_id=current_user.organization_id
        )
```

---

## Complete Example: Player Control Route

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from shared.websocket_manager import websocket_manager

router = APIRouter()

@router.websocket("/devices/{device_id}/console/control")
async def console_control(
    websocket: WebSocket,
    device_id: int
):
    """Player control WebSocket endpoint"""
    await websocket.accept()

    try:
        # Register player control connection
        await websocket_manager.register_player_control(device_id, websocket)

        # Receive logs from player
        while True:
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "console_logs":
                logs = data.get("logs", [])
                log_type = data.get("logType", "realtime")

                # Broadcast to subscribed admins
                await websocket_manager.broadcast_console_log(
                    device_id=device_id,
                    organization_id=data.get("organization_id"),
                    logs=logs
                )

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"Player {device_id} control WebSocket disconnected")

    finally:
        # Cleanup on disconnect
        await websocket_manager.unregister_player_control(device_id)
```

---

## Redis Channels

### Console Logs
**Channel**: `console:{device_id}:{org_id}`

**Message**:
```json
{
  "event": "device.console_log",
  "data": {
    "device_id": 123,
    "logs": [...]
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

### Commands (NEW)
**Channel**: `command:{device_id}`

**Message**:
```json
{
  "command": "start_streaming",
  "data": {
    "organization_id": 1
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

---

## Monitoring

### Check Active Connections

```python
stats = websocket_manager.get_connection_stats()

print(f"Player controls: {stats['total_player_controls']}")
print(f"Console subscriptions: {stats['console_subscriptions']}")
```

### Check Subscriber Count

```python
count = await websocket_manager.get_console_subscriber_count(
    device_id=123,
    organization_id=1
)

print(f"{count} admins subscribed")
```

### Monitor Logs

```bash
# Backend logs
docker logs signage-backend | grep "command"
docker logs signage-backend | grep "subscriber"

# Redis commands
docker exec signage-redis redis-cli MONITOR | grep "command:"
```

---

## Performance

### Typical Latencies

- **Direct WebSocket**: < 10ms
- **Redis Pub/Sub**: < 50ms
- **Command Processing**: < 5ms
- **Subscriber Count**: < 1ms

### Memory Usage

- **Per Player Control**: ~100 bytes
- **Per Subscriber**: ~200 bytes
- **Per Organization**: ~50 bytes

### Network Usage

- **Command Message**: ~200 bytes
- **Console Log Batch**: ~1-5 KB
- **Redis Overhead**: ~100 bytes per message

---

## Best Practices

1. **Always provide organization_id** - Required for multi-tenancy
2. **Handle WebSocket disconnects** - Clean up resources
3. **Check send_command_to_player() return** - Verify delivery
4. **Use try/finally blocks** - Ensure cleanup on errors
5. **Monitor subscriber counts** - Debug streaming issues
6. **Log all operations** - Aid troubleshooting
7. **Test multi-instance** - Verify Redis pub/sub works

---

## Common Issues

### Commands Not Received

**Check**:
- Player control WebSocket registered?
- Redis pub/sub listener running?
- Channel name correct (`command:{device_id}`)?

**Fix**:
```python
stats = websocket_manager.get_connection_stats()
if stats["total_player_controls"] == 0:
    logger.error("No player controls registered!")
```

### Subscriber Count Wrong

**Check**:
- organization_id correct?
- Unsubscribe called on disconnect?
- Lock contention?

**Fix**:
```python
count = await websocket_manager.get_console_subscriber_count(
    device_id=123,
    organization_id=1
)
logger.info(f"Actual subscriber count: {count}")
```

### Start/Stop Not Sent

**Check**:
- First/last subscriber logic?
- send_command_to_player() called?
- Command sent to correct device?

**Fix**:
```bash
docker logs signage-backend | grep "First subscriber"
docker logs signage-backend | grep "start_streaming"
```
