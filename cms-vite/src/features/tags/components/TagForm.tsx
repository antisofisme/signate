/**
 * Tag Form Component
 * Form for creating/editing tags
 */

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
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

interface TagFormProps {
  tag?: Tag;
  onClose: () => void;
  onSubmit: (data: CreateTagRequest | UpdateTagRequest) => void;
  isLoading: boolean;
}

export function TagForm({ tag, onClose, onSubmit, isLoading }: TagFormProps) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    tag_name: tag?.tag_name || '',
    description: tag?.description || '',
    color: tag?.color || '#3B82F6',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {tag ? t('tags.editTag') : t('tags.createNewTag')}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('tags.tagName')} *
            </label>
            <input
              type="text"
              value={formData.tag_name}
              onChange={(e) => setFormData({ ...formData, tag_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder={t('tags.tagNamePlaceholder')}
              required
            />
          </div>

          {/* Color */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('tags.color')}
            </label>
            <select
              value={formData.color}
              onChange={(e) => setFormData({ ...formData, color: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {TAG_COLORS.map((color) => (
                <option key={color.value} value={color.value}>
                  {t(`tags.colors.${color.label.toLowerCase()}`)}
                </option>
              ))}
            </select>
            <div className="mt-2 flex items-center gap-2">
              <div
                className="w-8 h-8 rounded border-2"
                style={{ backgroundColor: formData.color }}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">{t('tags.preview')}</span>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('tags.description')}
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder={t('tags.descriptionPlaceholder')}
              rows={3}
            />
          </div>

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
              disabled={isLoading || !formData.tag_name.trim()}
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
      </div>
    </div>
  );
}

export default TagForm;
