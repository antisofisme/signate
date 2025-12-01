/**
 * Playlist List Component
 * Table display of playlists with actions
 */

import { Pencil, Trash2, Clock, FileText, List, Monitor, Plus, Copy } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TableSkeleton, EmptyState, Button, TABLE_STYLES } from '@/shared/components';
import type { Playlist } from '../types/playlist';

interface PlaylistListProps {
  playlists: Playlist[];
  isLoading: boolean;
  onEdit?: (playlist: Playlist) => void;
  onDelete?: (playlist: Playlist) => void;
  onDuplicate?: (playlist: Playlist) => void;
  onManageContent: (playlist: Playlist) => void;
  onManageAssignments: (playlist: Playlist) => void;
  onCreateNew?: () => void;
}

export function PlaylistList({
  playlists,
  isLoading,
  onEdit,
  onDelete,
  onDuplicate,
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
    <div className={TABLE_STYLES.container}>
      <table className={TABLE_STYLES.table}>
        <thead className={TABLE_STYLES.thead}>
          <tr>
            <th className={TABLE_STYLES.th}>
              {t('playlists.name')}
            </th>
            <th className={TABLE_STYLES.th}>
              Status
            </th>
            <th className={TABLE_STYLES.th}>
              Priority
            </th>
            <th className={TABLE_STYLES.th}>
              {t('playlists.items')}
            </th>
            <th className={TABLE_STYLES.th}>
              {t('playlists.duration')}
            </th>
            <th className={TABLE_STYLES.th}>
              {t('common.actions')}
            </th>
          </tr>
        </thead>
        <tbody className={TABLE_STYLES.tbody}>
          {playlists.map((playlist) => (
            <tr key={playlist.id} className={TABLE_STYLES.tr}>
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
              <td className={TABLE_STYLES.td}>
                <div className="flex items-center gap-2">
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
                  {onDuplicate && (
                    <button
                      onClick={() => onDuplicate(playlist)}
                      className="p-2 text-orange-600 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded-lg"
                      title={t('playlists.duplicate', 'Duplicate')}
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  )}
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
