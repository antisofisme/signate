/**
 * Pagination Component
 *
 * Reusable pagination controls with consistent styling.
 * Works with usePagination hook for state management.
 *
 * Features:
 * - Page navigation (Previous/Next)
 * - Current page indicator
 * - Items count display
 * - Optional page size selector
 * - Responsive design with Tailwind CSS
 *
 * @example
 * ```tsx
 * const pagination = usePagination({ pageSize: 50 });
 *
 * <Pagination
 *   currentPage={pagination.currentPage}
 *   totalPages={pagination.getTotalPages(data?.pagination?.total || 0)}
 *   totalItems={data?.pagination?.total || 0}
 *   pageSize={pagination.pageSize}
 *   onPageChange={pagination.goToPage}
 * />
 * ```
 */

import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface PaginationProps {
  /** Current page number (0-indexed) */
  currentPage: number;
  /** Total number of pages */
  totalPages: number;
  /** Total number of items */
  totalItems: number;
  /** Items per page */
  pageSize: number;
  /** Callback when page changes */
  onPageChange: (page: number) => void;
  /** Optional: Callback when page size changes */
  onPageSizeChange?: (size: number) => void;
  /** Optional: Custom class name */
  className?: string;
}

/**
 * Pagination component with navigation controls
 */
export function Pagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
  className = ''
}: PaginationProps) {
  // Calculate display indices (1-indexed for UI)
  const startIndex = totalItems === 0 ? 0 : currentPage * pageSize + 1;
  const endIndex = Math.min((currentPage + 1) * pageSize, totalItems);

  // Navigation handlers
  const handlePrevious = () => {
    if (currentPage > 0) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages - 1) {
      onPageChange(currentPage + 1);
    }
  };

  // Don't render if no items
  if (totalItems === 0) {
    return (
      <div className={`flex items-center justify-center py-4 text-sm text-gray-500 ${className}`}>
        No items to display
      </div>
    );
  }

  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between gap-4 py-4 ${className}`}>
      {/* Items count display */}
      <div className="text-sm text-gray-700">
        Showing <span className="font-medium">{startIndex}</span> to{' '}
        <span className="font-medium">{endIndex}</span> of{' '}
        <span className="font-medium">{totalItems}</span> results
      </div>

      {/* Center: Page navigation */}
      <div className="flex items-center gap-2">
        <button
          onClick={handlePrevious}
          disabled={currentPage === 0}
          className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white transition-colors"
          aria-label="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
          Previous
        </button>

        <span className="text-sm text-gray-700 px-4">
          Page <span className="font-medium">{currentPage + 1}</span> of{' '}
          <span className="font-medium">{totalPages}</span>
        </span>

        <button
          onClick={handleNext}
          disabled={currentPage >= totalPages - 1}
          className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white transition-colors"
          aria-label="Next page"
        >
          Next
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Right: Page size selector (optional) */}
      {onPageSizeChange && (
        <div className="flex items-center gap-2">
          <label htmlFor="pageSize" className="text-sm text-gray-700">
            Show:
          </label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={(e) => {
              onPageSizeChange(Number(e.target.value));
              // Reset to first page when changing page size
              onPageChange(0);
            }}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
          <span className="text-sm text-gray-700">per page</span>
        </div>
      )}
    </div>
  );
}

/**
 * Compact version of Pagination (no page size selector, smaller buttons)
 */
export function PaginationCompact({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  className = ''
}: Omit<PaginationProps, 'onPageSizeChange'>) {
  const startIndex = totalItems === 0 ? 0 : currentPage * pageSize + 1;
  const endIndex = Math.min((currentPage + 1) * pageSize, totalItems);

  if (totalItems === 0) {
    return null;
  }

  return (
    <div className={`flex items-center justify-between gap-4 py-3 ${className}`}>
      <div className="text-xs text-gray-600">
        {startIndex}-{endIndex} of {totalItems}
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 0}
          className="p-1 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <span className="text-xs text-gray-600 px-2">
          {currentPage + 1} / {totalPages}
        </span>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages - 1}
          className="p-1 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Next page"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
