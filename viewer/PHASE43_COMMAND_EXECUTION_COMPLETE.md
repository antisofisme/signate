# Phase 4.3: Device Command Execution - COMPLETE ✅

**Status**: Production-Ready
**Date**: 2025-10-28
**Version**: 1.0.0

## Overview

Implemented comprehensive device command execution system in the viewer that receives and executes commands from the backend with security, timeout protection, and result reporting.

## Files Created

### 1. `/viewer/js/shell/command-executor.js` (720 lines)
Main command execution engine with support for 6 command types.

**Features**:
- Secure command execution with whitelist
- WebOS TV API integration
- Browser fallbacks for testing
- Timeout protection (30s max)
- Result reporting back to backend
- Execution queue management

**Supported Commands**:
1. **volume**: Set audio volume (0-100%)
2. **brightness**: Set screen brightness (0-100%)
3. **screenshot**: Capture current display (with upload option)
4. **reboot**: Restart device (with delay)
5. **shell**: Execute whitelisted shell commands (WebOS only, heavily restricted)
6. **info**: Get detailed device information

**Command Execution Flow**:
```javascript
// 1. Command received from backend
{
  id: 123,
  command_type: 'volume',
  parameters: { level: 75 },
  reason: 'User request from web admin'
}

// 2. Executor validates and executes
await ShellCommandExecutor.executeCommand(command);

// 3. Reports status
- 'running' → Command started
- 'completed' → Command succeeded (with result)
- 'failed' → Command failed (with error)
```

**Security Features**:
- Shell command whitelist (only 12 safe commands)
- Parameter validation (level 0-100 for volume/brightness)
- Timeout protection (30s max execution time)
- Error handling and logging

**Shell Command Whitelist**:
```javascript
[
  'uptime',           // System uptime
  'date',             // Current date/time
  'hostname',         // Device hostname
  'whoami',           // Current user
  'df -h',            // Disk usage
  'free -m',          // Memory usage
  'ps aux | head -20', // Process list
  'uname -a',         // System info
  'cat /proc/meminfo | head -10',
  'cat /proc/cpuinfo | head -20',
  'ip addr',          // Network interfaces
  'netstat -tuln | head -20' // Network connections
]
```

### 2. `/viewer/js/shell/device-controls.js` (510 lines)
Low-level device control utilities with platform detection.

**Modules**:

#### Volume Controls
```javascript
// Set volume
await ShellDeviceControls.volume.set(75);

// Get current volume
const level = await ShellDeviceControls.volume.get();

// Mute/unmute
await ShellDeviceControls.volume.setMute(true);
```

#### Brightness Controls
```javascript
// Set brightness
await ShellDeviceControls.brightness.set(80);

// Get current brightness
const level = await ShellDeviceControls.brightness.get();
```

#### Power Controls
```javascript
// Reboot with 1 second delay
await ShellDeviceControls.power.reboot(1);

// Power off (WebOS only)
await ShellDeviceControls.power.powerOff();
```

#### System Information
```javascript
// Get system info
const info = await ShellDeviceControls.system.getInfo();

// Get memory info
const memory = ShellDeviceControls.system.getMemoryInfo();
```

#### Network Controls
```javascript
// Get network info
const netInfo = ShellDeviceControls.network.getInfo();

// Get WiFi info (WebOS only)
const wifiInfo = await ShellDeviceControls.network.getWiFiInfo();

// Ping test
const latency = await ShellDeviceControls.network.ping();
```

#### Display Controls
```javascript
// Fullscreen
await ShellDeviceControls.display.enterFullscreen();
await ShellDeviceControls.display.exitFullscreen();

// Check fullscreen state
const isFullscreen = ShellDeviceControls.display.isFullscreen();

// Get orientation
const orientation = ShellDeviceControls.display.getOrientation();
```

**Platform Detection**:
- Detects WebOS TV, Tizen, Android TV, Chrome, Firefox, Safari, Edge
- Uses WebOS luna:// APIs when available
- Falls back to HTML5 APIs in browsers

### 3. Updated `/viewer/js/shell/commands.js` (+50 lines)
Added advanced command support alongside legacy commands.

**New Method**:
```javascript
// Check for advanced commands (volume, brightness, screenshot, etc.)
await ShellCommands.checkAdvancedCommands();
```

**Integration**:
- Legacy commands: reset, refresh, reload, run_speed_test
- Advanced commands: volume, brightness, screenshot, reboot, shell, info
- Both types coexist without conflicts

### 4. Updated `/viewer/js/shell/heartbeat.js` (+6 lines)
Integrated advanced command checking into heartbeat cycle.

