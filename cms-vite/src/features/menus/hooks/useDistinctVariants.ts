/**
 * Hook to get distinct variants for a menu
 * Used for auto-suggest in bulk edit modal
 */

import { useQuery } from '@tanstack/react-query';
import { menuApi } from '../api/menuApi';
import { menuKeys } from './useMenus';

/**
 * Extract unique variants from menu items variant field
 */
export const useDistinctVariants = (menuId: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: [...menuKeys.items(menuId), 'variants'],
    queryFn: async () => {
      // Fetch all items to extract variants
      const response = await menuApi.listItems(menuId, { limit: 1000 });

      // Extract unique variants
      const variantSet = new Set<string>();

      response.items.forEach((item) => {
        if (item.variant) {
          // Split by comma and add each variant
          item.variant.split(',').forEach((v) => {
            const trimmed = v.trim();
            if (trimmed) {
              variantSet.add(trimmed);
            }
          });
        }
      });

      // Return sorted array
      return Array.from(variantSet).sort((a, b) =>
        a.localeCompare(b, undefined, { sensitivity: 'base' })
      );
    },
    enabled: enabled && !!menuId,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  });
};
