/**
 * DataTable Component
 * Reusable table with standardized styles across the CMS
 *
 * Usage:
 * - For simple tables: Use DataTable component directly
 * - For complex tables: Import TABLE_STYLES constants for consistent styling
 */

import { cn } from '@/lib/utils';
import { TableSkeleton } from './feedback/TableSkeleton';
import { EmptyState } from './feedback/EmptyState';
import { Package, LucideIcon } from 'lucide-react';

// ============================================
// STANDARD TABLE STYLES - Export for complex tables
// ============================================

export const TABLE_STYLES = {
  // Container wrapping the table
  container: 'overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700',

  // The table element itself
  table: 'min-w-full divide-y divide-gray-200 dark:divide-gray-700',

  // Table header (thead)
  thead: 'bg-gray-50 dark:bg-gray-900',

  // Header cell (th)
  th: 'px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider',

  // Table body (tbody)
  tbody: 'bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700',

  // Body row (tr)
  tr: 'hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors',

  // Body cell (td)
  td: 'px-6 py-4 text-sm text-gray-900 dark:text-white',

  // Secondary/muted text within cells
  muted: 'text-gray-500 dark:text-gray-400',

  // Whitespace nowrap cell
  tdNoWrap: 'px-6 py-4 text-sm text-gray-900 dark:text-white whitespace-nowrap',
} as const;

// ============================================
// COMPONENT TYPES
// ============================================

export interface Column<T> {
  /** Unique key for the column */
  key: string;
  /** Header text */
  header: string;
  /** Custom render function for cell content */
  render?: (item: T, index: number) => React.ReactNode;
  /** Additional classes for this column's cells */
  className?: string;
  /** Additional classes for header cell */
  headerClassName?: string;
}

export interface DataTableProps<T> {
  /** Column definitions */
  columns: Column<T>[];
  /** Data array to display */
  data: T[];
  /** Function to extract unique key from each item */
  keyExtractor: (item: T) => string | number;
  /** Whether data is loading */
  isLoading?: boolean;
  /** Message to show when data is empty */
  emptyMessage?: string;
  /** Description for empty state */
  emptyDescription?: string;
  /** Icon for empty state */
  emptyIcon?: LucideIcon;
  /** Action component for empty state */
  emptyAction?: React.ReactNode;
  /** Click handler for rows */
  onRowClick?: (item: T) => void;
  /** Function to add custom classes to rows */
  rowClassName?: (item: T) => string;
  /** Additional classes for the container */
  className?: string;
  /** Number of skeleton rows when loading */
  skeletonRows?: number;
}

// ============================================
// COMPONENT
// ============================================

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  isLoading = false,
  emptyMessage = 'No data found',
  emptyDescription,
  emptyIcon = Package,
  emptyAction,
  onRowClick,
  rowClassName,
  className,
  skeletonRows = 5,
}: DataTableProps<T>) {
  // Loading state
  if (isLoading) {
    return (
      <div className={cn(TABLE_STYLES.container, className)}>
        <TableSkeleton columns={columns.length} rows={skeletonRows} />
      </div>
    );
  }

  // Empty state
  if (data.length === 0) {
    return (
      <div className={cn(TABLE_STYLES.container, className)}>
        <EmptyState
          icon={emptyIcon}
          title={emptyMessage}
          description={emptyDescription}
          action={emptyAction}
        />
      </div>
    );
  }

  // Table with data
  return (
    <div className={cn(TABLE_STYLES.container, className)}>
      <div className="overflow-x-auto">
        <table className={TABLE_STYLES.table}>
          <thead className={TABLE_STYLES.thead}>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(TABLE_STYLES.th, column.headerClassName)}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className={TABLE_STYLES.tbody}>
            {data.map((item, rowIndex) => (
              <tr
                key={keyExtractor(item)}
                className={cn(
                  TABLE_STYLES.tr,
                  onRowClick && 'cursor-pointer',
                  rowClassName?.(item)
                )}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map((column) => (
                  <td
                    key={`${keyExtractor(item)}-${column.key}`}
                    className={cn(TABLE_STYLES.td, column.className)}
                  >
                    {column.render
                      ? column.render(item, rowIndex)
                      : (item as Record<string, unknown>)[column.key] as React.ReactNode}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DataTable;
