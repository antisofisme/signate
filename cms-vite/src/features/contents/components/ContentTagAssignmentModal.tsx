/**
 * Content Tag Assignment Modal
 *
 * Kebalikan dari TagContentAssignmentModal:
 * - TagContentAssignmentModal: 1 tag → banyak content (halaman Tag)
 * - ContentTagAssignmentModal: 1 content → banyak tag (halaman Konten)
 *
 * Features:
 * - Two-column layout: Available Tags (left) | Assigned Tags (right)
 * - Click to assign tag to content
 * - Remove button to unassign tag from content
 * - Optimistic UI updates
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Tag, Trash2, Loader2, ArrowRight } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { useTags } from '@/shared/hooks/useSharedTags';
import {
  useAssignTagToContents,
  useUnassignTagFromContents,
} from '@/features/tags/hooks/useTags';
import { tagsApi } from '@/features/tags/api/tagsApi';
import { useQuery } from '@tanstack/react-query';
import type { Content } from '../types/content';
import type { Tag as TagType } from '@/features/tags/types/tag';

interface ContentTagAssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedContent: Content[];
}

export function ContentTagAssignmentModal({
  isOpen,
  onClose,
  selectedContent,
}: ContentTagAssignmentModalProps) {
  const { t } = useTranslation();

  // LOCAL STATE for optimistic UI updates
  const [assignedTags, setAssignedTags] = useState<TagType[]>([]);

  // Fetch all tags
  const { data: allTags, isLoading: isLoadingAllTags } = useTags({ sort_by: 'name_asc' });

  // Fetch tags already assigned to the first content item
  const contentId = selectedContent.length === 1 ? selectedContent[0].id : null;
  const { data: contentTags, isLoading: isLoadingContentTags } = useQuery({
    queryKey: ['content', 'tags', contentId],
    queryFn: () => tagsApi.getContentTags(contentId!),
    enabled: !!contentId && isOpen,
  });

  // Mutations
  const assignMutation = useAssignTagToContents();
  const unassignMutation = useUnassignTagFromContents();

  // Sync assigned tags from query data to local state
  useEffect(() => {
    if (!contentTags) return;

    // Only update if items actually changed (compare IDs)
    const currentIds = assignedTags.map(t => t.id).sort().join(',');
    const newIds = contentTags.map((t: TagType) => t.id).sort().join(',');

    if (currentIds !== newIds) {
      setAssignedTags(contentTags);
    }
  }, [contentTags]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setAssignedTags([]);
    }
  }, [isOpen]);

  // Derive available tags from all tags minus assigned
  const availableTags = (allTags || []).filter(
    (tag) => !assignedTags.some((assigned) => assigned.id === tag.id)
  );

  if (!isOpen) return null;

  // Handle assign with OPTIMISTIC UI UPDATE
  const handleAssignTag = async (tag: TagType) => {
    const contentIds = selectedContent.map((c) => c.id);

    // OPTIMISTIC UPDATE: Add to assigned immediately
    setAssignedTags((prev) => [...prev, tag]);

    try {
      await assignMutation.mutateAsync({
        tagId: tag.id,
        contentIds,
      });
      // Success - local state already updated
    } catch (error) {
      // ROLLBACK on error: Remove from assigned
      setAssignedTags((prev) => prev.filter((t) => t.id !== tag.id));
    }
  };

  // Handle unassign with OPTIMISTIC UI UPDATE
  const handleUnassignTag = async (tag: TagType) => {
    const contentIds = selectedContent.map((c) => c.id);

    // OPTIMISTIC UPDATE: Remove from assigned immediately
    setAssignedTags((prev) => prev.filter((t) => t.id !== tag.id));

    try {
      await unassignMutation.mutateAsync({
        tagId: tag.id,
        contentIds,
      });
      // Success - local state already updated
    } catch (error) {
      // ROLLBACK on error: Add back to assigned
      setAssignedTags((prev) => [...prev, tag]);
    }
  };

  const isOperationPending = assignMutation.isPending || unassignMutation.isPending;
  const isLoading = isLoadingAllTags || isLoadingContentTags;

  // Get content title for header
  const contentTitle = selectedContent.length === 1
    ? selectedContent[0].title
    : `${selectedContent.length} ${t('common.contents', 'contents')}`;

  // Custom header with content info
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        {t('contents.tagModal.title', 'Manage Tags for Content')}
      </h2>
      <div className="flex items-center gap-2 mt-1">
        {selectedContent.length === 1 && selectedContent[0].thumbnail_url ? (
          <img
            src={selectedContent[0].thumbnail_url}
            alt={contentTitle}
            className="w-6 h-6 rounded object-cover"
          />
        ) : (
          <Tag className="w-4 h-4 text-gray-400" />
        )}
        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
          {contentTitle}
        </p>
      </div>
    </div>
  );

  // Footer with close button
  const footer = (
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button variant="secondary" onClick={onClose} disabled={isOperationPending}>
        {t('common.close', 'Close')}
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="5xl"
      customHeader={customHeader}
      footer={footer}
      closeOnBackdropClick={!isOperationPending}
      className="h-[85vh]"
    >
      {/* Two Column Layout */}
      <div className="p-6 min-h-[500px]">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">
            {/* Left Column - Available Tags */}
            <div className="border-r border-gray-200 dark:border-gray-700 pr-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Tag className="w-4 h-4" />
                {t('contents.tagModal.availableTags', 'Available Tags')} ({availableTags.length})
              </h4>

              {availableTags.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Tag className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">
                    {allTags && allTags.length > 0
                      ? t('contents.tagModal.allTagsAssigned', 'All tags are assigned to this content')
                      : t('contents.tagModal.noTagsAvailable', 'No tags available')}
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[calc(85vh-280px)] overflow-y-auto pr-2">
                  {availableTags.map((tag) => (
                    <div
                      key={tag.id}
                      className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-purple-500 dark:hover:border-purple-400 transition-colors cursor-pointer bg-white dark:bg-gray-800"
                      onClick={() => handleAssignTag(tag)}
                    >
                      <div className="flex gap-3 items-center">
                        {/* Tag color */}
                        <div
                          className="w-4 h-4 rounded-full flex-shrink-0"
                          style={{ backgroundColor: tag.color }}
                        />

                        {/* Tag info */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {tag.tag_name}
                          </p>
                          {tag.device_count > 0 && (
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {tag.device_count} {t('common.devices', 'devices')}
                            </p>
                          )}
                        </div>

                        {/* Assign Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAssignTag(tag);
                          }}
                          disabled={assignMutation.isPending}
                          className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 transition-all"
                          title={t('common.assign', 'Assign')}
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
                <Tag className="w-4 h-4 text-purple-600" />
                {t('contents.tagModal.assignedTags', 'Assigned Tags')} ({assignedTags.length})
              </h4>

              {assignedTags.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Tag className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">{t('contents.tagModal.noAssignedTags', 'No tags assigned to this content yet')}</p>
                  <p className="text-xs mt-1">{t('contents.tagModal.clickToAdd', 'Click tags on the left to add')}</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[calc(85vh-280px)] overflow-y-auto pr-2">
                  {assignedTags.map((tag) => (
                    <div
                      key={tag.id}
                      className="group relative border border-purple-200 dark:border-purple-700 rounded-lg p-3 transition-colors bg-purple-50 dark:bg-purple-900/20"
                    >
                      <div className="flex gap-3 items-center">
                        {/* Tag color */}
                        <div
                          className="w-4 h-4 rounded-full flex-shrink-0"
                          style={{ backgroundColor: tag.color }}
                        />

                        {/* Tag info */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {tag.tag_name}
                          </p>
                          {tag.device_count > 0 && (
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {tag.device_count} {t('common.devices', 'devices')}
                            </p>
                          )}
                        </div>

                        {/* Remove Button */}
                        <button
                          onClick={() => handleUnassignTag(tag)}
                          disabled={unassignMutation.isPending}
                          className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all"
                          title={t('common.remove', 'Remove')}
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
    </Modal>
  );
}

export default ContentTagAssignmentModal;
