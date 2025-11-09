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
import type { PlaylistSync as IPlaylistSync, PlaylistSyncResponse, Playlist } from '../types/player.types';

/**
 * Player Playlist Sync Class
 * Singleton pattern for playlist synchronization
 */
class PlayerPlaylistSyncClass implements IPlaylistSync {
  private syncInterval: number | null = null;
  private readonly syncIntervalMs = 60000; // Sync every 60 seconds
  private currentPlaylistVersion: string | null = null;
  private _isRunning = false;

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

      // Fetch current playlist from backend
      const data = await SharedAPIClient.get<PlaylistSyncResponse>(
        `${config.api.baseURL}/api/client/playlist?device_id=${deviceId}`
      );

      SharedLogger.log('[PlayerPlaylistSync] 📊 Sync response:', {
        hasPlaylist: !!data.playlist,
        hasChanges: data.has_changes,
        message: data.message,
      });

      // No playlist assigned
      if (!data.playlist) {
        SharedLogger.warn('[PlayerPlaylistSync] ⚠️ No playlist assigned to device');

        // Clear current playlist if exists
        if (this.currentPlaylistVersion) {
          this.currentPlaylistVersion = null;
          this.notifyPlaylistChange(null);
          return true;
        }

        return false;
      }

      // Check if playlist changed
      const newVersion = this.calculatePlaylistVersion(data.playlist);

      if (this.currentPlaylistVersion !== newVersion) {
        SharedLogger.log('[PlayerPlaylistSync] ✅ Playlist changed!', {
          oldVersion: this.currentPlaylistVersion,
          newVersion,
          playlistId: data.playlist.id,
          itemCount: data.playlist.items?.length || 0,
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

    // Dispatch custom event for player to handle
    const event = new CustomEvent('playlist-changed', {
      detail: { playlist },
    });
    window.dispatchEvent(event);

    // Also update global player if available
    if (window.PlayerHLS) {
      if (playlist) {
        void window.PlayerHLS.loadPlaylist(playlist);
      } else {
        window.PlayerHLS.stop();
      }
    } else {
      SharedLogger.warn('[PlayerPlaylistSync] PlayerHLS not available');
    }
  }

  /**
   * Get current playlist version
   */
  getCurrentVersion(): string | null {
    return this.currentPlaylistVersion;
  }

  /**
   * Force playlist reload (clear version cache)
   */
  forceReload(): void {
    SharedLogger.log('[PlayerPlaylistSync] 🔄 Forcing playlist reload...');
    this.currentPlaylistVersion = null;
    void this.syncNow();
  }
}

// Export singleton instance
export const PlayerPlaylistSync = new PlayerPlaylistSyncClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  window.PlayerPlaylistSync = PlayerPlaylistSync;
}
