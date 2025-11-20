# Player-Vite Error Remediation Guide

**Purpose**: Step-by-step fixes for critical errors and security vulnerabilities
**Audience**: Development team
**Priority**: CRITICAL, HIGH, MEDIUM

---

## CRITICAL FIXES (Apply Immediately)

### Fix 1: Shell Registration - Missing Null Checks (Line 178-230)

**Status**: Critical - Blocks device registration
**Time**: 30 minutes
**Risk**: High - Breaks entire device registration flow

**Changes Required**:
- File: `/mnt/g/khoirul/signate/player-vite/src/shell/services/shell-registration.ts`
- Lines: 178-230
- Change: Add null/undefined validation before property access

**Implementation**:
```typescript
// BEFORE (Vulnerable)
if (existingCheck && existingCheck.device_id) {
  SharedDeviceState.setDeviceId(existingCheck.device_id);
  SharedDeviceState.setDeviceCode(existingCheck.unique_code); // Crashes if undefined
}

// AFTER (Safe)
if (existingCheck?.device_id) {
  const code = existingCheck.unique_code;
  if (!code) {
    throw new Error('Invalid registration response: missing unique_code');
  }

  SharedDeviceState.setDeviceId(existingCheck.device_id);
  SharedDeviceState.setDeviceCode(code);
  SharedDeviceState.setDeviceStatus(existingCheck.status || 'pending');

  if (existingCheck.device_name) {
    SharedDeviceState.setDeviceName(existingCheck.device_name);
  }

  if (existingCheck.organization_id) {
    SharedDeviceState.setOrganizationId(existingCheck.organization_id);
  }
} else {
  SharedLogger.warn('[ShellRegistration] Invalid response: missing device_id');
  throw new Error('Backend returned invalid device response');
}
```

**Test Case**:
```typescript
// Test with missing fields
const invalidResponse = {
  device_id: 123,
  // missing: unique_code, status, device_name, organization_id
};

// Should throw clear error, not crash
try {
  // Simulate response
  expect(() => {
    // The code should validate and throw
  }).toThrow('missing unique_code');
} catch (e) {
  console.log('PASS: Proper error thrown');
}
```

---

### Fix 2: API Client - Add Request Timeout

**Status**: Critical - Prevents hanging requests
**Time**: 20 minutes
**Risk**: Medium - Requires careful timeout value selection

**Changes Required**:
- File: `/mnt/g/khoirul/signate/player-vite/src/shared/api/shared-api-client.ts`
- Lines: 27-88
- Change: Add AbortController for timeout

**Implementation**:
```typescript
// BEFORE (Can hang forever)
async request<T = unknown>(url: string, options: RequestOptions = {}): Promise<T> {
  const startTime = performance.now();

  try {
    const response = await fetch(url, requestOptions);
    // Can hang indefinitely here
  } catch (error) {
    // ...
  }
}

// AFTER (With timeout)
async request<T = unknown>(url: string, options: RequestOptions = {}): Promise<T> {
  const startTime = performance.now();
  const requestId = this.generateRequestId();
  const REQUEST_TIMEOUT = 30000; // 30 seconds for normal ops, 10s for heartbeat

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    SharedLogger.warn(`[SharedAPIClient] Request ${requestId} timeout after 30s`);
    controller.abort();
  }, REQUEST_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...requestOptions,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // ... rest of code ...
  } catch (error) {
    clearTimeout(timeoutId);
    const duration = Math.round(performance.now() - startTime);

    if (error instanceof DOMException && error.name === 'AbortError') {
      const apiError = new Error(`Request timeout after ${duration}ms`) as Error & APIError;
      apiError.name = 'APIClientError';
      apiError.isNetworkError = true;
      apiError.requestId = requestId;
      apiError.duration = duration;
      apiError.url = url;

      this.logError(requestId, apiError);
      throw apiError;
    }

    // ... existing error handling ...
  }
}
```

**Configuration**:
```typescript
// Different timeouts for different operations
const TIMEOUT_CONFIG = {
  heartbeat: 10000,    // 10 seconds for heartbeat (frequent)
  registration: 30000, // 30 seconds for registration
  playlistSync: 20000, // 20 seconds for playlist
  generic: 30000,      // 30 seconds default
};

// Use in request:
async request<T = unknown>(url: string, options: RequestOptions & { timeout?: number } = {}): Promise<T> {
  const timeout = options.timeout || TIMEOUT_CONFIG.generic;
  // ...
}
```

