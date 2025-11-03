# HTML Integration Guide - Command Pattern

## Script Loading Order

The scripts must be loaded in a specific order for proper initialization. Use this exact order in your HTML:

### Complete Integration Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Player Application</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div id="app">
        <!-- Your app content -->
    </div>

    <!-- ===== CRITICAL: Load in this exact order ===== -->

    <!-- 1. FIRST: Config and dependencies -->
    <script src="js/config/config.js"></script>
    <script src="js/core/utils/eventBus.js"></script>
    <script src="js/core/api/endpoints.js"></script>

    <!-- 2. SECOND: State management -->
    <script src="js/sync/activation/init.js"></script>
    <script src="js/sync/services/heartbeat.js"></script>

    <!-- 3. THIRD: Command Pattern - Base class FIRST -->
    <script src="js/sync/commands/BaseCommand.js"></script>

    <!-- 4. FOURTH: Command Pattern - Utilities -->
    <script src="js/sync/utils/device-info.js"></script>
    <script src="js/sync/utils/command-reporter.js"></script>

    <!-- 5. FIFTH: Command Pattern - All command classes -->
    <script src="js/sync/commands/VolumeCommand.js"></script>
    <script src="js/sync/commands/BrightnessCommand.js"></script>
    <script src="js/sync/commands/ScreenshotCommand.js"></script>
    <script src="js/sync/commands/RebootCommand.js"></script>
    <script src="js/sync/commands/ShellCommand.js"></script>
    <script src="js/sync/commands/InfoCommand.js"></script>

    <!-- 6. SIXTH: Command Pattern - Orchestrator (NEW) -->
    <script src="js/sync/services/command-executor-new.js"></script>

    <!-- 7. OPTIONAL: Old executor (for transition period only) -->
    <!-- <script src="js/sync/services/command-executor.js"></script> -->

    <!-- 8. LAST: Application initialization -->
    <script src="js/main.js"></script>

    <!-- ===== Initialization code (optional) ===== -->
    <script>
        // Verify all modules loaded
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Checking command pattern modules...');

            // Check base class
            if (window.BaseCommand) {
                console.log('✓ BaseCommand loaded');
            }

            // Check utilities
            if (window.DeviceInfo) {
                console.log('✓ DeviceInfo loaded');
            }
            if (window.CommandReporter) {
                console.log('✓ CommandReporter loaded');
            }

            // Check commands
            const commands = [
                'VolumeCommand',
                'BrightnessCommand',
                'ScreenshotCommand',
                'RebootCommand',
                'ShellCommand',
                'InfoCommand'
            ];

            commands.forEach(cmd => {
                if (window[cmd]) {
                    console.log(`✓ ${cmd} loaded`);
                } else {
                    console.error(`✗ ${cmd} NOT loaded`);
                }
            });

            // Check orchestrator
            if (window.ShellCommandExecutor) {
                console.log('✓ ShellCommandExecutor (orchestrator) loaded');
                console.log('Ready to receive commands');
            } else {
                console.error('✗ ShellCommandExecutor NOT loaded');
            }
        });
    </script>
</body>
</html>
```

## Minimal Integration

If you want a faster load, here's the minimal version:

```html
<!-- Minimal Command Pattern Integration -->

<!-- 1. Base class -->
<script src="js/sync/commands/BaseCommand.js"></script>

<!-- 2. Utilities -->
<script src="js/sync/utils/device-info.js"></script>
<script src="js/sync/utils/command-reporter.js"></script>

<!-- 3. Commands (can be combined into single file if needed) -->
<script src="js/sync/commands/VolumeCommand.js"></script>
<script src="js/sync/commands/BrightnessCommand.js"></script>
<script src="js/sync/commands/ScreenshotCommand.js"></script>
<script src="js/sync/commands/RebootCommand.js"></script>
<script src="js/sync/commands/ShellCommand.js"></script>
<script src="js/sync/commands/InfoCommand.js"></script>

