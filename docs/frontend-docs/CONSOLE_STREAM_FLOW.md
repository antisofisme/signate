# Console Stream Hook - Data Flow Diagram

## Connection Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CMS: User Opens Console Tab                              │
│    → useConsoleLiveStream({ deviceId: 123, enabled: true }) │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Hook State Changes                                        │
│    isConnecting: true                                        │
│    isLoadingHistory: false (wait for connection)             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. WebSocket Connection Opens                                │
│    ws.onopen()                                               │
│    → setIsConnected(true)                                    │
│    → setIsConnecting(false)                                  │
│    → setIsLoadingHistory(true) ⏳                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Backend Sends Confirmation                                │
│    {                                                         │
│      event: "console.subscribed",                            │
│      data: { message: "Subscribed to console stream" }       │
│    }                                                         │
│    → console.log("Subscription confirmed")                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Backend Sends Historical Logs (ONE TIME)                  │
│    Option A: Separate event                                 │
│    {                                                         │
│      event: "console.historical",                            │
│      data: { logs: [500 logs...] }                           │
│    }                                                         │
│    OR                                                        │
│    Option B: Same event with metadata                       │
│    {                                                         │
│      event: "device.console_log",                            │
│      data: { logs: [500 logs...], logType: "historical" }    │
│    }                                                         │
│                                                              │
│    → setLogs([500 logs]) // REPLACE                          │
│    → setIsLoadingHistory(false) ✅                           │
│    → UI shows all logs immediately                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Backend Streams Real-time Logs (CONTINUOUS)               │
│    Every 2-3 seconds:                                        │
│    {                                                         │
│      event: "device.console_log",                            │
│      data: { logs: [1 new log] }                             │
│    }                                                         │
│    OR (with explicit metadata)                              │
│    {                                                         │
│      event: "device.console_log",                            │
│      data: { logs: [1 new log], logType: "realtime" }        │
│    }                                                         │
│                                                              │
│    → setLogs(prev => [...prev, newLog]) // APPEND           │
│    → UI auto-scrolls to bottom                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. User Closes Console Tab                                   │
│    → useConsoleLiveStream({ enabled: false })                │
│    → ws.close()                                              │
│    → setIsConnected(false)                                   │
│    → setIsLoadingHistory(false)                              │
└─────────────────────────────────────────────────────────────┘
```

## Message Handler Logic Tree

```
ws.onmessage(event)
  ↓
Parse JSON message
  ↓
Switch on message.event:

┌─────────────────────────────────────────────────────────┐
│ Case: "console.subscribed"                              │
│   → Log confirmation                                    │
│   → No state changes                                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Case: "console.historical"                              │
│   → Extract logs from message.data.logs                 │
│   → setLogs(logs.slice(-maxLogs))  [REPLACE]            │
│   → setIsLoadingHistory(false)                          │
│   → console.log("📦 Historical logs:", count)           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Case: "device.console_log"                              │
│   ↓                                                     │
│   Check logType (message.data.logType || 'realtime')    │
│   ↓                                                     │
│   If logType === 'historical':                          │
│     → setLogs(logs.slice(-maxLogs))  [REPLACE]          │
│     → setIsLoadingHistory(false)                        │
│     → console.log("📦 Historical logs (via logType)")   │
│   ↓                                                     │
│   Else (realtime):                                      │
│     → setLogs(prev => [...prev, ...newLogs])  [APPEND]  │
│     → Keep last maxLogs (default 1000)                  │
│     → console.log("⚡ Real-time log received")          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Default: Unknown event                                  │
│   → console.warn("⚠️ Unhandled message event")          │
└─────────────────────────────────────────────────────────┘
```

## State Transitions

```
┌─────────────────┐
│ Initial State   │
│ - logs: []      │
│ - isConnected: false
│ - isConnecting: false
│ - isLoadingHistory: false
└─────────────────┘
        ↓ connect()
┌─────────────────┐
│ Connecting      │
│ - logs: []      │
│ - isConnected: false
│ - isConnecting: true ⏳
│ - isLoadingHistory: false
└─────────────────┘
        ↓ ws.onopen()