**Test Case**:
```typescript
it('should timeout requests after 30 seconds', async () => {
  const slowEndpoint = 'http://localhost:8001/api/slow';

  const startTime = Date.now();
  try {
    await SharedAPIClient.get(slowEndpoint, { timeout: 1000 });
    fail('Should have timed out');
  } catch (error) {
    const elapsed = Date.now() - startTime;
    expect(error.message).toContain('timeout');
    expect(elapsed).toBeLessThan(2000); // Allow 1s buffer
  }
});
```

---

### Fix 3: Token Security - Redact from Logs

**Status**: Critical - Security vulnerability
**Time**: 15 minutes
**Risk**: Low - Logs only, no functional impact

**Changes Required**:
- File: `/mnt/g/khoirul/signate/player-vite/src/shared/api/shared-api-client.ts`
- Lines: 189-199, 242-249, 272-279
- Change: Redact sensitive data from error logs

**Implementation**:
```typescript
// BEFORE (Exposes token)
private logError(requestId: string, error: Error & Partial<APIError>): void {
  SharedLogger.error(`[SharedAPIClient] ✗ Error (${error.duration || 0}ms)`, {
    requestId,
    message: error.message,
    status: error.status,
    url: error.url, // May contain ?token=...
  });
}

// AFTER (Redacted)
private redactSensitiveData(url: string): string {
  return url
    .replace(/[\?&]token=[^&]*/gi, '?token=***')
    .replace(/[\?&]key=[^&]*/gi, '?key=***')
    .replace(/[\?&]password=[^&]*/gi, '?password=***')
    .replace(/Bearer\s+[^\s]*/gi, 'Bearer ***')
    .replace(/\/([a-zA-Z0-9_-]{20,})[^\/]*$/gi, '/***'); // Redact long IDs
}

private logError(requestId: string, error: Error & Partial<APIError>): void {
  const safeUrl = error.url ? this.redactSensitiveData(error.url) : '(unknown)';

  SharedLogger.error(`[SharedAPIClient] ✗ Error (${error.duration || 0}ms)`, {
    requestId,
    message: error.message,
    status: error.status,
    url: safeUrl,
  });
}

private logRequest(requestId: string, url: string, options: RequestInit): void {
  if (!this.isDebugMode()) return;

  const safeUrl = this.redactSensitiveData(url);

  SharedLogger.log(`[SharedAPIClient] → ${options.method || 'GET'} ${safeUrl}`, {
    requestId,
    // Don't log headers as they may contain Authorization
  });
}
```

**Test Case**:
```typescript
it('should redact tokens from logged URLs', () => {
  const client = new SharedAPIClientClass();

  const urls = [
    'http://api.com/endpoint?token=abc123def456',
    'http://api.com/endpoint?key=secret123',
    'http://api.com/endpoint?password=hunter2',
    'http://api.com/device/uuid-very-long-uuid-here/details',
  ];

  urls.forEach(url => {
    const redacted = client.redactSensitiveData(url);
    expect(redacted).not.toContain('abc123');
    expect(redacted).not.toContain('secret');
    expect(redacted).not.toContain('hunter2');
  });
});
```

---

### Fix 4: WebSocket Message Queue - Prevent Unbounded Growth

**Status**: Critical - Memory leak
**Time**: 20 minutes
**Risk**: Medium - Changes queue behavior

**Changes Required**:
- File: `/mnt/g/khoirul/signate/player-vite/src/shared/websocket/shared-websocket.ts`
- Lines: 368-376
- Change: Implement proper queue overflow handling

**Implementation**:
```typescript
// BEFORE (Queue grows unbounded)
private queueMessage(message: WSMessage): void {
  if (this.messageQueue.length >= this.maxQueueSize) {
    SharedLogger.warn('[WebSocket] Message queue full, dropping oldest message');
    this.messageQueue.shift();
  }
  this.messageQueue.push(message);
}

// AFTER (Proper overflow handling)
private queueMessage(message: WSMessage): void {
  if (this.messageQueue.length >= this.maxQueueSize) {
    // Don't just drop 1, drop 10% of queue to make breathing room
    const dropCount = Math.ceil(this.maxQueueSize * 0.1);
    this.messageQueue = this.messageQueue.slice(dropCount);

    SharedLogger.warn(
      `[WebSocket] Message queue overflow (${this.messageQueue.length}/${this.maxQueueSize}), ` +
      `dropped ${dropCount} oldest messages`
    );
  }

  this.messageQueue.push(message);

  // Log if queue is getting full (>80%)
  if (this.messageQueue.length > this.maxQueueSize * 0.8) {
    SharedLogger.log(
      `[WebSocket] Message queue at ${Math.round((this.messageQueue.length / this.maxQueueSize) * 100)}%`
    );
  }
}
```

