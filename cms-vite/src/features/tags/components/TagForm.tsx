/**
 * Tag Form Component
 * Form for creating/editing tags using shared Modal and React Hook Form
 */

import { useEffect } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, Save, Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Modal, Button, FormInput, FormSelect, FormTextarea } from '@/shared/components';
import type { Tag, CreateTagRequest, UpdateTagRequest } from '../types/tag';

const TAG_COLORS = [
  { label: 'Blue', value: '#3B82F6' },
  { label: 'Red', value: '#EF4444' },
  { label: 'Green', value: '#10B981' },
  { label: 'Yellow', value: '#F59E0B' },
  { label: 'Purple', value: '#8B5CF6' },
  { label: 'Pink', value: '#EC4899' },
  { label: 'Gray', value: '#6B7280' },
];

// Zod validation schema
const tagSchema = z.object({
  tag_name: z.string().min(1, 'Tag name is required').max(100, 'Tag name must be less than 100 characters'),
  description: z.string().max(500, 'Description must be less than 500 characters').optional().nullable(),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid color format'),
});

type TagFormData = z.infer<typeof tagSchema>;

interface TagFormProps {
  tag?: Tag;
  onClose: () => void;
  onSubmit: (data: CreateTagRequest | UpdateTagRequest) => void;
  isLoading: boolean;
}

export function TagForm({ tag, onClose, onSubmit, isLoading }: TagFormProps) {
  const { t } = useTranslation();
  const isEditing = !!tag;

  // React Hook Form setup
  const methods = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: {
      tag_name: tag?.tag_name || '',
      description: tag?.description || '',
      // Normalize color to uppercase to match TAG_COLORS values
      color: tag?.color?.toUpperCase() || '#3B82F6',
    },
  });

  const { handleSubmit, watch, reset } = methods;

  // Reset form when tag changes
  useEffect(() => {
    if (tag) {
      reset({
        tag_name: tag.tag_name,
        description: tag.description || '',
        // Normalize color to uppercase to match TAG_COLORS values
        color: tag.color?.toUpperCase() || '#3B82F6',
      });
    }
  }, [tag, reset]);

  // Watch color for preview
  const selectedColor = watch('color');

  const onFormSubmit = (data: TagFormData) => {
    onSubmit(data);
  };

  const handleClose = () => {
    methods.reset();
    onClose();
  };

  // Convert color options for FormSelect
  const colorOptions = TAG_COLORS.map((color) => ({
    label: t(`tags.colors.${color.label.toLowerCase()}`),
    value: color.value,
  }));

  return (
    <Modal
      isOpen={true}
      onClose={handleClose}
      title={isEditing ? t('tags.editTag') : t('tags.createNewTag')}
      maxWidth="md"
    >
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onFormSubmit)} className="p-6 space-y-4">
          {/* Name */}
          <FormInput
            name="tag_name"
            label={t('tags.tagName')}
            placeholder={t('tags.tagNamePlaceholder')}
            required
          />

          {/* Color */}
          <div>
            <FormSelect
              name="color"
              label={t('tags.color')}
              options={colorOptions}
            />
            <div className="mt-2 flex items-center gap-2">
              <div
                className="w-8 h-8 rounded border-2 border-gray-300 dark:border-gray-600"
                style={{ backgroundColor: selectedColor }}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">{t('tags.preview')}</span>
            </div>
          </div>

          {/* Description */}
          <FormTextarea
            name="description"
            label={t('tags.description')}
            placeholder={t('tags.descriptionPlaceholder')}
            rows={3}
          />

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              disabled={isLoading}
            >
              {t('tags.cancel')}
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isLoading}
              loading={isLoading}
              leftIcon={isEditing ? <Save className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            >
              {isEditing ? t('tags.update') : t('tags.create')}
            </Button>
          </div>
        </form>
      </FormProvider>
    </Modal>
  );
}

export default TagForm;
