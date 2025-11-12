/**
 * Shared Tags Hook
 *
 * Reusable hook for accessing tags across features
 * Used by: contents, devices features
 */

import { useTags } from '@/features/tags/hooks/useTags';

/**
 * Shared hook to access tags from any feature
 * This prevents direct cross-feature imports
 */
export function useSharedTags() {
  return useTags();
}

export { useTags };
