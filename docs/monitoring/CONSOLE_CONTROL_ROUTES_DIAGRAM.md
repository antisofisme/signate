# Console Control Routes - Architecture Diagram

## 📊 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ PLAYER (Device Browser)                                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ Console Interceptor                                        │    │
│  │ - Intercepts all console.log/info/warn/error/debug        │    │
│  │ - Persistent circular buffer (1000 logs max, FIFO)        │    │
│  │ - State: BUFFERING | STREAMING                            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ WebSocket Control Client (NEW)                            │    │
│  │ ws://backend/devices/{id}/console/control                 │    │
│  │                                                            │    │
│  │ Outgoing:                                                  │    │
│  │   - console_logs (historical/realtime)                    │    │
│  │   - ping                                                   │    │
│  │                                                            │    │
│  │ Incoming:                                                  │    │
│  │   - start_streaming → Send buffer + stream                │    │
│  │   - stop_streaming → Stop upload, keep buffering          │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              ↕ WebSocket (bidirectional)
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND (FastAPI + Redis)                                           │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ console_control_routes.py (NEW)                           │    │
│  │ @router.websocket("/devices/{id}/console/control")       │    │
│  │                                                            │    │
│  │ Responsibilities:                                          │    │
│  │  1. Accept player WebSocket                               │    │
│  │  2. Validate device_id (database lookup)                  │    │
│  │  3. Register with WebSocket Manager                       │    │
│  │  4. Run concurrent listeners:                             │    │
│  │     a. _listen_player_messages                            │    │
│  │        - Receive logs from player                         │    │
│  │        - Validate log entries                             │    │
│  │        - Enrich with logType metadata                     │    │
│  │        - Broadcast to admins                              │    │
│  │     b. _listen_redis_commands                             │    │
│  │        - Subscribe to command:{device_id}                 │    │
│  │        - Forward commands to player WebSocket             │    │
│  │  5. Unregister on disconnect                              │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ WebSocket Manager (shared/websocket_manager.py)           │    │
│  │                                                            │    │
│  │ Methods:                                                   │    │
│  │  - register_player_control(device_id, websocket)         │    │
│  │  - unregister_player_control(device_id)                  │    │
│  │  - send_command_to_player(device_id, command)            │    │
│  │  - broadcast_console_log(device_id, org_id, logs)        │    │
│  │  - subscribe_to_console(device_id, admin_id, ws)         │    │
│  │  - unsubscribe_from_console(device_id, admin_id)         │    │
│  │  - get_console_subscriber_count(device_id, org_id)       │    │
│  │                                                            │    │
│  │ Storage:                                                   │    │
│  │  - _player_control_connections: {device_id: websocket}   │    │
│  │  - _console_subscriptions: {device_id: {admin_id: ws}}   │    │
│  │  - _console_subscriber_counts: {device_id: {org_id: N}}  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ Redis Pub/Sub                                             │    │
│  │                                                            │    │
│  │ Channels:                                                  │    │
│  │  - console:{device_id}:{org_id}  (log broadcast)         │    │
│  │  - command:{device_id}           (control signals)       │    │
│  │                                                            │    │
│  │ Listeners:                                                 │    │
│  │  - _redis_listener (console logs)                        │    │
│  │  - _command_listener (commands)                          │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ console_routes.py                                         │    │
│  │ @router.websocket("/devices/{id}/console/stream")        │    │
│  │                                                            │    │
│  │ Responsibilities:                                          │    │
│  │  - Accept admin WebSocket                                 │    │
│  │  - Subscribe admin to console logs                        │    │
│  │  - Send start_streaming command (first subscriber)       │    │
│  │  - Send stop_streaming command (last subscriber)         │    │
│  │  - Forward logs from Redis to admin WebSocket            │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ WebSocket (one-way: server → client)
┌─────────────────────────────────────────────────────────────────────┐
│ CMS (React + Vite)                                                  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ useConsoleLiveStream Hook                                 │    │
│  │                                                            │    │
│  │ On modal open:                                             │    │
│  │   1. Connect WebSocket to /console/stream                 │    │
│  │   2. Backend triggers start_streaming to player           │    │
│  │   3. Receive historical logs (logType="historical")       │    │
│  │   4. Replace existing logs in UI                          │    │
│  │   5. Receive realtime logs (logType="realtime")           │    │
│  │   6. Append to logs in UI                                 │    │
│  │                                                            │    │
│  │ On modal close:                                            │    │
│  │   1. Disconnect WebSocket                                 │    │
│  │   2. Backend triggers stop_streaming to player            │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Message Flow: Admin Opens Console Tab

