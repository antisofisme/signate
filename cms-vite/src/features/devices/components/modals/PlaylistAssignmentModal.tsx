/**
 * Playlist Assignment Modal Component
 *
 * Manage playlist assignments for devices (Priority 3 - Lowest)
 * Uses centralized Modal component
 */

import { useState } from 'react';
import { List, Plus, Trash2, Loader2 } from 'lucide-react';
import { Modal } from '@/shared/components';
import { useDevicePlaylists, useAssignPlaylist, useUnassignPlaylist } from '../../hooks/useDevices';
import { usePlaylistList } from '@/shared/hooks/useSharedPlaylists';
import type { Device } from '../../types/device';

interface PlaylistAssignmentModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

export function PlaylistAssignmentModal({
  isOpen,
  device,
  onClose,
}: PlaylistAssignmentModalProps) {
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<number | null>(null);

  // Fetch assigned playlists for this device
  const { data: assignedData, isLoading: loadingAssigned } = useDevicePlaylists(
    device?.id || 0,
    isOpen && !!device
  );

  // Fetch all available playlists
  const { data: allPlaylistsData, isLoading: loadingAllPlaylists } = usePlaylistList();

  // Mutations
  const assignPlaylist = useAssignPlaylist();
  const unassignPlaylist = useUnassignPlaylist();

  if (!device) return null;

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

  // Custom header with icon
  const customHeader = (
    <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <List className="w-5 h-5" />
            Manage Playlists
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {device.device_name} - Priority 3 (Lowest)
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="2xl"
      customHeader={customHeader}
      footer={
        <div className="border-t border-gray-200 dark:border-gray-700">
          {/* Info */}
          <div className="px-6 pt-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                <strong>Priority 3 (Lowest):</strong> Playlist content is shown when no direct content or tag-based content is assigned.
                Multiple playlists will be combined and shuffled.
              </p>
            </div>
          </div>

          {/* Close Button */}
          <div className="px-6 py-4">
            <div className="flex justify-end">
              <button
                onClick={onClose}
                disabled={assignPlaylist.isPending || unassignPlaylist.isPending}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      }
    >
      {/* Content */}
      <div className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Assign New Playlist */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Assign New Playlist
              </label>
              {availablePlaylists.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  All available playlists are already assigned to this device.
                </p>
              ) : (
                <div className="flex gap-2">
                  <select
                    value={selectedPlaylistId || ''}
                    onChange={(e) => setSelectedPlaylistId(Number(e.target.value) || null)}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    disabled={assignPlaylist.isPending}
                  >
                    <option value="">Select a playlist...</option>
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
                        Assigning...
                      </>
                    ) : (
                      <>
                        <Plus className="w-4 h-4" />
                        Assign
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>

            {/* Currently Assigned Playlists */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Currently Assigned Playlists ({assignedPlaylists.length})
              </label>
              {assignedPlaylists.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No playlists assigned to this device yet.
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
                        title="Remove playlist"
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
    </Modal>
  );
}
