# Console Interceptor - Implementation Guide

## Quick Start

This guide provides step-by-step instructions to implement the Console Interceptor in player-vite.

---

## Step 1: Create Type Definitions

**File**: `/src/shared/logger/console-interceptor.types.ts`

Copy the complete TypeScript interfaces from the architecture document (Section 2.2).

**Verification**:
```bash
cd /mnt/g/khoirul/signate/player-vite
npx tsc --noEmit src/shared/logger/console-interceptor.types.ts
```

---

## Step 2: Create Circular Reference Handler

**File**: `/src/shared/logger/console-circular-replacer.ts`

Copy the complete implementation from the architecture document (Section 2.3).

**Test**:
```typescript
import { safeJSONStringify } from './console-circular-replacer';

// Test circular reference
const obj: any = { a: 1 };
obj.self = obj;

const { json, hadCircular } = safeJSONStringify(obj);
console.log('Had circular:', hadCircular); // Should be true
console.log('JSON:', json); // Should contain [Circular Reference]
```

---

## Step 3: Create Main Interceptor

**File**: `/src/shared/logger/console-interceptor.ts`

Copy the complete implementation from the architecture document (Section 2.4).

**Key Points**:
- Uses `SharedAPIClient` for backend calls
- Uses `SharedDeviceState` for device ID and token
- Uses `SharedLogger` for internal logging (no conflict!)

---

## Step 4: Update Barrel Export

**File**: `/src/shared/logger/index.ts`

Add exports:

```typescript
// Existing exports
export { SharedLogger } from './shared-logger';
export { LogNamespace } from './shared-logger';
export type { Logger, LogLevel, LogEntry, LoggerConfig } from './logger.types';

// NEW: Console Interceptor exports
export { ConsoleInterceptor } from './console-interceptor';
export type {
  ConsoleMethod,
  ConsoleLogEntry,
  ConsoleInterceptor as IConsoleInterceptor,
  ConsoleInterceptorConfig,
  SerializedArgs,
} from './console-interceptor.types';
```

---

## Step 5: Add Configuration

**File**: `/src/shared/config/config.types.ts`

Add to `AppConfig` interface:

```typescript
export interface ConsoleInterceptorConfig {
  enabled: boolean;
  flushInterval: number;
  maxBufferSize: number;
  immediateErrorSend: boolean;
  maxArgLength: number;
  captureStackTrace: boolean;
}

export interface AppConfig {
  api: ApiConfig;
  device: DeviceConfig;
  retry: RetryConfig;
  log: LogConfig;
  debug: DebugConfig;
  player: PlayerConfig;
  consoleInterceptor: ConsoleInterceptorConfig; // NEW
}
```

**File**: `/src/shared/config/index.ts` (or wherever config is defined)

Add default values:

```typescript
export const config: AppConfig = {
  // ... existing config
  consoleInterceptor: {
    enabled: true,
    flushInterval: 30000, // 30 seconds
    maxBufferSize: 100,
    immediateErrorSend: true,
    maxArgLength: 10000,
    captureStackTrace: true,
  },
};
```

---

## Step 6: Initialize in Main

**File**: `/src/main.ts`

Add initialization EARLY in the initialization chain:

```typescript
import './index.css';
import { config } from '@shared/config';
import { SharedLogger, ConsoleInterceptor } from '@shared/logger'; // Import both
import { ShellBootstrap, ShellActivationScreen } from '@shell';
// ... other imports

// Log startup
SharedLogger.log('🎬 Player-Vite Started');

/**
 * Initialize application
 */
const initApp = async () => {
  SharedLogger.log('🔍 Initializing app...');

  // ✅ NEW: Initialize console interceptor EARLY
  // This captures all subsequent console output
  ConsoleInterceptor.init();
  SharedLogger.log('📡 Console interceptor initialized');

  // ... rest of initialization
  const shellContainer = document.getElementById('shell-container');
  const playerContainer = document.getElementById('player-container');
  // ...
};

// Start app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => void initApp());
} else {
  void initApp();
}
```

**IMPORTANT**: Initialize AFTER `SharedLogger` is imported but BEFORE other services initialize.

---

## Step 7: Create Backend Endpoint

**File**: `/backend-python/services/device/console_log_routes.py` (NEW)

```python
"""
Console Logs Routes
Handles browser console logs from player devices
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from shared.database import get_db
from services.auth.dependencies import require_device_auth
from services.device.models import DeviceModel
from .console_log_models import ConsoleLogModel
from .console_log_dtos import ConsoleLogBatchRequest, ConsoleLogEntry, ConsoleLogBatchResponse

router = APIRouter(prefix="/client/console-logs", tags=["console-logs"])

@router.post("/batch", response_model=ConsoleLogBatchResponse)
async def batch_console_logs(
    request: ConsoleLogBatchRequest,
    db: Session = Depends(get_db),
    device: DeviceModel = Depends(require_device_auth),
):
    """
    Batch upload console logs from device

    Receives browser console output (log, error, warn, etc) and stores in database
    for debugging and monitoring purposes.
    """

    # Verify device_id matches authenticated device
    if request.device_id != device.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device ID mismatch"
        )

    # Insert logs into database
    stored_count = 0
    for log_entry in request.logs:
        try:
            console_log = ConsoleLogModel(
                device_id=device.id,
                level=log_entry.level,
                args=log_entry.args,
                args_count=log_entry.args_count,
                timestamp=datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00')),
                stack_trace=log_entry.stack_trace,
                source=log_entry.source,
                user_agent=log_entry.user_agent,
            )
            db.add(console_log)
            stored_count += 1
        except Exception as e:
            # Log error but continue processing other logs
            print(f"Failed to store console log: {e}")
            continue

    # Commit all logs at once (batch insert)
    db.commit()

    return ConsoleLogBatchResponse(
        received=len(request.logs),
        stored=stored_count
    )
```

