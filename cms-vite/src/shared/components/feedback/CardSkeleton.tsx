/**
 * CardSkeleton Component
 * Loading skeleton for card layouts
 */
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface CardSkeletonProps {
  showImage?: boolean;
  showBadge?: boolean;
  showActions?: boolean;
  className?: string;
}

export function CardSkeleton({
  showImage = true,
  showBadge = true,
  showActions = true,
  className,
}: CardSkeletonProps) {
  return (
    <div
      className={cn(
        'bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden',
        className
      )}
    >
      {/* Image placeholder */}
      {showImage && <Skeleton className="w-full h-40" />}

      {/* Content */}
      <div className="p-4 space-y-3">
        {/* Title and badge */}
        <div className="flex items-start justify-between gap-2">
          <Skeleton className="h-5 w-3/4" />
          {showBadge && <Skeleton className="h-5 w-16 rounded-full" />}
        </div>

        {/* Description */}
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </div>

        {/* Meta info */}
        <div className="flex items-center gap-4">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-20" />
        </div>

        {/* Actions */}
        {showActions && (
          <div className="flex items-center gap-2 pt-2">
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-8 w-8" />
          </div>
        )}
      </div>
    </div>
  );
}

interface CardGridSkeletonProps {
  count?: number;
  columns?: 2 | 3 | 4;
  showImage?: boolean;
  className?: string;
}

export function CardGridSkeleton({
  count = 6,
  columns = 3,
  showImage = true,
  className,
}: CardGridSkeletonProps) {
  const gridCols = {
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
  };

  return (
    <div className={cn('grid gap-4', gridCols[columns], className)}>
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} showImage={showImage} />
      ))}
    </div>
  );
}
