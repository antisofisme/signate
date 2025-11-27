/**
 * PageSkeleton Component
 * Full page loading skeleton
 */
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface PageSkeletonProps {
  showHeader?: boolean;
  showFilters?: boolean;
  showTable?: boolean;
  tableRows?: number;
  className?: string;
}

export function PageSkeleton({
  showHeader = true,
  showFilters = true,
  showTable = true,
  tableRows = 5,
  className,
}: PageSkeletonProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* Page Header */}
      {showHeader && (
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-72" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="flex gap-4">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-32" />
        </div>
      )}

      {/* Table */}
      {showTable && (
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          {/* Table Header */}
          <div className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
            <div className="flex gap-4">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-4 w-1/5" />
              <Skeleton className="h-4 w-1/5" />
              <Skeleton className="h-4 w-1/6" />
              <Skeleton className="h-4 w-16" />
            </div>
          </div>

          {/* Table Rows */}
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {Array.from({ length: tableRows }).map((_, i) => (
              <div key={i} className="px-4 py-3 bg-white dark:bg-gray-900">
                <div className="flex gap-4 items-center">
                  <Skeleton
                    className="h-4 w-1/4"
                    style={{ opacity: 1 - i * 0.1 }}
                  />
                  <Skeleton
                    className="h-4 w-1/5"
                    style={{ opacity: 1 - i * 0.1 }}
                  />
                  <Skeleton
                    className="h-4 w-1/5"
                    style={{ opacity: 1 - i * 0.1 }}
                  />
                  <Skeleton
                    className="h-6 w-16 rounded-full"
                    style={{ opacity: 1 - i * 0.1 }}
                  />
                  <Skeleton
                    className="h-8 w-8 rounded"
                    style={{ opacity: 1 - i * 0.1 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-48" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-8 w-8" />
        </div>
      </div>
    </div>
  );
}
