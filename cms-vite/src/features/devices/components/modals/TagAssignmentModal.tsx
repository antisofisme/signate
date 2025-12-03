/**
 * Tag Assignment Modal Component
 *
 * Manage tag assignments for devices
 * Uses centralized Modal component
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Tag as TagIcon, Plus, Trash2, Loader2 } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
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
  const { t } = useTranslation();
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

  if (!device) return null;

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

  // Custom header with icon
  const customHeader = (
    <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <TagIcon className="w-5 h-5" />
            {t('devices.modals.tags')}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {device.device_name}
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
                <strong>{t('devices.modals.priority2Medium')}:</strong> {t('devices.modals.priority2Info')}
              </p>
            </div>
          </div>

          {/* Close Button */}
          <div className="flex justify-end gap-3 px-6 py-4">
            <Button
              variant="secondary"
              onClick={onClose}
              disabled={assignTag.isPending || unassignTag.isPending}
            >
              {t('common.close')}
            </Button>
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
            {/* Assign New Tag */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                {t('devices.modals.assignNewTag')}
              </label>
              {availableTags.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t('devices.modals.allTagsAssigned')}
                </p>
              ) : (
                <div className="flex gap-2">
                  <select
                    value={selectedTagId || ''}
                    onChange={(e) => setSelectedTagId(Number(e.target.value) || null)}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    disabled={assignTag.isPending}
                  >
                    <option value="">{t('devices.modals.selectTag')}</option>
                    {availableTags.map((tag) => (
                      <option key={tag.id} value={tag.id}>
                        {tag.tag_name}
                      </option>
                    ))}
                  </select>
                  <Button
                    onClick={handleAssign}
                    disabled={!selectedTagId || assignTag.isPending}
                    loading={assignTag.isPending}
                    leftIcon={<Plus className="w-4 h-4" />}
                  >
                    {assignTag.isPending ? t('devices.modals.assigning') : t('devices.modals.assign')}
                  </Button>
                </div>
              )}
            </div>

            {/* Currently Assigned Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                {t('devices.modals.currentlyAssignedTags')} ({assignedTags.length})
              </label>
              {assignedTags.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t('devices.modals.noTagsAssigned')}
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
                        title={t('devices.modals.removeTag')}
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