**Monitoring**:
```typescript
// Add queue size monitoring
getQueueMetrics() {
  return {
    size: this.messageQueue.length,
    maxSize: this.maxQueueSize,
    percentFull: Math.round((this.messageQueue.length / this.maxQueueSize) * 100),
    isHealthy: this.messageQueue.length < this.maxQueueSize * 0.8,
  };
}

// Call periodically
setInterval(() => {
  const metrics = SharedWebSocket.getQueueMetrics();
  if (!metrics.isHealthy) {
    SharedLogger.warn('[WebSocket] Queue unhealthy:', metrics);
  }
}, 30000);
```

---

### Fix 5: Image Blob URL Leak - Revoke on Cleanup

**Status**: Critical - Memory leak
**Time**: 25 minutes
**Risk**: Medium - Affects image playback

**Changes Required**:
- File: `/mnt/g/khoirul/signate/player-vite/src/player/services/player-videojs.ts`
- Lines: 340-399
- Change: Track and revoke blob URLs

**Implementation**:
```typescript
// ADD to class properties
private imageBlobUrls: string[] = [];

// MODIFY playImage method
private async playImage(item: PlaylistItem): Promise<void> {
  if (!this.videoElement) return;

  this.videoElement.style.display = 'none';

  const imageUrl = item.content.file_path || item.content.url || '';

  let finalImageUrl = imageUrl;
  let isFromCache = false;

  const PlayerMediaCache = ServiceRegistry.get<any>('PlayerMediaCache');
  if (PlayerMediaCache && imageUrl) {
    const cachedMedia = await PlayerMediaCache.getCachedMedia(imageUrl);

    if (cachedMedia) {
      finalImageUrl = await PlayerMediaCache.createBlobUrl(cachedMedia);
      isFromCache = true;
      // TRACK blob URL for later revocation
      this.imageBlobUrls.push(finalImageUrl);
    } else {
      PlayerMediaCache.cacheMedia(imageUrl, item.content_id)
        .then(() => {
          SharedLogger.log('[PlayerVideoJS] ✅ Image background download complete:', imageUrl);
        })
        .catch((err: Error) => {
          SharedLogger.warn('[PlayerVideoJS] Image background download failed:', err.message);
        });
    }
  }

  // Create image element
  const imageElement = document.createElement('img');
  imageElement.src = finalImageUrl;
  imageElement.style.width = '100%';
  imageElement.style.height = '100%';
  imageElement.style.objectFit = 'contain';
  imageElement.id = 'temp-image';

  this.videoElement.parentElement?.appendChild(imageElement);

  // Log playback start
  if (this.state.playlist) {
    void PlayerPlaybackLogger.logPlaybackStart(item, this.state.playlist.id);
  }

  // Set timer for duration
  this.itemTimer = window.setTimeout(() => {
    void PlayerPlaybackLogger.logPlaybackEnd(true);
    void this.next();
  }, item.duration * 1000);

  SharedLogger.log(
    `[PlayerVideoJS] ${isFromCache ? '💾 OFFLINE' : '🌐 STREAMING'} image for ${item.duration}s`
  );
}

// MODIFY cleanupTemporaryElements
private cleanupTemporaryElements(): void {
  document.getElementById('temp-image')?.remove();
  document.getElementById('temp-iframe')?.remove();

  // REVOKE all tracked blob URLs
  for (const blobUrl of this.imageBlobUrls) {
    try {
      URL.revokeObjectURL(blobUrl);
    } catch (e) {
      SharedLogger.error('[PlayerVideoJS] Failed to revoke blob URL:', e);
    }
  }
  this.imageBlobUrls = [];

  playerWidgetRenderer.clearWidgets();

  if (this.videoElement) {
    this.videoElement.style.display = 'block';
  }
}

// MODIFY destroy
destroy(): void {
  this.stop();

  if (this.player) {
    this.player.dispose();
    this.player = null;
  }

  playerWidgetRenderer.destroy();

  // REVOKE any remaining blob URLs
  for (const blobUrl of this.imageBlobUrls) {
    try {
      URL.revokeObjectURL(blobUrl);
    } catch (e) {
      // Already revoked or invalid
    }
  }
  this.imageBlobUrls = [];

  this.state = {
    currentItemIndex: 0,
    isPlaying: false,
    currentItem: null,
    playlist: null,
    error: null,
  };

  SharedLogger.log('[PlayerVideoJS] Player destroyed');
}
```

---

### Fix 6: Race Condition in Activation Poll - Add Check Flag

**Status**: Critical - Concurrent state mutations
**Time**: 20 minutes
**Risk**: Medium - Prevents duplicate registrations

