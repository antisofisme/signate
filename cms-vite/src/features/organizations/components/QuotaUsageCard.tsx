/**
 * Quota Usage Card
 *
 * Displays quota usage for a specific resource (devices, users, content, playlists)
 * with progress bar and color-coded indicators
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { QuotaInfo, StorageQuotaInfo } from '../types/organization';

interface QuotaUsageCardProps {
  title: string;
  description: string;
  quota: QuotaInfo | StorageQuotaInfo;
  icon?: React.ReactNode;
  isStorage?: boolean;
}

export function QuotaUsageCard({
  title,
  description,
  quota,
  icon,
  isStorage = false,
}: QuotaUsageCardProps) {
  const getProgressColor = (percentage: number) => {
    if (percentage >= 95) return 'bg-red-500';
    if (percentage >= 80) return 'bg-orange-500';
    if (percentage >= 60) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getBadgeColor = (percentage: number) => {
    if (percentage >= 95) return 'bg-red-100 text-red-800';
    if (percentage >= 80) return 'bg-orange-100 text-orange-800';
    if (percentage >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  // For storage quota, show both items and size
  if (isStorage && 'max_items' in quota) {
    const storageQuota = quota as StorageQuotaInfo;

    return (
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              {icon}
              <div>
                <CardTitle className="text-lg">{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Items Quota */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Content Items</span>
              <span
                className={cn(
                  'text-xs px-2 py-0.5 rounded-full font-medium',
                  getBadgeColor(storageQuota.items_percentage_used)
                )}
              >
                {storageQuota.items_percentage_used.toFixed(1)}%
              </span>
            </div>
            <Progress
              value={storageQuota.items_percentage_used}
              className={cn('h-2', getProgressColor(storageQuota.items_percentage_used))}
            />
            <div className="mt-1 flex justify-between text-xs text-gray-600">
              <span>
                {storageQuota.current_items.toLocaleString()} /{' '}
                {storageQuota.max_items.toLocaleString()} items
              </span>
              <span>{storageQuota.available_items.toLocaleString()} available</span>
            </div>
          </div>

          {/* Storage Size Quota */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Storage Size</span>
              <span
                className={cn(
                  'text-xs px-2 py-0.5 rounded-full font-medium',
                  getBadgeColor(storageQuota.size_percentage_used)
                )}
              >
                {storageQuota.size_percentage_used.toFixed(1)}%
              </span>
            </div>
            <Progress
              value={storageQuota.size_percentage_used}
              className={cn('h-2', getProgressColor(storageQuota.size_percentage_used))}
            />
            <div className="mt-1 flex justify-between text-xs text-gray-600">
              <span>
                {storageQuota.current_size_gb.toFixed(2)} / {storageQuota.max_size_gb} GB
              </span>
              <span>{storageQuota.available_size_gb.toFixed(2)} GB available</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Standard quota (devices, users, playlists)
  const standardQuota = quota as QuotaInfo;
  const percentage = standardQuota.percentage_used;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {icon}
            <div>
              <CardTitle className="text-lg">{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </div>
          </div>
          <span
            className={cn(
              'text-xs px-2 py-0.5 rounded-full font-medium',
              getBadgeColor(percentage)
            )}
          >
            {percentage.toFixed(1)}%
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <Progress
          value={percentage}
          className={cn('h-2', getProgressColor(percentage))}
        />
        <div className="mt-2 flex justify-between text-sm text-gray-600">
          <span>
            {standardQuota.current.toLocaleString()} / {standardQuota.max.toLocaleString()}
          </span>
          <span>{standardQuota.available.toLocaleString()} available</span>
        </div>
      </CardContent>
    </Card>
  );
}
