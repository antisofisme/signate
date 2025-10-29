# Device Command Execution - Examples

Quick copy-paste examples for testing and integration.

---

## Console Testing (Browser)

Open viewer in browser and paste in console:

### Test All Commands
```javascript
// 1. Volume Control
await ShellCommandExecutor.setVolume(75);
// Expected: {volume: 75, success: true, method: 'html5_video'}

// 2. Brightness Control
await ShellCommandExecutor.setBrightness(80);
// Expected: {brightness: 80, success: true, method: 'css_filter'}

// 3. Screenshot (Base64)
const screenshot = await ShellCommandExecutor.takeScreenshot({
  quality: 'high',
  upload: false
});
console.log('Screenshot:', screenshot.size_kb, 'KB');
// Expected: {success: true, uploaded: false, screenshot_base64: '...', size_kb: 240}

// 4. Device Info
const info = await ShellCommandExecutor.getDeviceInfo();
console.log('Device Info:', info.info);
// Expected: {success: true, info: {...}}

// 5. Shell Command (WebOS only)
try {
  const result = await ShellCommandExecutor.executeShell('uptime');
  console.log('Shell output:', result.stdout);
} catch (error) {
  console.log('Shell not available:', error.message);
}
// Expected WebOS: {success: true, stdout: '...'}
// Expected Browser: Error (not available)

// 6. Check Executor Status
console.log('Executor:', ShellCommandExecutor.getStatus());
// Expected: {is_executing: false, current_command: null, queue_length: 0}
```

### Test Device Controls
```javascript
// Volume
await ShellDeviceControls.volume.set(75);
const vol = await ShellDeviceControls.volume.get();
console.log('Current volume:', vol);

// Brightness
await ShellDeviceControls.brightness.set(80);
const bright = await ShellDeviceControls.brightness.get();
console.log('Current brightness:', bright);

// System Info
const sys = await ShellDeviceControls.system.getInfo();
console.log('System:', sys);

// Network Info
const net = ShellDeviceControls.network.getInfo();
console.log('Network:', net);

// Ping Test
const latency = await ShellDeviceControls.network.ping();
console.log('Ping:', latency, 'ms');
```

---

## Backend API Testing (cURL)

### Send Volume Command
```bash
curl -X POST http://192.168.5.12:8001/api/devices/1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "volume",
    "parameters": {"level": 75},
    "reason": "Test volume control"
  }'
```

### Send Brightness Command
```bash
curl -X POST http://192.168.5.12:8001/api/devices/1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "brightness",
    "parameters": {"level": 80},
    "reason": "Test brightness control"
  }'
```

### Send Screenshot Command
```bash
curl -X POST http://192.168.5.12:8001/api/devices/1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "screenshot",
    "parameters": {
      "quality": "high",
      "upload": true
    },
    "reason": "Admin screenshot request"
  }'
```

### Send Device Info Command
```bash
curl -X POST http://192.168.5.12:8001/api/devices/1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "info",
    "parameters": {},
    "reason": "Collect diagnostics"
  }'
```

### Send Shell Command (WebOS only)
```bash
curl -X POST http://192.168.5.12:8001/api/devices/1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "shell",
    "parameters": {"command": "uptime"},
    "reason": "System diagnostics"
  }'
```

### Send Reboot Command
```bash
curl -X POST http://192.168.5.12:8001/api/devices/1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "reboot",
    "parameters": {"delay": 3},
    "reason": "Scheduled maintenance"
  }'
```

### Check Pending Commands
```bash
curl http://192.168.5.12:8001/api/devices/1/commands/pending
```

### Check Command Result
```bash
curl http://192.168.5.12:8001/api/devices/1/commands/123
```

---

## JavaScript Integration Examples

### Send Command via Fetch
```javascript
async function sendCommand(deviceId, commandType, parameters, reason) {
  const response = await fetch(
    `http://192.168.5.12:8001/api/devices/${deviceId}/commands`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        command_type: commandType,
        parameters: parameters,
        reason: reason
      })
    }
  );

  const data = await response.json();
  return data;
}

// Usage
await sendCommand(1, 'volume', { level: 75 }, 'User adjustment');
await sendCommand(1, 'brightness', { level: 80 }, 'Scheduled change');
await sendCommand(1, 'screenshot', { quality: 'high', upload: true }, 'Admin request');
await sendCommand(1, 'info', {}, 'Diagnostics');
```

### Check Command Status
```javascript
async function checkCommandStatus(deviceId, commandId) {
  const response = await fetch(
    `http://192.168.5.12:8001/api/devices/${deviceId}/commands/${commandId}`
  );

  const data = await response.json();
  console.log('Command status:', data.status);
  console.log('Result:', data.result);
  console.log('Error:', data.error);

  return data;
}

