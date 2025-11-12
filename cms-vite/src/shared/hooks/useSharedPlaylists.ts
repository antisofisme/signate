/**
 * Shared Playlists Hook
 *
 * Reusable hook for accessing playlists across features
 * Used by: devices feature
 */

import {
  usePlaylistList,
  usePlaylist,
  useCreatePlaylist,
  useUpdatePlaylist,
  useDeletePlaylist,
} from '@/features/playlists/hooks/usePlaylist';

/**
 * Shared hook to access playlist list from any feature
 * This prevents direct cross-feature imports
 */
export function useSharedPlaylists(filters?: any) {
  return usePlaylistList(filters);
}

// Re-export all playlist hooks
export {
  usePlaylistList,
  usePlaylist,
  useCreatePlaylist,
  useUpdatePlaylist,
  useDeletePlaylist,
};
