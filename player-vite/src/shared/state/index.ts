/**
 * Shared State Management
 * Barrel export for all state managers
 *
 * @module State
 * @description
 * Centralized state management for the player application.
 * Uses singleton pattern with EventBus for reactive updates.
 *
 * @features
 * - PlayerState: Playlist playback and content sequencing
 * - SharedDeviceState: Device registration, activation, and preferences
 * - Type-safe state management with TypeScript
 * - Event-driven reactive updates
 * - LocalStorage persistence (device state)
 *
 * @usage
 * ```typescript
 * import { PlayerState, SharedDeviceState } from '@shared/state';
 *
 * // Load device from storage on app start
 * SharedDeviceState.loadFromStorage();
 *
 * // Set playlist and start playback
 * PlayerState.setPlaylist(playlistData);
 * PlayerState.setPlaying(true);
 *
 * // Subscribe to state changes
 * SharedEventBus.on('playlist:loaded', (data) => {
 *   console.log('Playlist loaded:', data.playlist.name);
 * });
 *
 * SharedEventBus.on('device:status-changed', (data) => {
 *   console.log('Device status:', data.status);
 * });
 * ```
 */

// Player State
export { PlayerState } from './player-state';
export type { PlayerStateData } from './player-state';
