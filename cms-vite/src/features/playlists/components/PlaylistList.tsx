/**
 * Playlist List Component
 * Table display of playlists with actions
 */

import { Pencil, Trash2, Clock, FileText, List, FileSymlink, Plus, Copy, Monitor } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TableSkeleton, EmptyState, Button, TABLE_STYLES } from '@/shared/components';
import type { Playlist } from '../types/playlist';

interface PlaylistListProps {
  playlists: Playlist[];
  isLoading: boolean;
  onEdit?: (playlist: Playlist) => void;
  onDelete?: (playlist: Playlist) => void;
  onDuplicate?: (playlist: Playlist) => void;
  onManage: (playlist: Playlist) => void;
  onCreateNew?: () => void;
}

export function PlaylistList({
  playlists,
  isLoading,
  onEdit,
  onDelete,
  onDuplicate,
  onManage,
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
    return <TableSkeleton rows={5} columns={7} />;
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
      <div className="overflow-x-auto">
        <table className={`${TABLE_STYLES.table} table-fixed`}>
          <thead className={TABLE_STYLES.thead}>
          <tr>
            <th className={`${TABLE_STYLES.th} w-[25%]`}>
              {t('playlists.name')}
            </th>
            <th className={`${TABLE_STYLES.th} w-20`}>
              Status
            </th>
            <th className={`${TABLE_STYLES.th} w-20`}>
              Priority
            </th>
            <th className={`${TABLE_STYLES.th} w-24`}>
              {t('playlists.content', 'Konten')}
            </th>
            <th className={`${TABLE_STYLES.th} w-24`}>
              {t('playlists.devices', 'Device')}
            </th>
            <th className={`${TABLE_STYLES.th} w-24`}>
              {t('playlists.duration')}
            </th>
            <th className={`${TABLE_STYLES.th} w-32`}>
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
                  {playlist.content_count} {t('playlists.contentSuffix', 'konten')}
                </div>
              </td>
              <td className="px-6 py-4">
                <div className="flex items-center text-sm text-gray-900 dark:text-white">
                  <Monitor className="w-4 h-4 mr-2 text-gray-400" />
                  {playlist.device_count || 0} {t('playlists.deviceSuffix', 'device')}
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
                  {onDuplicate && (
                    <button
                      onClick={() => onDuplicate(playlist)}
                      className={TABLE_STYLES.actionBtnOrange}
                      title={t('playlists.duplicate', 'Duplicate')}
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => onManage(playlist)}
                    className={TABLE_STYLES.actionBtnPurple}
                    title={t('playlists.manage', 'Manage')}
                  >
                    <FileSymlink className="w-4 h-4" />
                  </button>
                  {onEdit && (
                    <button
                      onClick={() => onEdit(playlist)}
                      className={TABLE_STYLES.actionBtnBlue}
                      title={t('common.edit')}
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => onDelete(playlist)}
                      className={TABLE_STYLES.actionBtnRed}
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
    </div>
  );
}

export default PlaylistList;
