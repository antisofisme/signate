# Command Pattern - Quick Reference Guide

## File Structure

```
js/sync/
├── commands/
│   ├── BaseCommand.js              # Base class (do not modify)
│   ├── VolumeCommand.js            # Volume control
│   ├── BrightnessCommand.js        # Screen brightness
│   ├── ScreenshotCommand.js        # Display capture
│   ├── RebootCommand.js            # Device restart
│   ├── ShellCommand.js             # Shell execution (WebOS only)
│   └── InfoCommand.js              # Device information
├── utils/
│   ├── device-info.js              # Device detection utilities
│   └── command-reporter.js         # Status reporting
└── services/
    ├── command-executor-new.js     # Orchestrator (new)
    ├── command-executor.js         # Original (deprecated)
    └── heartbeat.js                # Keepalive (existing)
```

## Usage Examples

### 1. Volume Control
```javascript
const cmd = new VolumeCommand();
try {
  const result = await cmd.executeWithTimeout({ level: 50 });
  console.log('Volume set to:', result.volume);
} catch (error) {
  console.error('Failed:', error.message);
}
```

### 2. Brightness Control
```javascript
const cmd = new BrightnessCommand();
const result = await cmd.executeWithTimeout({ level: 80 });
```

### 3. Take Screenshot
```javascript
const cmd = new ScreenshotCommand();
// Download to backend
const result = await cmd.executeWithTimeout({
  quality: 'high',
  upload: true
});

// Get base64 data
const result = await cmd.executeWithTimeout({
  quality: 'medium',
  upload: false
});
console.log(result.screenshot_base64); // data:image/jpeg;base64,...
```

### 4. Reboot Device
```javascript
const cmd = new RebootCommand();
await cmd.executeWithTimeout({ delay: 5 }); // 5 second delay
```

### 5. Execute Shell Command (WebOS Only)
```javascript
const cmd = new ShellCommand();
const result = await cmd.executeWithTimeout({ command: 'uptime' });
console.log('Output:', result.stdout);
console.log('Errors:', result.stderr);
console.log('Return code:', result.returnValue);

// Check whitelist
if (ShellCommand.isWhitelisted('df -h')) {
  // safe to execute
}
```

### 6. Get Device Info
```javascript
const cmd = new InfoCommand();
const result = await cmd.executeWithTimeout();
console.log('Device ID:', result.info.device_id);
console.log('Platform:', result.info.platform);
console.log('Memory:', result.info.memory);
console.log('Storage:', result.info.storage);
```

### 7. Use High-Level API (Recommended)
```javascript
// This is the standard way to execute commands
await window.ShellCommandExecutor.executeCommand({
  id: 123,                           // Command ID from backend
  command_type: 'volume',            // volume, brightness, screenshot, etc.
  parameters: { level: 50 },         // Command-specific parameters
  reason: 'User adjusted volume'     // Optional description
});
```

## Device Detection

### WebOS TV
```javascript
const cmd = new VolumeCommand();
if (cmd.isWebOS()) {
  // Will use luna:// service APIs
  // Real hardware control
}
```

### Browser/Desktop
```javascript
if (cmd.isBrowser()) {
  // Will use fallback implementations
  // CSS filters, DOM manipulation, localStorage
}
```

## Creating New Commands

### Step 1: Create Command Class
```javascript
class CustomCommand extends BaseCommand {
  constructor() {
    super('Custom');
  }

  validate(parameters) {
    if (!parameters.value) {
      throw new Error('value parameter required');
    }
  }

  async execute(parameters) {
    this.validate(parameters);
    this.log(`Executing with value: ${parameters.value}`);

    if (this.isWebOS()) {
      return await this._executeWebOS(parameters.value);
    } else {
      return this._executeBrowser(parameters.value);
    }
  }

  async _executeWebOS(value) {
    try {
      const response = await this.webOSRequest(
        'luna://com.webos.service.custom',
        'myMethod',
        { value }
      );
      this.log('Success');
      return { success: true, response };
    } catch (error) {
      this.logError('Failed', error);
      throw error;
    }
  }

  _executeBrowser(value) {
    this.log('Browser mode - implementing fallback');
    return { success: true, note: 'Browser fallback' };
  }
}
```

### Step 2: Add to Orchestrator
In `command-executor-new.js`, add to switch statement:
```javascript
case 'custom':
  return await this._executeCustom(parameters);
```

Then add method:
```javascript
_executeCustom: async function(parameters) {
  if (!this.commands.custom) {
    this.commands.custom = new window.CustomCommand();
  }
  return await this.commands.custom.executeWithTimeout(parameters);
}
```

### Step 3: Use It
```javascript
await window.ShellCommandExecutor.executeCommand({
  id: 1,
  command_type: 'custom',
  parameters: { value: 'test' }
});
```

## Debugging

### Check Current Execution Status
```javascript
const status = window.ShellCommandExecutor.getStatus();
console.log('Is executing:', status.is_executing);
console.log('Current command:', status.current_command);
console.log('Queue length:', status.queue_length);
```

