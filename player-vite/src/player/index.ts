/**
 * Player Module Entry Point
 * Exports all player services and types
 *
 * @module Player
 * @description
 * Player context handles media playback, caching, and synchronization.
 * This is the main context for activated devices.
 */

// Services
export { PlayerVideoJS } from './services/player-videojs';
export { PlayerMediaCache } from './services/player-media-cache';
export { PlayerHLSCache } from './services/player-hls-cache';
export { PlayerPlaylistSync } from './services/player-playlist-sync';
export { PlayerHeartbeat } from './services/player-heartbeat';
export { PlayerCommandExecutor } from './services/player-command-executor';
export { PlayerPlaybackLogger } from './services/player-playback-logger';
export { PlayerHealthReporter } from './services/player-health-reporter';
export { playerScheduleManager } from './services/player-schedule-manager';

// Types
export type {
  ContentType,
  PlaylistItem,
  ContentItem,
  Playlist,
  PlaylistSyncResponse,
  PlayerConfig,
  PlayerState,
  PlayerVideoJS as IPlayerVideoJS,
  CachedMedia,
  CacheStats,
  PlayerMediaCache as IPlayerMediaCache,
  HeartbeatPayload,
  SystemInfo,
  Heartbeat as IHeartbeat,
  PlaylistSync as IPlaylistSync,
} from './types/player.types';

// Command Executor Types
export type {
  Command,
  CommandResult,
  CommandType,
} from './services/player-command-executor';
