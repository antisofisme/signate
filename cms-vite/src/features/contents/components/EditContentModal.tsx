/**
 * Edit Content Modal Component
 * Edit individual content metadata
 *
 * ✅ REFACTORED: Uses React Hook Form + Zod + Pure Tailwind
 * - Fixed header (title)
 * - Fixed footer (buttons)
 * - Scrollable content (form fields)
 * - Click outside to close
 */

import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Save } from 'lucide-react';
import { Modal, Button, FormInput, FormTextarea, FormSwitch } from '@/shared/components';
import { useUpdateContent } from '../hooks/useContent';
import type { Content } from '../types/content';

// Zod validation schema
const editContentSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required')
    .max(200, 'Title must be less than 200 characters')
    .trim(),
  description: z.string().max(1000, 'Description must be less than 1000 characters').optional(),
  duration: z
    .number()
    .min(1, 'Duration must be at least 1 second')
    .max(86400, 'Duration cannot exceed 24 hours'),
  is_active: z.boolean(),
});

type EditContentForm = z.infer<typeof editContentSchema>;

interface EditContentModalProps {
  isOpen: boolean;
  onClose: () => void;
  content: Content | null;
}

export function EditContentModal({ isOpen, onClose, content }: EditContentModalProps) {
  const { t } = useTranslation();
  const updateMutation = useUpdateContent();

  // Initialize React Hook Form with Zod resolver
  const methods = useForm<EditContentForm>({
    resolver: zodResolver(editContentSchema),
    defaultValues: {
      title: '',
      description: '',
      duration: 10,
      is_active: true,
    },
  });

  const { handleSubmit, reset, formState: { isValid } } = methods;

  // Pre-populate form when content changes
  useEffect(() => {
    if (content) {
      reset({
        title: content.title || '',
        description: content.description || '',
        duration: content.duration || 10,
        is_active: content.is_active ?? true,
      });
    }
  }, [content, reset]);

  if (!content) return null;

  const onSubmit = async (data: EditContentForm) => {
    try {
      await updateMutation.mutateAsync({
        id: content.id,
        data: {
          title: data.title.trim(),
          description: data.description?.trim() || undefined,
          duration: data.duration,
          is_active: data.is_active,
        },
      });

      onClose();
    } catch (error) {
      // Error handled by mutation hook
      console.error('Update error:', error);
    }
  };

  const handleClose = () => {
    if (updateMutation.isPending) return;
    onClose();
  };

  // Footer with action buttons
  const footer = (
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        type="button"
        variant="secondary"
        onClick={handleClose}
        disabled={updateMutation.isPending}
      >
        {t('contents.buttons.cancel')}
      </Button>
      <Button
        type="submit"
        form="edit-content-form"
        disabled={!isValid || updateMutation.isPending}
        loading={updateMutation.isPending}
        leftIcon={<Save className="w-4 h-4" />}
      >
        {updateMutation.isPending ? t('contents.buttons.updating') : t('contents.buttons.saveChanges')}
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('contents.modals.editContent')}
      maxWidth="2xl"
      footer={footer}
      closeOnBackdropClick={!updateMutation.isPending}
    >
      {/* Scrollable content */}
      <FormProvider {...methods}>
        <form id="edit-content-form" onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Content Info */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500 dark:text-gray-400">{t('contents.form.fileName')}</p>
                <p className="text-gray-900 dark:text-white font-medium truncate">
                  {content.original_filename}
                </p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">{t('contents.form.type')}</p>
                <p className="text-gray-900 dark:text-white font-medium">
                  {content.content_type.toUpperCase()}
                </p>
              </div>
            </div>
          </div>

          {/* Title */}
          <FormInput
            name="title"
            label={t('contents.form.title')}
            placeholder={t('contents.placeholders.title')}
            required
            disabled={updateMutation.isPending}
          />

          {/* Description */}
          <FormTextarea
            name="description"
            label={t('contents.form.description')}
            placeholder={t('contents.placeholders.description')}
            rows={3}
            disabled={updateMutation.isPending}
          />

          {/* Duration */}
          <FormInput
            name="duration"
            type="number"
            label={t('contents.form.displayDuration')}
            description={t('contents.form.durationHelp')}
            min={1}
            max={86400}
            required
            disabled={updateMutation.isPending}
          />

          {/* Active Status */}
          <FormSwitch
            name="is_active"
            label={t('contents.form.activeLabel')}
            description={t('contents.form.activeDescription')}
            disabled={updateMutation.isPending}
          />
        </form>
      </FormProvider>
    </Modal>
  );
}
