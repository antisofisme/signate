/**
 * Player Playback Logger Service
 * Tracks and logs content playback for analytics
 *
 * @features
 * - Log playback start/end to backend API
 * - Track playback duration and completion
 * - Device and content metadata tracking
 * - Error handling and retry logic
 * - Offline queue for reliable analytics
 */

import { SharedAPIClient } from '@shared/api';
import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import type { PlaylistItem } from '@player/types/player.types';

/**
 * Playback log entry
 */
interface PlaybackLog {
  logId: number | null;
  contentId: number;
  playlistId: number | null;
  deviceId: number;
  startedAt: string;
  endedAt: string | null;
  durationSeconds: number | null;
  completed: boolean;
}

/**
 * Offline queue entry for pending analytics
 */
interface QueuedAnalyticsEntry {
  id: string;
  type: 'start' | 'end';
  payload: Record<string, unknown>;
  timestamp: number;
  retryCount: number;
}

/**
 * Playback start response from API
 */
interface PlaybackStartResponse {
  log_id: number;
  content_id: number;
  device_id: number;
  started_at: string;
}

const OFFLINE_QUEUE_KEY = 'playback_analytics_queue';
const MAX_QUEUE_SIZE = 100;
const MAX_RETRY_COUNT = 3;

/**
 * Playback Logger Class
 * Singleton pattern for centralized playback tracking
 */
class PlayerPlaybackLoggerClass {
  private currentLog: PlaybackLog | null = null;
  private startTime: number | null = null;
  private offlineQueue: QueuedAnalyticsEntry[] = [];
  private isProcessingQueue = false;
  private onlineCleanup: (() => void) | null = null;

  constructor() {
    // Load offline queue from storage
    this.loadOfflineQueue();
    // Setup online event listener for queue sync
    this.setupOnlineListener();
  }

  /**
   * Setup listener for online event to process queue
   */
  private setupOnlineListener(): void {
    this.onlineCleanup = SharedEventBus.on('device:online', () => {
      SharedLogger.log('[PlaybackLogger] Device came online - processing offline queue');
      void this.processOfflineQueue();
    });
  }

  /**
   * Load offline queue from localStorage
   */
  private loadOfflineQueue(): void {
    try {
      const stored = SharedDeviceState.getPreference<string>(OFFLINE_QUEUE_KEY, '[]');
      this.offlineQueue = JSON.parse(stored);
      if (this.offlineQueue.length > 0) {
        SharedLogger.log(`[PlaybackLogger] Loaded ${this.offlineQueue.length} queued analytics entries`);
      }
    } catch (error) {
      SharedLogger.error('[PlaybackLogger] Failed to load offline queue:', error);
      this.offlineQueue = [];
    }
  }

  /**
   * Save offline queue to localStorage
   */
  private saveOfflineQueue(): void {
    try {
      SharedDeviceState.setPreference(OFFLINE_QUEUE_KEY, JSON.stringify(this.offlineQueue));
    } catch (error) {
      SharedLogger.error('[PlaybackLogger] Failed to save offline queue:', error);
    }
  }

  /**
   * Add entry to offline queue
   */
  private queueEntry(type: 'start' | 'end', payload: Record<string, unknown>): void {
    // Enforce max queue size
    if (this.offlineQueue.length >= MAX_QUEUE_SIZE) {
      SharedLogger.warn('[PlaybackLogger] Offline queue full, removing oldest entry');
      this.offlineQueue.shift();
    }

    const entry: QueuedAnalyticsEntry = {
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      payload,
      timestamp: Date.now(),
      retryCount: 0,
    };

    this.offlineQueue.push(entry);
    this.saveOfflineQueue();
    SharedLogger.log(`[PlaybackLogger] Queued ${type} entry for later sync (queue size: ${this.offlineQueue.length})`);
  }

  /**
   * Process offline queue when online
   */
  async processOfflineQueue(): Promise<void> {
    if (this.isProcessingQueue || this.offlineQueue.length === 0) {
      return;
    }

    this.isProcessingQueue = true;
    SharedLogger.log(`[PlaybackLogger] Processing ${this.offlineQueue.length} queued entries`);

    const successfulIds: string[] = [];
    const failedEntries: QueuedAnalyticsEntry[] = [];

    for (const entry of this.offlineQueue) {
      try {
        if (entry.type === 'start') {
          await SharedAPIClient.post(
            `${config.api.baseURL}/api/v1/analytics/playback/start`,
            { body: JSON.stringify(entry.payload) }
          );
        } else {
          // For end entries, we need the log_id which might not exist if start failed
          // Skip end entries without log_id
          if (entry.payload.log_id) {
            await SharedAPIClient.put(
              `${config.api.baseURL}/api/v1/analytics/playback/${entry.payload.log_id}/end`,
              { body: JSON.stringify(entry.payload) }
            );
          }
        }
        successfulIds.push(entry.id);
      } catch (error) {
        entry.retryCount++;
        if (entry.retryCount < MAX_RETRY_COUNT) {
          failedEntries.push(entry);
        } else {
          SharedLogger.warn(`[PlaybackLogger] Dropping entry after ${MAX_RETRY_COUNT} retries:`, entry.id);
        }
      }
    }

    // Update queue with remaining failed entries
    this.offlineQueue = failedEntries;
    this.saveOfflineQueue();

    this.isProcessingQueue = false;
    SharedLogger.log(`[PlaybackLogger] Queue processed: ${successfulIds.length} success, ${failedEntries.length} remaining`);
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    if (this.onlineCleanup) {
      this.onlineCleanup();
      this.onlineCleanup = null;
    }
  }

