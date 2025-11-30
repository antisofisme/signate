/**
 * Playlist Assignment Modal
 *
 * Features:
 * - View current assignments (devices & tags)
 * - Assign to devices (multi-select)
 * - Assign to tags (multi-select)
 * - Unassign from devices/tags
 * - Tabs for Devices and Tags
 *
 * ✅ REFACTORED: Now uses shared Modal component
 * - Fixed header (title with playlist name subtitle)
 * - Fixed footer (close button)
 * - Scrollable content (tabs + assignment lists)
 * - Click outside to close (disabled during operations)
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Monitor, Tag, Plus, Trash2, Loader2 } from 'lucide-react';
import { Modal } from '@/shared/components';
import { toast } from 'sonner';
import {
  usePlaylistAssignments,
  useAssignPlaylistToDevices,
  useAssignPlaylistToTags,
  useUnassignPlaylistFromDevices,
  useUnassignPlaylistFromTags,
} from '../hooks/usePlaylist';
import { useDeviceList } from '@/features/devices/hooks/useDevices';
import { useTags } from '@/features/tags/hooks/useTags';

interface PlaylistAssignmentModalProps {
  playlistId: number;
  playlistName: string;
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'devices' | 'tags';

export default function PlaylistAssignmentModal({
  playlistId,
  playlistName,
  isOpen,
  onClose,
}: PlaylistAssignmentModalProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabType>('devices');
  const [showAddDevices, setShowAddDevices] = useState(false);
  const [showAddTags, setShowAddTags] = useState(false);
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<number[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);

  // Fetch assignments
  const { data: assignments, isLoading } = usePlaylistAssignments(playlistId, isOpen);

  // Fetch available devices and tags from API (filtered by organization via backend)
  const { data: devicesData, isLoading: isLoadingDevices } = useDeviceList({ limit: 1000 });
  const { data: tagsData, isLoading: isLoadingTags } = useTags();

  // Mutations
  const assignDevices = useAssignPlaylistToDevices();
  const assignTags = useAssignPlaylistToTags();
  const unassignDevices = useUnassignPlaylistFromDevices();
  const unassignTags = useUnassignPlaylistFromTags();

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

  const handleAssignTags = async () => {
    if (selectedTagIds.length === 0) {
      toast.error(t('playlists.assignmentModal.selectAtLeastOneTag'));
      return;
    }

    try {
      await assignTags.mutateAsync({
        id: playlistId,
        data: { tag_ids: selectedTagIds },
      });
      setSelectedTagIds([]);
      setShowAddTags(false);
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

  const handleUnassignTag = async (tagId: number) => {
    if (!confirm(t('playlists.assignmentModal.tags.confirmUnassign'))) return;

    try {
      await unassignTags.mutateAsync({
        id: playlistId,
        data: { tag_ids: [tagId] },
      });
    } catch (error) {
      // Error handled by hook
    }
  };

  // Get real data from API (already filtered by organization via backend)
  const allDevices = devicesData?.items || [];
  // Tags API returns array directly, not { items: [] }
  const allTags = tagsData || [];

  const assignedDevices = assignments?.devices || [];
  const assignedTags = assignments?.tags || [];

  // Filter out already assigned devices/tags
  const availableDevices = allDevices.filter(
    (device) => !assignedDevices.some((d) => d.device_id === device.id)
  );

  const availableTags = allTags.filter(
    (tag) => !assignedTags.some((t) => t.id === tag.id)
  );

  const isOperationPending =
    assignDevices.isPending ||
    assignTags.isPending ||
    unassignDevices.isPending ||
    unassignTags.isPending;

  const isLoadingData = isLoading || isLoadingDevices || isLoadingTags;

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
        {/* Tabs */}
        <div className="flex border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10">
          <button
            onClick={() => setActiveTab('devices')}
            className={`flex-1 px-6 py-3 font-medium flex items-center justify-center gap-2 ${
              activeTab === 'devices'
                ? 'text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            <Monitor className="w-4 h-4" />
            {t('playlists.assignmentModal.tabs.devices', { count: assignedDevices.length })}
          </button>
          <button
            onClick={() => setActiveTab('tags')}
            className={`flex-1 px-6 py-3 font-medium flex items-center justify-center gap-2 ${
              activeTab === 'tags'
                ? 'text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            <Tag className="w-4 h-4" />
            {t('playlists.assignmentModal.tabs.tags', { count: assignedTags.length })}
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {isLoadingData ? (
            <div className="flex items-center justify-center py-8 text-gray-500 dark:text-gray-400">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              {t('playlists.assignmentModal.loading')}
            </div>
          ) : activeTab === 'devices' ? (
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
          ) : (
            <>
              {/* Add Tags Section */}
              {showAddTags ? (
                <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                    {t('playlists.assignmentModal.tags.assignToTags')}
                  </h3>

                  <div className="space-y-2 max-h-48 overflow-y-auto mb-4">
                    {availableTags.length === 0 ? (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {t('playlists.assignmentModal.tags.noAvailableTags')}
                      </p>
                    ) : (
                      availableTags.map((tag) => (
                        <label
                          key={tag.id}
                          className="flex items-center gap-3 p-3 bg-white dark:bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-600"
                        >
                          <input
                            type="checkbox"
                            checked={selectedTagIds.includes(tag.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedTagIds([...selectedTagIds, tag.id]);
                              } else {
                                setSelectedTagIds(
                                  selectedTagIds.filter((id) => id !== tag.id)
                                );
                              }
                            }}
                            className="w-4 h-4 text-blue-600 rounded"
                          />
                          <div
                            className="w-4 h-4 rounded-full flex-shrink-0"
                            style={{ backgroundColor: tag.color || '#3B82F6' }}
                          />
                          <div className="flex-1">
                            <p className="font-medium text-gray-900 dark:text-white">
                              {tag.tag_name}
                            </p>
                            {tag.description && (
                              <p className="text-sm text-gray-500 dark:text-gray-400">
                                {tag.description}
                              </p>
                            )}
                          </div>
                        </label>
                      ))
                    )}
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={handleAssignTags}
                      disabled={selectedTagIds.length === 0 || assignTags.isPending}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {assignTags.isPending
                        ? t('playlists.assignmentModal.tags.assigning')
                        : t(
                            selectedTagIds.length > 1
                              ? 'playlists.assignmentModal.tags.assignTags_plural'
                              : 'playlists.assignmentModal.tags.assignTags',
                            { count: selectedTagIds.length }
                          )}
                    </button>
                    <button
                      onClick={() => {
                        setShowAddTags(false);
                        setSelectedTagIds([]);
                      }}
                      className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
                    >
                      {t('playlists.assignmentModal.cancel')}
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowAddTags(true)}
                  className="mb-6 w-full p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                >
                  <Plus className="w-5 h-5" />
                  {t('playlists.assignmentModal.tags.assignToTags')}
                </button>
              )}

              {/* Current Tags */}
              <div className="space-y-2">
                <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                  {t('playlists.assignmentModal.tags.assignedTags', { count: assignedTags.length })}
                </h3>

                {assignedTags.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    {t('playlists.assignmentModal.tags.notAssignedYet')}
                  </div>
                ) : (
                  assignedTags.map((assignment) => (
                    <div
                      key={assignment.id}
                      className="flex items-center gap-3 p-4 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
                    >
                      <div
                        className="w-4 h-4 rounded-full flex-shrink-0"
                        style={{ backgroundColor: assignment.color || '#3B82F6' }}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 dark:text-white">
                          {assignment.name ||
                            t('playlists.assignmentModal.tags.tagFallback', { id: assignment.id })}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {t('playlists.assignmentModal.tags.tagId', { id: assignment.id })}
                        </p>
                      </div>
                      <button
                        onClick={() => handleUnassignTag(assignment.id)}
                        disabled={unassignTags.isPending}
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
