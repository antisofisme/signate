# Command Execution - Quick Reference

## Command Types

| Command | Description | Parameters | WebOS | Browser |
|---------|-------------|------------|-------|---------|
| `volume` | Set audio volume | `level: 0-100` | ✅ Full | ⚠️ Video only |
| `brightness` | Set screen brightness | `level: 0-100` | ✅ Hardware | ⚠️ CSS filter |
| `screenshot` | Capture display | `quality: low/medium/high`, `upload: true/false` | ✅ Yes | ✅ Yes |
| `reboot` | Restart device | `delay: seconds` | ✅ Full reboot | ⚠️ Page reload |
| `shell` | Execute shell command | `command: string` (whitelist only) | ✅ Yes | ❌ No |
| `info` | Get device info | None | ✅ Extended | ✅ Basic |

## Command Examples

### Volume Control
```json
{
  "command_type": "volume",
  "parameters": { "level": 75 },
  "reason": "User adjustment"
}
```

### Screenshot
```json
{
  "command_type": "screenshot",
  "parameters": {
    "quality": "high",
    "upload": true
  },
  "reason": "Admin screenshot"
}
```

### Device Info
```json
{
  "command_type": "info",
  "parameters": {},
  "reason": "Diagnostics"
}
```

## Shell Command Whitelist

```
uptime                      # System uptime
date                        # Current date/time
hostname                    # Device hostname
whoami                      # Current user
df -h                       # Disk usage
free -m                     # Memory usage
ps aux | head -20          # Process list (top 20)
uname -a                    # System information
cat /proc/meminfo | head -10
cat /proc/cpuinfo | head -20
ip addr                     # Network interfaces
netstat -tuln | head -20   # Network connections
```

## Console Testing

```javascript
// Test volume
await ShellCommandExecutor.setVolume(75);

// Test brightness
await ShellCommandExecutor.setBrightness(80);

// Test screenshot (no upload)
const screenshot = await ShellCommandExecutor.takeScreenshot({
  quality: 'high',
  upload: false
});
console.log('Screenshot:', screenshot.size_kb, 'KB');

// Get device info
const info = await ShellCommandExecutor.getDeviceInfo();
console.log('Device info:', info.info);

// Check executor status
console.log(ShellCommandExecutor.getStatus());
```

## API Endpoints

### Send Command
```bash
POST /api/devices/{device_id}/commands
{
  "command_type": "volume",
  "parameters": {"level": 75},
  "reason": "User request"
}
```

### Get Pending Commands
```bash
GET /api/devices/{device_id}/commands/pending
# Returns: {commands: [...]}
```

### Report Status
```bash
POST /api/devices/{device_id}/commands/{command_id}/report
{
  "command_id": 123,
  "status": "completed",
  "executed_at": "2025-10-28T10:30:00Z",
  "result": {...},
  "error": null
}
```

## Status Flow

```
pending → running → completed
                 → failed
```

## Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Volume level must be between 0 and 100` | Invalid parameter | Use 0-100 range |
| `Command not in whitelist` | Unauthorized shell command | Use whitelisted commands only |
| `Shell commands only available on WebOS TV` | Platform limitation | Use WebOS TV device |
| `Command execution timeout after 30000ms` | Command too slow | Check device/network |
| `WebOS API error: ...` | Platform API failure | Check WebOS logs |

## Platform Detection

```javascript
// Check platform
console.log('Platform:', ShellDeviceControls.platform);
console.log('Is WebOS:', ShellDeviceControls.isWebOS);
console.log('Is Browser:', ShellDeviceControls.isBrowser);
```

## Device Controls API

### Volume
```javascript
await ShellDeviceControls.volume.set(75);
const level = await ShellDeviceControls.volume.get();
await ShellDeviceControls.volume.setMute(true);
```

### Brightness
```javascript
await ShellDeviceControls.brightness.set(80);
const level = await ShellDeviceControls.brightness.get();
```

### Power
```javascript
await ShellDeviceControls.power.reboot(3); // 3 second delay
await ShellDeviceControls.power.powerOff(); // WebOS only
```

### Network
```javascript
const info = ShellDeviceControls.network.getInfo();
const latency = await ShellDeviceControls.network.ping();
```

### Display
```javascript
await ShellDeviceControls.display.enterFullscreen();
await ShellDeviceControls.display.exitFullscreen();
const isFS = ShellDeviceControls.display.isFullscreen();
```

## Debugging

### Enable Logs
```javascript
// Browser console
localStorage.setItem('API_DEBUG', 'true');
```

### Check Module Load
```javascript
// Verify modules loaded
console.log('CommandExecutor:', !!window.ShellCommandExecutor);
console.log('DeviceControls:', !!window.ShellDeviceControls);
console.log('Commands:', !!window.ShellCommands);
```

### Monitor Command Queue
```javascript
// Check executor status
setInterval(() => {
  const status = ShellCommandExecutor.getStatus();
  console.log('Executor status:', status);
}, 5000);
```

## Security

- ✅ Shell commands whitelisted (12 safe commands only)
- ✅ Parameter validation (level: 0-100)
- ✅ Timeout protection (30s max)
- ✅ Error reporting to backend
- ✅ Platform-specific restrictions

## Performance

- Volume: ~100-500ms (WebOS) / ~10ms (browser)
- Brightness: ~100-500ms (WebOS) / ~10ms (browser)
- Screenshot: ~200-2000ms (depends on resolution)
- Reboot: 1-3s delay + restart time
- Shell: ~100-5000ms (depends on command)
- Info: ~50-200ms

## Files

- `/viewer/js/shell/command-executor.js` - Main executor (720 lines)
- `/viewer/js/shell/device-controls.js` - Device APIs (510 lines)
- `/viewer/js/shell/commands.js` - Command checker (updated)
- `/viewer/js/shell/heartbeat.js` - Heartbeat integration (updated)
- `/viewer/index.html` - Module loading (updated)
