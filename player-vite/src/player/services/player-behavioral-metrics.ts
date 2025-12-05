/**
 * Player Behavioral Metrics Service
 * Tracks playback behavioral metrics for reliability monitoring
 *
 * Phase 3: Behavioral Metrics Implementation
 *
 * @features
 * - Playback stalls tracking (video.stalled event)
 * - Buffer underruns tracking (video.waiting event)
 * - Time to first playback measurement
 * - Content play count tracking
 * - Quality switches tracking (HLS)
 * - Content load failures tracking
 * - Error rate calculation
 */

import { SharedLogger } from '@shared/logger';
import { ConnectionLogger } from '@shared/services/connection-logger';

/**
 * Behavioral Metrics Interface
 */
export interface BehavioralMetrics {
  // Playback events
  playback_stalls_count: number;
  buffer_underruns_count: number;
  time_to_first_playback_ms: number | null;

  // Content metrics
  content_play_count: number;
  quality_switches_count: number;
  content_load_failures_count: number;

  // Calculated metrics
  error_rate_percent: number;
  total_operations: number;
}

/**
 * Content play tracking entry
 */
interface ContentPlayEntry {
  content_id: number;
  play_count: number;
  last_played_at: number;
}

/**
 * Player Behavioral Metrics Class
 * Singleton pattern for tracking behavioral metrics
 */
class PlayerBehavioralMetricsClass {
  // Playback event counters (reset on startup)
  private playbackStallsCount = 0;
  private bufferUnderrunsCount = 0;
  private qualitySwitchesCount = 0;
  private contentLoadFailuresCount = 0;

  // Current content tracking (for logging context)
  private currentContentId: number | null = null;
  private currentContentName: string | null = null;

  // Time to first playback tracking
  private loadStartTime: number | null = null;
  private timeToFirstPlayback: number | null = null;
  private hasRecordedFirstPlayback = false;

  // Stall/Buffer duration tracking
  private stallStartTime: number | null = null;
  private bufferStartTime: number | null = null;
  private isStalled = false;
  private isBuffering = false;

  // Content display duration tracking
  private contentPlayStartTime: number | null = null;

  // Content play tracking (per session)
  private contentPlayCounts: Map<number, ContentPlayEntry> = new Map();
  private totalContentPlays = 0;

  // Operation tracking for error rate
  private totalOperations = 0;
  private failedOperations = 0;

  // Event listeners for cleanup
  private boundHandlers: Map<string, EventListener> = new Map();

  /**
   * Initialize metrics tracking
   * Call this when player starts
   */
  initialize(): void {
    SharedLogger.log('[BehavioralMetrics] 📊 Initializing behavioral metrics tracking');
    this.resetSessionMetrics();
  }

  /**
   * Reset all session metrics
   * Called on player initialization or device restart
   */
  resetSessionMetrics(): void {
    this.playbackStallsCount = 0;
    this.bufferUnderrunsCount = 0;
    this.qualitySwitchesCount = 0;
    this.contentLoadFailuresCount = 0;
    this.loadStartTime = null;
    this.timeToFirstPlayback = null;
    this.hasRecordedFirstPlayback = false;
    this.stallStartTime = null;
    this.bufferStartTime = null;
    this.isStalled = false;
    this.isBuffering = false;
    this.contentPlayStartTime = null;
    this.contentPlayCounts.clear();
    this.totalContentPlays = 0;
    this.totalOperations = 0;
    this.failedOperations = 0;

    SharedLogger.log('[BehavioralMetrics] ♻️ Session metrics reset');
  }

