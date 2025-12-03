/**
 * Bulk Edit Modal Component
 * Edit multiple content items at once with simplified bulk update
 *
 * ✅ REFACTORED: Uses React Hook Form + Zod + Pure Tailwind
 * - Fixed header (title + subtitle)
 * - Fixed footer (action buttons)
 * - Scrollable content (bulk fields + content list with progress tracking)
 * - Click outside to close (disabled during update)
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Save, FileImage, FileVideo, FileAudio, Loader2 } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Modal, Button, FormInput, FormSelect } from '@/shared/components';
import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type { Content } from '../types/content';
import { contentKeys } from '../hooks/useContent';

// Zod validation schema
const bulkEditSchema = z.object({
  duration: z.string().optional(), // String to allow empty value
  is_active: z.string(), // 'true', 'false', or '' for no change
});

type BulkEditForm = z.infer<typeof bulkEditSchema>;

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

  // Initialize React Hook Form with Zod resolver
  const methods = useForm<BulkEditForm>({
    resolver: zodResolver(bulkEditSchema),
    defaultValues: {
      duration: '',
      is_active: '',
    },
  });

  const { handleSubmit, watch, reset } = methods;
  const durationValue = watch('duration');
  const isActiveValue = watch('is_active');

  if (!isOpen) return null;

  const onSubmit = async (data: BulkEditForm) => {
    const duration = data.duration ? parseInt(data.duration, 10) : null;
    const isActive = data.is_active === '' ? null : data.is_active === 'true';

    if (duration === null && isActive === null) {
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
        if (duration !== null) updateData.duration = duration;
        if (isActive !== null) updateData.is_active = isActive;

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

    // Invalidate ALL content queries using predicate for guaranteed matching
    queryClient.invalidateQueries({
      predicate: (query) => query.queryKey[0] === 'content',
    });

    setUpdating(false);
    reset();

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

  // Check if any field has a value
  const hasChanges = (durationValue && durationValue !== '') || (isActiveValue && isActiveValue !== '');

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
          disabled={updating || !hasChanges}
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

  // Active status options
  const activeStatusOptions = [
    { value: '', label: t('contents.form.dontChange') },
    { value: 'true', label: t('contents.form.active') },
    { value: 'false', label: t('contents.form.inactive') },
  ];

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
        <FormProvider {...methods}>
          <form id="bulk-edit-form" onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Bulk Update Fields */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-3">
                {t('contents.form.applyToAll')}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Duration */}
                <FormInput
                  name="duration"
                  type="number"
                  label={t('contents.form.durationSeconds')}
                  placeholder={t('contents.form.leaveEmptyToSkip')}
                  min={1}
                  max={86400}
                  disabled={updating}
                />

                {/* Active Status */}
                <FormSelect
                  name="is_active"
                  label={t('contents.form.activeStatus')}
                  options={activeStatusOptions}
                  placeholder=""
                  disabled={updating}
                />
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
        </FormProvider>
      </div>
    </Modal>
  );
}
