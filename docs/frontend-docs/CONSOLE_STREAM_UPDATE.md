# Console Live Stream Hook - Historical/Real-time Differentiation

## Summary

Updated `useConsoleLiveStream.ts` to properly differentiate between historical and real-time console logs according to the Hybrid Architecture design.

## Key Changes

### 1. Updated TypeScript Types

**ConsoleLogEvent**:
```typescript
interface ConsoleLogEvent {
  event: 'console.subscribed' | 'console.historical' | 'device.console_log';
  data: {
    device_id: number;
    logs?: ConsoleLog[];
    logType?: 'historical' | 'realtime';  // NEW: Metadata support
    message?: string;
  };
  timestamp: string;
}
```

**UseConsoleLiveStreamReturn**:
```typescript
interface UseConsoleLiveStreamReturn {
  logs: ConsoleLog[];
  isConnected: boolean;
  isConnecting: boolean;
  isLoadingHistory: boolean;  // NEW: Loading state
  error: Error | null;
  clearLogs: () => void;
  reconnect: () => void;
}
```

### 2. Added Loading State Management

- `isLoadingHistory` state tracks historical log loading
- Set to `true` when WebSocket opens
- Set to `false` when historical logs received
- Reset to `false` on disconnect or error

### 3. Event Handler Logic

**Three event types now handled**:

1. **console.subscribed**: Subscription confirmation
   ```typescript
   if (message.event === 'console.subscribed') {
     console.log('[ConsoleStream] Subscription confirmed:', message.data.message);
   }
   ```

2. **console.historical**: Historical logs (sent once)
   ```typescript
   else if (message.event === 'console.historical') {
     const historicalLogs = message.data.logs || [];
     console.log('[ConsoleStream] 📦 Historical logs received:', historicalLogs.length);
     setLogs(historicalLogs.slice(-maxLogs)); // REPLACE existing
     setIsLoadingHistory(false);
   }
   ```

3. **device.console_log**: Real-time logs (continuous)
   ```typescript
   else if (message.event === 'device.console_log' && message.data.logs) {
     const logType = message.data.logType || 'realtime';

     if (logType === 'historical') {
       // Alternative: Backend uses same event with metadata
       setLogs(message.data.logs.slice(-maxLogs)); // REPLACE
       setIsLoadingHistory(false);
     } else {
       // Real-time logs
       setLogs((prev) => {
         const newLogs = [...prev, ...message.data.logs!];
         return newLogs.slice(-maxLogs); // APPEND
       });
     }
   }
   ```

## Behavior Differences

### Historical Logs (Sent Once)
- **Event**: `console.historical` OR `device.console_log` with `logType: 'historical'`
- **Action**: REPLACE existing logs (`setLogs(newLogs)`)
- **Purpose**: Load all buffered logs since player page load
- **Loading**: Sets `isLoadingHistory` to `false`
- **Example**: 500 logs buffered since player started

### Real-time Logs (Continuous)
- **Event**: `device.console_log` with `logType: 'realtime'` (or no logType)
- **Action**: APPEND to existing logs (`setLogs(prev => [...prev, ...newLogs])`)
- **Purpose**: Stream new logs as they occur
- **Loading**: No effect on loading state
- **Example**: New log every 2-3 seconds

## Benefits

1. **Clear Separation**: Historical vs real-time handling is explicit
2. **Better UX**: Show loading spinner while waiting for history
3. **No Duplication**: Historical logs replace (not append)
4. **Flexible Protocol**: Supports both separate events and metadata approach
5. **State Management**: Proper loading state tracking

## UI Integration

Parent components can now use `isLoadingHistory`:

```typescript
const { logs, isConnected, isLoadingHistory } = useConsoleLiveStream({
  deviceId,
  enabled: isOpen,
});

return (
  <>
    {isLoadingHistory && <LoadingSpinner />}
    {!isLoadingHistory && logs.map(log => <LogEntry key={...} log={log} />)}
  </>
);
```

## Backend Requirements

Backend must send:

1. **On subscribe**:
   - `console.subscribed` (confirmation)
   - `console.historical` (all buffered logs) OR `device.console_log` with `logType: 'historical'`

2. **Continuous**:
   - `device.console_log` (real-time logs)

## Testing Checklist

- [ ] Historical logs load on modal open
- [ ] Loading spinner shows while waiting for history
- [ ] Historical logs replace existing state (not append)
- [ ] Real-time logs append to existing state
- [ ] No log duplication
- [ ] Loading state resets on disconnect
- [ ] Multiple subscribers don't duplicate logs
- [ ] Reconnect handles state properly

## File Location

**Updated**: `/mnt/g/khoirul/signate/cms-vite/src/features/devices/hooks/useConsoleLiveStream.ts`

## Architecture Reference

See `/tmp/CONSOLE_STREAMING_HYBRID_ARCHITECTURE.md` for full architecture design.
