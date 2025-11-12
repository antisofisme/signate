/**
 * Active Playlists Table Component
 *
 * LAYER 1: PRESENTATION
 * Active playlist assignments overview
 */

import { ListVideo, Monitor, FileImage, Clock } from 'lucide-react';
import { ActivePlaylistAssignment } from '../api/dashboard.api';
import { formatDistanceToNow } from 'date-fns';

interface ActivePlaylistsTableProps {
  data: ActivePlaylistAssignment[] | undefined;
  isLoading: boolean;
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h`;
};

export default function ActivePlaylistsTable({ data, isLoading }: ActivePlaylistsTableProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <ListVideo className="w-5 h-5" />
          Active Playlists & Assignments
        </h2>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-24 bg-gray-200 dark:bg-gray-700 animate-pulse rounded-lg" />
          ))
        ) : data && data.length > 0 ? (
          data.map((playlist) => (
            <div
              key={playlist.playlist_id}
              className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                    {playlist.playlist_name}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Updated {formatDistanceToNow(new Date(playlist.last_updated), { addSuffix: true })}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <Monitor className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Devices</p>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {playlist.device_count}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                    <FileImage className="w-4 h-4 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Content</p>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {playlist.content_count}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                    <Clock className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Duration</p>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {formatDuration(playlist.total_duration_seconds)}
                    </p>
                  </div>
                </div>

                <div className="col-span-2 lg:col-span-1">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Assigned to:</p>
                  <div className="flex flex-wrap gap-1">
                    {playlist.devices.slice(0, 3).map((device, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                      >
                        {device}
                      </span>
                    ))}
                    {playlist.devices.length > 3 && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                        +{playlist.devices.length - 3}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            No active playlists found
          </div>
        )}
      </div>
    </div>
  );
}
