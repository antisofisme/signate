/**
 * Playlist Assignment Modal
 *
 * Features:
 * - View current assignments (devices & tags)
 * - Assign to devices (multi-select)
 * - Assign to tags (multi-select)
 * - Unassign from devices/tags
 * - Tabs for Devices and Tags
 */

import { useState } from 'react';
import { X, Monitor, Tag, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import {
  usePlaylistAssignments,
  useAssignPlaylistToDevices,
  useAssignPlaylistToTags,
  useUnassignPlaylistFromDevices,
  useUnassignPlaylistFromTags,
} from '../hooks/usePlaylist';

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
  const [activeTab, setActiveTab] = useState<TabType>('devices');
  const [showAddDevices, setShowAddDevices] = useState(false);
  const [showAddTags, setShowAddTags] = useState(false);
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<number[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);

  // Fetch assignments
  const { data: assignments, isLoading } = usePlaylistAssignments(playlistId, isOpen);

  // Mutations
  const assignDevices = useAssignPlaylistToDevices();
  const assignTags = useAssignPlaylistToTags();
  const unassignDevices = useUnassignPlaylistFromDevices();
  const unassignTags = useUnassignPlaylistFromTags();

  if (!isOpen) return null;

  const handleAssignDevices = async () => {
    if (selectedDeviceIds.length === 0) {
      toast.error('Please select at least one device');
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
      toast.error('Please select at least one tag');
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
    if (!confirm('Unassign this playlist from the device?')) return;

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
    if (!confirm('Unassign this playlist from the tag?')) return;

    try {
      await unassignTags.mutateAsync({
        id: playlistId,
        data: { tag_ids: [tagId] },
      });
    } catch (error) {
      // Error handled by hook
    }
  };

  // Mock available devices/tags (replace with actual API calls)
  const mockAvailableDevices = [
    { id: 1, device_name: 'Lobby Display', status: 'online' },
    { id: 2, device_name: 'Reception TV', status: 'online' },
    { id: 3, device_name: 'Conference Room', status: 'offline' },
  ];

  const mockAvailableTags = [
    { id: 1, tag_name: 'Lobby', color: '#3B82F6' },
    { id: 2, tag_name: 'Marketing', color: '#10B981' },
    { id: 3, tag_name: 'Corporate', color: '#F59E0B' },
  ];

  const assignedDevices = assignments?.devices || [];
  const assignedTags = assignments?.tags || [];

  const availableDevices = mockAvailableDevices.filter(
    (device) => !assignedDevices.some((d) => d.device_id === device.id)
  );

  const availableTags = mockAvailableTags.filter(
    (tag) => !assignedTags.some((t) => t.tag_id === tag.id)
  );

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Playlist Assignments
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {playlistName}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b dark:border-gray-700">
          <button
            onClick={() => setActiveTab('devices')}
            className={`flex-1 px-6 py-3 font-medium flex items-center justify-center gap-2 ${
              activeTab === 'devices'
                ? 'text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            <Monitor className="w-4 h-4" />
            Devices ({assignedDevices.length})
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
            Tags ({assignedTags.length})
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              Loading assignments...
            </div>
          ) : activeTab === 'devices' ? (
            <>
              {/* Add Devices Section */}
              {showAddDevices ? (
                <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                    Assign to Devices
                  </h3>

                  <div className="space-y-2 max-h-48 overflow-y-auto mb-4">
                    {availableDevices.length === 0 ? (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No available devices to assign
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
                          <Monitor className="w-4 h-4 text-gray-400" />
                          <div className="flex-1">
                            <p className="font-medium text-gray-900 dark:text-white">
                              {device.device_name}
                            </p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              Status: {device.status}
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
                        ? 'Assigning...'
                        : `Assign ${selectedDeviceIds.length} device(s)`}
                    </button>
                    <button
                      onClick={() => {
                        setShowAddDevices(false);
                        setSelectedDeviceIds([]);
                      }}
                      className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowAddDevices(true)}
                  className="mb-6 w-full p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                >
                  <Plus className="w-5 h-5" />
                  Assign to Devices
                </button>
              )}

              {/* Current Devices */}
              <div className="space-y-2">
                <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                  Assigned Devices ({assignedDevices.length})
                </h3>

                {assignedDevices.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    Not assigned to any devices yet
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
                          {assignment.device_name || `Device #${assignment.device_id}`}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Assigned: {new Date(assignment.created_at).toLocaleDateString()}
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
                    Assign to Tags
                  </h3>

                  <div className="space-y-2 max-h-48 overflow-y-auto mb-4">
                    {availableTags.length === 0 ? (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No available tags to assign
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
                            style={{ backgroundColor: tag.color }}
                          />
                          <div className="flex-1">
                            <p className="font-medium text-gray-900 dark:text-white">
                              {tag.tag_name}
                            </p>
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
                        ? 'Assigning...'
                        : `Assign ${selectedTagIds.length} tag(s)`}
                    </button>
                    <button
                      onClick={() => {
                        setShowAddTags(false);
                        setSelectedTagIds([]);
                      }}
                      className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowAddTags(true)}
                  className="mb-6 w-full p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                >
                  <Plus className="w-5 h-5" />
                  Assign to Tags
                </button>
              )}

              {/* Current Tags */}
              <div className="space-y-2">
                <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                  Assigned Tags ({assignedTags.length})
                </h3>

                {assignedTags.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    Not assigned to any tags yet
                  </div>
                ) : (
                  assignedTags.map((assignment) => (
                    <div
                      key={assignment.id}
                      className="flex items-center gap-3 p-4 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
                    >
                      <div
                        className="w-4 h-4 rounded-full flex-shrink-0"
                        style={{ backgroundColor: assignment.tag_color || '#3B82F6' }}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 dark:text-white">
                          {assignment.tag_name || `Tag #${assignment.tag_id}`}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Assigned: {new Date(assignment.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <button
                        onClick={() => handleUnassignTag(assignment.tag_id)}
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

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
