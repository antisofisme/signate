# WebSocket Quick Reference

## 📡 WebSocket Endpoints

### Device Connection
```
WS /api/websocket/ws/device/{device_id}?token={activation_code}
```

**Example:** `ws://192.168.5.12:8001/api/websocket/ws/device/123?token=ABCDEF`

### Admin Connection
```
WS /api/websocket/ws/admin?token={jwt_token}
```

---

## 📨 Message Format (ALL Messages)

```json
{
  "success": true,
  "type": "command",
  "data": {...},
  "meta": {
    "timestamp": "2025-10-28T10:30:00.123456Z",
    "message_id": "msg-abc123",
    "version": "1.0.0"
  }
}
```

---

## 🌐 HTTP Endpoints

### Get Stats
```
GET /api/websocket/stats
```

### Broadcast
```
POST /api/websocket/broadcast
```

---

## 🔧 Integration

```python
from app.api.websocket_v2 import send_command_to_device

await send_command_to_device(device_id=123, command_id=456, command_type="reload", params={})
```

---

**Full Documentation:** WEBSOCKET_QUICK_WINS_MIGRATION_COMPLETE.md