**Changes Required**:
- File: `/mnt/g/khoirul/signate/player-vite/src/shell/services/shell-activation-poll.ts`
- Lines: 25-183
- Change: Add concurrent check prevention

**Implementation**:
```typescript
// ADD to class properties
private isCheckingActivation = false;

// MODIFY checkActivation method
async checkActivation(): Promise<void> {
  // Guard: prevent concurrent checks
  if (this.isCheckingActivation) {
    SharedLogger.log('[ShellActivationPoll] Activation check already in progress, skipping');
    return;
  }

  const activationCode = SharedDeviceState.getDeviceCode();

  if (!activationCode) {
    this.stopPolling();
    return;
  }

  this.isCheckingActivation = true;

  try {
    SharedLogger.log(`[ShellActivationPoll] Checking activation...`);

    const data = await SharedAPIClient.get<ActivationCheckResponse>(
      `${config.api.baseURL}/api/v1/devices/check-activation/${activationCode}`
    );

    SharedLogger.log('[ShellActivationPoll] Activation status:', data);

    // Handle code expiration
    if (data.expired && !data.activated) {
      SharedLogger.warn('[ShellActivationPoll] Code expired, requesting new code...');

      this.stopPolling();

      const shellRegistration = getShellRegistration();
      if (shellRegistration) {
        // Add delay to prevent race conditions
        await new Promise(resolve => setTimeout(resolve, 1000));

        await shellRegistration.registerDevice(true);
        SharedLogger.log('[ShellActivationPoll] New activation code requested');
      } else {
        SharedLogger.error('[ShellActivationPoll] Cannot request code - ShellRegistration unavailable');
      }

      return;
    }

    // Handle activation success
    if (data.activated && data.device_id) {
      SharedLogger.log(
        `[ShellActivationPoll] ✅ Code activated! Device ID: ${data.device_id}`
      );

      this.stopPolling();

      // Validate response before using
      if (!data.unique_code) {
        throw new Error('Invalid activation response: missing unique_code');
      }

      // ... rest of activation handling ...

      const oldDeviceId = SharedDeviceState.getDeviceId();
      const newDeviceId = data.device_id;

      if (oldDeviceId && oldDeviceId !== String(newDeviceId)) {
        SharedLogger.warn(`[ShellActivationPoll] Device ID changed: ${oldDeviceId} → ${newDeviceId}`);
      }

      // Stop old heartbeat
      const shellHeartbeat = ServiceRegistry.get<any>('ShellHeartbeat');
      if (shellHeartbeat?.stop) {
        shellHeartbeat.stop();
        await new Promise((resolve) => setTimeout(resolve, 200));
      }

      // Clear media cache
      await this.clearMediaCache();

      // Mark as activated
      SharedDeviceState.markAsActivated(
        newDeviceId,
        data.device_name || null,
        data.organization_id || null
      );

      // Save token
      if (data.device_token) {
        SharedDeviceState.setDeviceToken(data.device_token);
      }

      // Save config to IndexedDB
      await deviceConfigStorage.setDeviceConfig({
        device_id: newDeviceId,
        organization_id: data.organization_id || null,
        access_token: data.device_token || data.access_token || null,
        refresh_token: data.refresh_token || null,
        token_expires_at: data.token_expires_at || null,
        unique_code: data.unique_code || null,
      });

      // Save org PIN
      if (data.organization_pin) {
        SharedDeviceState.setOrganizationPin(data.organization_pin);
      }

      // Clear pending code
      if (getShellRegistration()) {
        await getShellRegistration().setPendingCode(null);
      }

      // Reload to player
      SharedLogger.log('[ShellActivationPoll] Reloading to player context...');
      window.location.reload();
    }
  } catch (error) {
    SharedLogger.error('[ShellActivationPoll] Activation check failed:', error);
    // Continue polling - network might be temporarily down
  } finally {
    this.isCheckingActivation = false; // Always reset
  }
}
```

---

## HIGH-PRIORITY FIXES (Apply Within 1 Week)

### Fix 7: Template Processor - Cleanup Timer Leaks

**File**: `/mnt/g/khoirul/signate/player-vite/src/shared/services/template-processor.ts`

```typescript
// ADD timer ID tracking
private startSystemVariableRefresh(): void {
  // Store interval IDs for cleanup
  const timeInterval = setInterval(() => {
    this.updateVariable('current_time', new Date().toLocaleTimeString());
  }, 1000);
  this.refreshTimers.set('_system_time', timeInterval);

  const dateInterval = setInterval(() => {
    const now = new Date();
    this.updateVariable('current_date', now.toLocaleDateString());
    this.updateVariable('day_of_week', now.toLocaleDateString('en-US', { weekday: 'long' }));
  }, 60000);
  this.refreshTimers.set('_system_date', dateInterval);

  const monthYearInterval = setInterval(() => {
    const now = new Date();
    this.updateVariable('month', now.toLocaleDateString('en-US', { month: 'long' }));
    this.updateVariable('year', now.getFullYear());
  }, 3600000);
  this.refreshTimers.set('_system_month_year', monthYearInterval);
}
```