  /**
   * Log playback start
   * Called when content starts playing
   */
  async logPlaybackStart(item: PlaylistItem, playlistId: number | null = null): Promise<void> {
    try {
      const deviceId = SharedDeviceState.getDeviceId();
      const deviceToken = SharedDeviceState.getDeviceToken();

      if (!deviceId) {
        SharedLogger.warn('[PlaybackLogger] No device ID - skipping playback logging');
        return;
      }

      // Skip logging if no device token (authentication not available)
      if (!deviceToken) {
        SharedLogger.log('[PlaybackLogger] No device token - skipping playback logging (optional feature)');
        return;
      }

      // Record start time
      this.startTime = Date.now();

      // Prepare payload
      const payload = {
        content_id: item.content_id,
        device_id: deviceId,
        playlist_id: playlistId,
        started_at: new Date().toISOString(),
      };

      SharedLogger.log('[PlaybackLogger] Logging playback start:', {
        content: item.content.name,
        content_id: item.content_id,
        device_id: deviceId,
      });

      // Send to backend
      const response = await SharedAPIClient.post<PlaybackStartResponse>(
        `${config.api.baseURL}/api/v1/analytics/playback/start`,
        {
          body: JSON.stringify(payload),
        }
      );

      // Store current log
      this.currentLog = {
        logId: response.log_id,
        contentId: item.content_id,
        playlistId: playlistId,
        deviceId: parseInt(deviceId, 10),
        startedAt: response.started_at,
        endedAt: null,
        durationSeconds: null,
        completed: false,
      };

      SharedLogger.log('[PlaybackLogger] Playback start logged successfully:', {
        log_id: response.log_id,
      });
    } catch (error) {
      SharedLogger.error('[PlaybackLogger] Failed to log playback start:', error);

      // Queue for offline sync
      const payload = {
        content_id: item.content_id,
        device_id: deviceId,
        playlist_id: playlistId,
        started_at: new Date().toISOString(),
      };
      this.queueEntry('start', payload);

      // Don't throw - analytics failure shouldn't break playback
    }
  }

  /**
   * Log playback end
   * Called when content finishes playing or is skipped
   */
  async logPlaybackEnd(completed: boolean = true): Promise<void> {
    if (!this.currentLog || !this.currentLog.logId || !this.startTime) {
      SharedLogger.warn('[PlaybackLogger] No active playback log to end');
      return;
    }

    try {
      // Calculate duration
      const endTime = Date.now();
      const durationSeconds = Math.floor((endTime - this.startTime) / 1000);

      // Prepare payload
      const payload = {
        ended_at: new Date().toISOString(),
        duration_seconds: durationSeconds,
        completed: completed,
      };

      SharedLogger.log('[PlaybackLogger] Logging playback end:', {
        log_id: this.currentLog.logId,
        duration_seconds: durationSeconds,
        completed: completed,
      });

      // Send to backend
      await SharedAPIClient.put(
        `${config.api.baseURL}/api/v1/analytics/playback/${this.currentLog.logId}/end`,
        {
          body: JSON.stringify(payload),
        }
      );

      SharedLogger.log('[PlaybackLogger] Playback end logged successfully');

      // Clear current log
      this.currentLog = null;
      this.startTime = null;
    } catch (error) {
      SharedLogger.error('[PlaybackLogger] Failed to log playback end:', error);

      // Queue for offline sync (include log_id for later processing)
      const endTime = Date.now();
      const durationSeconds = Math.floor((endTime - this.startTime!) / 1000);
      const queuePayload = {
        log_id: this.currentLog.logId,
        ended_at: new Date().toISOString(),
        duration_seconds: durationSeconds,
        completed: completed,
      };
      this.queueEntry('end', queuePayload);

      // Don't throw - analytics failure shouldn't break playback

      // Still clear the log to prevent duplicate attempts
      this.currentLog = null;
      this.startTime = null;
    }
  }

  /**
   * Cancel current log without sending end event
   * Used when playback is interrupted abnormally
   */
  cancelCurrentLog(): void {
    if (this.currentLog) {
      SharedLogger.log('[PlaybackLogger] Canceling current playback log:', {
        log_id: this.currentLog.logId,
      });

      this.currentLog = null;
      this.startTime = null;
    }
  }

  /**
   * Get current active log
   */
  getCurrentLog(): PlaybackLog | null {
    return this.currentLog;
  }

  /**
   * Check if there's an active log
   */
  hasActiveLog(): boolean {
    return this.currentLog !== null && this.currentLog.logId !== null;
  }
}

// Export singleton instance
export const PlayerPlaybackLogger = new PlayerPlaybackLoggerClass();

// Make available globally for debugging
if (typeof window !== 'undefined') {
  // window.PlayerPlaybackLogger = PlayerPlaybackLogger;
}
