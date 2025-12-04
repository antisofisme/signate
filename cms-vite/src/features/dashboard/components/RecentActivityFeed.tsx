/**
 * Recent Activity Feed Component
 *
 * LAYER 1: PRESENTATION
 * Recent system activity and audit trail with human-readable formatting
 */

import { Activity, User, Monitor, FileImage, ListVideo, Settings, Calendar, Tag, Menu, Shield } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { RecentActivity } from '../api/dashboard.api';
import { formatDistanceToNow } from 'date-fns';
import { id as idLocale } from 'date-fns/locale';

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
    case 'schedule':
      return Calendar;
    case 'tag':
      return Tag;
    case 'menu':
      return Menu;
    case 'role':
      return Shield;
    default:
      return Activity;
  }
};

const getActivityColor = (action: string) => {
  if (action.includes('create') || action.includes('add') || action.includes('upload')) {
    return 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400';
  }
  if (action.includes('update') || action.includes('edit') || action.includes('modify')) {
    return 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400';
  }
  if (action.includes('delete') || action.includes('remove')) {
    return 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400';
  }
  if (action.includes('login') || action.includes('logout') || action.includes('auth')) {
    return 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400';
  }
  return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400';
};

// Human-readable action mappings (Indonesian)
const ACTION_MAP: Record<string, string> = {
  // Content actions
  'content.create': 'mengunggah konten',
  'content.upload': 'mengunggah konten',
  'content.update': 'memperbarui konten',
  'content.delete': 'menghapus konten',

  // Playlist actions
  'playlist.create': 'membuat playlist',
  'playlist.update': 'memperbarui playlist',
  'playlist.delete': 'menghapus playlist',
  'playlist.add_content': 'menambahkan konten ke playlist',
  'playlist.remove_content': 'menghapus konten dari playlist',

  // Device actions
  'device.create': 'mendaftarkan perangkat',
  'device.update': 'memperbarui perangkat',
  'device.delete': 'menghapus perangkat',
  'device.activate': 'mengaktifkan perangkat',
  'device.deactivate': 'menonaktifkan perangkat',

  // Schedule actions
  'schedule.create': 'membuat jadwal',
  'schedule.update': 'memperbarui jadwal',
  'schedule.delete': 'menghapus jadwal',

  // User actions
  'user.create': 'membuat pengguna',
  'user.update': 'memperbarui pengguna',
  'user.delete': 'menghapus pengguna',
  'user.login': 'masuk ke sistem',
  'user.logout': 'keluar dari sistem',

  // Tag actions
  'tag.create': 'membuat tag',
  'tag.update': 'memperbarui tag',
  'tag.delete': 'menghapus tag',

  // Menu actions
  'menu.create': 'membuat menu',
  'menu.update': 'memperbarui menu',
  'menu.delete': 'menghapus menu',
};

// Format action to human-readable text
const formatAction = (action: string): string => {
  return ACTION_MAP[action] || action.replace(/[._]/g, ' ');
};

// Format details JSON to human-readable text
const formatDetails = (details: string | undefined, action: string): string | null => {
  if (!details) return null;

  try {
    // Try to parse as JSON (handle Python-style single quotes)
    const jsonStr = details.replace(/'/g, '"');
    const parsed = JSON.parse(jsonStr);

    // Extract meaningful info based on action type
    if (action.includes('content')) {
      if (parsed.title) return parsed.title;
      if (parsed.content_type) return parsed.content_type;
    }

    if (action.includes('playlist')) {
      if (parsed.name) return parsed.name;
      if (parsed.content_item_id) return null; // Hide technical IDs
    }

    if (action.includes('device')) {
      if (parsed.name) return parsed.name;
      if (parsed.device_name) return parsed.device_name;
    }

    if (action.includes('schedule')) {
      if (parsed.name) return parsed.name;
      if (parsed.playlist_id) return null;
    }

    if (action.includes('user')) {
      if (parsed.username) return parsed.username;
      if (parsed.email) return parsed.email;
    }

    // For other cases, try to find a meaningful field
    const meaningfulFields = ['name', 'title', 'username', 'email', 'description'];
    for (const field of meaningfulFields) {
      if (parsed[field]) return parsed[field];
    }

    return null; // Hide raw JSON if no meaningful field found
  } catch {
    // If not valid JSON, return original but cleaned up
    return details.length > 50 ? null : details;
  }
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
            const formattedAction = formatAction(activity.action);
            const formattedDetails = formatDetails(activity.details, activity.action);

            return (
              <div key={activity.id} className="flex gap-3 group">
                <div className={`p-2 rounded-full ${getActivityColor(activity.action)} flex-shrink-0`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 dark:text-white">
                    <span className="font-medium">{activity.user}</span>{' '}
                    <span className="text-gray-600 dark:text-gray-400">{formattedAction}</span>
                    {activity.resource_name && !activity.resource_name.match(/^\d+$/) && (
                      <span className="font-medium"> "{activity.resource_name}"</span>
                    )}
                  </p>
                  {formattedDetails && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                      {formattedDetails}
                    </p>
                  )}
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true, locale: idLocale })}
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
