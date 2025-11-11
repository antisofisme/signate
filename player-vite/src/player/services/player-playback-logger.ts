/**
 * Player Playback Logger Service
 * Tracks and logs content playback for analytics
 *
 * @features
 * - Log playback start/end to backend API
 * - Track playback duration and completion
 * - Device and content metadata tracking
 * - Error handling and retry logic
 */

import { SharedAPIClient } from '@shared/api';
import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';
import type { PlaylistItem } from '../types/player.types';

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
 * Playback start response from API
 */
interface PlaybackStartResponse {
  log_id: number;
  content_id: number;
  device_id: number;
  started_at: string;
}

/**
 * Playback Logger Class
 * Singleton pattern for centralized playback tracking
 */
class PlayerPlaybackLoggerClass {
  private currentLog: PlaybackLog | null = null;
  private startTime: number | null = null;

  /**
   * Log playback start
   * Called when content starts playing
   */
  async logPlaybackStart(item: PlaylistItem, playlistId: number | null = null): Promise<void> {
    try {
      const deviceId = SharedDeviceState.getDeviceId();

      if (!deviceId) {
        SharedLogger.warn('[PlaybackLogger] No device ID - skipping playback logging');
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
