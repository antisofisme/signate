/**
 * Tag Form Component
 * Form for creating/editing tags
 */

import { useEffect } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { FormInput, FormSelect, FormTextarea } from '@/shared/components';
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

  // React Hook Form setup
  const methods = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
    defaultValues: {
      tag_name: tag?.tag_name || '',
      description: tag?.description || '',
      color: tag?.color || '#3B82F6',
    },
  });

  const { handleSubmit, watch, reset, formState: { isDirty } } = methods;

  // Reset form when tag changes
  useEffect(() => {
    if (tag) {
      reset({
        tag_name: tag.tag_name,
        description: tag.description || '',
        color: tag.color,
      });
    }
  }, [tag, reset]);

  // Watch color for preview
  const selectedColor = watch('color');

  const onFormSubmit = (data: TagFormData) => {
    onSubmit(data);
  };

  // Convert color options for FormSelect
  const colorOptions = TAG_COLORS.map((color) => ({
    label: t(`tags.colors.${color.label.toLowerCase()}`),
    value: color.value,
  }));

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {tag ? t('tags.editTag') : t('tags.createNewTag')}
        </h3>

        <FormProvider {...methods}>
          <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
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

            {/* Buttons */}
            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                disabled={isLoading}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
              >
                {t('tags.cancel')}
              </button>
              <button
                type="submit"
                disabled={isLoading || !isDirty}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    {tag ? t('tags.updating') : t('tags.creating')}
                  </>
                ) : (
                  <>{tag ? t('tags.update') : t('tags.create')}</>
                )}
              </button>
            </div>
          </form>
        </FormProvider>
      </div>
    </div>
  );
}

export default TagForm;
