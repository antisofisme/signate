/**
 * Shared Organizations Hook
 *
 * Reusable hook for accessing organizations across features
 * Used by: users feature
 */

import { useOrganizations } from '@/features/organizations/hooks/useOrganizations';

/**
 * Shared hook to access organizations from any feature
 * This prevents direct cross-feature imports
 */
export function useSharedOrganizations() {
  return useOrganizations();
}

export { useOrganizations };
