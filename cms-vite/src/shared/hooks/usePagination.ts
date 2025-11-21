/**
 * usePagination Hook
 *
 * Custom hook for managing pagination state in a standardized way.
 * Matches backend pagination defaults (skip/limit pattern).
 *
 * @example
 * ```tsx
 * const pagination = usePagination({ pageSize: 50 });
 *
 * const { data } = useQuery({
 *   queryKey: ['items', pagination.skip, pagination.limit],
 *   queryFn: () => fetchItems({ skip: pagination.skip, limit: pagination.limit })
 * });
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

import { useState, useCallback, useMemo } from 'react';

export interface PaginationConfig {
  /** Initial page number (0-indexed). Default: 0 */
  initialPage?: number;
  /** Number of items per page. Default: 50 (matches backend) */
  pageSize?: number;
}

export interface UsePaginationReturn {
  /** Current page number (0-indexed) */
  currentPage: number;
  /** Number of items per page */
  pageSize: number;
  /** Offset for API requests (currentPage * pageSize) */
  skip: number;
  /** Limit for API requests (same as pageSize) */
  limit: number;

  /** Navigate to specific page */
  goToPage: (page: number) => void;
  /** Go to next page */
  nextPage: () => void;
  /** Go to previous page */
  prevPage: () => void;
  /** Reset to first page */
  resetPage: () => void;

  /** Calculate total pages from total items count */
  getTotalPages: (totalItems: number) => number;
  /** Get display indices (1-indexed for UI) */
  getDisplayIndices: (totalItems: number) => { start: number; end: number };
}

/**
 * Custom hook for pagination state management
 */
export function usePagination(config: PaginationConfig = {}): UsePaginationReturn {
  const { initialPage = 0, pageSize = 50 } = config;

  const [currentPage, setCurrentPage] = useState(initialPage);

  // Calculate skip and limit for API requests
  const skip = useMemo(() => currentPage * pageSize, [currentPage, pageSize]);
  const limit = pageSize;

  // Navigation functions
  const goToPage = useCallback((page: number) => {
    setCurrentPage(Math.max(0, page));
  }, []);

  const nextPage = useCallback(() => {
    setCurrentPage(prev => prev + 1);
  }, []);

  const prevPage = useCallback(() => {
    setCurrentPage(prev => Math.max(0, prev - 1));
  }, []);

  const resetPage = useCallback(() => {
    setCurrentPage(0);
  }, []);

  // Utility functions
  const getTotalPages = useCallback((totalItems: number) => {
    return Math.ceil(totalItems / pageSize);
  }, [pageSize]);

  const getDisplayIndices = useCallback((totalItems: number) => {
    const start = currentPage * pageSize + 1;
    const end = Math.min((currentPage + 1) * pageSize, totalItems);
    return { start, end };
  }, [currentPage, pageSize]);

  return {
    currentPage,
    pageSize,
    skip,
    limit,
    goToPage,
    nextPage,
    prevPage,
    resetPage,
    getTotalPages,
    getDisplayIndices
  };
}
