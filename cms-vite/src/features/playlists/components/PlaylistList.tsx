/**
 * Playlist List Component
 * Table display of playlists with actions
 */

import { Pencil, Trash2, Clock, FileText, List, Monitor, Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TableSkeleton, EmptyState, Button } from '@/shared/components';
import type { Playlist } from '../types/playlist';

interface PlaylistListProps {
  playlists: Playlist[];
  isLoading: boolean;
  onEdit?: (playlist: Playlist) => void;
  onDelete?: (playlist: Playlist) => void;
  onManageContent: (playlist: Playlist) => void;
  onManageAssignments: (playlist: Playlist) => void;
  onCreateNew?: () => void;
}

export function PlaylistList({
  playlists,
  isLoading,
  onEdit,
  onDelete,
  onManageContent,
  onManageAssignments,
  onCreateNew,
}: PlaylistListProps) {
  const { t } = useTranslation();

  const formatDuration = (seconds: number): string => {
    if (seconds === 0) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    const parts = [];
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    if (secs > 0) parts.push(`${secs}s`);

    return parts.join(' ');
  };

  if (isLoading) {
    return <TableSkeleton rows={5} columns={6} />;
  }

  if (playlists.length === 0) {
    return (
      <EmptyState
        icon={List}
        title={t('playlists.messages.noPlaylists')}
        description={t('playlists.messages.noPlaylistsDesc')}
      />
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              {t('playlists.name')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Priority
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              {t('playlists.items')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              {t('playlists.duration')}
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              {t('common.actions')}
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          {playlists.map((playlist) => (
            <tr key={playlist.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
              <td className="px-6 py-4">
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {playlist.name}
                  </div>
                  {playlist.description && (
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {playlist.description}
                    </div>
                  )}
                </div>
              </td>
              <td className="px-6 py-4">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    playlist.is_active
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  {playlist.is_active ? 'Aktif' : 'Nonaktif'}
                </span>
              </td>
              <td className="px-6 py-4">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  {playlist.priority}
                </span>
              </td>
              <td className="px-6 py-4">
                <div className="flex items-center text-sm text-gray-900 dark:text-white">
                  <FileText className="w-4 h-4 mr-2 text-gray-400" />
                  {playlist.content_count} item
                </div>
              </td>
              <td className="px-6 py-4">
                <div className="flex items-center text-sm text-gray-900 dark:text-white">
                  <Clock className="w-4 h-4 mr-2 text-gray-400" />
                  {formatDuration(playlist.total_duration)}
                </div>
              </td>
              <td className="px-6 py-4 text-right">
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => onManageContent(playlist)}
                    className="p-2 text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg"
                    title="Manage Content"
                  >
                    <List className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onManageAssignments(playlist)}
                    className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg"
                    title={t('playlists.manageAssignments')}
                  >
                    <Monitor className="w-4 h-4" />
                  </button>
                  {onEdit && (
                    <button
                      onClick={() => onEdit(playlist)}
                      className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"
                      title={t('common.edit')}
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => onDelete(playlist)}
                      className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                      title={t('common.delete')}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default PlaylistList;