  /**
   * Attach event listeners to video element
   * Must be called after video element is ready
   */
  attachToVideoElement(videoElement: HTMLVideoElement): void {
    if (!videoElement) {
      SharedLogger.warn('[BehavioralMetrics] No video element provided');
      return;
    }

    // Remove any existing listeners first
    this.detachFromVideoElement(videoElement);

    // Create bound handlers for cleanup
    const stalledHandler = this.handleStalled.bind(this);
    const waitingHandler = this.handleWaiting.bind(this);
    const playingHandler = this.handlePlaying.bind(this);
    const errorHandler = this.handleError.bind(this);

    // Store for cleanup
    this.boundHandlers.set('stalled', stalledHandler);
    this.boundHandlers.set('waiting', waitingHandler);
    this.boundHandlers.set('playing', playingHandler);
    this.boundHandlers.set('error', errorHandler);

    // Attach listeners
    videoElement.addEventListener('stalled', stalledHandler);
    videoElement.addEventListener('waiting', waitingHandler);
    videoElement.addEventListener('playing', playingHandler);
    videoElement.addEventListener('error', errorHandler);

    SharedLogger.log('[BehavioralMetrics] ✅ Attached to video element');
  }

  /**
   * Detach event listeners from video element
   */
  detachFromVideoElement(videoElement: HTMLVideoElement): void {
    if (!videoElement) return;

    this.boundHandlers.forEach((handler, event) => {
      videoElement.removeEventListener(event, handler);
    });
    this.boundHandlers.clear();

    SharedLogger.log('[BehavioralMetrics] Detached from video element');
  }

  /**
   * Handle stalled event (playback stall)
   * Fires when browser is trying to get media data but none is available
   */
  private handleStalled(): void {
    // Only count if not already stalled (avoid duplicate events)
    if (!this.isStalled) {
      this.isStalled = true;
      this.stallStartTime = performance.now();
      this.playbackStallsCount++;
      SharedLogger.warn(`[BehavioralMetrics] ⏸️ Playback stalled (total: ${this.playbackStallsCount})`);
    }
    // Note: Duration will be logged when playing resumes
  }

  /**
   * Handle waiting event (buffer underrun)
   * Fires when playback stops due to lack of data
   */
  private handleWaiting(): void {
    // Only count if not already buffering (avoid duplicate events)
    if (!this.isBuffering) {
      this.isBuffering = true;
      this.bufferStartTime = performance.now();
      this.bufferUnderrunsCount++;
      SharedLogger.warn(`[BehavioralMetrics] ⏳ Buffer underrun (total: ${this.bufferUnderrunsCount})`);
    }
    // Note: Duration will be logged when playing resumes
  }

  /**
   * Handle playing event (first playback measurement + stall/buffer recovery)
   */
  private handlePlaying(): void {
    const now = performance.now();

    // Log time to first playback
    if (!this.hasRecordedFirstPlayback && this.loadStartTime !== null) {
      this.timeToFirstPlayback = now - this.loadStartTime;
      this.hasRecordedFirstPlayback = true;
      SharedLogger.log(`[BehavioralMetrics] ⏱️ Time to first playback: ${this.timeToFirstPlayback.toFixed(0)}ms`);

      // Log to ConnectionLogger for Playback tab
      void ConnectionLogger.log({
        eventType: 'playback',
        status: 'started',
        metadata: {
          playbackEventType: 'started',
          contentId: this.currentContentId,
          contentName: this.currentContentName,
          durationMs: this.timeToFirstPlayback,
          details: `Time to first playback: ${this.timeToFirstPlayback.toFixed(0)}ms`,
        },
      });
    }

    // Log stall recovery with duration
    if (this.isStalled && this.stallStartTime !== null) {
      const stallDuration = now - this.stallStartTime;
      SharedLogger.log(`[BehavioralMetrics] ▶️ Recovered from stall (duration: ${stallDuration.toFixed(0)}ms)`);

      void ConnectionLogger.log({
        eventType: 'playback',
        status: 'stall',
        metadata: {
          playbackEventType: 'stall',
          contentId: this.currentContentId,
          contentName: this.currentContentName,
          durationMs: stallDuration,
          details: `Stall recovered after ${stallDuration.toFixed(0)}ms`,
          totalStalls: this.playbackStallsCount,
        },
      });

      this.isStalled = false;
      this.stallStartTime = null;
    }

    // Log buffer recovery with duration
    if (this.isBuffering && this.bufferStartTime !== null) {
      const bufferDuration = now - this.bufferStartTime;
      SharedLogger.log(`[BehavioralMetrics] ▶️ Recovered from buffer (duration: ${bufferDuration.toFixed(0)}ms)`);

      void ConnectionLogger.log({
        eventType: 'playback',
        status: 'buffer',
        metadata: {
          playbackEventType: 'buffer_underrun',
          contentId: this.currentContentId,
          contentName: this.currentContentName,
          durationMs: bufferDuration,
          details: `Buffer recovered after ${bufferDuration.toFixed(0)}ms`,
          totalBufferUnderruns: this.bufferUnderrunsCount,
        },
      });

      this.isBuffering = false;
      this.bufferStartTime = null;
    }
  }

