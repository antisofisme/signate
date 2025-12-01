/**
 * Playlist Assignment Tab
 *
 * Priority 3 - Lowest priority playlist-based content assignment
 * Two-column layout: Available Playlists (left) | Assigned Playlists (right)
 */

import { useTranslation } from 'react-i18next';
import { List, Trash2, Loader2, ArrowRight } from 'lucide-react';
import {
  useDevicePlaylists,
  useAssignPlaylist,
  useUnassignPlaylist,
} from '../../../hooks/useDevices';
import { usePlaylistList } from '@/shared/hooks/useSharedPlaylists';
import type { Device } from '../../../types/device';

interface PlaylistAssignmentTabProps {
  device: Device;
}

export function PlaylistAssignmentTab({ device }: PlaylistAssignmentTabProps) {
  const { t } = useTranslation();

  // Fetch assigned playlists for this device
  const { data: assignedData, isLoading: loadingAssigned } = useDevicePlaylists(device.id, true);

  // Fetch all available playlists
  const { data: allPlaylistsData, isLoading: loadingAllPlaylists } = usePlaylistList();

  // Mutations
  const assignPlaylist = useAssignPlaylist();
  const unassignPlaylist = useUnassignPlaylist();

  const assignedPlaylists = assignedData?.items || [];
  const allPlaylists = allPlaylistsData?.items || [];

  // Filter out already assigned playlists
  const availablePlaylists = allPlaylists.filter(
    (playlist) => !assignedPlaylists.some((assigned) => assigned.playlist_id === playlist.id)
  );

  // Handle assign
  const handleAssign = async (playlistId: number) => {
    try {
      await assignPlaylist.mutateAsync({ deviceId: device.id, playlistId });
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle unassign
  const handleUnassign = async (playlistId: number) => {
    try {
      await unassignPlaylist.mutateAsync({ deviceId: device.id, playlistId });
    } catch (error) {
      // Error handled by mutation
    }
  };

  const isLoading = loadingAssigned || loadingAllPlaylists;

  return (
    <div className="p-6 min-h-[600px]">
      {/* Info */}
      <div className="mb-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
        <p className="text-sm text-blue-700 dark:text-blue-300">
          <strong>{t('devices.modals.priority3Lowest')}:</strong> {t('devices.modals.priority3Info')}
        </p>
      </div>

      {/* Content - 2 Column Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-6">
          {/* Left Column - Available Playlists */}
          <div className="border-r border-gray-200 dark:border-gray-700 pr-4">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <List className="w-4 h-4" />
              {t('devices.modals.availablePlaylists', 'Playlist Tersedia')} ({availablePlaylists.length})
            </h4>
            {availablePlaylists.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('devices.modals.allPlaylistsAssigned')}
              </p>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {availablePlaylists.map((playlist) => (
                  <div
                    key={playlist.id}
                    className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer"
                    onClick={() => handleAssign(playlist.id)}
                  >
                    <div className="flex items-center gap-3">
                      {/* Icon */}
                      <div className="w-8 h-8 rounded bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
                        <List className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                      </div>
                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {playlist.name}
                        </p>
                        {playlist.description && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                            {playlist.description}
                          </p>
                        )}
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                          {playlist.content_count || 0} {t('playlists.contentSuffix', 'konten')}
                        </p>
                      </div>
                      {/* Assign Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAssign(playlist.id);
                        }}
                        disabled={assignPlaylist.isPending}
                        className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-all"
                        title={t('devices.modals.assign')}
                      >
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right Column - Assigned Playlists */}
          <div className="pl-4">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <List className="w-4 h-4 text-green-600" />
              {t('devices.modals.assignedPlaylists', 'Playlist Ditetapkan')} ({assignedPlaylists.length})
            </h4>
            {assignedPlaylists.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('devices.modals.noPlaylistsAssigned')}
              </p>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {assignedPlaylists.map((assigned) => (
                  <div
                    key={assigned.id}
                    className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 transition-colors bg-white dark:bg-gray-800"
                  >
                    <div className="flex items-center gap-3">
                      {/* Icon */}
                      <div className="w-8 h-8 rounded bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
                        <List className="w-4 h-4 text-green-600 dark:text-green-400" />
                      </div>
                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {assigned.playlist_name}
                        </p>
                      </div>
                      {/* Remove Button */}
                      <button
                        onClick={() => handleUnassign(assigned.playlist_id)}
                        disabled={unassignPlaylist.isPending}
                        className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all"
                        title={t('devices.modals.removePlaylist')}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
