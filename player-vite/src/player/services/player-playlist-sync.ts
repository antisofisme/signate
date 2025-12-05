/**
 * Player Playlist Sync Service
 * Synchronizes playlist from backend and triggers playback updates
 *
 * @features
 * - Periodic playlist sync from backend
 * - Detects playlist changes and triggers reload
 * - Handles sync errors with automatic retry
 * - Type-safe with TypeScript
 */

import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedAPIClient } from '@shared/api';
import { SharedDeviceState } from '@shared/device';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import { playerScheduleManager } from './player-schedule-manager';
import { PlayerBackgroundAudio } from './player-background-audio';
import type { PlaylistSync as IPlaylistSync, PlaylistSyncResponse, Playlist } from '@player/types/player.types';
import { ServiceRegistry, getPlayerVideoJS, getPlayerMediaCache, getPlayerHLSCache } from '@shared/services/service-registry';
import { WaitingForContent } from '@player/components';

/**
 * Player Playlist Sync Class
 * Singleton pattern for playlist synchronization
 */
class PlayerPlaylistSyncClass implements IPlaylistSync {
  private syncInterval: number | null = null;
  private readonly syncIntervalMs = 60000; // Sync every 60 seconds
  private currentPlaylistVersion: string | null = null;
  private currentPlaylist: Playlist | null = null; // Store current playlist
  private _isRunning = false;
  private scheduledPlaylistId: number | null = null;
  private activeScheduleId: number | null = null;  // Track active schedule ID
  private activeScheduleMode: 'override' | 'rotate' = 'rotate';  // Track schedule mode
  private useScheduling = true; // Feature flag for scheduling

  /**
   * Start periodic playlist sync
   */
  async start(): Promise<void> {
    if (this._isRunning) {
      SharedLogger.warn('[PlayerPlaylistSync] Already running');
      return;
    }

    const deviceId = SharedDeviceState.getDeviceId();
    if (!deviceId) {
      SharedLogger.error('[PlayerPlaylistSync] Cannot start - no device_id');
      return;
    }

    SharedLogger.log('[PlayerPlaylistSync] 🔄 Starting playlist sync...');
    this._isRunning = true;

    // Initialize schedule manager if scheduling is enabled
    // IMPORTANT: Wait for schedule manager to initialize BEFORE first playlist sync
    // This ensures we know the active schedule mode (override vs rotate)
    if (this.useScheduling) {
      SharedLogger.log('[PlayerPlaylistSync] ⏳ Waiting for schedule manager to initialize...');
      await playerScheduleManager.initialize();
      this.setupScheduleListeners();
      SharedLogger.log('[PlayerPlaylistSync] ✅ Schedule manager initialized');

      // FIX #4: Force initial schedule state from schedule manager
      // This ensures PlaylistSync has the correct mode even if event was emitted before listener setup
      const currentSchedule = playerScheduleManager.getCurrentSchedule();
      if (currentSchedule) {
        this.activeScheduleId = currentSchedule.id;
        this.activeScheduleMode = currentSchedule.mode || 'rotate';
        this.scheduledPlaylistId = currentSchedule.playlist_id;
        SharedLogger.log('[PlayerPlaylistSync] 🎯 Force-set initial schedule state:', {
          schedule_id: this.activeScheduleId,
          mode: this.activeScheduleMode,
          playlist_id: this.scheduledPlaylistId,
        });
      } else {
        SharedLogger.log('[PlayerPlaylistSync] No active schedule at start, using rotate mode');
        this.activeScheduleMode = 'rotate';
      }
    }

    // FIX #3: AWAIT first sync instead of fire-and-forget
    // Previously: void this.syncNow() - could run before schedule info available
    SharedLogger.log('[PlayerPlaylistSync] 🔄 Running first playlist sync...');
    await this.syncNow();
    SharedLogger.log('[PlayerPlaylistSync] ✅ First playlist sync complete');

    // Then sync periodically
    this.syncInterval = window.setInterval(() => {
      void this.syncNow();
    }, this.syncIntervalMs);
  }

  /**
   * Stop periodic playlist sync
   */
  stop(): void {
    if (!this._isRunning) {
      return;
    }

    if (this.syncInterval !== null) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }

    // Stop schedule manager
    if (this.useScheduling) {
      playerScheduleManager.stop();
    }

    // Clean up EventBus listeners to prevent duplicate handlers on restart
    SharedEventBus.removeNamespace('playlist-sync');

    this._isRunning = false;
    SharedLogger.log('[PlayerPlaylistSync] ⏹️ Playlist sync stopped');
  }

  /**
   * Sync playlist now (manual trigger)
   * @returns true if playlist changed, false if no changes
   */
  async syncNow(): Promise<boolean> {
    const deviceId = SharedDeviceState.getDeviceId();
    if (!deviceId) {
      SharedLogger.error('[PlayerPlaylistSync] Cannot sync - no device_id');
      return false;
    }

    try {
      SharedLogger.log('[PlayerPlaylistSync] 📥 Syncing playlist from backend...');

      // Fetch current playlist from backend (with schedule support)
      const data = await this.fetchPlaylist(deviceId);

      SharedLogger.log('[PlayerPlaylistSync] 📊 Sync response:', {
        hasPlaylist: !!data.playlist,
        hasChanges: data.has_changes,
        message: data.message,
      });

      // No playlist assigned
      if (!data.playlist) {
        SharedLogger.warn('[PlayerPlaylistSync] ⚠️ No playlist assigned to device');

        // Show waiting for content screen
        WaitingForContent.show();

        // Clear current playlist if exists
        if (this.currentPlaylistVersion) {
          this.currentPlaylistVersion = null;
          this.notifyPlaylistChange(null);
          return true;
        }

        return false;
      }

      // Playlist exists - hide waiting screen
      WaitingForContent.hide();

      // Handle device settings (volume, background audio, rotation)
      if (data.device_settings) {
        SharedLogger.log('[PlayerPlaylistSync] 📊 Device settings received:', {
          volume: data.device_settings.volume_level,
          rotation: data.device_settings.rotation,
          background_audio: data.device_settings.background_audio_name,
        });

        // Update volume for content playback
        if (getPlayerVideoJS()) { getPlayerVideoJS()!.setVolume(data.device_settings.volume_level);
        }

        // Apply rotation (global device setting)
        if (typeof data.device_settings.rotation === 'number') {
          SharedDeviceState.setScreenRotation(data.device_settings.rotation);
          const { ShellDisplaySettings } = await import('@shell/services/shell-display-settings');
          ShellDisplaySettings.applyRotation();
          SharedLogger.log(`[PlayerPlaylistSync] ✅ Applied rotation: ${data.device_settings.rotation}deg`);
        }

        // Load background audio
        await PlayerBackgroundAudio.loadFromSettings(data.device_settings);
      }

      // Check if playlist changed
      const newVersion = this.calculatePlaylistVersion(data.playlist);
      const isFirstLoad = this.currentPlaylistVersion === null;

      SharedLogger.log('[PlayerPlaylistSync] Version check:', {
        currentVersion: this.currentPlaylistVersion,
        newVersion,
        isFirstLoad,
        hasChanged: this.currentPlaylistVersion !== newVersion,
      });

      if (this.currentPlaylistVersion !== newVersion || isFirstLoad) {
        SharedLogger.log('[PlayerPlaylistSync] ✅ Playlist changed!', {
          oldVersion: this.currentPlaylistVersion,
          newVersion,
          playlistId: data.playlist.id,
          itemCount: data.playlist.items?.length || 0,
          isFirstLoad,
        });

        // Update version
        this.currentPlaylistVersion = newVersion;

        // Notify player about playlist change
        this.notifyPlaylistChange(data.playlist);

        return true;
      } else {
        SharedLogger.log('[PlayerPlaylistSync] No playlist changes detected');
        return false;
      }
    } catch (error) {
      SharedLogger.error('[PlayerPlaylistSync] ❌ Sync failed:', error);
      return false;
    }
  }

  /**
   * Check if sync is running
   */
  isRunning(): boolean {
    return this._isRunning;
  }

  /**
   * Calculate playlist version (hash) for change detection
   * Based on playlist ID, item count, and item order
   */
  private calculatePlaylistVersion(playlist: Playlist): string {
    const itemSignature = playlist.items
      ?.map((item) => `${item.id}-${item.content_id}-${item.order}`)
      .join('|') || '';

    return `${playlist.id}:${playlist.items?.length || 0}:${itemSignature}`;
  }

  /**
   * Notify player about playlist change
   * Triggers HLS player to reload playlist
   */
  private notifyPlaylistChange(playlist: Playlist | null): void {
    SharedLogger.log('[PlayerPlaylistSync] 📢 Notifying player about playlist change...');

    // Clean up orphaned cache from removed content (async, don't block)
    this.cleanupOrphanedCache(this.currentPlaylist, playlist);

    // Store current playlist
    this.currentPlaylist = playlist;

    // Emit event via SharedEventBus
    SharedEventBus.emit('playlist:changed', { playlist });

    // Also update global player if available
    if (getPlayerVideoJS()) {
      if (playlist) {
        void getPlayerVideoJS()?.loadPlaylist(playlist);
      } else {
        getPlayerVideoJS()?.stop();
      }
    } else {
      SharedLogger.warn('[PlayerPlaylistSync] PlayerVideoJS not available');
    }
  }

  /**
   * Clean up cache for content that was removed from playlist
   * Only removes content that's no longer in any playlist
   *
   * IMPORTANT: Skip cleanup when in override mode!
   * Override mode only controls what's PLAYED, not what's CACHED.
   * Content from direct/tag assignments should stay cached even when not playing.
   */
  private async cleanupOrphanedCache(oldPlaylist: Playlist | null, newPlaylist: Playlist | null): Promise<void> {
    if (!oldPlaylist?.items || oldPlaylist.items.length === 0) {
      // No old playlist, nothing to clean up
      return;
    }

    // ========================================================================
    // SKIP CLEANUP IN OVERRIDE MODE
    // Override only affects playback, cache should continue for all content
    // ========================================================================
    if (this.activeScheduleMode === 'override') {
      SharedLogger.log('[PlayerPlaylistSync] ⏭️ Skipping cache cleanup - override mode active (cache continues for all content)');
      return;
    }

    try {
      // Get content IDs from old and new playlists
      const oldContentIds = new Set(oldPlaylist.items.map(item => item.content_id));
      const newContentIds = new Set(newPlaylist?.items?.map(item => item.content_id) || []);

      // Find removed content IDs
      const removedContentIds = [...oldContentIds].filter(id => !newContentIds.has(id));

      if (removedContentIds.length === 0) {
        SharedLogger.log('[PlayerPlaylistSync] No content removed from playlist');
        return;
      }

      SharedLogger.log('[PlayerPlaylistSync] 🗑️ Cleaning up orphaned cache...', {
        removedCount: removedContentIds.length,
        removedIds: removedContentIds,
      });

      // Get caches
      const PlayerMediaCache = getPlayerMediaCache();
      const PlayerHLSCache = getPlayerHLSCache();

      // Clean up from MediaCache
      if (PlayerMediaCache) {
        for (const contentId of removedContentIds) {
          // Find and delete by content ID
          const oldItem = oldPlaylist.items.find(item => item.content_id === contentId);
          if (oldItem) {
            const url = oldItem.content?.file_path || oldItem.content?.url;
            if (url) {
              try {
                await PlayerMediaCache.deleteMedia(url);
                SharedLogger.log(`[PlayerPlaylistSync] ✅ Deleted cache for content ${contentId}`);
              } catch (e) {
                // Ignore errors (might not be cached)
              }
            }
          }
        }
      }

      // Clean up from HLS cache
      if (PlayerHLSCache) {
        for (const contentId of removedContentIds) {
          try {
            await PlayerHLSCache.clearCache(contentId);
            SharedLogger.log(`[PlayerPlaylistSync] ✅ Deleted HLS cache for content ${contentId}`);
          } catch (e) {
            // Ignore errors (might not be cached)
          }
        }
      }

      SharedLogger.log('[PlayerPlaylistSync] ✅ Cache cleanup complete');
    } catch (error) {
      SharedLogger.error('[PlayerPlaylistSync] Cache cleanup failed:', error);
    }
  }

  /**
   * Get current playlist version
   */
  getCurrentVersion(): string | null {
    return this.currentPlaylistVersion;
  }

  /**
   * Get current playlist
   * Returns the last loaded playlist or null if not loaded yet
   */
  getCurrentPlaylist(): Playlist | null {
    return this.currentPlaylist;
  }

  /**
   * Force playlist reload (clear version cache)
   */
  forceReload(): void {
    SharedLogger.log('[PlayerPlaylistSync] 🔄 Forcing playlist reload...');
    this.currentPlaylistVersion = null;
    void this.syncNow();
  }

  /**
   * Setup schedule event listeners
   * Uses namespace 'playlist-sync' for cleanup in stop()
   */
  private setupScheduleListeners(): void {
    // Listen for schedule changes (with namespace for cleanup)
    SharedEventBus.on('schedule:changed', (event: any) => {
      const { schedule, playlist_id, mode } = event;

      SharedLogger.log('[PlayerPlaylistSync] 📅 Schedule changed:', {
        schedule: schedule?.name,
        schedule_id: schedule?.id,
        playlist_id,
        mode: mode || 'rotate',
        previous_playlist_id: this.scheduledPlaylistId,
        previous_mode: this.activeScheduleMode,
      });

      // Track schedule info for override mode
      const newScheduleId = schedule?.id || null;
      const newMode = mode || 'rotate';

      // If scheduled playlist OR mode changed, force sync
      const playlistChanged = playlist_id !== this.scheduledPlaylistId;
      const modeChanged = newMode !== this.activeScheduleMode;

      if (playlistChanged || modeChanged) {
        this.scheduledPlaylistId = playlist_id;
        this.activeScheduleId = newScheduleId;
        this.activeScheduleMode = newMode;

        SharedLogger.log('[PlayerPlaylistSync] 🔄 Schedule info updated:', {
          schedule_id: this.activeScheduleId,
          playlist_id: this.scheduledPlaylistId,
          mode: this.activeScheduleMode,
        });

        // Clear version to force reload
        this.currentPlaylistVersion = null;

        // Sync immediately
        void this.syncNow();
      }
    }, 'playlist-sync');
  }

  /**
   * Get playlist ID to sync (considers scheduling)
   */
  private async getTargetPlaylistId(): Promise<number | null> {
    // If scheduling is enabled and we have a scheduled playlist, use it
    if (this.useScheduling && this.scheduledPlaylistId !== null) {
      SharedLogger.debug('[PlayerPlaylistSync] Using scheduled playlist:', this.scheduledPlaylistId);
      return this.scheduledPlaylistId;
    }

    // Otherwise, let backend decide based on device assignment
    return null;
  }

  /**
   * Fetch playlist with schedule support
   * Includes schedule_id and schedule_mode for override mode
   */
  private async fetchPlaylist(deviceId: string): Promise<PlaylistSyncResponse> {
    const targetPlaylistId = await this.getTargetPlaylistId();

    // Build API URL
    let url = `${config.api.baseURL}/api/v1/client/playlist?device_id=${deviceId}`;

    // If we have a specific playlist from schedule, request it
    if (targetPlaylistId !== null) {
      url += `&playlist_id=${targetPlaylistId}`;
    }

    // Debug: Log current schedule state before fetch
    SharedLogger.log('[PlayerPlaylistSync] 📋 Schedule state before fetch:', {
      activeScheduleMode: this.activeScheduleMode,
      activeScheduleId: this.activeScheduleId,
      scheduledPlaylistId: this.scheduledPlaylistId,
    });

    // Include schedule info for override mode
    // This tells backend to return ONLY the scheduled playlist content
    if (this.activeScheduleMode === 'override' && this.activeScheduleId) {
      url += `&schedule_id=${this.activeScheduleId}`;
      url += `&schedule_mode=override`;
      SharedLogger.log('[PlayerPlaylistSync] 🎯 Fetching with OVERRIDE mode:', {
        schedule_id: this.activeScheduleId,
        playlist_id: targetPlaylistId,
      });
    } else {
      SharedLogger.log('[PlayerPlaylistSync] 📋 Fetching with ROTATE mode (normal merge)');
    }

    SharedLogger.log('[PlayerPlaylistSync] 🌐 Final URL:', url);

    return await SharedAPIClient.get<PlaylistSyncResponse>(url);
  }
}

// Export singleton instance
export const PlayerPlaylistSync = new PlayerPlaylistSyncClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('PlayerPlaylistSync', PlayerPlaylistSync);
}