  /**
   * Handle error event
   */
  private handleError(): void {
    this.failedOperations++;
    SharedLogger.warn(`[BehavioralMetrics] ❌ Playback error (failures: ${this.failedOperations})`);

    // Log to ConnectionLogger for Playback tab
    void ConnectionLogger.log({
      eventType: 'playback',
      status: 'error',
      metadata: {
        playbackEventType: 'error',
        contentId: this.currentContentId,
        contentName: this.currentContentName,
        details: 'Playback error occurred',
        totalFailures: this.failedOperations,
      },
    });
  }

  /**
   * Mark content load start (for time to first playback)
   * Call this when a new content item starts loading
   */
  markContentLoadStart(): void {
    this.loadStartTime = performance.now();
    this.hasRecordedFirstPlayback = false;
    this.totalOperations++;
    SharedLogger.log('[BehavioralMetrics] 📥 Content load started');
  }

  /**
   * Record content play (for content_play_count)
   */
  recordContentPlay(contentId: number, contentName?: string): void {
    this.totalContentPlays++;

    // Store current content info for event logging context
    this.currentContentId = contentId;
    this.currentContentName = contentName || null;

    // Track start time for duration calculation
    this.contentPlayStartTime = performance.now();

    const existing = this.contentPlayCounts.get(contentId);
    if (existing) {
      existing.play_count++;
      existing.last_played_at = Date.now();
    } else {
      this.contentPlayCounts.set(contentId, {
        content_id: contentId,
        play_count: 1,
        last_played_at: Date.now(),
      });
    }

    SharedLogger.log(`[BehavioralMetrics] ▶️ Content ${contentId} played (total plays this session: ${this.totalContentPlays})`);

    // Log to ConnectionLogger for Playback tab
    void ConnectionLogger.log({
      eventType: 'playback',
      status: 'play',
      metadata: {
        playbackEventType: 'play',
        contentId: contentId,
        contentName: contentName || 'Unknown',
        details: `Content play #${this.totalContentPlays} this session`,
        playCount: this.contentPlayCounts.get(contentId)?.play_count || 1,
      },
    });
  }

  /**
   * Record content complete (when content finishes displaying)
   * Call this when content ends (video ended, image timer finished, etc.)
   */
  recordContentComplete(completed: boolean = true): void {
    if (this.contentPlayStartTime === null || this.currentContentId === null) {
      return;
    }

    const durationMs = performance.now() - this.contentPlayStartTime;
    const durationSeconds = Math.round(durationMs / 100) / 10; // 1 decimal place

    SharedLogger.log(`[BehavioralMetrics] ✅ Content ${this.currentContentId} completed (duration: ${durationSeconds}s)`);

    // Log to ConnectionLogger for Playback tab
    void ConnectionLogger.log({
      eventType: 'playback',
      status: 'completed',
      metadata: {
        playbackEventType: 'completed',
        contentId: this.currentContentId,
        contentName: this.currentContentName,
        durationMs: durationMs,
        durationSeconds: durationSeconds,
        details: `Displayed for ${durationSeconds}s`,
        completed: completed,
      },
    });

    // Reset for next content
    this.contentPlayStartTime = null;
  }