// Usage
const status = await checkCommandStatus(1, 123);
```

### Poll Command Completion
```javascript
async function waitForCommandCompletion(deviceId, commandId, timeout = 30000) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const status = await checkCommandStatus(deviceId, commandId);

    if (status.status === 'completed') {
      console.log('Command completed:', status.result);
      return status;
    }

    if (status.status === 'failed') {
      throw new Error('Command failed: ' + status.error);
    }

    // Wait 1 second before checking again
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  throw new Error('Command timeout');
}

// Usage
try {
  const result = await waitForCommandCompletion(1, 123, 60000);
  console.log('Command result:', result);
} catch (error) {
  console.error('Command error:', error.message);
}
```

---

## React/TypeScript Integration

### Custom Hook
```typescript
import { useState, useEffect } from 'react';

interface CommandResult {
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

function useDeviceCommand(deviceId: number, commandId: number) {
  const [result, setResult] = useState<CommandResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch(
          `http://192.168.5.12:8001/api/devices/${deviceId}/commands/${commandId}`
        );
        const data = await response.json();
        setResult(data);

        if (data.status === 'completed' || data.status === 'failed') {
          setLoading(false);
        }
      } catch (error) {
        console.error('Error checking command status:', error);
        setLoading(false);
      }
    };

    // Check status every 2 seconds
    const interval = setInterval(checkStatus, 2000);
    checkStatus(); // Initial check

    return () => clearInterval(interval);
  }, [deviceId, commandId]);

  return { result, loading };
}

// Usage in component
function DeviceControl({ deviceId }: { deviceId: number }) {
  const [commandId, setCommandId] = useState<number | null>(null);
  const { result, loading } = useDeviceCommand(deviceId, commandId!);

  const sendVolumeCommand = async (level: number) => {
    const response = await fetch(
      `http://192.168.5.12:8001/api/devices/${deviceId}/commands`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command_type: 'volume',
          parameters: { level },
          reason: 'User adjustment'
        })
      }
    );

    const data = await response.json();
    setCommandId(data.id);
  };

  return (
    <div>
      <button onClick={() => sendVolumeCommand(75)}>
        Set Volume to 75%
      </button>

      {loading && <p>Executing command...</p>}
      {result?.status === 'completed' && <p>Success: {JSON.stringify(result.result)}</p>}
      {result?.status === 'failed' && <p>Error: {result.error}</p>}
    </div>
  );
}
```

---

## Python Backend Integration

### FastAPI Endpoint
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()

class CommandRequest(BaseModel):
    command_type: str
    parameters: Dict[str, Any]
    reason: str

class CommandStatusReport(BaseModel):
    command_id: int
    status: str
    executed_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/api/devices/{device_id}/commands")
async def create_command(device_id: int, command: CommandRequest):
    """Create a new command for device"""
    # Store command in database
    db_command = {
        "id": 123,
        "device_id": device_id,
        "command_type": command.command_type,
        "parameters": command.parameters,
        "reason": command.reason,
        "status": "pending",
        "created_at": "2025-10-28T10:30:00Z"
    }

    return {"success": True, "data": db_command}

@router.get("/api/devices/{device_id}/commands/pending")
async def get_pending_commands(device_id: int):
    """Get pending commands for device"""
    # Query database for pending commands
    pending_commands = [
        {
            "id": 123,
            "command_type": "volume",
            "parameters": {"level": 75},
            "reason": "User adjustment",
            "status": "pending"
        }
    ]

    return {"success": True, "data": {"commands": pending_commands}}

@router.post("/api/devices/{device_id}/commands/{command_id}/report")
async def report_command_status(device_id: int, command_id: int, report: CommandStatusReport):
    """Receive command execution status from viewer"""
    # Update command status in database
    print(f"Command {command_id} status: {report.status}")

    if report.result:
        print(f"Result: {report.result}")

    if report.error:
        print(f"Error: {report.error}")

    return {"success": True, "data": {"message": "Status received"}}

@router.get("/api/devices/{device_id}/commands/{command_id}")
async def get_command_status(device_id: int, command_id: int):
    """Get command status"""
    # Query database
    command = {
        "id": command_id,
        "device_id": device_id,
        "status": "completed",
        "result": {"volume": 75, "success": True},
        "error": None,
        "executed_at": "2025-10-28T10:30:05Z"
    }

    return {"success": True, "data": command}
```

