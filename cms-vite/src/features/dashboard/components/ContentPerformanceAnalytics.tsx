/**
 * Content Performance Analytics Component
 *
 * LAYER 1: PRESENTATION
 * Top performing content analytics
 */

import { TrendingUp, Play, Users, Clock } from 'lucide-react';
import { ContentPerformance } from '../api/dashboard.api';

interface ContentPerformanceAnalyticsProps {
  data: ContentPerformance[] | undefined;
  isLoading: boolean;
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h`;
};

export default function ContentPerformanceAnalytics({ data, isLoading }: ContentPerformanceAnalyticsProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Top Performing Content
        </h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                Content
              </th>
              <th className="text-center py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                <Play className="w-4 h-4 mx-auto" />
              </th>
              <th className="text-center py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                <Users className="w-4 h-4 mx-auto" />
              </th>
              <th className="text-center py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                <Clock className="w-4 h-4 mx-auto" />
              </th>
              <th className="text-center py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                Completion
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, index) => (
                <tr key={index} className="border-b border-gray-200 dark:border-gray-700">
                  <td colSpan={5} className="py-3">
                    <div className="h-12 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
                  </td>
                </tr>
              ))
            ) : data && data.length > 0 ? (
              data.map((content, index) => (
                <tr
                  key={content.content_id}
                  className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <td className="py-3 px-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {content.content_name}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {content.content_type}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {content.total_plays}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {content.unique_devices}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {formatDuration(content.total_duration_seconds)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            content.avg_completion_rate >= 80
                              ? 'bg-green-500 dark:bg-green-600'
                              : content.avg_completion_rate >= 50
                              ? 'bg-yellow-500 dark:bg-yellow-600'
                              : 'bg-red-500 dark:bg-red-600'
                          }`}
                          style={{ width: `${content.avg_completion_rate}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-gray-500 dark:text-gray-400 w-10">
                        {Math.round(content.avg_completion_rate)}%
                      </span>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="py-8 text-center text-gray-500 dark:text-gray-400">
                  No content data available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
