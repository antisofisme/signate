/**
 * Hook to get distinct variants (subcategory values) for a menu
 * Used for auto-suggest in bulk edit modal
 */

import { useQuery } from '@tanstack/react-query';
import { menuApi } from '../api/menuApi';
import { menuKeys } from './useMenus';

/**
 * Extract unique variants from menu items subcategory field
 */
export const useDistinctVariants = (menuId: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: [...menuKeys.items(menuId), 'variants'],
    queryFn: async () => {
      // Fetch all items to extract variants
      const response = await menuApi.listItems(menuId, { limit: 1000 });

      // Extract unique subcategories (variants)
      const variantSet = new Set<string>();

      response.items.forEach((item) => {
        if (item.subcategory) {
          // Split by comma and add each variant
          item.subcategory.split(',').forEach((v) => {
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