**File**: `/backend-python/services/device/console_log_models.py` (NEW)

```python
"""
Console Log Database Model
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ARRAY, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from shared.database import Base

class ConsoleLogModel(Base):
    """Console logs from player devices"""
    __tablename__ = "console_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)

    # Log data
    level = Column(String(10), nullable=False, index=True)  # log, error, warn, info, debug
    args = Column(ARRAY(Text), nullable=False)  # Serialized console arguments
    args_count = Column(Integer, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)

    # Debug info
    stack_trace = Column(Text, nullable=True)
    source = Column(String(500), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    device = relationship("DeviceModel", back_populates="console_logs")
```

**File**: `/backend-python/services/device/console_log_dtos.py` (NEW)

```python
"""
Console Log DTOs
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ConsoleLogEntry(BaseModel):
    """Single console log entry"""
    level: str  # log, error, warn, info, debug
    args: List[str]
    args_count: int
    timestamp: str
    stack_trace: Optional[str] = None
    source: Optional[str] = None
    user_agent: Optional[str] = None

class ConsoleLogBatchRequest(BaseModel):
    """Batch console logs request"""
    device_id: int
    logs: List[ConsoleLogEntry]

class ConsoleLogBatchResponse(BaseModel):
    """Batch console logs response"""
    received: int
    stored: int
```

**File**: `/backend-python/services/device/models.py`

Add relationship to DeviceModel:

```python
from sqlalchemy.orm import relationship

class DeviceModel(Base):
    # ... existing code

    # NEW: Console logs relationship
    console_logs = relationship("ConsoleLogModel", back_populates="device", cascade="all, delete-orphan")
```

---

## Step 8: Create Database Migration

**File**: `/backend-python/migrations/046_create_console_logs_table.sql`

```sql
-- Migration: 046
-- Description: Create console_logs table for browser console output
-- Date: 2025-01-22

BEGIN;

-- Create console_logs table
CREATE TABLE console_logs (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  level VARCHAR(10) NOT NULL,
  args TEXT[] NOT NULL,
  args_count INTEGER NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  stack_trace TEXT,
  source VARCHAR(500),
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_console_logs_device ON console_logs(device_id);
CREATE INDEX idx_console_logs_level ON console_logs(level);
CREATE INDEX idx_console_logs_timestamp ON console_logs(timestamp);

-- Comments
COMMENT ON TABLE console_logs IS 'Browser console logs from player devices';
COMMENT ON COLUMN console_logs.level IS 'Console method: log, error, warn, info, debug';
COMMENT ON COLUMN console_logs.args IS 'Serialized console arguments (JSON-safe strings)';
COMMENT ON COLUMN console_logs.timestamp IS 'When the log was created in browser';
COMMENT ON COLUMN console_logs.stack_trace IS 'Stack trace for errors';

COMMIT;
```

---

## Step 9: Register Backend Routes

**File**: `/backend-python/main.py`

Add console log routes:

```python
from services.device.console_log_routes import router as console_log_router

# ... existing code

# Register console log routes
app.include_router(console_log_router, prefix="/api")
```

---

## Step 10: Deploy Migration

```bash
# 1. Backup database
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres pg_dump -U signage_user -d signage_db" \
  > backups/pre_migration_046_$(date +%Y%m%d_%H%M%S).sql

# 2. Stop backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml stop backend-api"

# 3. Upload migration
sshpass -p 'Password@2021' scp backend-python/migrations/046_*.sql \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/migrations/

# 4. Run migration
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signate/backend-python/migrations/046_create_console_logs_table.sql"

# 5. Sync backend code
sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' \
  backend-python/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/

# 6. Restart backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml start backend-api"

# 7. Verify
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c '\d console_logs'"
```

---

## Step 11: Test Frontend

```bash
# 1. Build player-vite
cd /mnt/g/khoirul/signate/player-vite
npm run build

# 2. Deploy to server
sshpass -p 'Password@2021' rsync -avz --delete dist/ \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/player-vite/dist/

# 3. Open player in browser
# Navigate to: http://192.168.5.12:8080/

# 4. Open browser console and test
console.log('Test log');
console.error('Test error');
console.warn('Test warning');

# 5. Wait 30 seconds or manually flush
window.ConsoleInterceptor?.flush();

# 6. Check backend logs
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker logs signage-backend-api --tail 50"

# 7. Check database
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c 'SELECT * FROM console_logs ORDER BY created_at DESC LIMIT 10'"
```

