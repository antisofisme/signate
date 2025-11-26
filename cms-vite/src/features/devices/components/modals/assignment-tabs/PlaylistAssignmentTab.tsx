/**
 * Playlist Assignment Tab
 *
 * Priority 3 - Lowest priority playlist-based content assignment
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { List, Plus, Trash2, Loader2 } from 'lucide-react';
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
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<number | null>(null);

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
  const handleAssign = async () => {
    if (!selectedPlaylistId) return;

    try {
      await assignPlaylist.mutateAsync({ deviceId: device.id, playlistId: selectedPlaylistId });
      setSelectedPlaylistId(null);
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

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Assign New Playlist */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              {t('devices.modals.assignNewPlaylist')}
            </label>
            {availablePlaylists.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('devices.modals.allPlaylistsAssigned')}
              </p>
            ) : (
              <div className="flex gap-2">
                <select
                  value={selectedPlaylistId || ''}
                  onChange={(e) => setSelectedPlaylistId(Number(e.target.value) || null)}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  disabled={assignPlaylist.isPending}
                >
                  <option value="">{t('devices.modals.selectPlaylist')}</option>
                  {availablePlaylists.map((playlist) => (
                    <option key={playlist.id} value={playlist.id}>
                      {playlist.name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleAssign}
                  disabled={!selectedPlaylistId || assignPlaylist.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
                >
                  {assignPlaylist.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      {t('devices.modals.assigning')}
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4" />
                      {t('devices.modals.assign')}
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Currently Assigned Playlists */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              {t('devices.modals.currentlyAssignedPlaylists')} ({assignedPlaylists.length})
            </label>
            {assignedPlaylists.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('devices.modals.noPlaylistsAssigned')}
              </p>
            ) : (
              <div className="space-y-2">
                {assignedPlaylists.map((assigned) => (
                  <div
                    key={assigned.id}
                    className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <List className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {assigned.playlist_name}
                      </span>
                    </div>
                    <button
                      onClick={() => handleUnassign(assigned.playlist_id)}
                      disabled={unassignPlaylist.isPending}
                      className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50"
                      title={t('devices.modals.removePlaylist')}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
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