**Flow**:
```javascript
// Every 30 seconds
1. Send heartbeat
2. Check legacy commands (reset, refresh, reload, speed_test)
3. Check advanced commands (volume, brightness, screenshot, reboot, shell, info)
4. Check display settings
```

### 5. Updated `/viewer/index.html` (+2 scripts)
Added command executor and device controls to module loading.

**Load Order**:
```html
<!-- Device controls (low-level APIs) -->
<script src="js/shell/device-controls.js?v=20251028-phase43"></script>

<!-- Command executor (uses device controls) -->
<script src="js/shell/command-executor.js?v=20251028-phase43"></script>

<!-- Heartbeat (checks for commands) -->
<script src="js/shell/heartbeat.js?v=20251028-phase43-commands"></script>

<!-- Legacy commands (reset, refresh, reload) -->
<script src="js/shell/commands.js?v=20251028-phase43-commands"></script>
```

## Command Examples

### 1. Volume Control
```javascript
// Backend sends
{
  id: 101,
  command_type: 'volume',
  parameters: { level: 75 },
  reason: 'User adjustment from web admin'
}

// Viewer executes
await ShellCommandExecutor.executeCommand(command);

// Result
{
  volume: 75,
  success: true,
  method: 'webos_api', // or 'html5_video' or 'preference_only'
  response: {...}
}
```

### 2. Brightness Control
```javascript
// Backend sends
{
  id: 102,
  command_type: 'brightness',
  parameters: { level: 80 },
  reason: 'Scheduled brightness adjustment'
}

// Result
{
  brightness: 80,
  success: true,
  method: 'webos_api', // or 'css_filter'
  response: {...}
}
```

### 3. Screenshot Capture
```javascript
// Backend sends
{
  id: 103,
  command_type: 'screenshot',
  parameters: {
    quality: 'high',  // 'low', 'medium', 'high'
    upload: true      // Upload to backend
  },
  reason: 'Admin requested device screenshot'
}

// Result (with upload)
{
  success: true,
  uploaded: true,
  screenshot_url: '/uploads/screenshots/screenshot_123456.jpg',
  size_bytes: 245678,
  size_kb: 240,
  width: 1920,
  height: 1080,
  quality: 'high'
}

// Result (without upload - base64)
{
  success: true,
  uploaded: false,
  screenshot_base64: 'data:image/jpeg;base64,/9j/4AAQSkZJRg...',
  size_bytes: 245678,
  size_kb: 240,
  width: 1920,
  height: 1080,
  quality: 'high'
}
```

### 4. Device Reboot
```javascript
// Backend sends
{
  id: 104,
  command_type: 'reboot',
  parameters: { delay: 3 }, // 3 seconds
  reason: 'Scheduled maintenance reboot'
}

// Result
{
  rebooting: true,
  method: 'webos_api', // or 'page_reload'
  delay_seconds: 3
}
```

### 5. Shell Command (WebOS Only)
```javascript
// Backend sends
{
  id: 105,
  command_type: 'shell',
  parameters: { command: 'uptime' },
  reason: 'System diagnostics'
}

// Result
{
  success: true,
  command: 'uptime',
  stdout: ' 10:23:45 up 5 days,  2:15,  1 user,  load average: 0.12, 0.08, 0.05',
  stderr: '',
  returnValue: true,
  method: 'webos_sdkagent'
}
```

### 6. Device Info
```javascript
// Backend sends
{
  id: 106,
  command_type: 'info',
  parameters: {},
  reason: 'Collect device diagnostics'
}

// Result
{
  success: true,
  info: {
    device_id: '42',
    device_code: 'ABC123',
    activation_status: 'activated',
    screen_width: 1920,
    screen_height: 1080,
    viewport_width: 1920,
    viewport_height: 1080,
    device_pixel_ratio: 1,
    color_depth: 24,
    platform: 'webOS',
    user_agent: 'Mozilla/5.0 ...',
    language: 'en-US',
    online: true,
    connection_type: '4g',
    connection_speed: 10.5,
    connection_rtt: 50,
    memory: {
      used_mb: 256,
      total_mb: 512,
      limit_mb: 1024
    },
    storage: {
      localStorage: { used_kb: 45 },
      quota: { usage_mb: 120, quota_mb: 1024, percent_used: 12 }
    },
    webos_version: '6.0',
    timestamp: '2025-10-28T10:30:00.000Z'
  }
}
```

## Status Reporting

Commands report status at 3 stages:

