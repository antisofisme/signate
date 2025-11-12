/**
 * Shared Playlists Hook
 *
 * Reusable hook for accessing playlists across features
 * Used by: devices feature
 */

import { usePlaylistList } from '@/features/playlists/hooks/usePlaylist';

/**
 * Shared hook to access playlist list from any feature
 * This prevents direct cross-feature imports
 */
export function useSharedPlaylists(filters?: any) {
  return usePlaylistList(filters);
}

export { usePlaylistList };
