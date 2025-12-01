/**
 * Tag Assignment Tab
 *
 * Priority 2 - Medium priority tag-based content assignment
 * Two-column layout: Available Tags (left) | Assigned Tags (right)
 */

import { useTranslation } from 'react-i18next';
import { Tag as TagIcon, Trash2, Loader2, ArrowRight } from 'lucide-react';
import { useDeviceTags, useAssignTag, useUnassignTag } from '../../../hooks/useDevices';
import { useTags } from '@/shared/hooks/useSharedTags';
import type { Device } from '../../../types/device';

interface TagAssignmentTabProps {
  device: Device;
}

export function TagAssignmentTab({ device }: TagAssignmentTabProps) {
  const { t } = useTranslation();

  // Fetch assigned tags for this device
  const { data: assignedData, isLoading: loadingAssigned } = useDeviceTags(device.id, true);

  // Fetch all available tags
  const { data: allTagsData, isLoading: loadingAllTags } = useTags();

  // Mutations
  const assignTag = useAssignTag();
  const unassignTag = useUnassignTag();

  const assignedTags = assignedData?.items || [];
  const allTags = allTagsData || [];

  // Filter out already assigned tags
  const availableTags = allTags.filter(
    (tag) => !assignedTags.some((assigned) => assigned.tag_id === tag.id)
  );

  // Handle assign
  const handleAssign = async (tagId: number) => {
    try {
      await assignTag.mutateAsync({ deviceId: device.id, tagId });
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
    <div className="p-6 min-h-[600px]">
      {/* Info */}
      <div className="mb-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
        <p className="text-sm text-blue-700 dark:text-blue-300">
          <strong>{t('devices.modals.priority2Medium')}:</strong> {t('devices.modals.priority2Info')}
        </p>
      </div>

      {/* Content - 2 Column Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-6">
          {/* Left Column - Available Tags */}
          <div className="border-r border-gray-200 dark:border-gray-700 pr-4">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <TagIcon className="w-4 h-4" />
              {t('devices.modals.availableTags', 'Tag Tersedia')} ({availableTags.length})
            </h4>
            {availableTags.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('devices.modals.allTagsAssigned')}
              </p>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {availableTags.map((tag) => (
                  <div
                    key={tag.id}
                    className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer"
                    onClick={() => handleAssign(tag.id)}
                  >
                    <div className="flex items-center gap-3">
                      {/* Color indicator */}
                      <div
                        className="w-4 h-4 rounded flex-shrink-0"
                        style={{ backgroundColor: tag.color }}
                      />
                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {tag.tag_name}
                        </p>
                        {tag.description && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                            {tag.description}
                          </p>
                        )}
                      </div>
                      {/* Assign Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAssign(tag.id);
                        }}
                        disabled={assignTag.isPending}
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

          {/* Right Column - Assigned Tags */}
          <div className="pl-4">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <TagIcon className="w-4 h-4 text-green-600" />
              {t('devices.modals.assignedTags', 'Tag Ditetapkan')} ({assignedTags.length})
            </h4>
            {assignedTags.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('devices.modals.noTagsAssigned')}
              </p>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {assignedTags.map((assigned) => (
                  <div
                    key={assigned.id}
                    className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 transition-colors bg-white dark:bg-gray-800"
                  >
                    <div className="flex items-center gap-3">
                      {/* Color indicator */}
                      <div
                        className="w-4 h-4 rounded flex-shrink-0"
                        style={{ backgroundColor: assigned.tag_color }}
                      />
                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {assigned.tag_name}
                        </p>
                      </div>
                      {/* Remove Button */}
                      <button
                        onClick={() => handleUnassign(assigned.tag_id)}
                        disabled={unassignTag.isPending}
                        className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all"
                        title={t('devices.modals.removeTag')}
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
