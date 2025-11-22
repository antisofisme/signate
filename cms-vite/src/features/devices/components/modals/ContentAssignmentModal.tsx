/**
 * Content Assignment Modal Component
 *
 * Manage content assignments for devices (Priority 1 - Direct Assignment)
 * Uses centralized Modal component
 */

import { useState } from 'react';
import { FileText, Plus, Trash2, Loader2, Star, Image, Video, Music, ArrowRight } from 'lucide-react';
import { Modal } from '@/shared/components';
import { useDeviceContents, useAssignContent, useUnassignContent } from '../../hooks/useDevices';
import { useContentList } from '@/shared/hooks/useSharedContents';
import type { Device } from '../../types/device';
import type { Content } from '@/features/contents/types/content';

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

  if (!device) return null;

  const assignedContents = assignedData?.items || [];
  const allContents = allContentData?.data || [];

  // Filter out already assigned content
  const availableContents = allContents.filter(
    (content) => !assignedContents.some((assigned) => assigned.content_id === content.id)
  );

  // Get content type icon
  const getContentIcon = (type: string) => {
    switch (type) {
      case 'image':
        return Image;
      case 'video':
        return Video;
      case 'audio':
        return Music;
      default:
        return FileText;
    }
  };

  // Get content details by ID
  const getContentDetails = (contentId: number) => {
    return allContents.find((c) => c.id === contentId);
  };

  // Handle assign with priority
  const handleAssign = async (contentId: number) => {
    try {
      await assignContent.mutateAsync({
        deviceId: device.id,
        contentId,
        priority,
      });
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

  // Custom header with icon and priority selector
  const customHeader = (
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
        <div className="flex items-center gap-2">
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
          />
          <span className="text-xs text-gray-500 dark:text-gray-400">
            (Higher = More Important)
          </span>
        </div>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="4xl"
      customHeader={customHeader}
      footer={
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
      }
    >
      {/* Content - 2 Column Grid */}
      <div className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-6">
            {/* Left Column - Available Content */}
            <div className="border-r border-gray-200 dark:border-gray-700 pr-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Available Content ({availableContents.length})
              </h4>
              {availableContents.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  All content is already assigned.
                </p>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {availableContents.map((content: Content) => {
                    const Icon = getContentIcon(content.content_type);
                    return (
                      <div
                        key={content.id}
                        className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer"
                        onClick={() => handleAssign(content.id)}
                      >
                        <div className="flex gap-3">
                          {/* Thumbnail */}
                          <div className="w-16 h-16 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
                            {content.thumbnail_url ? (
                              <img
                                src={content.thumbnail_url}
                                alt={content.title}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <Icon className="w-6 h-6 text-gray-400" />
                              </div>
                            )}
                          </div>

                          {/* Info */}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                              {content.title}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                              {content.content_type} • {content.duration}s
                            </p>
                          </div>

                          {/* Assign Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleAssign(content.id);
                            }}
                            disabled={assignContent.isPending}
                            className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-all"
                            title="Assign to device"
                          >
                            <ArrowRight className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Right Column - Assigned Content */}
            <div className="pl-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Star className="w-4 h-4 text-yellow-500" />
                Assigned Content ({assignedContents.length})
              </h4>
              {assignedContents.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No content assigned yet.
                </p>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {assignedContents
                    .sort((a, b) => b.priority - a.priority)
                    .map((assigned) => {
                      const content = getContentDetails(assigned.content_id);
                      if (!content) return null;
                      const Icon = getContentIcon(assigned.content_type);
                      return (
                        <div
                          key={assigned.id}
                          className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-red-500 dark:hover:border-red-400 transition-colors"
                        >
                          <div className="flex gap-3">
                            {/* Priority Badge */}
                            <div className="flex-shrink-0 w-8 h-16 flex items-center justify-center">
                              <div className="flex flex-col items-center">
                                <Star className="w-4 h-4 text-yellow-500" />
                                <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
                                  {assigned.priority}
                                </span>
                              </div>
                            </div>

                            {/* Thumbnail */}
                            <div className="w-16 h-16 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
                              {content.thumbnail_url ? (
                                <img
                                  src={content.thumbnail_url}
                                  alt={content.title}
                                  className="w-full h-full object-cover"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                  <Icon className="w-6 h-6 text-gray-400" />
                                </div>
                              )}
                            </div>

                            {/* Info */}
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                {assigned.content_name}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                {assigned.content_type}
                              </p>
                            </div>

                            {/* Remove Button */}
                            <button
                              onClick={() => handleUnassign(assigned.content_id)}
                              disabled={unassignContent.isPending}
                              className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all"
                              title="Remove from device"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                </div>
              )}

              {/* Info */}
              <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  <strong>Priority 1 (Highest):</strong> Direct assignments override tag-based and playlist assignments.
                  Higher priority numbers are shown first.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
