/**
 * TopContentTable Component
 * Display top performing content with ranking
 */

import { Trophy, Play, CheckCircle, Monitor, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { ContentPerformance } from '../types';

interface TopContentTableProps {
  data: ContentPerformance[];
  isLoading?: boolean;
  limit?: number;
}

export function TopContentTable({ data, isLoading, limit = 10 }: TopContentTableProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
        <div className="p-6 pb-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t('analytics.topContent', 'Top Performing Content')}
            </h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {t('analytics.topContentDesc', 'Content ranked by total plays')}
          </p>
        </div>
        <div className="p-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 py-3 animate-pulse">
              <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full" />
              <div className="flex-1">
                <div className="h-4 w-48 bg-gray-200 dark:bg-gray-700 rounded" />
                <div className="h-3 w-24 bg-gray-200 dark:bg-gray-700 rounded mt-2" />
              </div>
              <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
        <div className="p-6 pb-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t('analytics.topContent', 'Top Performing Content')}
            </h3>
          </div>
        </div>
        <div className="p-8 text-center text-gray-500 dark:text-gray-400">
          {t('analytics.noContentData', 'No content performance data available')}
        </div>
      </div>
    );
  }

  const displayData = data.slice(0, limit);

  const getRankStyle = (rank: number) => {
    switch (rank) {
      case 1:
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 ring-2 ring-yellow-400';
      case 2:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 ring-2 ring-gray-400';
      case 3:
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 ring-2 ring-orange-400';
      default:
        return 'bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400';
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('id-ID').format(num);
  };

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
      <div className="p-6 pb-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Trophy className="h-5 w-5 text-yellow-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('analytics.topContent', 'Top Performing Content')}
          </h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {t('analytics.topContentDesc', 'Content ranked by total plays')}
        </p>
      </div>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {displayData.map((content, index) => {
          const rank = index + 1;
          const completionRate = content.completion_rate ??
            (content.total_plays > 0 ? (content.completed_plays / content.total_plays) * 100 : 0);

          return (
            <div
              key={content.content_id}
              className="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              {/* Rank Badge */}
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${getRankStyle(rank)}`}
              >
                {rank}
              </div>

              {/* Content Info */}
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 dark:text-white truncate">
                  {content.title}
                </h4>
                <div className="flex items-center gap-4 mt-1 text-sm text-gray-500 dark:text-gray-400">
                  <span className="flex items-center gap-1">
                    <Play className="h-3 w-3" />
                    {formatNumber(content.total_plays)} {t('analytics.plays', 'plays')}
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3" />
                    {completionRate.toFixed(0)}%
                  </span>
                  <span className="flex items-center gap-1">
                    <Monitor className="h-3 w-3" />
                    {content.unique_devices}
                  </span>
                </div>
              </div>

              {/* Content Type Badge */}
              <span className="px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                {content.content_type}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