---

### Fix 8: HLS Cache - Validate Parsing

**File**: `/mnt/g/khoirul/signate/player-vite/src/player/services/player-hls-cache.ts`

```typescript
private async parseVariantPlaylist(playlistUrl: string): Promise<HLSSegment[]> {
  const response = await fetch(playlistUrl);
  const text = await response.text();
  const lines = text.split('\n');

  const segments: HLSSegment[] = [];
  let currentDuration = 6.0;
  let segmentIndex = 0;

  // Use URL API for proper URL handling
  const baseUrl = new URL(playlistUrl).href;
  const basePath = baseUrl.substring(0, baseUrl.lastIndexOf('/') + 1);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (line.startsWith('#EXTINF:')) {
      const match = line.match(/#EXTINF:([\d.]+)/);
      if (match) {
        const duration = parseFloat(match[1]);
        if (!isNaN(duration) && duration > 0) {
          currentDuration = duration;
        } else {
          SharedLogger.warn(`[PlayerHLSCache] Invalid duration: ${match[1]}`);
          currentDuration = 6.0;
        }
      }
    }

    if (line.endsWith('.ts')) {
      // Validate duration before using
      if (!isFinite(currentDuration) || currentDuration <= 0) {
        currentDuration = 6.0;
      }

      segments.push({
        segmentUrl: basePath + line,
        duration: currentDuration,
        index: segmentIndex++,
      });
    }
  }

  return segments;
}
```

---

## TESTING CHECKLIST

### Unit Tests Required

- [ ] Shell Registration - Test null response handling
- [ ] API Client - Test timeout behavior
- [ ] WebSocket - Test queue overflow handling
- [ ] Player VideoJS - Test blob URL revocation
- [ ] Activation Poll - Test concurrent check prevention
- [ ] Template Processor - Test timer cleanup on destroy
- [ ] HLS Cache - Test invalid duration handling

### Integration Tests

- [ ] Device registration flow with invalid responses
- [ ] API request timeout during network outage
- [ ] Multiple image playback with memory monitoring
- [ ] Activation polling with code expiration
- [ ] WebSocket reconnection with queue recovery

### Regression Tests

- [ ] All existing device registration scenarios
- [ ] All API endpoints with timeout enabled
- [ ] All player content types (video, image, audio, url, widget)
- [ ] Device state persistence across reloads

---

## DEPLOYMENT CHECKLIST

Before deploying fixes:

- [ ] All CRITICAL fixes implemented and tested
- [ ] Security review completed
- [ ] Performance benchmarks run
- [ ] Memory leak tests passed
- [ ] Network timeout tests verified
- [ ] Browser console errors checked
- [ ] Load testing with multiple devices
- [ ] Backup created of production database
- [ ] Rollback plan documented
- [ ] Team notified of changes

---

## MONITORING POST-DEPLOYMENT

### Key Metrics to Monitor

1. **Crash Reports**
   - Monitor for "Cannot read property" errors
   - Track TypeError exceptions
   - Alert on Out of Memory errors

2. **Network Health**
   - Request timeout rate (should be <1%)
   - API response time (should be <5s p95)
   - WebSocket queue depth (should be <10% of max)

3. **Memory Usage**
   - Heap size growth over time
   - Blob URL count
   - Timer count

4. **Registration Metrics**
   - Registration success rate (should be >99%)
   - Activation time (should be <1 minute)
   - Retry count per registration

### Alert Thresholds

- Error rate >1% in 5 minutes
- Memory growth >500MB in 1 hour
- API timeout rate >5% in 5 minutes
- WebSocket disconnect rate >10% in 5 minutes

---

## SUMMARY

**Total Critical Issues Fixed**: 6
**Total High Priority Issues**: 2+ (address in Phase 2)
**Estimated Implementation Time**: 4-5 hours
**Testing Time**: 2-3 hours
**Total Effort**: ~8 hours

**High-Impact Changes**:
1. API request timeout (prevents hanging)
2. Race condition prevention (prevents duplicate registration)
3. Token security (prevents credential leakage)
4. Memory leak fixes (prevents crashes)

**Expected Outcome**: Stable, crash-free device player with proper error handling and security measures.
