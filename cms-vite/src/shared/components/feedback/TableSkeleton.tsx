/**
 * TableSkeleton Component
 * Loading skeleton for data tables
 */
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
  className?: string;
}

export function TableSkeleton({
  rows = 5,
  columns = 4,
  showHeader = true,
  className,
}: TableSkeletonProps) {
  return (
    <div
      className={cn(
        'w-full border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden',
        className
      )}
    >
      {/* Header */}
      {showHeader && (
        <div className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
          <div className="flex gap-4">
            {Array.from({ length: columns }).map((_, i) => (
              <Skeleton
                key={`header-${i}`}
                className="h-4 flex-1"
                style={{ maxWidth: i === 0 ? '40%' : '20%' }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Rows */}
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div
            key={`row-${rowIndex}`}
            className="px-4 py-3 bg-white dark:bg-gray-900"
          >
            <div className="flex gap-4 items-center">
              {Array.from({ length: columns }).map((_, colIndex) => (
                <Skeleton
                  key={`cell-${rowIndex}-${colIndex}`}
                  className="h-4 flex-1"
                  style={{
                    maxWidth: colIndex === 0 ? '40%' : '20%',
                    opacity: 1 - rowIndex * 0.1,
                  }}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
