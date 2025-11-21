/**
 * Content Assignment Modal Component
 *
 * Manage content assignments for devices (Priority 1 - Direct Assignment)
 */

import { useState } from 'react';
import { X, FileText, Plus, Trash2, Loader2, Star } from 'lucide-react';
import { useDeviceContents, useAssignContent, useUnassignContent } from '../../hooks/useDevices';
import { useContentList } from '@/shared/hooks/useSharedContents';
import type { Device } from '../../types/device';

interface ContentAssignmentModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

export function ContentAssignmentModal({
  isOpen,
  device,
  onClose,
}: ContentAssignmentModalProps) {
  const [selectedContentId, setSelectedContentId] = useState<number | null>(null);
  const [priority, setPriority] = useState<number>(1);

  // Fetch assigned content for this device
  const { data: assignedData, isLoading: loadingAssigned } = useDeviceContents(
    device?.id || 0,
    isOpen && !!device
  );

  // Fetch all available content
  const { data: allContentData, isLoading: loadingAllContent } = useContentList();

  // Mutations
  const assignContent = useAssignContent();
  const unassignContent = useUnassignContent();

  if (!isOpen || !device) return null;

  const assignedContents = assignedData?.items || [];
  const allContents = allContentData?.data || [];

  // Filter out already assigned content
  const availableContents = allContents.filter(
    (content) => !assignedContents.some((assigned) => assigned.content_id === content.id)
  );

  // Handle assign
  const handleAssign = async () => {
    if (!selectedContentId) return;

    try {
      await assignContent.mutateAsync({
        deviceId: device.id,
        contentId: selectedContentId,
        priority,
      });
      setSelectedContentId(null);
      setPriority(1);
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle unassign
  const handleUnassign = async (contentId: number) => {
    try {
      await unassignContent.mutateAsync({ deviceId: device.id, contentId });
    } catch (error) {
      // Error handled by mutation
    }
  };

  const isLoading = loadingAssigned || loadingAllContent;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Manage Content (Direct Assignment)
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {device.device_name} - Priority 1 (Highest)
              </p>
            </div>
            <button
              onClick={onClose}
              disabled={assignContent.isPending || unassignContent.isPending}
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
              {/* Assign New Content */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Assign New Content
                </label>
                {availableContents.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    All available content is already assigned to this device.
                  </p>
                ) : (
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <select
                        value={selectedContentId || ''}
                        onChange={(e) => setSelectedContentId(Number(e.target.value) || null)}
                        className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        disabled={assignContent.isPending}
                      >
                        <option value="">Select content...</option>
                        {availableContents.map((content) => (
                          <option key={content.id} value={content.id}>
                            {content.title} ({content.content_type})
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={handleAssign}
                        disabled={!selectedContentId || assignContent.isPending}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
                      >
                        {assignContent.isPending ? (
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

                    {/* Priority Input */}
                    {selectedContentId && (
                      <div className="flex items-center gap-3">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1">
                          <Star className="w-4 h-4" />
                          Priority:
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="100"
                          value={priority}
                          onChange={(e) => setPriority(parseInt(e.target.value) || 1)}
                          className="w-20 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          disabled={assignContent.isPending}
                        />
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          (Higher = More Important)
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Currently Assigned Content */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Currently Assigned Content ({assignedContents.length})
                </label>
                {assignedContents.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    No content directly assigned to this device yet.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {assignedContents
                      .sort((a, b) => b.priority - a.priority)
                      .map((assigned) => (
                        <div
                          key={assigned.id}
                          className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                        >
                          <div className="flex items-center gap-3 flex-1">
                            <div className="flex items-center gap-2">
                              <Star className="w-4 h-4 text-yellow-500" />
                              <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                {assigned.priority}
                              </span>
                            </div>
                            <div>
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {assigned.content_name}
                              </div>
                              <div className="text-xs text-gray-500 dark:text-gray-400">
                                {assigned.content_type}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => handleUnassign(assigned.content_id)}
                            disabled={unassignContent.isPending}
                            className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50"
                            title="Remove content"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  <strong>Priority 1 (Highest):</strong> Direct assignments override tag-based and playlist assignments.
                  Higher priority numbers are shown first.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              disabled={assignContent.isPending || unassignContent.isPending}
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