<!-- 4. Orchestrator -->
<script src="js/sync/services/command-executor-new.js"></script>
```

## Transition Path (Old to New)

### Phase 1: Dual Loading (For Testing)
Keep both old and new executors loaded:

```html
<!-- Old executor (current) -->
<script src="js/sync/services/command-executor.js"></script>

<!-- New executor (parallel) -->
<script src="js/sync/commands/BaseCommand.js"></script>
<script src="js/sync/utils/device-info.js"></script>
<script src="js/sync/utils/command-reporter.js"></script>
<script src="js/sync/commands/VolumeCommand.js"></script>
<script src="js/sync/commands/BrightnessCommand.js"></script>
<script src="js/sync/commands/ScreenshotCommand.js"></script>
<script src="js/sync/commands/RebootCommand.js"></script>
<script src="js/sync/commands/ShellCommand.js"></script>
<script src="js/sync/commands/InfoCommand.js"></script>
<script src="js/sync/services/command-executor-new.js"></script>
```

### Phase 2: Verify New Works
```javascript
// Test new executor in console
await window.ShellCommandExecutor.executeCommand({
  id: 999,
  command_type: 'info',
  parameters: {}
});

// Check logs for successful execution
```

### Phase 3: Remove Old
Once verified, comment out old executor:
```html
<!-- Old executor (deprecated - keeping for rollback) -->
<!-- <script src="js/sync/services/command-executor.js"></script> -->
```

### Phase 4: Full Cleanup
After 2-4 weeks with no issues, delete old executor:
```bash
# Safe to delete
rm js/sync/services/command-executor.js
```

## File Size Impact

### Current Setup (Old Executor Only)
```
command-executor.js: 27 KB
Total: 27 KB
```

### New Setup (New Executor)
```
BaseCommand.js:           5 KB
device-info.js:           4 KB
command-reporter.js:      2 KB
VolumeCommand.js:         4 KB
BrightnessCommand.js:     4 KB
ScreenshotCommand.js:     8 KB
RebootCommand.js:         4 KB
ShellCommand.js:          5 KB
InfoCommand.js:           8 KB
command-executor-new.js:  6 KB
Total:                   50 KB
```

**Note:** Slightly larger due to documentation, but gzip will reduce this. In production, consider bundling/minifying.

## Bundling Considerations

If using a bundler (webpack, rollup, vite):

### CommonJS / ES6 Module Syntax
All files support both:
```javascript
// CommonJS
const BaseCommand = require('js/sync/commands/BaseCommand');
const cmd = new BaseCommand('test');

// ES6
import BaseCommand from 'js/sync/commands/BaseCommand';
```

### Example Rollup Config
```javascript
// rollup.config.js
export default {
  input: 'js/main.js',
  external: [],
  output: {
    file: 'dist/app.js',
    format: 'iife'
  }
};
```

### Example Webpack Entry
```javascript
// webpack.config.js
module.exports = {
  entry: {
    commands: './js/sync/commands/index.js',
    app: './js/main.js'
  },
  output: {
    filename: '[name].bundle.js'
  }
};
```

## Loading Verification

Add this to your page to verify all modules loaded:

```html
<script>
function verifyCommandPatternModules() {
  const required = {
    'BaseCommand': 'Base command class',
    'DeviceInfo': 'Device info utility',
    'CommandReporter': 'Status reporter',
    'VolumeCommand': 'Volume command',
    'BrightnessCommand': 'Brightness command',
    'ScreenshotCommand': 'Screenshot command',
    'RebootCommand': 'Reboot command',
    'ShellCommand': 'Shell command',
    'InfoCommand': 'Info command'
  };

  let allLoaded = true;

  for (const [name, description] of Object.entries(required)) {
    if (window[name]) {
      console.log(`✓ ${name}: ${description}`);
    } else {
      console.error(`✗ ${name}: NOT LOADED`);
      allLoaded = false;
    }
  }

  // Check orchestrator
  if (window.ShellCommandExecutor &&
      window.ShellCommandExecutor.executeCommand) {
    console.log('✓ ShellCommandExecutor: Orchestrator ready');
  } else {
    console.error('✗ ShellCommandExecutor: NOT ready');
    allLoaded = false;
  }

  if (allLoaded) {
    console.log('\nAll command pattern modules loaded successfully!');
  } else {
    console.error('\nSome modules failed to load. Check file paths and order.');
  }

  return allLoaded;
}

