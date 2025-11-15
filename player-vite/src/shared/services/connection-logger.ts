/**
 * Connection Logger Service
 * Logs network and server connection events with automatic upload
 *
 * @features
 * - Log connection status changes
 * - Log speed test results
 * - Automatic batch upload every 5 minutes
 * - Local storage with rotation
 */

import { SharedLogger } from '@shared/logger';
import { SharedAPIClient } from '@shared/api';
import { SharedDeviceState } from '@shared/device';
import { config } from '@shared/config';
import { ConnectionLogStorage, type ConnectionLogEntry } from '@shared/storage/connection-log-storage';

interface LogEntryInput {
  eventType: 'network' | 'server' | 'speed_test';
  status: 'online' | 'offline' | 'connected' | 'disconnected' | 'tested';
  latencyMs?: number;
  errorMessage?: string;
  downloadSpeedMbps?: number;
  uploadSpeedMbps?: number;
  metadata?: Record<string, any>;
}

class ConnectionLoggerClass {
  private uploadInterval: number | null = null;
  private readonly UPLOAD_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

  /**
   * Initialize logger
   */
  async init(): Promise<void> {
    try {
      // Initialize storage
      await ConnectionLogStorage.init();

      // Start batch upload scheduler
      this.startUploadScheduler();

      // Get network information
      const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

      // Log initial network status with detailed info
      await this.log({
        eventType: 'network',
        status: navigator.onLine ? 'online' : 'offline',
        metadata: {
          event: 'initial_status',
          connectionType: connection?.type || 'unknown',
          effectiveType: connection?.effectiveType || 'unknown',
          downlink: connection?.downlink || 0,
          rtt: connection?.rtt || 0,
          saveData: connection?.saveData || false
        }
      });

      SharedLogger.log('[ConnectionLogger] ✅ Initialized');
    } catch (error) {
      SharedLogger.error('[ConnectionLogger] Failed to initialize:', error);
    }
  }

  /**
   * Generate UUID (fallback for browsers without crypto.randomUUID)
   */
  private generateUUID(): string {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    // Fallback UUID v4 generator
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  /**
   * Log a connection event
   */
  async log(entry: LogEntryInput): Promise<void> {
    try {
      const logEntry: ConnectionLogEntry = {
        id: this.generateUUID(),
        timestamp: Date.now(),
        eventType: entry.eventType,
        status: entry.status,
        latencyMs: entry.latencyMs,
        errorMessage: entry.errorMessage,
        downloadSpeedMbps: entry.downloadSpeedMbps,
        uploadSpeedMbps: entry.uploadSpeedMbps,
        metadata: entry.metadata,
        isSent: false
      };

      await ConnectionLogStorage.addLog(logEntry);

      SharedLogger.log(
        `[ConnectionLogger] Logged: ${entry.eventType} - ${entry.status}`,
        entry.latencyMs ? `(${entry.latencyMs}ms)` : ''
      );
    } catch (error) {
      SharedLogger.error('[ConnectionLogger] Failed to log event:', error);
    }
  }

  /**
   * Get recent logs
   */
  async getLogs(limit = 100, filter?: 'network' | 'server' | 'speed_test'): Promise<ConnectionLogEntry[]> {
    try {
      return await ConnectionLogStorage.getLogs(limit, filter);
    } catch (error) {
      SharedLogger.error('[ConnectionLogger] Failed to get logs:', error);
      return [];
    }
  }

  /**
   * Get logs count
   */
  async getCount(): Promise<number> {
    try {
      return await ConnectionLogStorage.getCount();
    } catch (error) {
      SharedLogger.error('[ConnectionLogger] Failed to get count:', error);
      return 0;
    }
  }

  /**
   * Upload unsent logs to server
   */
  async uploadToServer(): Promise<void> {
    try {
      const deviceId = SharedDeviceState.getDeviceId();
      if (!deviceId) {
        SharedLogger.warn('[ConnectionLogger] No device ID, skipping upload');
        return;
      }

      const unsentLogs = await ConnectionLogStorage.getUnsentLogs();
      if (unsentLogs.length === 0) {
        SharedLogger.log('[ConnectionLogger] No unsent logs to upload');
        return;
      }

      SharedLogger.log(`[ConnectionLogger] Uploading ${unsentLogs.length} logs to server...`);

      // Prepare payload with new dedicated fields
      const payload = {
        logs: unsentLogs.map(log => ({
          logged_at: new Date(log.timestamp).toISOString(),
          event_type: log.eventType,
          status: log.status,
          latency_ms: log.latencyMs,
          error_message: log.errorMessage,
          download_speed_mbps: log.downloadSpeedMbps,
          upload_speed_mbps: log.uploadSpeedMbps,

          // Dedicated fields for better query performance (migration 046)
          connection_type: log.metadata?.connectionType || null,
          effective_type: log.metadata?.effectiveType || null,
          rtt_ms: log.metadata?.rtt || null,
          endpoint: log.metadata?.endpoint || null,
          http_status: log.metadata?.httpStatus || log.metadata?.statusCode || null,
          test_trigger: log.metadata?.trigger || null,
          test_duration_ms: log.metadata?.testDurationMs || null,

          metadata: log.metadata
        }))
      };

      // Upload to server
      await SharedAPIClient.post(
        `${config.api.baseURL}/api/v1/devices/${deviceId}/connection-logs`,
        payload
      );

      // Mark as sent
      const logIds = unsentLogs.map(log => log.id);
      await ConnectionLogStorage.markAsSent(logIds);

      SharedLogger.log(`[ConnectionLogger] ✅ Uploaded ${unsentLogs.length} logs successfully`);
    } catch (error) {
      SharedLogger.error('[ConnectionLogger] Failed to upload logs:', error);
      // Don't throw - will retry on next upload cycle
    }
  }

  /**
   * Start automatic batch upload scheduler
   */
  private startUploadScheduler(): void {
    // Upload immediately on start (for any pending logs)
    setTimeout(() => {
      this.uploadToServer();
    }, 10000); // Wait 10s after init

    // Then upload every 5 minutes
    this.uploadInterval = window.setInterval(() => {
      this.uploadToServer();
    }, this.UPLOAD_INTERVAL_MS);

    SharedLogger.log('[ConnectionLogger] Upload scheduler started (every 5 minutes)');
  }

  /**
   * Stop upload scheduler (for cleanup)
   */
  stop(): void {
    if (this.uploadInterval) {
      clearInterval(this.uploadInterval);
      this.uploadInterval = null;
      SharedLogger.log('[ConnectionLogger] Upload scheduler stopped');
    }
  }

  /**
   * Force immediate upload (can be called manually)
   */
  async forceUpload(): Promise<void> {
    SharedLogger.log('[ConnectionLogger] Force upload triggered');
    await this.uploadToServer();
  }
}

// Export singleton instance
export const ConnectionLogger = new ConnectionLoggerClass();

// Make available globally
if (typeof window !== 'undefined') {
  (window as any).ConnectionLogger = ConnectionLogger;
}