```
┌─────────┐   ┌─────────────────┐   ┌──────────────┐   ┌────────┐
│   CMS   │   │ console_routes  │   │ WS Manager   │   │ Redis  │
└────┬────┘   └────────┬────────┘   └──────┬───────┘   └───┬────┘
     │                 │                    │               │
     │ 1. Connect WS   │                    │               │
     │────────────────>│                    │               │
     │                 │                    │               │
     │                 │ 2. subscribe_to_console()          │
     │                 │───────────────────>│               │
     │                 │                    │               │
     │                 │                    │ 3. Check subscriber count (0 → 1)
     │                 │                    │               │
     │                 │                    │ 4. send_command_to_player("start_streaming")
     │                 │                    │──────────────>│
     │                 │                    │               │
     │                 │                    │  Publish to command:{device_id}
     │                 │                    │               │
     │                 │                    │               ▼

┌──────────────┐   ┌─────────────────────────┐   ┌────────┐
│ Player       │   │ console_control_routes  │   │ Redis  │
└──────┬───────┘   └────────────┬────────────┘   └───┬────┘
       │                        │                     │
       │                        │ 5. _listen_redis_commands
       │                        │<────────────────────│
       │                        │    receives "start_streaming"
       │                        │                     │
       │ 6. Forward command     │                     │
       │<───────────────────────│                     │
       │                        │                     │
       │ 7. Send ALL buffered logs (logType="historical")
       │───────────────────────>│                     │
       │                        │                     │
       │                        │ 8. _listen_player_messages
       │                        │    validates + enriches
       │                        │                     │
       │                        │ 9. broadcast_console_log()
       │                        │───────────────────> │
       │                        │    Publish to console:{device_id}:{org_id}
       │                        │                     │
       │                        │                     ▼

┌─────────┐   ┌──────────────┐   ┌────────┐
│   CMS   │   │ WS Manager   │   │ Redis  │
└────┬────┘   └──────┬───────┘   └───┬────┘
     │               │                │
     │               │ 10. _redis_listener receives logs
     │               │<───────────────│
     │               │                │
     │               │ 11. _broadcast_console_local()
     │               │                │
     │ 12. Receive logs (event="device.console_log")
     │<──────────────│                │
     │               │                │
     │ 13. Display logs in UI         │
     │               │                │
```

---

## 🔄 Message Flow: Player Sends Logs

```
┌──────────────┐   ┌─────────────────────────┐
│ Player       │   │ console_control_routes  │
│              │   │ (control WebSocket)     │
└──────┬───────┘   └────────────┬────────────┘
       │                        │
       │ 1. Intercept console.log("Hello")
       │                        │
       │ 2. Add to buffer       │
       │                        │
       │ 3. Send logs batch     │
       │   {                    │
       │     type: "console_logs",
       │     logs: [...],       │
       │     logType: "realtime"│
       │   }                    │
       │───────────────────────>│
       │                        │
       │                        │ 4. _listen_player_messages
       │                        │    - Validate logs
       │                        │    - Enrich with logType
       │                        │
       │                        ▼

┌──────────────┐   ┌────────┐   ┌─────────┐
│ WS Manager   │   │ Redis  │   │   CMS   │
└──────┬───────┘   └───┬────┘   └────┬────┘
       │               │              │
       │ 5. broadcast_console_log()  │
       │──────────────>│              │
       │   Publish to console:{device_id}:{org_id}
       │               │              │
       │               │ 6. _redis_listener
       │<──────────────│              │
       │               │              │
       │ 7. _broadcast_console_local()│
       │──────────────────────────────>│
       │               │              │
       │               │              │ 8. Append to logs UI
       │               │              │
```

---

## 🔄 Message Flow: Admin Closes Console Tab

```
┌─────────┐   ┌─────────────────┐   ┌──────────────┐   ┌────────┐
│   CMS   │   │ console_routes  │   │ WS Manager   │   │ Redis  │
└────┬────┘   └────────┬────────┘   └──────┬───────┘   └───┬────┘
     │                 │                    │               │
     │ 1. Close modal  │                    │               │
     │                 │                    │               │
     │ 2. Disconnect WS│                    │               │
     │────────────────>│                    │               │
     │                 │                    │               │
     │                 │ 3. unsubscribe_from_console()      │
     │                 │───────────────────>│               │
     │                 │                    │               │
     │                 │                    │ 4. Check subscriber count (1 → 0)
     │                 │                    │               │
     │                 │                    │ 5. send_command_to_player("stop_streaming")
     │                 │                    │──────────────>│
     │                 │                    │               │
     │                 │                    │  Publish to command:{device_id}
     │                 │                    │               │
     │                 │                    │               ▼

┌──────────────┐   ┌─────────────────────────┐   ┌────────┐
│ Player       │   │ console_control_routes  │   │ Redis  │
└──────┬───────┘   └────────────┬────────────┘   └───┬────┘
       │                        │                     │
       │                        │ 6. _listen_redis_commands
       │                        │<────────────────────│
       │                        │    receives "stop_streaming"
       │                        │                     │
       │ 7. Forward command     │                     │
       │<───────────────────────│                     │
       │                        │                     │
       │ 8. Stop uploading logs │                     │
       │    (keep buffering)    │                     │
       │                        │                     │
```