---

## Expected Results

### Volume Command Result
```json
{
  "volume": 75,
  "success": true,
  "method": "webos_api",
  "response": {...}
}
```

### Brightness Command Result
```json
{
  "brightness": 80,
  "success": true,
  "method": "webos_api",
  "response": {...}
}
```

### Screenshot Command Result (with upload)
```json
{
  "success": true,
  "uploaded": true,
  "screenshot_url": "/uploads/screenshots/screenshot_1698765432.jpg",
  "size_bytes": 245678,
  "size_kb": 240,
  "width": 1920,
  "height": 1080,
  "quality": "high"
}
```

### Screenshot Command Result (without upload)
```json
{
  "success": true,
  "uploaded": false,
  "screenshot_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "size_bytes": 245678,
  "size_kb": 240,
  "width": 1920,
  "height": 1080,
  "quality": "high"
}
```

### Device Info Result
```json
{
  "success": true,
  "info": {
    "device_id": "42",
    "device_code": "ABC123",
    "activation_status": "activated",
    "screen_width": 1920,
    "screen_height": 1080,
    "viewport_width": 1920,
    "viewport_height": 1080,
    "device_pixel_ratio": 1,
    "color_depth": 24,
    "platform": "webOS",
    "user_agent": "Mozilla/5.0 ...",
    "language": "en-US",
    "online": true,
    "connection_type": "4g",
    "connection_speed": 10.5,
    "connection_rtt": 50,
    "memory": {
      "used_mb": 256,
      "total_mb": 512,
      "limit_mb": 1024
    },
    "storage": {
      "localStorage": {"used_kb": 45},
      "quota": {"usage_mb": 120, "quota_mb": 1024, "percent_used": 12}
    },
    "webos_version": "6.0",
    "timestamp": "2025-10-28T10:30:00.000Z"
  }
}
```

### Shell Command Result
```json
{
  "success": true,
  "command": "uptime",
  "stdout": " 10:23:45 up 5 days,  2:15,  1 user,  load average: 0.12, 0.08, 0.05",
  "stderr": "",
  "returnValue": true,
  "method": "webos_sdkagent"
}
```

### Reboot Command Result
```json
{
  "rebooting": true,
  "method": "webos_api",
  "delay_seconds": 3
}
```

---

## Error Examples

### Invalid Volume Level
```javascript
await ShellCommandExecutor.setVolume(150);
// Error: Volume level must be between 0 and 100
```

### Shell Command Not in Whitelist
```javascript
await ShellCommandExecutor.executeShell('rm -rf /');
// Error: Command rejected: Not in whitelist
```

### Shell Command on Browser
```javascript
await ShellCommandExecutor.executeShell('uptime');
// Error: Shell commands only available on WebOS TV platform
```

### Command Timeout
```javascript
await ShellCommandExecutor.executeCommand({...});
// Error: Command execution timeout after 30000ms
```

---

## Debugging Examples

### Enable Debug Mode
```javascript
// Enable API debug logging
localStorage.setItem('API_DEBUG', 'true');

// Or via URL
// http://192.168.5.12:8080/?api_debug=true
```

### Check Module Status
```javascript
// Check if modules loaded
console.log('Modules loaded:', {
  CommandExecutor: !!window.ShellCommandExecutor,
  DeviceControls: !!window.ShellDeviceControls,
  Commands: !!window.ShellCommands,
  Heartbeat: !!window.ShellHeartbeat
});

// Check platform
console.log('Platform:', ShellDeviceControls.platform);
console.log('WebOS:', ShellDeviceControls.isWebOS);
console.log('Browser:', ShellDeviceControls.isBrowser);

// Check executor status
console.log('Executor:', ShellCommandExecutor.getStatus());

// Check shell whitelist
console.log('Shell whitelist:', ShellCommandExecutor.SHELL_WHITELIST);
```

### Monitor Command Queue
```javascript
// Real-time monitoring
setInterval(() => {
  const status = ShellCommandExecutor.getStatus();
  if (status.is_executing || status.queue_length > 0) {
    console.log('[Monitor] Executor status:', status);
  }
}, 5000);
```

---

**Copy-paste these examples directly into your console or code for testing!**