### 1. Running
```javascript
{
  command_id: 101,
  status: 'running',
  executed_at: '2025-10-28T10:30:00.000Z',
  result: null,
  error: null
}
```

### 2. Completed
```javascript
{
  command_id: 101,
  status: 'completed',
  executed_at: '2025-10-28T10:30:05.000Z',
  result: { volume: 75, success: true, method: 'webos_api' },
  error: null
}
```

### 3. Failed
```javascript
{
  command_id: 101,
  status: 'failed',
  executed_at: '2025-10-28T10:30:05.000Z',
  result: null,
  error: 'Volume level must be between 0 and 100'
}
```

## Error Handling

### Timeout Protection
```javascript
// Command execution timeout: 30 seconds
const result = await Promise.race([
  executeCommandInternal(command),
  createTimeoutPromise(30000)
]);

// If timeout occurs
throw new Error('Command execution timeout after 30000ms');
```

### Validation Errors
```javascript
// Invalid volume level
if (level < 0 || level > 100) {
  throw new Error('Volume level must be between 0 and 100');
}
```

### Shell Command Security
```javascript
// Command not in whitelist
if (!SHELL_WHITELIST.includes(command)) {
  throw new Error('Command rejected: Not in whitelist');
}

// WebOS not available
if (!window.webOS) {
  throw new Error('Shell commands only available on WebOS TV platform');
}
```

### API Failures
```javascript
// WebOS API failure
window.webOS.service.request('luna://...', {
  method: 'setVolume',
  onSuccess: (res) => resolve(res),
  onFailure: (err) => reject(new Error(err.errorText || 'Unknown error'))
});
```

## Platform Support

### WebOS TV (Full Support)
- ✅ Volume control via luna://com.webos.audio
- ✅ Brightness control via luna://com.webos.settingsservice
- ✅ Screenshot capture (video frame or DOM)
- ✅ Reboot via luna://com.webos.service.tvpower
- ✅ Shell commands via luna://com.webos.service.sdkagent (whitelisted)
- ✅ Device info (WebOS specific fields)

### Tizen TV (Partial Support)
- ⚠️ Volume/brightness may need Tizen-specific APIs
- ✅ Screenshot capture (video frame or DOM)
- ✅ Reboot (page reload)
- ❌ Shell commands not available
- ✅ Device info (basic fields)

### Browser (Fallback Support)
- ⚠️ Volume control (HTML5 video elements only)
- ⚠️ Brightness control (CSS filter, not hardware)
- ✅ Screenshot capture (canvas API)
- ⚠️ Reboot (page reload only)
- ❌ Shell commands not available
- ✅ Device info (basic fields)

## Testing Commands

### Console Testing (Browser)
```javascript
// Test volume
await ShellCommandExecutor.setVolume(75);

// Test brightness
await ShellCommandExecutor.setBrightness(80);

// Test screenshot
const screenshot = await ShellCommandExecutor.takeScreenshot({ quality: 'high', upload: false });
console.log('Screenshot size:', screenshot.size_kb, 'KB');

// Test device info
const info = await ShellCommandExecutor.getDeviceInfo();
console.log('Device info:', info);

// Test reboot (WARNING: will reload page)
// await ShellCommandExecutor.reboot({ delay: 3 });

// Get executor status
const status = ShellCommandExecutor.getStatus();
console.log('Executor status:', status);
```

### Backend API Testing
```bash
# Send volume command
curl -X POST http://192.168.5.12:8001/api/devices/1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "volume",
    "parameters": {"level": 75},
    "reason": "Test volume control"
  }'

# Send screenshot command
curl -X POST http://192.168.5.12:8001/api/devices/1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "screenshot",
    "parameters": {"quality": "high", "upload": true},
    "reason": "Test screenshot capture"
  }'

# Send device info command
curl -X POST http://192.168.5.12:8001/api/devices/1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "info",
    "parameters": {},
    "reason": "Collect diagnostics"
  }'

# Check pending commands
curl http://192.168.5.12:8001/api/devices/1/commands/pending

# Check command status
curl http://192.168.5.12:8001/api/devices/1/commands/123
```

## Integration with Backend

### Backend API Endpoints Required

1. **GET /api/devices/{id}/commands/pending**
   - Returns list of pending commands for device
   - Called every 30s during heartbeat

2. **POST /api/devices/{id}/commands/{command_id}/report**
   - Reports command execution status
   - Called 3 times per command (running, completed/failed)

3. **POST /api/screenshots/upload** (Optional)
   - Uploads screenshot blob
   - Returns screenshot URL