┌─────────────────┐
│ Connected       │
│ - logs: []      │
│ - isConnected: true ✅
│ - isConnecting: false
│ - isLoadingHistory: true ⏳
└─────────────────┘
        ↓ Receive historical logs
┌─────────────────┐
│ History Loaded  │
│ - logs: [500]   │
│ - isConnected: true ✅
│ - isConnecting: false
│ - isLoadingHistory: false ✅
└─────────────────┘
        ↓ Receive real-time logs
┌─────────────────┐
│ Streaming       │
│ - logs: [501]   │  (continuously growing)
│ - isConnected: true ✅
│ - isConnecting: false
│ - isLoadingHistory: false ✅
└─────────────────┘
        ↓ disconnect()
┌─────────────────┐
│ Disconnected    │
│ - logs: [501]   │  (preserved)
│ - isConnected: false
│ - isConnecting: false
│ - isLoadingHistory: false
└─────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────┐
│ Connection Error (ws.onerror)                           │
│   → setError(new Error("WebSocket connection error"))   │
│   → onError?.(error) // Optional callback                │
│   → No auto-reconnect (wait for onclose)                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Connection Closed (ws.onclose)                          │
│   → setIsConnected(false)                               │
│   → setIsConnecting(false)                              │
│   → setIsLoadingHistory(false)                          │
│   ↓                                                     │
│   IF enabled && reconnectAttempts < 5:                  │
│     → Calculate backoff delay (1s, 2s, 4s, 8s, 16s)     │
│     → setTimeout(() => connect(), delay)                 │
│   ELSE:                                                 │
│     → Stop reconnecting (max attempts reached)          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ JSON Parse Error (ws.onmessage)                         │
│   → console.error("Failed to parse message")            │
│   → Ignore message, continue listening                  │
│   → No state changes                                    │
└─────────────────────────────────────────────────────────┘
```

## UI Integration Example

```typescript
function ConsoleTab({ deviceId }: { deviceId: number }) {
  const {
    logs,
    isConnected,
    isLoadingHistory,
    error,
    clearLogs,
    reconnect
  } = useConsoleLiveStream({
    deviceId,
    enabled: true,
    maxLogs: 1000,
    onError: (err) => toast.error(err.message)
  });

  return (
    <div className="console-panel">
      {/* Header with status */}
      <div className="console-header">
        <StatusIndicator connected={isConnected} />
        {error && <ErrorBanner error={error} onRetry={reconnect} />}
        <Button onClick={clearLogs}>Clear</Button>
      </div>

      {/* Loading state */}
      {isLoadingHistory && (
        <div className="loading-overlay">
          <Spinner />
          <p>Loading console history...</p>
        </div>
      )}

      {/* Logs display */}
      {!isLoadingHistory && (
        <VirtualizedLogList logs={logs} autoScroll={isConnected} />
      )}

      {/* Footer */}
      <div className="console-footer">
        {logs.length} logs • {isConnected ? 'Live' : 'Disconnected'}
      </div>
    </div>
  );
}
```

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Initial load time | ~100-500ms | Depends on backend buffering |
| Historical logs count | ~500-1000 | Configurable via maxLogs |
| Real-time latency | <100ms | WebSocket direct connection |
| Memory usage | ~1MB per 1000 logs | Depends on message size |
| Reconnect backoff | 1s → 30s | Exponential with max 30s |
| Max reconnect attempts | 5 | Before giving up |

## Key Differences from Old Implementation

| Feature | Old (v1) | New (v2) |
|---------|----------|----------|
| Historical logs | ❌ Lost before modal opened | ✅ All logs since page load |
| Loading state | ❌ No indicator | ✅ Shows spinner while loading |
| Log handling | ❌ Always append | ✅ Replace historical, append real-time |
| Event differentiation | ❌ Single event type | ✅ Three event types |
| Backend protocol | ❌ No logType metadata | ✅ Supports logType metadata |
| UX | ⚠️ Empty on first open | ✅ Instant full history |