### Enable Detailed Logging
```javascript
// All commands log with their name prefix
// [Command:Volume] Setting volume to 50%
// [Command:Screenshot] Taking screenshot
// [CommandReporter] Reporting status: completed

// View logs in browser DevTools Console tab
```

### Verify Device Info
```javascript
const platform = DeviceInfo.detectPlatform();
console.log('Platform:', platform); // 'webOS', 'Chrome', 'Firefox', etc.

const connInfo = {
  type: DeviceInfo.getConnectionType(),
  speed: DeviceInfo.getConnectionSpeed(),
  rtt: DeviceInfo.getConnectionRTT()
};
console.log('Connection:', connInfo);
```

## Error Handling

### Parameter Validation
```javascript
// Automatically checked before execution
try {
  await cmd.executeWithTimeout({ level: 150 }); // Out of range
} catch (error) {
  // "Brightness level must be between 0 and 100"
}
```

### Timeout Protection
```javascript
// All commands have 30-second timeout
try {
  await cmd.executeWithTimeout(params);
} catch (error) {
  if (error.message.includes('timeout')) {
    // Command took too long
  }
}
```

### Platform Restrictions
```javascript
const cmd = new ShellCommand();
try {
  await cmd.executeWithTimeout({ command: 'uptime' });
} catch (error) {
  if (error.message.includes('only available on WebOS')) {
    // Running on browser - not supported
  }
}
```

### Whitelist Enforcement
```javascript
const cmd = new ShellCommand();
try {
  await cmd.executeWithTimeout({ command: 'rm -rf /' });
} catch (error) {
  // "Command rejected: Not in whitelist..."
}
```

## Status Reporting

### Manual Reporting
```javascript
await CommandReporter.reportStatus(
  commandId,      // Command ID
  'completed',    // 'running', 'completed', or 'failed'
  result,         // Execution result (if successful)
  error           // Error message (if failed)
);
```

### Automatic Reporting
The orchestrator automatically reports:
1. When command starts: status='running'
2. When command completes: status='completed' + result
3. When command fails: status='failed' + error message

## Performance Tips

### Screenshot Quality
```javascript
// Low quality - smallest file, fast upload
quality: 'low'      // 0.5 JPEG quality

// Medium quality - balanced
quality: 'medium'   // 0.8 JPEG quality (default)

// High quality - best image, large file
quality: 'high'     // 0.95 JPEG quality
```

### Skip Unnecessary Uploads
```javascript
// Get screenshot without uploading
const result = await cmd.executeWithTimeout({
  quality: 'medium',
  upload: false      // Don't upload, just return base64
});
// Useful for testing or local processing
```

### Command Delays
```javascript
// Reboot with delay for graceful shutdown
await cmd.executeWithTimeout({
  delay: 10  // 10 seconds before reboot
});
// Allows current operations to finish
```

## Common Issues

### Issue: Commands Not Working
**Check:**
1. All script files loaded in correct order
2. Browser console for errors
3. Device ID set: `localStorage.getItem('device_id')`
4. API base URL configured: `window.Config.API_BASE_URL`

### Issue: Screenshot Upload Fails
**Fallback:** Returns base64 instead of URL
**Check:**
1. API endpoint `/api/screenshots/upload` exists
2. Device ID included in request
3. Sufficient storage space

### Issue: WebOS Commands Fail
**Check:**
1. Running on actual WebOS TV
2. WebOS service available: `window.webOS.service`
3. Required luna:// services accessible

### Issue: Shell Commands Not Whitelisted
**Solution:** Only approved commands allowed
**List:** `ShellCommand.getWhitelist()`
**Change:** Edit ShellCommand.js if new commands needed

## Testing Checklist

- [ ] Volume control works (WebOS and Browser)
- [ ] Brightness control works (WebOS and Browser)
- [ ] Screenshots captured and uploaded
- [ ] Reboot triggers correctly
- [ ] Shell commands execute (WebOS only)
- [ ] Device info collected completely
- [ ] Status reports sent to backend
- [ ] Timeout protection active (30s)
- [ ] Error messages descriptive
- [ ] Logging shows in console

## Integration Checklist

- [ ] All script files in HTML (in correct order)
- [ ] BaseCommand.js loaded first
- [ ] Utilities loaded before commands
- [ ] All commands loaded before orchestrator
- [ ] command-executor-new.js replaces old executor
- [ ] window.ShellCommandExecutor API available
- [ ] No console errors on page load
- [ ] Commands respond to backend requests
- [ ] Status reporting working
- [ ] Device info accessible

## Version Info

- **Command Executor:** 2.0.0 (Refactored with Command Pattern)
- **Base Version:** 1.0.0 (Original monolithic implementation)
- **Node:** Vanilla JavaScript (no dependencies)
- **Compatibility:** All browsers with canvas, WebOS TVs
