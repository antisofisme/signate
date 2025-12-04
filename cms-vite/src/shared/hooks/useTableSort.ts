/**
 * useTableSort Hook
 *
 * Manages table sorting state with URL persistence.
 * Works with DataTable component's sorting feature.
 *
 * Features:
 * - URL state persistence (?sort=name&dir=asc)
 * - Auto reset to page 1 on sort change (optional)
 * - TypeScript support for sort keys
 *
 * Usage:
 * ```tsx
 * const { sortConfig, onSortChange, sortParams } = useTableSort({
 *   defaultSort: { key: 'created_at', direction: 'desc' },
 *   onPageReset: () => setPage(1),
 * });
 *
 * // Pass to DataTable
 * <DataTable sortConfig={sortConfig} onSortChange={onSortChange} ... />
 *
 * // Pass to API query
 * useQuery(['items', sortParams], () => fetchItems(sortParams));
 * ```
 */

import { useSearchParams } from 'react-router-dom';
import { useCallback, useMemo } from 'react';
import type { SortConfig, SortDirection } from '../components/DataTable';

interface UseTableSortOptions {
  /** Default sort configuration */
  defaultSort?: SortConfig | null;
  /** Callback to reset page when sort changes */
  onPageReset?: () => void;
  /** URL param name for sort key (default: 'sort') */
  sortParam?: string;
  /** URL param name for sort direction (default: 'dir') */
  dirParam?: string;
}

interface UseTableSortReturn {
  /** Current sort configuration (for DataTable) */
  sortConfig: SortConfig | null;
  /** Handler for sort changes (for DataTable) */
  onSortChange: (config: SortConfig | null) => void;
  /** Sort params for API calls { sort_by, sort_dir } */
  sortParams: { sort_by?: string; sort_dir?: SortDirection };
  /** Clear sort and reset to default */
  clearSort: () => void;
}

export function useTableSort({
  defaultSort = null,
  onPageReset,
  sortParam = 'sort',
  dirParam = 'dir',
}: UseTableSortOptions = {}): UseTableSortReturn {
  const [searchParams, setSearchParams] = useSearchParams();

  // Parse current sort from URL
  const sortConfig = useMemo((): SortConfig | null => {
    const sortKey = searchParams.get(sortParam);
    const sortDir = searchParams.get(dirParam) as SortDirection;

    if (sortKey && (sortDir === 'asc' || sortDir === 'desc')) {
      return { key: sortKey, direction: sortDir };
    }

    // Return default if no URL params
    return defaultSort;
  }, [searchParams, sortParam, dirParam, defaultSort]);

  // Handle sort change
  const onSortChange = useCallback(
    (config: SortConfig | null) => {
      setSearchParams((prev) => {
        const newParams = new URLSearchParams(prev);

        if (config && config.direction) {
          newParams.set(sortParam, config.key);
          newParams.set(dirParam, config.direction);
        } else {
          newParams.delete(sortParam);
          newParams.delete(dirParam);
        }

        // Reset page param when sort changes
        newParams.delete('page');

        return newParams;
      });

      // Callback to reset page state
      onPageReset?.();
    },
    [setSearchParams, sortParam, dirParam, onPageReset]
  );

  // Clear sort
  const clearSort = useCallback(() => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      newParams.delete(sortParam);
      newParams.delete(dirParam);
      return newParams;
    });
  }, [setSearchParams, sortParam, dirParam]);

  // Params for API calls
  const sortParams = useMemo(() => {
    if (!sortConfig || !sortConfig.direction) {
      return {};
    }
    return {
      sort_by: sortConfig.key,
      sort_dir: sortConfig.direction,
    };
  }, [sortConfig]);

  return {
    sortConfig,
    onSortChange,
    sortParams,
    clearSort,
  };
}

export default useTableSort;