// Run on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', verifyCommandPatternModules);
} else {
  verifyCommandPatternModules();
}
</script>
```

## Debugging Script Loading

### Check What's Loaded
```javascript
// In browser console
Object.keys(window).filter(k => k.includes('Command'))
// Shows all loaded command classes

Object.keys(window).filter(k => k.includes('Device') || k.includes('Reporter'))
// Shows utilities
```

### Enable Verbose Logging
Each module logs on load:
```
[CommandExecutor] Loaded - Command Pattern architecture active
[Command:Volume] Module loaded
[Command:Brightness] Module loaded
// ... etc
```

### Check Individual Modules
```javascript
// Test a command
const cmd = new window.VolumeCommand();
console.log(cmd.name); // "Volume"
console.log(cmd.isWebOS()); // true or false
```

## Production Checklist

- [ ] All 10 script files included
- [ ] Scripts in correct loading order
- [ ] No console errors on load
- [ ] window.ShellCommandExecutor available
- [ ] All command classes instantiate
- [ ] window.BaseCommand available
- [ ] window.DeviceInfo available
- [ ] window.CommandReporter available
- [ ] Config and API endpoints loaded first
- [ ] Heartbeat service loaded before executor

## Performance Optimization

### Lazy Load Commands (Optional)
Instead of loading all commands upfront, load only when needed:

```html
<!-- Load base + essentials only -->
<script src="js/sync/commands/BaseCommand.js"></script>
<script src="js/sync/utils/device-info.js"></script>
<script src="js/sync/utils/command-reporter.js"></script>
<script src="js/sync/services/command-executor-new.js"></script>

<!-- Load specific commands when needed -->
<script>
// In command-executor-new.js, modify orchestrator:
_executeVolume: async function(parameters) {
  if (!this.commands.volume) {
    // Lazy load script
    await this._loadScript('js/sync/commands/VolumeCommand.js');
    this.commands.volume = new window.VolumeCommand();
  }
  return await this.commands.volume.executeWithTimeout(parameters);
},

_loadScript: function(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = resolve;
    script.onerror = reject;
    document.body.appendChild(script);
  });
}
</script>
```

## CDN Setup (Alternative)

If hosting scripts on CDN:

```html
<!-- CDN-based loading -->
<script src="https://cdn.example.com/command-pattern/v2.0.0/BaseCommand.js"></script>
<script src="https://cdn.example.com/command-pattern/v2.0.0/device-info.js"></script>
<script src="https://cdn.example.com/command-pattern/v2.0.0/command-reporter.js"></script>
<script src="https://cdn.example.com/command-pattern/v2.0.0/VolumeCommand.js"></script>
<script src="https://cdn.example.com/command-pattern/v2.0.0/BrightnessCommand.js"></script>
<script src="https://cdn.example.com/command-pattern/v2.0.0/ScreenshotCommand.js"></script>
<script src="https://cdn.example.com/command-pattern/v2.0.0/RebootCommand.js"></script>
<script src="https://cdn.example.com/command-pattern/v2.0.0/ShellCommand.js"></script>
<script src="https://cdn.example.com/command-pattern/v2.0.0/InfoCommand.js"></script>
<script src="https://cdn.example.com/command-pattern/v2.0.0/command-executor-new.js"></script>
```

## Rollback Steps

If you need to revert to old executor:

1. Remove new command scripts from HTML
2. Uncomment old executor script
3. Reload page
4. Verify commands work (old logs should appear)

```html
<!-- Remove these -->
<!-- <script src="js/sync/commands/BaseCommand.js"></script> -->
<!-- <script src="js/sync/utils/device-info.js"></script> -->
<!-- ... etc ... -->

<!-- Use this -->
<script src="js/sync/services/command-executor.js"></script>
```

No data migration needed - it's a pure replacement of the execution layer.
