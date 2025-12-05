/**
 * Playlist List Component
 * Table display of playlists with actions
 */

import { Pencil, Trash2, Clock, FileText, List, FileSymlink, Plus, Copy, Monitor, Calendar, Star } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TableSkeleton, EmptyState, Button, TABLE_STYLES, ACTION_BUTTON, SortableTableHeader, DateCell } from '@/shared/components';
import type { SortConfig } from '@/shared/components';
import type { Playlist } from '../types/playlist';

interface PlaylistListProps {
  playlists: Playlist[];
  isLoading: boolean;
  onEdit?: (playlist: Playlist) => void;
  onDelete?: (playlist: Playlist) => void;
  onDuplicate?: (playlist: Playlist) => void;
  onManage: (playlist: Playlist) => void;
  onCreateNew?: () => void;
  // Sorting props (optional - controlled by parent)
  sortConfig?: SortConfig | null;
  onSortChange?: (config: SortConfig | null) => void;
}

export function PlaylistList({
  playlists,
  isLoading,
  onEdit,
  onDelete,
  onDuplicate,
  onManage,
  onCreateNew,
  sortConfig,
  onSortChange,
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
    return <TableSkeleton rows={5} columns={9} />;
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
            <th className="w-72 px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {sortConfig && onSortChange ? (
                <SortableTableHeader columnKey="name" sortConfig={sortConfig} onSortChange={onSortChange}>
                  {t('playlists.name')}
                </SortableTableHeader>
              ) : t('playlists.name')}
            </th>
            <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {sortConfig && onSortChange ? (
                <SortableTableHeader columnKey="is_active" sortConfig={sortConfig} onSortChange={onSortChange}>
                  Status
                </SortableTableHeader>
              ) : 'Status'}
            </th>
            <th className="w-16 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {sortConfig && onSortChange ? (
                <SortableTableHeader columnKey="priority" sortConfig={sortConfig} onSortChange={onSortChange}>
                  Priority
                </SortableTableHeader>
              ) : 'Priority'}
            </th>
            <th className="w-16 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {sortConfig && onSortChange ? (
                <SortableTableHeader columnKey="content_count" sortConfig={sortConfig} onSortChange={onSortChange}>
                  {t('playlists.content', 'Konten')}
                </SortableTableHeader>
              ) : t('playlists.content', 'Konten')}
            </th>
            <th className="w-16 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {sortConfig && onSortChange ? (
                <SortableTableHeader columnKey="device_count" sortConfig={sortConfig} onSortChange={onSortChange}>
                  {t('playlists.devices', 'Device')}
                </SortableTableHeader>
              ) : t('playlists.devices', 'Device')}
            </th>
            <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {sortConfig && onSortChange ? (
                <SortableTableHeader columnKey="total_duration" sortConfig={sortConfig} onSortChange={onSortChange}>
                  {t('playlists.duration')}
                </SortableTableHeader>
              ) : t('playlists.duration')}
            </th>
            <th className="w-28 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {sortConfig && onSortChange ? (
                <SortableTableHeader columnKey="created_at" sortConfig={sortConfig} onSortChange={onSortChange}>
                  {t('playlists.created', 'Created')}
                </SortableTableHeader>
              ) : t('playlists.created', 'Created')}
            </th>
            <th className="w-36 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {t('common.actions')}
            </th>
          </tr>
        </thead>
        <tbody className={TABLE_STYLES.tbody}>
          {playlists.map((playlist) => (
            <tr key={playlist.id} className={TABLE_STYLES.tr}>
              <td className="px-3 py-4 overflow-hidden">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 dark:text-white truncate" title={playlist.name}>
                      {playlist.name}
                    </span>
                    {/* Default indicator */}
                    {playlist.is_default && (
                      <span
                        title={t('playlists.defaultPlaylist', 'Default Playlist')}
                        className="inline-flex items-center text-yellow-500 dark:text-yellow-400 flex-shrink-0"
                      >
                        <Star className="w-3.5 h-3.5 fill-current" />
                      </span>
                    )}
                    {/* Schedule indicator - show if playlist has a schedule */}
                    {playlist.schedule && Object.keys(playlist.schedule).length > 0 && (
                      <span
                        title={t('playlists.hasSchedule', 'Has Schedule')}
                        className="inline-flex items-center text-blue-600 dark:text-blue-400 flex-shrink-0"
                      >
                        <Calendar className="w-3.5 h-3.5" />
                      </span>
                    )}
                  </div>
                  {playlist.description && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate" title={playlist.description}>
                      {playlist.description}
                    </div>
                  )}
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
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
              <td className="px-4 py-4 whitespace-nowrap">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  {playlist.priority}
                </span>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <div className="flex items-center text-sm text-gray-900 dark:text-white">
                  <FileText className="w-4 h-4 mr-1 text-gray-400" />
                  {playlist.content_count}
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <div className="flex items-center text-sm text-gray-900 dark:text-white">
                  <Monitor className="w-4 h-4 mr-1 text-gray-400" />
                  {playlist.device_count || 0}
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <div className="flex items-center text-sm text-gray-900 dark:text-white">
                  <Clock className="w-4 h-4 mr-1 text-gray-400" />
                  {formatDuration(playlist.total_duration)}
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <div className="flex flex-col">
                  <DateCell date={playlist.created_at} />
                  {playlist.created_by_name && (
                    <span className="text-xs text-gray-500 dark:text-gray-400 truncate" title={playlist.created_by_name}>
                      {playlist.created_by_name}
                    </span>
                  )}
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
                    className={ACTION_BUTTON.ASSIGN}
                    title={t('playlists.manage', 'Manage')}
                  >
                    <FileSymlink className="w-4 h-4" />
                  </button>
                  {onEdit && (
                    <button
                      onClick={() => onEdit(playlist)}
                      className={ACTION_BUTTON.EDIT}
                      title={t('common.edit')}
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => onDelete(playlist)}
                      className={ACTION_BUTTON.DELETE}
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
