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
import type { PlaylistSync as IPlaylistSync, PlaylistSyncResponse, Playlist } from '../types/player.types';
import { ServiceRegistry } from '@shared/services/service-registry';
import { getPlayerVideoJS } from '@shared/services';
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
  private useScheduling = true; // Feature flag for scheduling

  /**
   * Start periodic playlist sync
   */
  start(): void {
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
    if (this.useScheduling) {
      playerScheduleManager.initialize();
      this.setupScheduleListeners();
    }

    // Sync immediately
    void this.syncNow();

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

    // Store current playlist
    this.currentPlaylist = playlist;

    // Dispatch custom event for player to handle
    const event = new CustomEvent('playlist-changed', {
      detail: { playlist },
    });
    window.dispatchEvent(event);

    // Also update global player if available
    if (getPlayerVideoJS()) {
      if (playlist) {
        void getPlayerVideoJS().loadPlaylist(playlist);
      } else {
        getPlayerVideoJS().stop();
      }
    } else {
      SharedLogger.warn('[PlayerPlaylistSync] PlayerVideoJS not available');
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
   */
  private setupScheduleListeners(): void {
    // Listen for schedule changes
    SharedEventBus.on('schedule:changed', (event: any) => {
      const { schedule, playlist_id } = event;
      
      SharedLogger.log('[PlayerPlaylistSync] 📅 Schedule changed:', {
        schedule: schedule?.name,
        playlist_id,
        previous_playlist_id: this.scheduledPlaylistId,
      });

      // If scheduled playlist changed, force sync
      if (playlist_id !== this.scheduledPlaylistId) {
        this.scheduledPlaylistId = playlist_id;
        
        // Clear version to force reload
        this.currentPlaylistVersion = null;
        
        // Sync immediately
        void this.syncNow();
      }
    });
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
   */
  private async fetchPlaylist(deviceId: string): Promise<PlaylistSyncResponse> {
    const targetPlaylistId = await this.getTargetPlaylistId();
    
    // Build API URL
    let url = `${config.api.baseURL}/api/v1/client/playlist?device_id=${deviceId}`;
    
    // If we have a specific playlist from schedule, request it
    if (targetPlaylistId !== null) {
      url += `&playlist_id=${targetPlaylistId}`;
    }

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
