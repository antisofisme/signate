/**
 * Tag Assignment Modal Component
 *
 * Manage tag assignments for devices
 */

import { useState } from 'react';
import { X, Tag as TagIcon, Plus, Trash2, Loader2 } from 'lucide-react';
import { useDeviceTags, useAssignTag, useUnassignTag } from '../../hooks/useDevices';
import { useTags } from '@/shared/hooks/useSharedTags';
import type { Device } from '../../types/device';

interface TagAssignmentModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

export function TagAssignmentModal({
  isOpen,
  device,
  onClose,
}: TagAssignmentModalProps) {
  const [selectedTagId, setSelectedTagId] = useState<number | null>(null);

  // Fetch assigned tags for this device
  const { data: assignedData, isLoading: loadingAssigned } = useDeviceTags(
    device?.id || 0,
    isOpen && !!device
  );

  // Fetch all available tags
  const { data: allTagsData, isLoading: loadingAllTags } = useTags();

  // Mutations
  const assignTag = useAssignTag();
  const unassignTag = useUnassignTag();

  if (!isOpen || !device) return null;

  const assignedTags = assignedData?.items || [];
  const allTags = allTagsData || [];

  // Filter out already assigned tags
  const availableTags = allTags.filter(
    (tag) => !assignedTags.some((assigned) => assigned.tag_id === tag.id)
  );

  // Handle assign
  const handleAssign = async () => {
    if (!selectedTagId) return;

    try {
      await assignTag.mutateAsync({ deviceId: device.id, tagId: selectedTagId });
      setSelectedTagId(null);
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle unassign
  const handleUnassign = async (tagId: number) => {
    try {
      await unassignTag.mutateAsync({ deviceId: device.id, tagId });
    } catch (error) {
      // Error handled by mutation
    }
  };

  const isLoading = loadingAssigned || loadingAllTags;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <TagIcon className="w-5 h-5" />
                Manage Tags
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {device.device_name}
              </p>
            </div>
            <button
              onClick={onClose}
              disabled={assignTag.isPending || unassignTag.isPending}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : (
            <div className="space-y-6">
              {/* Assign New Tag */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Assign New Tag
                </label>
                {availableTags.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    All available tags are already assigned to this device.
                  </p>
                ) : (
                  <div className="flex gap-2">
                    <select
                      value={selectedTagId || ''}
                      onChange={(e) => setSelectedTagId(Number(e.target.value) || null)}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      disabled={assignTag.isPending}
                    >
                      <option value="">Select a tag...</option>
                      {availableTags.map((tag) => (
                        <option key={tag.id} value={tag.id}>
                          {tag.tag_name}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={handleAssign}
                      disabled={!selectedTagId || assignTag.isPending}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
                    >
                      {assignTag.isPending ? (
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

              {/* Currently Assigned Tags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Currently Assigned Tags ({assignedTags.length})
                </label>
                {assignedTags.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    No tags assigned to this device yet.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {assignedTags.map((assigned) => (
                      <div
                        key={assigned.id}
                        className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className="w-4 h-4 rounded"
                            style={{ backgroundColor: assigned.tag_color }}
                          />
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {assigned.tag_name}
                          </span>
                        </div>
                        <button
                          onClick={() => handleUnassign(assigned.tag_id)}
                          disabled={unassignTag.isPending}
                          className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50"
                          title="Remove tag"
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

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              disabled={assignTag.isPending || unassignTag.isPending}
              className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
