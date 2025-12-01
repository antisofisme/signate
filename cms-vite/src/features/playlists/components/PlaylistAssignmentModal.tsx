/**
 * Playlist Assignment Modal
 *
 * Features:
 * - View current assignments (devices)
 * - Assign to devices (multi-select)
 * - Unassign from devices
 *
 * NOTE: Tag assignments have been removed.
 * Tags are assigned to Devices/Content only, NOT to Playlists.
 * See architecture decision: Device Groups = view management only
 *
 * ✅ REFACTORED: Now uses shared Modal component
 * - Fixed header (title with playlist name subtitle)
 * - Fixed footer (close button)
 * - Scrollable content
 * - Click outside to close (disabled during operations)
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Monitor, Plus, Trash2, Loader2 } from 'lucide-react';
import { Modal } from '@/shared/components';
import { toast } from 'sonner';
import {
  usePlaylistAssignments,
  useAssignPlaylistToDevices,
  useUnassignPlaylistFromDevices,
} from '../hooks/usePlaylist';
import { useDeviceList } from '@/features/devices/hooks/useDevices';

interface PlaylistAssignmentModalProps {
  playlistId: number;
  playlistName: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function PlaylistAssignmentModal({
  playlistId,
  playlistName,
  isOpen,
  onClose,
}: PlaylistAssignmentModalProps) {
  const { t } = useTranslation();
  const [showAddDevices, setShowAddDevices] = useState(false);
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<number[]>([]);

  // Fetch assignments
  const { data: assignments, isLoading } = usePlaylistAssignments(playlistId, isOpen);

  // Fetch available devices from API (filtered by organization via backend)
  const { data: devicesData, isLoading: isLoadingDevices } = useDeviceList({ limit: 1000 });

  // Mutations
  const assignDevices = useAssignPlaylistToDevices();
  const unassignDevices = useUnassignPlaylistFromDevices();

  if (!isOpen) return null;

  const handleAssignDevices = async () => {
    if (selectedDeviceIds.length === 0) {
      toast.error(t('playlists.assignmentModal.selectAtLeastOneDevice'));
      return;
    }

    try {
      await assignDevices.mutateAsync({
        id: playlistId,
        data: { device_ids: selectedDeviceIds },
      });
      setSelectedDeviceIds([]);
      setShowAddDevices(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  const handleUnassignDevice = async (deviceId: number) => {
    if (!confirm(t('playlists.assignmentModal.devices.confirmUnassign'))) return;

    try {
      await unassignDevices.mutateAsync({
        id: playlistId,
        data: { device_ids: [deviceId] },
      });
    } catch (error) {
      // Error handled by hook
    }
  };

  // Get real data from API (already filtered by organization via backend)
  const allDevices = devicesData?.items || [];
  const assignedDevices = assignments?.devices || [];

  // Filter out already assigned devices
  const availableDevices = allDevices.filter(
    (device) => !assignedDevices.some((d) => d.device_id === device.id)
  );

  const isOperationPending = assignDevices.isPending || unassignDevices.isPending;
  const isLoadingData = isLoading || isLoadingDevices;

  // Custom header with subtitle
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        {t('playlists.assignmentModal.title')}
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
        {playlistName}
      </p>
    </div>
  );

  // Footer with close button
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end">
        <button
          onClick={onClose}
          disabled={isOperationPending}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
        >
          {t('playlists.assignmentModal.close')}
        </button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="4xl"
      customHeader={customHeader}
      footer={footer}
      closeOnBackdropClick={!isOperationPending}
      className="h-[90vh]"
    >
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        {/* Content */}
        <div className="p-6">
          {isLoadingData ? (
            <div className="flex items-center justify-center py-8 text-gray-500 dark:text-gray-400">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              {t('playlists.assignmentModal.loading')}
            </div>
          ) : (
            <>
              {/* Add Devices Section */}
              {showAddDevices ? (
                <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                    {t('playlists.assignmentModal.devices.assignToDevices')}
                  </h3>

                  <div className="space-y-2 max-h-48 overflow-y-auto mb-4">
                    {availableDevices.length === 0 ? (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {t('playlists.assignmentModal.devices.noAvailableDevices')}
                      </p>
                    ) : (
                      availableDevices.map((device) => (
                        <label
                          key={device.id}
                          className="flex items-center gap-3 p-3 bg-white dark:bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-600"
                        >
                          <input
                            type="checkbox"
                            checked={selectedDeviceIds.includes(device.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedDeviceIds([...selectedDeviceIds, device.id]);
                              } else {
                                setSelectedDeviceIds(
                                  selectedDeviceIds.filter((id) => id !== device.id)
                                );
                              }
                            }}
                            className="w-4 h-4 text-blue-600 rounded"
                          />
                          <Monitor className={`w-4 h-4 ${device.is_online ? 'text-green-500' : 'text-gray-400'}`} />
                          <div className="flex-1">
                            <p className="font-medium text-gray-900 dark:text-white">
                              {device.device_name}
                            </p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {device.is_online ? 'Online' : 'Offline'} • {device.device_type}
                              {device.room_number && ` • ${device.room_number}`}
                            </p>
                          </div>
                        </label>
                      ))
                    )}
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={handleAssignDevices}
                      disabled={selectedDeviceIds.length === 0 || assignDevices.isPending}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {assignDevices.isPending
                        ? t('playlists.assignmentModal.devices.assigning')
                        : t(
                            selectedDeviceIds.length > 1
                              ? 'playlists.assignmentModal.devices.assignDevices_plural'
                              : 'playlists.assignmentModal.devices.assignDevices',
                            { count: selectedDeviceIds.length }
                          )}
                    </button>
                    <button
                      onClick={() => {
                        setShowAddDevices(false);
                        setSelectedDeviceIds([]);
                      }}
                      className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
                    >
                      {t('playlists.assignmentModal.cancel')}
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowAddDevices(true)}
                  className="mb-6 w-full p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                >
                  <Plus className="w-5 h-5" />
                  {t('playlists.assignmentModal.devices.assignToDevices')}
                </button>
              )}

              {/* Current Devices */}
              <div className="space-y-2">
                <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                  {t('playlists.assignmentModal.devices.assignedDevices', {
                    count: assignedDevices.length,
                  })}
                </h3>

                {assignedDevices.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    {t('playlists.assignmentModal.devices.notAssignedYet')}
                  </div>
                ) : (
                  assignedDevices.map((assignment) => (
                    <div
                      key={assignment.id}
                      className="flex items-center gap-3 p-4 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
                    >
                      <Monitor className="w-5 h-5 text-gray-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 dark:text-white">
                          {assignment.device_name ||
                            t('playlists.assignmentModal.devices.deviceFallback', {
                              id: assignment.device_id,
                            })}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {assignment.location
                            ? t('playlists.assignmentModal.devices.location', {
                                location: assignment.location,
                              })
                            : t('playlists.assignmentModal.devices.noLocation')}
                        </p>
                      </div>
                      <button
                        onClick={() => handleUnassignDevice(assignment.device_id)}
                        disabled={unassignDevices.isPending}
                        className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg disabled:opacity-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </Modal>
  );
}
