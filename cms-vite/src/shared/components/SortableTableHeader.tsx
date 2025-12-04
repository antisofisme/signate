/**
 * SortableTableHeader Component
 *
 * Reusable sortable table header for tables using TABLE_STYLES.
 * Works with useTableSort hook for server-side sorting with URL persistence.
 *
 * Usage:
 * ```tsx
 * import { SortableTableHeader, TABLE_STYLES } from '@/shared/components';
 * import { useTableSort } from '@/shared/hooks';
 *
 * const { sortConfig, onSortChange, sortParams } = useTableSort();
 *
 * // Pass sortParams to your API call
 * const { data } = useMyList({ ...filters, ...sortParams });
 *
 * // In your table header
 * <th className={TABLE_STYLES.th}>
 *   <SortableTableHeader
 *     columnKey="name"
 *     sortConfig={sortConfig}
 *     onSortChange={onSortChange}
 *   >
 *     Name
 *   </SortableTableHeader>
 * </th>
 * ```
 */

import { ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';
import type { SortConfig, SortDirection } from './DataTable';

export interface SortableTableHeaderProps {
  /** Column key used for sorting (sent to backend as sort_by) */
  columnKey: string;
  /** Current sort configuration from useTableSort */
  sortConfig: SortConfig | null;
  /** Callback to update sort from useTableSort */
  onSortChange: (config: SortConfig | null) => void;
  /** Header content (text or React node) */
  children: React.ReactNode;
  /** Optional custom className */
  className?: string;
}

/**
 * Get the appropriate sort icon based on current sort state
 */
function getSortIcon(columnKey: string, sortConfig: SortConfig | null) {
  if (!sortConfig || sortConfig.key !== columnKey) {
    return <ArrowUpDown className="w-4 h-4 opacity-40" />;
  }
  return sortConfig.direction === 'asc' ? (
    <ArrowUp className="w-4 h-4 text-blue-500" />
  ) : (
    <ArrowDown className="w-4 h-4 text-blue-500" />
  );
}

/**
 * Handle sort toggle logic:
 * - Click on unsorted column → sort ascending
 * - Click on ascending column → sort descending
 * - Click on descending column → clear sort
 */
function handleSortClick(
  columnKey: string,
  sortConfig: SortConfig | null,
  onSortChange: (config: SortConfig | null) => void
) {
  if (!sortConfig || sortConfig.key !== columnKey) {
    // New column - set to ascending
    onSortChange({ key: columnKey, direction: 'asc' });
  } else if (sortConfig.direction === 'asc') {
    // Same column, was asc - switch to desc
    onSortChange({ key: columnKey, direction: 'desc' });
  } else {
    // Same column, was desc - clear sort
    onSortChange(null);
  }
}

export function SortableTableHeader({
  columnKey,
  sortConfig,
  onSortChange,
  children,
  className = '',
}: SortableTableHeaderProps) {
  const isActive = sortConfig?.key === columnKey;

  return (
    <button
      type="button"
      onClick={() => handleSortClick(columnKey, sortConfig, onSortChange)}
      className={`flex items-center gap-1 transition-colors group ${
        isActive
          ? 'text-blue-600 dark:text-blue-400'
          : 'hover:text-blue-600 dark:hover:text-blue-400'
      } ${className}`}
    >
      {children}
      <span
        className={
          isActive
            ? 'opacity-100'
            : 'opacity-0 group-hover:opacity-100 transition-opacity'
        }
      >
        {getSortIcon(columnKey, sortConfig)}
      </span>
    </button>
  );
}

export default SortableTableHeader;
