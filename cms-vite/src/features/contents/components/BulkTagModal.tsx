/**
 * Bulk Tag Modal Component
 * Assign/unassign tags to multiple content items
 *
 * ✅ REFACTORED: Now uses shared Modal component
 * - Fixed header (title + subtitle)
 * - Fixed footer (buttons)
 * - Scrollable content (tag selection + content list)
 * - Click outside to close
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Tag, Plus, Loader2 } from 'lucide-react';
import { Modal } from '@/shared/components';
import { useTags, useAssignTagToContents } from '@/shared/hooks/useSharedTags';
import type { Content } from '../types/content';

interface BulkTagModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedContent: Content[];
}

export function BulkTagModal({ isOpen, onClose, selectedContent }: BulkTagModalProps) {
  const { t } = useTranslation();
  const [selectedTagId, setSelectedTagId] = useState<number | null>(null);

  // Fetch tags
  const { data: tags, isLoading: tagsLoading } = useTags({ sort_by: 'name_asc' });

  // Assign mutation
  const assignMutation = useAssignTagToContents();

  const handleAssign = async () => {
    if (!selectedTagId) {
      return;
    }

    const contentIds = selectedContent.map(c => c.id);

    try {
      await assignMutation.mutateAsync({ tagId: selectedTagId, contentIds });
      onClose();
    } catch (error) {
      // Error handled by mutation
      console.error('Assign error:', error);
    }
  };

  const handleClose = () => {
    if (!assignMutation.isPending) {
      onClose();
    }
  };

  const selectedTag = tags?.find(t => t.id === selectedTagId);

  // Custom header with subtitle
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">
        {t('contents.actions.bulkTagAssignment')}
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
        {t('contents.actions.assignTagToItems', { count: selectedContent.length })}
      </p>
    </div>
  );

  // Footer with action buttons
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={handleClose}
          disabled={assignMutation.isPending}
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 transition-colors"
        >
          {t('common.cancel')}
        </button>
        <button
          type="button"
          onClick={handleAssign}
          disabled={!selectedTagId || assignMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          {assignMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {t('contents.actions.assigningTag')}
            </>
          ) : (
            <>
              <Plus className="w-4 h-4" />
              {t('contents.actions.assignTag')}
            </>
          )}
        </button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      maxWidth="2xl"
      customHeader={customHeader}
      footer={footer}
      closeOnBackdropClick={!assignMutation.isPending}
    >
      {/* Scrollable content */}
      <div className="p-6 space-y-6">
        {/* Tag Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            {t('contents.actions.selectTag')}
          </label>

          {tagsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            </div>
          ) : tags && tags.length > 0 ? (
            <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto border dark:border-gray-700 rounded-lg p-3">
              {tags.map((tag) => (
                <button
                  key={tag.id}
                  onClick={() => setSelectedTagId(tag.id)}
                  disabled={assignMutation.isPending}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
                    selectedTagId === tag.id
                      ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
                  } disabled:opacity-50`}
                >
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: tag.color }}
                  />
                  <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {tag.tag_name}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <Tag className="w-12 h-12 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('contents.actions.noTagsAvailable')}</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                {t('contents.actions.createTagsFirst')}
              </p>
            </div>
          )}
        </div>

        {/* Selected Tag Preview */}
        {selectedTag && (
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-2">
              {t('contents.actions.selectedTag')}
            </p>
            <div className="flex items-center gap-2">
              <div
                className="w-6 h-6 rounded-full"
                style={{ backgroundColor: selectedTag.color }}
              />
              <span className="text-lg font-bold text-gray-900 dark:text-white">
                {selectedTag.tag_name}
              </span>
            </div>
            {selectedTag.description && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                {selectedTag.description}
              </p>
            )}
          </div>
        )}

        {/* Selected Content List */}
        <div>
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            {t('contents.actions.contentToBeTagged', { count: selectedContent.length })}
          </p>
          <div className="space-y-2 max-h-48 overflow-y-auto border dark:border-gray-700 rounded-lg p-3">
            {selectedContent.map((content) => (
              <div
                key={content.id}
                className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-700 rounded"
              >
                <p className="text-sm text-gray-900 dark:text-white truncate flex-1">
                  {content.title}
                </p>
                <span className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded">
                  {content.content_type}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}
