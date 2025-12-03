/**
 * Recent Activity Feed Component
 *
 * LAYER 1: PRESENTATION
 * Recent system activity and audit trail
 */

import { Activity, User, Monitor, FileImage, ListVideo, Settings } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { RecentActivity } from '../api/dashboard.api';
import { formatDistanceToNow } from 'date-fns';

interface RecentActivityFeedProps {
  data: RecentActivity[] | undefined;
  isLoading: boolean;
}

const getActivityIcon = (resourceType: string) => {
  switch (resourceType.toLowerCase()) {
    case 'device':
      return Monitor;
    case 'content':
      return FileImage;
    case 'playlist':
      return ListVideo;
    case 'user':
      return User;
    case 'settings':
      return Settings;
    default:
      return Activity;
  }
};

const getActivityColor = (action: string) => {
  if (action.includes('created') || action.includes('added')) {
    return 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400';
  }
  if (action.includes('updated') || action.includes('modified')) {
    return 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400';
  }
  if (action.includes('deleted') || action.includes('removed')) {
    return 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400';
  }
  return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400';
};

export default function RecentActivityFeed({ data, isLoading }: RecentActivityFeedProps) {
  const { t } = useTranslation();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <Activity className="w-5 h-5" />
          {t('dashboard.activity.title', 'Recent Activity')}
        </h2>
      </div>

      <div className="space-y-4 max-h-96 overflow-y-auto">
        {isLoading ? (
          Array.from({ length: 8 }).map((_, index) => (
            <div key={index} className="flex gap-3">
              <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 animate-pulse rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-3/4" />
                <div className="h-3 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-1/2" />
              </div>
            </div>
          ))
        ) : data && data.length > 0 ? (
          data.map((activity) => {
            const Icon = getActivityIcon(activity.resource_type);
            return (
              <div key={activity.id} className="flex gap-3 group">
                <div className={`p-2 rounded-full ${getActivityColor(activity.action)} flex-shrink-0`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 dark:text-white">
                    <span className="font-medium">{activity.user}</span>{' '}
                    <span className="text-gray-600 dark:text-gray-400">{activity.action}</span>{' '}
                    <span className="font-medium">{activity.resource_name}</span>
                  </p>
                  {activity.details && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                      {activity.details}
                    </p>
                  )}
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                  </p>
                </div>
              </div>
            );
          })
        ) : (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            {t('dashboard.activity.noActivity', 'No recent activity')}
          </div>
        )}
      </div>
    </div>
  );
}
