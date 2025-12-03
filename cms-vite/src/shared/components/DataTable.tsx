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
  // Container wrapping the table (outer border with rounded corners)
  container: 'rounded-lg border border-gray-200 dark:border-gray-700',

  // Scroll wrapper - enables horizontal scroll on mobile/small screens
  scrollWrapper: 'overflow-x-auto',

  // The table element itself (min-w-full for desktop, will expand if needed)
  table: 'min-w-full divide-y divide-gray-200 dark:divide-gray-700',

  // Responsive table - forces horizontal scroll on mobile by preventing cell wrap
  tableResponsive: 'min-w-full divide-y divide-gray-200 dark:divide-gray-700 [&_td]:whitespace-nowrap [&_th]:whitespace-nowrap',

  // Table header (thead)
  thead: 'bg-gray-50 dark:bg-gray-900',

  // Header cell (th) - Normal
  th: 'px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider',

  // Header cell (th) - Compact
  thCompact: 'px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider',

  // Table body (tbody)
  tbody: 'bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700',

  // Body row (tr)
  tr: 'hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors',

  // Body cell (td) - Normal
  td: 'px-6 py-4 text-sm text-gray-900 dark:text-white',

  // Body cell (td) - Compact
  tdCompact: 'px-3 py-2 text-sm text-gray-900 dark:text-white',

  // Secondary/muted text within cells
  muted: 'text-gray-500 dark:text-gray-400',

  // Whitespace nowrap cell - Normal
  tdNoWrap: 'px-6 py-4 text-sm text-gray-900 dark:text-white whitespace-nowrap',

  // Whitespace nowrap cell - Compact
  tdNoWrapCompact: 'px-3 py-2 text-sm text-gray-900 dark:text-white whitespace-nowrap',

  // ============================================
  // ACTION BUTTON STYLES - For table row actions
  // Background sama dengan thead: bg-gray-50 dark:bg-gray-900 (rgb(17 24 39))
  // ============================================

  // Base action button
  actionBtn: 'p-2 bg-gray-50 dark:bg-gray-900 rounded-lg transition-colors',

  // Action button color variants
  actionBtnPurple: 'p-2 bg-gray-50 dark:bg-gray-900 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-800 rounded-lg transition-colors',
  actionBtnGray: 'p-2 bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors',
  actionBtnIndigo: 'p-2 bg-gray-50 dark:bg-gray-900 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-800 rounded-lg transition-colors',
  actionBtnBlue: 'p-2 bg-gray-50 dark:bg-gray-900 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-800 rounded-lg transition-colors',
  actionBtnGreen: 'p-2 bg-gray-50 dark:bg-gray-900 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-800 rounded-lg transition-colors',
  actionBtnOrange: 'p-2 bg-gray-50 dark:bg-gray-900 text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-800 rounded-lg transition-colors',
  actionBtnRed: 'p-2 bg-gray-50 dark:bg-gray-900 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-800 rounded-lg transition-colors',
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
  /** Use compact row height (py-2 instead of py-4) */
  compact?: boolean;
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
  compact = false,
}: DataTableProps<T>) {
  // Select styles based on compact mode
  const thStyle = compact ? TABLE_STYLES.thCompact : TABLE_STYLES.th;
  const tdStyle = compact ? TABLE_STYLES.tdCompact : TABLE_STYLES.td;
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
                  className={cn(thStyle, column.headerClassName)}
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
                    className={cn(tdStyle, column.className)}
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