---

## 📊 Component Interaction Matrix

| From → To | Player | console_control_routes | console_routes | WS Manager | Redis | CMS |
|-----------|--------|------------------------|----------------|------------|-------|-----|
| **Player** | - | ✅ Logs (WS) | - | - | - | - |
| **console_control_routes** | ✅ Commands (WS) | - | - | ✅ Broadcast logs | ✅ Subscribe commands | - |
| **console_routes** | - | - | - | ✅ Subscribe/Unsubscribe | - | ✅ Stream logs (WS) |
| **WS Manager** | ✅ Direct commands (WS) | ✅ Redis commands | ✅ Broadcast to WS | - | ✅ Pub/Sub | ✅ Broadcast to WS |
| **Redis** | - | ✅ Command messages | ✅ Log messages | ✅ Messages | - | - |
| **CMS** | - | - | ✅ Connect/Disconnect | - | - | - |

**Legend**:
- ✅ = Direct communication
- WS = WebSocket
- Pub/Sub = Redis publish/subscribe

---

## 🔐 Security Flow

```
┌────────────────────────────────────────────────────────────────┐
│ Security Validation Layers                                     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Player Connection (console_control_routes)                  │
│    ┌─────────────────────────────────────────────────────┐    │
│    │ Accept WS → Validate device_id in database          │    │
│    │           → Check organization_id exists            │    │
│    │           → Reject if invalid                       │    │
│    └─────────────────────────────────────────────────────┘    │
│                             ↓                                   │
│ 2. Message Validation                                          │
│    ┌─────────────────────────────────────────────────────┐    │
│    │ Receive logs → Validate structure                   │    │
│    │              → Check required fields                │    │
│    │              → Validate log level                   │    │
│    │              → Skip invalid logs                    │    │
│    └─────────────────────────────────────────────────────┘    │
│                             ↓                                   │
│ 3. Multi-Tenant Routing (WS Manager)                           │
│    ┌─────────────────────────────────────────────────────┐    │
│    │ Get organization_id from database (NOT player)      │    │
│    │ Publish to console:{device_id}:{org_id}            │    │
│    │ Only admins in same org receive logs               │    │
│    └─────────────────────────────────────────────────────┘    │
│                             ↓                                   │
│ 4. Admin Subscription (console_routes)                         │
│    ┌─────────────────────────────────────────────────────┐    │
│    │ JWT authentication (query params)                   │    │
│    │ Organization isolation enforced                     │    │
│    │ Subscribe only to own org's devices                │    │
│    └─────────────────────────────────────────────────────┘    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

**Security Guarantees**:
1. ✅ Device must exist in database
2. ✅ Device must be activated (has organization_id)
3. ✅ Invalid logs are rejected (not broadcasted)
4. ✅ Organization ID sourced from database (untrusted player cannot spoof)
5. ✅ Redis channels include org_id for isolation
6. ✅ Admins can only subscribe to devices in their organization

---

## 🎯 Key Design Decisions

### 1. Bidirectional WebSocket (Not HTTP + WebSocket)

**Decision**: Use single bidirectional WebSocket for player control

**Rationale**:
- ✅ Lower latency (no HTTP request overhead)
- ✅ Persistent connection (no reconnection for each log batch)
- ✅ Real-time commands (start/stop streaming)
- ✅ Efficient resource usage (one connection instead of two)

### 2. Concurrent Listeners (asyncio.gather)

**Decision**: Run two listeners concurrently instead of sequentially

**Rationale**:
- ✅ Non-blocking (both can receive messages simultaneously)
- ✅ Commands can be sent while logs are streaming
- ✅ No race conditions (each listener handles own message type)

### 3. Log Enrichment (logType metadata)

**Decision**: Add logType field to logs before broadcasting

**Rationale**:
- ✅ CMS can differentiate historical vs realtime logs
- ✅ Better UX (auto-scroll only for realtime logs)
- ✅ No need for separate endpoints
- ✅ Player doesn't need to change message format

### 4. Organization ID from Database (Not Player)

**Decision**: Always lookup organization_id from database, never trust player

**Rationale**:
- ✅ Security (prevents cross-tenant data leakage)
- ✅ Simplicity (player doesn't need to know org_id)
- ✅ Consistency (single source of truth)

### 5. Graceful Error Handling (Continue on Invalid Logs)

**Decision**: Skip invalid logs but continue processing valid ones

**Rationale**:
- ✅ Resilience (one bad log doesn't crash entire system)
- ✅ Observability (invalid logs are logged for debugging)
- ✅ User experience (valid logs still appear)

---

**Created**: 2025-01-13
**Diagram Version**: 1.0
**Status**: Final ✅
