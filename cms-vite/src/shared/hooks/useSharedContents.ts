/**
 * Shared Contents Hook
 *
 * Reusable hook for accessing content across features
 * Used by: devices, playlists features
 */

import { useContentList } from '@/features/contents/hooks/useContent';

/**
 * Shared hook to access content list from any feature
 * This prevents direct cross-feature imports
 */
export function useSharedContents(filters?: any) {
  return useContentList(filters);
}

export { useContentList };
