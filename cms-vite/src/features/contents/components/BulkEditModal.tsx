/**
 * Bulk Edit Modal Component
 * Edit multiple content items at once with simplified bulk update
 *
 * ✅ REFACTORED: Now uses shared Modal component
 * - Fixed header (title + subtitle)
 * - Fixed footer (action buttons)
 * - Scrollable content (bulk fields + content list with progress tracking)
 * - Click outside to close (disabled during update)
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Save, FileImage, FileVideo, FileAudio, Loader2 } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Modal, Button } from '@/shared/components';
import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type { Content } from '../types/content';
import { contentKeys } from '../hooks/useContent';

interface BulkEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedContent: Content[];
}

export function BulkEditModal({ isOpen, onClose, selectedContent }: BulkEditModalProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [updating, setUpdating] = useState(false);
  const [updateProgress, setUpdateProgress] = useState<{[key: number]: 'pending' | 'updating' | 'success' | 'error'}>({});

  // Bulk update mode: Apply same changes to all
  const [bulkDuration, setBulkDuration] = useState<number | ''>('');
  const [bulkIsActive, setBulkIsActive] = useState<boolean | null>(null);

  if (!isOpen) return null;

  const handleBulkUpdate = async (e: React.FormEvent) => {
    e.preventDefault();

    if (bulkDuration === '' && bulkIsActive === null) {
      toast.error(t('contents.messages.setAtLeastOneField'));
      return;
    }

    setUpdating(true);

    // Initialize progress
    const initialProgress: {[key: number]: 'pending' | 'updating' | 'success' | 'error'} = {};
    selectedContent.forEach(content => {
      initialProgress[content.id] = 'pending';
    });
    setUpdateProgress(initialProgress);

    let successCount = 0;
    let failCount = 0;

    // Update all content in parallel
    const updatePromises = selectedContent.map(async (content) => {
      try {
        setUpdateProgress(prev => ({ ...prev, [content.id]: 'updating' }));

        const updateData: any = {};
        if (bulkDuration !== '') updateData.duration = bulkDuration;
        if (bulkIsActive !== null) updateData.is_active = bulkIsActive;

        await apiClient.put(API_ENDPOINTS.CONTENT.UPDATE(content.id), updateData);

        setUpdateProgress(prev => ({ ...prev, [content.id]: 'success' }));
        successCount++;
      } catch (error) {
        setUpdateProgress(prev => ({ ...prev, [content.id]: 'error' }));
        failCount++;
        console.error(`Failed to update content ${content.id}:`, error);
      }
    });

    await Promise.all(updatePromises);

    // Invalidate queries
    queryClient.invalidateQueries({ queryKey: contentKeys.lists() });

    setUpdating(false);

    // Show result
    if (failCount === 0) {
      toast.success(t('contents.messages.successfullyUpdated', { count: successCount }));
      onClose();
    } else {
      toast.warning(t('contents.messages.updatedWithFailures', { successCount, failCount }));
    }
  };

  const getContentIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <FileImage className="w-5 h-5 text-green-600" />;
      case 'video':
        return <FileVideo className="w-5 h-5 text-blue-600" />;
      case 'audio':
        return <FileAudio className="w-5 h-5 text-purple-600" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: 'pending' | 'updating' | 'success' | 'error') => {
    switch (status) {
      case 'pending':
        return <span className="text-xs text-gray-500">{t('contents.status.pending')}</span>;
      case 'updating':
        return <span className="text-xs text-blue-600 flex items-center gap-1">
          <Loader2 className="w-3 h-3 animate-spin" /> {t('contents.status.updating')}
        </span>;
      case 'success':
        return <span className="text-xs text-green-600">{t('contents.status.success')}</span>;
      case 'error':
        return <span className="text-xs text-red-600">{t('contents.status.failed')}</span>;
      default:
        return null;
    }
  };

  const handleClose = () => {
    if (!updating) {
      onClose();
    }
  };

  // Custom header with subtitle
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">
        {t('contents.modals.bulkEdit')}
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
        {t('contents.modals.editingItems', { count: selectedContent.length })}
      </p>
    </div>
  );

  // Footer with action buttons
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end gap-3">
        <Button
          variant="ghost"
          onClick={handleClose}
          disabled={updating}
        >
          {t('contents.buttons.cancel')}
        </Button>
        <Button
          variant="primary"
          type="submit"
          form="bulk-edit-form"
          disabled={updating || (bulkDuration === '' && bulkIsActive === null)}
          loading={updating}
          leftIcon={!updating ? <Save className="w-4 h-4" /> : undefined}
        >
          {updating
            ? t('contents.buttons.updatingItems', { count: selectedContent.length })
            : t('contents.buttons.updateAll')
          }
        </Button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      maxWidth="4xl"
      customHeader={customHeader}
      footer={footer}
      closeOnBackdropClick={!updating}
      className="h-[90vh]"
    >
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-6">
        <form id="bulk-edit-form" onSubmit={handleBulkUpdate} className="space-y-6">
          {/* Bulk Update Fields */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-3">
              {t('contents.form.applyToAll')}
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {/* Duration */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('contents.form.durationSeconds')}
                </label>
                <input
                  type="number"
                  value={bulkDuration}
                  onChange={(e) => setBulkDuration(e.target.value ? parseInt(e.target.value) : '')}
                  disabled={updating}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
                  placeholder={t('contents.form.leaveEmptyToSkip')}
                  min={1}
                  max={86400}
                />
              </div>

              {/* Active Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('contents.form.activeStatus')}
                </label>
                <select
                  value={bulkIsActive === null ? '' : bulkIsActive.toString()}
                  onChange={(e) => setBulkIsActive(e.target.value === '' ? null : e.target.value === 'true')}
                  disabled={updating}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
                >
                  <option value="">{t('contents.form.dontChange')}</option>
                  <option value="true">{t('contents.form.active')}</option>
                  <option value="false">{t('contents.form.inactive')}</option>
                </select>
              </div>
            </div>
          </div>

          {/* Selected Content List */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              {t('contents.form.selectedContent', { count: selectedContent.length })}
            </h3>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {selectedContent.map((content) => (
                <div
                  key={content.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {getContentIcon(content.content_type)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {content.title}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {content.original_filename}
                      </p>
                    </div>
                  </div>
                  {updating && updateProgress[content.id] && (
                    <div>{getStatusBadge(updateProgress[content.id])}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </form>
      </div>
    </Modal>
  );
}
