/**
 * Shared Tags Hook
 *
 * Reusable hook for accessing tags across features
 * Used by: contents, devices features
 */

import {
  useTags,
  useCreateTag,
  useUpdateTag,
  useDeleteTag,
  useAssignTagToContents,
} from '@/features/tags/hooks/useTags';

/**
 * Shared hook to access tags from any feature
 * This prevents direct cross-feature imports
 */
export function useSharedTags() {
  return useTags();
}

// Re-export all tag hooks
export {
  useTags,
  useCreateTag,
  useUpdateTag,
  useDeleteTag,
  useAssignTagToContents,
};
