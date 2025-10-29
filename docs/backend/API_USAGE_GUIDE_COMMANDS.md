# Command System API - Quick Reference Guide

## Base URL
```
http://192.168.5.12:8001/api/commands
```

---

## Quick Start Examples

### 1. Adjust Volume on Single Device

```bash
curl -X POST http://192.168.5.12:8001/api/commands/execute \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 1,
    "command_type": "volume",
    "parameters": {"volume": 50},
    "reason": "Presentation mode"
  }'
```

**Response:**
```json
{
  "id": 123,
  "device_id": 1,
  "command_type": "volume",
  "status": "pending",
  "risk_level": "low",
  "created_at": "2025-10-28T10:00:00Z"
}
```

---

### 2. Take Screenshot

```bash
curl -X POST http://192.168.5.12:8001/api/commands/execute \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 1,
    "command_type": "screenshot",
    "parameters": {
      "quality": 90,
      "upload": true
    }
  }'
```

---

### 3. Reboot Device

```bash
curl -X POST http://192.168.5.12:8001/api/commands/execute \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 1,
    "command_type": "reboot",
    "parameters": {
      "delay_seconds": 60
    },
    "reason": "Weekly maintenance"
  }'
```

---

### 4. Batch Reboot (All Lobby TVs)

```bash
curl -X POST http://192.168.5.12:8001/api/commands/batch \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": [1, 2, 3, 4, 5],
    "command_type": "reboot",
    "parameters": {"delay_seconds": 30},
    "execution_mode": "sequential",
    "reason": "Maintenance window"
  }'
```

**Response:**
```json
{
  "batch_id": "batch-abc123",
  "total": 5,
  "successful": 5,
  "failed": 0,
  "results": [
    {"device_id": 1, "success": true, "command_id": 101},
    {"device_id": 2, "success": true, "command_id": 102},
    ...
  ]
}
```

---

### 5. Check Command Status

```bash
curl http://192.168.5.12:8001/api/commands/123
```

**Response:**
```json
{
  "id": 123,
  "device_id": 1,
  "device_name": "Lobby TV",
  "command_type": "volume",
  "status": "completed",
  "result": {
    "success": true,
    "previous_volume": 70,
    "new_volume": 50
  },
  "created_at": "2025-10-28T10:00:00Z",
  "completed_at": "2025-10-28T10:00:02Z"
}
```

---

### 6. List Commands for Device

```bash
curl "http://192.168.5.12:8001/api/commands/device/1?status=pending&limit=20"
```

---

### 7. Cancel Pending Command

```bash
curl -X DELETE http://192.168.5.12:8001/api/commands/123 \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Wrong device selected"
  }'
```

---

### 8. Retry Failed Command

```bash
curl -X POST http://192.168.5.12:8001/api/commands/123/retry \
  -H "Content-Type: application/json" \
  -d '{
    "reset_parameters": true
  }'
```

---

## All Available Commands

| Command Type | Description | Parameters | Risk Level | Rate Limit |
|-------------|-------------|------------|-----------|-----------|
| `volume` | Set volume level | `volume: 0-100` | LOW | 10/min |
| `brightness` | Set brightness | `brightness: 0-100` | LOW | 10/min |
| `screenshot` | Take screenshot | `quality: 1-100`, `upload: bool` | LOW | 5/min |
| `network_test` | Test network | `test_type`, `target`, `count` | LOW | 5/min |
| `clear_cache` | Clear cache | None | MEDIUM | 5/min |
| `reload` | Reload player | None | MEDIUM | 5/min |
| `refresh` | Refresh content | None | MEDIUM | 5/min |
| `reboot` | Reboot device | `delay_seconds: 0-300`, `force: bool` | MEDIUM | 3/min |
| `update` | Update system | `package`, `version`, `force` | HIGH | 1/min |
| `shell` | Execute command | `command`, `timeout: 1-60` | **CRITICAL** | 1/min |

---

## Command Parameters Reference

### Volume Command
```json
{
  "command_type": "volume",
  "parameters": {
    "volume": 50  // 0-100
  }
}
```

### Brightness Command
```json
{
  "command_type": "brightness",
  "parameters": {
    "brightness": 75  // 0-100
  }
}
```

### Screenshot Command
```json
{
  "command_type": "screenshot",
  "parameters": {
    "quality": 90,      // 1-100 (JPEG quality)
    "upload": true      // Upload to server immediately
  }
}
```

### Reboot Command
```json
{
  "command_type": "reboot",
  "parameters": {
    "delay_seconds": 60,  // 0-300
    "force": false        // Force reboot without graceful shutdown
  }
}
```