### Backend Command Model
```python
class DeviceCommand(Base):
    id: int
    device_id: int
    command_type: str  # 'volume', 'brightness', 'screenshot', 'reboot', 'shell', 'info'
    parameters: dict   # Command-specific params
    reason: str        # Human-readable reason
    status: str        # 'pending', 'running', 'completed', 'failed'
    result: dict       # Execution result (if completed)
    error: str         # Error message (if failed)
    executed_at: datetime
    created_at: datetime
```

## Security Considerations

### Shell Command Whitelist
- Only 12 safe, read-only commands allowed
- No destructive commands (rm, dd, etc.)
- No file system modifications
- No network configuration changes
- No package installations

### Parameter Validation
- Volume/brightness: 0-100 range enforced
- Screenshot quality: limited to low/medium/high
- Reboot delay: reasonable delay required (1-10s)

### Timeout Protection
- All commands timeout after 30 seconds
- Prevents hanging/stuck executions
- Ensures responsive system

### Error Reporting
- All errors reported back to backend
- Security violations logged
- Execution failures tracked

## Performance

### Command Execution Times (Estimated)
- Volume: 100-500ms (WebOS API) / 10ms (browser)
- Brightness: 100-500ms (WebOS API) / 10ms (browser CSS)
- Screenshot: 200-2000ms (depends on resolution and quality)
- Reboot: 1-3s delay + restart time
- Shell: 100-5000ms (depends on command)
- Info: 50-200ms (data collection only)

### Heartbeat Integration
- Commands checked every 30 seconds
- Legacy commands checked first
- Advanced commands checked second
- No performance impact on playback

## Future Enhancements

### Phase 4.4: WebSocket Support (Next)
- Real-time command delivery (no 30s polling delay)
- Bi-directional communication
- Command acknowledgment
- Live status updates

### Phase 4.5: Command Queue
- Execute multiple commands in sequence
- Priority-based execution
- Batch command support
- Scheduling support

### Phase 4.6: Advanced Commands
- Audio settings (equalizer, balance)
- Picture settings (contrast, saturation, color temp)
- Network diagnostics (traceroute, DNS lookup)
- App management (launch, close, list)
- Remote debugging (logs, performance metrics)

## Files Modified/Created

### Created
1. `/viewer/js/shell/command-executor.js` (720 lines)
2. `/viewer/js/shell/device-controls.js` (510 lines)

### Modified
1. `/viewer/js/shell/commands.js` (+50 lines)
2. `/viewer/js/shell/heartbeat.js` (+6 lines)
3. `/viewer/index.html` (+2 script tags)

### Documentation
1. `/viewer/PHASE43_COMMAND_EXECUTION_COMPLETE.md` (this file)

## Total Implementation

- **Lines of Code**: ~1,280 new lines
- **Files Created**: 2 core modules
- **Files Modified**: 3 integration files
- **Supported Commands**: 6 types
- **Shell Whitelist**: 12 safe commands
- **Platform Support**: WebOS (full), Tizen (partial), Browser (fallback)
- **Security**: Whitelist + validation + timeout
- **Production Ready**: YES ✅

## Deployment Instructions

### 1. Deploy to Server
```bash
# From local machine
cd /mnt/g/khoirul/signate
sshpass -p 'Password@2021' scp -r viewer/js/shell/command-executor.js viewer/js/shell/device-controls.js viewer/index.html gzjbbk@192.168.5.12:/home/gzjbbk/signate/viewer/
```

### 2. Clear Browser Cache
- Hard refresh viewer: Ctrl+Shift+R
- Or restart device

### 3. Verify Loading
```javascript
// Open browser console on viewer
console.log('CommandExecutor:', window.ShellCommandExecutor);
console.log('DeviceControls:', window.ShellDeviceControls);

// Check status
console.log(ShellCommandExecutor.getStatus());
```

### 4. Test Command
```bash
# Send test command from backend
curl -X POST http://192.168.5.12:8001/api/devices/1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "info",
    "parameters": {},
    "reason": "Test Phase 4.3 implementation"
  }'
```

### 5. Monitor Execution
- Check browser console for "[CommandExecutor]" logs
- Check backend logs for status reports
- Verify command status in database

## Summary

✅ **Phase 4.3 Complete**: Device command execution fully implemented with:
- 6 command types supported (volume, brightness, screenshot, reboot, shell, info)
- Secure shell command whitelist (12 commands)
- WebOS TV API integration with browser fallbacks
- Timeout protection (30s max)
- Result reporting back to backend
- Production-ready error handling
- Comprehensive device controls library

🎯 **Next Phase**: Phase 4.4 - WebSocket integration for real-time command delivery
