/**
 * Shared Contents Hook
 *
 * Reusable hook for accessing content across features
 * Used by: devices, playlists features
 */

import {
  useContentList,
  useContent,
  useUploadContent,
  useUpdateContent,
  useDeleteContent,
  useBulkDeleteContent,
  useContentStats,
} from '@/features/contents/hooks/useContent';

/**
 * Shared hook to access content list from any feature
 * This prevents direct cross-feature imports
 */
export function useSharedContents(filters?: any) {
  return useContentList(filters);
}

// Re-export all content hooks
export {
  useContentList,
  useContent,
  useUploadContent,
  useUpdateContent,
  useDeleteContent,
  useBulkDeleteContent,
  useContentStats,
};