### Shell Command (ADMIN ONLY + 2FA)
```json
{
  "command_type": "shell",
  "parameters": {
    "command": "df -h",    // Max 500 chars
    "timeout": 30,         // 1-60 seconds
    "working_directory": "/opt/viewer"  // Optional
  }
}
```

### Network Test Command
```json
{
  "command_type": "network_test",
  "parameters": {
    "test_type": "ping",   // ping, traceroute, bandwidth
    "target": "8.8.8.8",   // Optional
    "count": 4             // 1-10
  }
}
```

---

## Status Values

| Status | Description |
|--------|-------------|
| `pending` | Queued, waiting to be sent |
| `sent` | Sent to device via WebSocket |
| `running` | Device is currently executing |
| `completed` | Successfully executed ✅ |
| `failed` | Execution failed ❌ |
| `cancelled` | Cancelled by admin |
| `expired` | Expired before execution (24h) |

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Command 'invalid_command' not allowed"
}
```

### 403 Forbidden
```json
{
  "detail": "Role 'editor' not authorized for command 'shell'"
}
```

### 404 Not Found
```json
{
  "detail": "Device 99999 not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "parameters", "volume"],
      "msg": "Volume must be between 0 and 100",
      "type": "value_error"
    }
  ]
}
```

### 429 Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded for 'volume' (10 requests per minute)"
}
```

---

## Common Use Cases

### Use Case 1: Morning Routine (Volume Up)

```bash
# Set volume to 70 on all guest room TVs
curl -X POST http://192.168.5.12:8001/api/commands/batch \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "command_type": "volume",
    "parameters": {"volume": 70},
    "execution_mode": "parallel",
    "reason": "Morning volume increase"
  }'
```

---

### Use Case 2: Evening Routine (Dim & Lower Volume)

```bash
# Batch: Brightness 30, Volume 30
curl -X POST http://192.168.5.12:8001/api/commands/batch \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": [1, 2, 3, 4, 5],
    "command_type": "brightness",
    "parameters": {"brightness": 30},
    "execution_mode": "parallel",
    "reason": "Evening mode"
  }'

curl -X POST http://192.168.5.12:8001/api/commands/batch \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": [1, 2, 3, 4, 5],
    "command_type": "volume",
    "parameters": {"volume": 30},
    "execution_mode": "parallel",
    "reason": "Evening mode"
  }'
```

---

### Use Case 3: Maintenance Window (Sequential Reboot)

```bash
# Reboot devices one by one (1s delay between)
curl -X POST http://192.168.5.12:8001/api/commands/batch \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": [10, 11, 12, 13, 14, 15],
    "command_type": "reboot",
    "parameters": {"delay_seconds": 5},
    "execution_mode": "sequential",
    "priority": 3,
    "reason": "Weekly maintenance reboot"
  }'
```

---

### Use Case 4: Troubleshooting (Screenshot All)

```bash
# Take screenshots of all devices for status check
curl -X POST http://192.168.5.12:8001/api/commands/batch \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": [1, 2, 3, 4, 5],
    "command_type": "screenshot",
    "parameters": {"quality": 90, "upload": true},
    "execution_mode": "parallel",
    "reason": "Status check"
  }'
```

---

### Use Case 5: Emergency Announcement (Max Volume)

```bash
# Immediate max volume on all devices
curl -X POST http://192.168.5.12:8001/api/commands/batch \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": [1, 2, 3, ..., 50],
    "command_type": "volume",
    "parameters": {"volume": 100},
    "execution_mode": "parallel",
    "priority": 1,
    "reason": "Emergency announcement"
  }'
```

---

## JavaScript/TypeScript Examples

### Example 1: Execute Command (Fetch API)

```typescript
async function executeCommand(deviceId: number, commandType: string, parameters: any) {
  const response = await fetch('http://192.168.5.12:8001/api/commands/execute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      device_id: deviceId,
      command_type: commandType,
      parameters: parameters,
      reason: 'Executed from web admin'
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
}

// Usage
try {
  const result = await executeCommand(1, 'volume', { volume: 50 });
  console.log('Command queued:', result.id);
} catch (error) {
  console.error('Failed to execute command:', error.message);
}
```

---

### Example 2: Batch Command with Progress

```typescript
async function batchReboot(deviceIds: number[]) {
  const response = await fetch('http://192.168.5.12:8001/api/commands/batch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      device_ids: deviceIds,
      command_type: 'reboot',
      parameters: { delay_seconds: 60 },
      execution_mode: 'sequential',
      reason: 'Maintenance'
    })
  });

  const result = await response.json();

  console.log(`Batch ${result.batch_id}:`);
  console.log(`- Total: ${result.total}`);
  console.log(`- Successful: ${result.successful}`);
  console.log(`- Failed: ${result.failed}`);

  return result;
}
```