  /**
   * Record content load failure
   */
  recordContentLoadFailure(contentId: number, error: string): void {
    this.contentLoadFailuresCount++;
    this.failedOperations++;

    SharedLogger.error(`[BehavioralMetrics] ❌ Content ${contentId} load failed: ${error} (total failures: ${this.contentLoadFailuresCount})`);

    // Log to ConnectionLogger for Playback tab
    void ConnectionLogger.log({
      eventType: 'playback',
      status: 'load_fail',
      errorMessage: error,
      metadata: {
        playbackEventType: 'load_fail',
        contentId: contentId,
        contentName: this.currentContentName,
        details: error,
        totalLoadFailures: this.contentLoadFailuresCount,
      },
    });
  }

  /**
   * Record quality switch (for HLS adaptive streaming)
   */
  recordQualitySwitch(fromQuality: string, toQuality: string): void {
    this.qualitySwitchesCount++;
    SharedLogger.log(`[BehavioralMetrics] 🔄 Quality switch: ${fromQuality} → ${toQuality} (total: ${this.qualitySwitchesCount})`);

    // Log to ConnectionLogger for Playback tab
    void ConnectionLogger.log({
      eventType: 'playback',
      status: 'quality_switch',
      metadata: {
        playbackEventType: 'quality_switch',
        contentId: this.currentContentId,
        contentName: this.currentContentName,
        details: `${fromQuality} → ${toQuality}`,
        fromQuality: fromQuality,
        toQuality: toQuality,
        totalQualitySwitches: this.qualitySwitchesCount,
      },
    });
  }

  /**
   * Get play count for specific content
   */
  getContentPlayCount(contentId: number): number {
    return this.contentPlayCounts.get(contentId)?.play_count || 0;
  }

  /**
   * Calculate error rate percentage
   */
  getErrorRatePercent(): number {
    if (this.totalOperations === 0) return 0;
    return Math.round((this.failedOperations / this.totalOperations) * 10000) / 100; // 2 decimal places
  }

  /**
   * Get all behavioral metrics
   */
  getMetrics(): BehavioralMetrics {
    return {
      playback_stalls_count: this.playbackStallsCount,
      buffer_underruns_count: this.bufferUnderrunsCount,
      time_to_first_playback_ms: this.timeToFirstPlayback,
      content_play_count: this.totalContentPlays,
      quality_switches_count: this.qualitySwitchesCount,
      content_load_failures_count: this.contentLoadFailuresCount,
      error_rate_percent: this.getErrorRatePercent(),
      total_operations: this.totalOperations,
    };
  }

  /**
   * Get summary string for logging
   */
  getSummary(): string {
    const metrics = this.getMetrics();
    return `Stalls: ${metrics.playback_stalls_count}, Buffers: ${metrics.buffer_underruns_count}, ` +
           `Plays: ${metrics.content_play_count}, Failures: ${metrics.content_load_failures_count}, ` +
           `Error Rate: ${metrics.error_rate_percent}%`;
  }

  /**
   * Destroy and cleanup
   */
  destroy(): void {
    this.boundHandlers.clear();
    this.contentPlayCounts.clear();
    SharedLogger.log('[BehavioralMetrics] 🗑️ Destroyed');
  }
}

// Export singleton instance
export const PlayerBehavioralMetrics = new PlayerBehavioralMetricsClass();

// Register to ServiceRegistry for global access
import { ServiceRegistry } from '@shared/services/service-registry';
if (typeof window !== 'undefined') {
  ServiceRegistry.register('PlayerBehavioralMetrics', PlayerBehavioralMetrics);
}