---

## Step 12: Runtime Configuration

### Enable/Disable via Console

```javascript
// Disable interceptor
ConsoleInterceptor.disable();

// Enable interceptor
ConsoleInterceptor.enable();

// Check status
console.log('Is active:', ConsoleInterceptor.isActive());
```

### Configure via localStorage

```javascript
// Disable interceptor
localStorage.setItem('CONSOLE_INTERCEPTOR_ENABLED', 'false');

// Change flush interval to 60 seconds
localStorage.setItem('CONSOLE_INTERCEPTOR_FLUSH_INTERVAL', '60000');

// Reload page for changes to take effect
location.reload();
```

### Configure via URL

```
# Disable interceptor
http://192.168.5.12:8080/?console_interceptor=false

# Enable debug mode
http://192.168.5.12:8080/?console_interceptor_debug=true
```

---

## Troubleshooting

### Issue 1: Logs not appearing in database

**Check**:
1. Device is activated: `SharedDeviceState.isActivated()`
2. Interceptor is active: `ConsoleInterceptor.isActive()`
3. Buffer has logs: `ConsoleInterceptor.getBuffer()`
4. Backend endpoint is correct in config
5. Device token is valid in localStorage

**Solution**:
```javascript
// Manually flush to test
await ConsoleInterceptor.flush();

// Check for errors
console.error('Test error'); // Should trigger immediate send
```

### Issue 2: Console not working after initialization

**Check**:
1. Interceptor preserveConsole is true (default)
2. No JavaScript errors in console
3. Original console methods are preserved

**Solution**:
```javascript
// Restore original console
ConsoleInterceptor.restore();

// Re-initialize
ConsoleInterceptor.init();
```

### Issue 3: Circular reference errors

**Check**:
1. Object has circular references
2. Serialization is using circular replacer

**Solution**:
```javascript
// Test circular replacer
import { safeJSONStringify } from '@shared/logger/console-circular-replacer';

const obj: any = { a: 1 };
obj.self = obj;

const { json, hadCircular } = safeJSONStringify(obj);
console.log('Had circular:', hadCircular); // Should be true
```

### Issue 4: High memory usage

**Check**:
1. Buffer size limit: `config.consoleInterceptor.maxBufferSize`
2. Flush interval: `config.consoleInterceptor.flushInterval`
3. Argument truncation: `config.consoleInterceptor.maxArgLength`

**Solution**:
```javascript
// Reduce buffer size
ConsoleInterceptor.configure({
  maxBufferSize: 50,
  flushInterval: 15000, // 15 seconds
  maxArgLength: 5000,
});
```

---

## Performance Monitoring

### Check Buffer Size

```javascript
// Get current buffer
const buffer = ConsoleInterceptor.getBuffer();
console.log('Buffer size:', buffer.length);

// Clear buffer manually
ConsoleInterceptor.clearBuffer();
```

### Monitor Flush Operations

```javascript
// Enable debug logging
SharedLogger.setLevel('debug');

// Flush manually and watch logs
await ConsoleInterceptor.flush();
```

### Measure Serialization Performance

```javascript
console.time('serialize');
const obj = { /* large object */ };
const { json } = safeJSONStringify(obj);
console.timeEnd('serialize');
```

---

## Best Practices

1. **Enable only in production**: Set `enabled: false` in development
2. **Monitor payload sizes**: Check backend logs for large payloads
3. **Set reasonable limits**: Don't buffer too many logs
4. **Test circular refs**: Ensure complex objects serialize correctly
5. **Use debug mode**: Enable verbose logging during testing
6. **Monitor memory**: Check browser memory usage
7. **Test error scenarios**: Verify errors are sent immediately
8. **Check backend logs**: Ensure logs are being received

---

## Verification Checklist

- [ ] TypeScript compiles without errors
- [ ] Console output still visible in browser DevTools
- [ ] Logs appear in database after 30 seconds
- [ ] Errors trigger immediate send
- [ ] Circular references handled correctly
- [ ] Buffer size limits working
- [ ] SharedLogger still works (no conflicts)
- [ ] Device token authentication works
- [ ] Backend endpoint responds correctly
- [ ] Memory usage is acceptable
- [ ] Performance impact is minimal

---

## Next Steps

After successful implementation:

1. **Monitor in production**: Watch for payload sizes and errors
2. **Analyze logs**: Use SQL queries to find common issues
3. **Optimize configuration**: Adjust buffer sizes and intervals
4. **Add analytics**: Track console error rates per device
5. **Create dashboard**: Visualize console logs in CMS admin
6. **Set up alerts**: Notify on high error rates
7. **Implement sampling**: Only send % of logs in high-volume scenarios

---

## Summary

This implementation provides:
- ✅ Browser console output capture
- ✅ Circular reference handling
- ✅ Memory-safe buffering
- ✅ Automatic backend sync
- ✅ No conflicts with SharedLogger
- ✅ Runtime configuration
- ✅ Production-ready error handling

**Estimated Time**: 4-6 hours (including testing)