---

### Example 3: Poll Command Status

```typescript
async function waitForCommandCompletion(commandId: number, timeout: number = 60000) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const response = await fetch(`http://192.168.5.12:8001/api/commands/${commandId}`);
    const command = await response.json();

    if (command.status === 'completed') {
      return command.result;
    }

    if (command.status === 'failed') {
      throw new Error(command.error_message);
    }

    // Wait 1 second before next poll
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  throw new Error('Command timeout');
}

// Usage
const command = await executeCommand(1, 'screenshot', { quality: 90 });
const result = await waitForCommandCompletion(command.id);
console.log('Screenshot URL:', result.screenshot_url);
```

---

## Python Examples

### Example 1: Execute Command

```python
import requests

def execute_command(device_id: int, command_type: str, parameters: dict):
    """Execute a command on a device."""
    url = 'http://192.168.5.12:8001/api/commands/execute'

    payload = {
        'device_id': device_id,
        'command_type': command_type,
        'parameters': parameters,
        'reason': 'Executed from script'
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    return response.json()

# Usage
result = execute_command(1, 'volume', {'volume': 50})
print(f"Command queued: {result['id']}")
```

---

### Example 2: Batch Command

```python
def batch_reboot(device_ids: list[int]):
    """Reboot multiple devices sequentially."""
    url = 'http://192.168.5.12:8001/api/commands/batch'

    payload = {
        'device_ids': device_ids,
        'command_type': 'reboot',
        'parameters': {'delay_seconds': 60},
        'execution_mode': 'sequential',
        'reason': 'Scheduled maintenance'
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    result = response.json()
    print(f"Batch {result['batch_id']}:")
    print(f"  Total: {result['total']}")
    print(f"  Successful: {result['successful']}")
    print(f"  Failed: {result['failed']}")

    return result

# Usage
batch_reboot([10, 11, 12, 13, 14, 15])
```

---

### Example 3: Monitor Command Status

```python
import time

def wait_for_command(command_id: int, timeout: int = 60):
    """Wait for command to complete."""
    url = f'http://192.168.5.12:8001/api/commands/{command_id}'
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(url)
        response.raise_for_status()
        command = response.json()

        if command['status'] == 'completed':
            return command['result']

        if command['status'] == 'failed':
            raise Exception(command['error_message'])

        time.sleep(1)  # Poll every second

    raise TimeoutError('Command timeout')

# Usage
command = execute_command(1, 'screenshot', {'quality': 90})
result = wait_for_command(command['id'])
print(f"Screenshot saved: {result['screenshot_url']}")
```

---

## Best Practices

### 1. Always Provide Reason
```json
{
  "device_id": 1,
  "command_type": "reboot",
  "parameters": {},
  "reason": "Weekly maintenance schedule"  // ✅ Good for audit trail
}
```

### 2. Use Sequential for Sensitive Operations
```json
{
  "device_ids": [1, 2, 3],
  "command_type": "reboot",
  "execution_mode": "sequential"  // ✅ Reboot one by one
}
```

### 3. Check Rate Limits Before Batch
```bash
# Check rate limit before executing
curl http://192.168.5.12:8001/api/commands/rate-limit/1/reboot

# Response: {"remaining": 2, "reset_at": "..."}
```

### 4. Poll for Completion (Critical Commands)
```typescript
// Don't assume immediate execution
const command = await executeCommand(1, 'update', {...});
await waitForCompletion(command.id);  // ✅ Wait for result
```

### 5. Handle Errors Gracefully
```typescript
try {
  await executeCommand(1, 'shell', {...});
} catch (error) {
  if (error.status === 403) {
    console.error('Permission denied');
  } else if (error.status === 429) {
    console.error('Rate limit exceeded - retry later');
  }
}
```

---

## Security Notes

⚠️ **Shell Commands:**
- Require admin role
- Require 2FA verification
- Require approval workflow
- Limited to 1 per minute
- Dangerous patterns blocked

⚠️ **Rate Limiting:**
- Enforced per device per command type
- Resets every 60 seconds
- Cannot be bypassed

⚠️ **Audit Logging:**
- All commands logged
- User context captured
- Security events flagged
- Cannot be disabled

---

**API Documentation:** http://192.168.5.12:8001/docs#tag/Device-Commands

**Version:** 1.0.0
**Last Updated:** 2025-10-28
