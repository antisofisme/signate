/**
 * Tag Content Assignment Modal
 *
 * Features:
 * - Two-column layout: Available (left) | Assigned (right)
 * - Click to assign content to tag
 * - Remove button to unassign content from tag
 * - Optimistic UI updates (like DirectContentAssignmentTab)
 *
 * Layout based on DirectContentAssignmentTab pattern
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Image, Film, Music, FileText, Trash2, Loader2, ArrowRight } from 'lucide-react';
import { Modal } from '@/shared/components';
import {
  useAssignTagToContents,
  useUnassignTagFromContents,
} from '../hooks/useTags';
import { useContentList } from '@/features/contents/hooks/useContent';
import type { Content } from '@/features/contents/types/content';

interface TagContentAssignmentModalProps {
  tagId: number;
  tagName: string;
  tagColor?: string;
  isOpen: boolean;
  onClose: () => void;
}

// Content type icon helper
function ContentTypeIcon({ type, className }: { type: string; className?: string }) {
  switch (type) {
    case 'image':
      return <Image className={className} />;
    case 'video':
      return <Film className={className} />;
    case 'audio':
      return <Music className={className} />;
    default:
      return <FileText className={className} />;
  }
}

export default function TagContentAssignmentModal({
  tagId,
  tagName,
  tagColor = '#3B82F6',
  isOpen,
  onClose,
}: TagContentAssignmentModalProps) {
  const { t } = useTranslation();

  // LOCAL STATE for optimistic UI updates (like DirectContentAssignmentTab)
  const [assignedItems, setAssignedItems] = useState<Content[]>([]);

  // Fetch content with this tag (assigned)
  const { data: assignedContentData, isLoading: isLoadingAssigned } = useContentList(
    { tag_ids: [tagId], limit: 1000 },
  );

  // Fetch all content
  const { data: allContentData, isLoading: isLoadingAll } = useContentList(
    { limit: 1000 },
  );

  // Mutations
  const assignMutation = useAssignTagToContents();
  const unassignMutation = useUnassignTagFromContents();

  // All content from query
  const allContent = allContentData?.data || [];

  // Sync assigned items from query data to local state
  // Only update when query data actually changes
  useEffect(() => {
    if (!assignedContentData) return;

    const newItems = assignedContentData.data || [];

    // Only update if items actually changed (compare IDs)
    const currentIds = assignedItems.map(c => c.id).sort().join(',');
    const newIds = newItems.map((c: Content) => c.id).sort().join(',');

    if (currentIds !== newIds) {
      setAssignedItems(newItems);
    }
  }, [assignedContentData]);

  // Derive available content from all content minus assigned
  const availableContent = allContent.filter(
    (content) => !assignedItems.some((assigned) => assigned.id === content.id)
  );

  if (!isOpen) return null;

  // Handle assign with OPTIMISTIC UI UPDATE
  const handleAssignContent = async (contentId: number) => {
    // Find the content to assign
    const contentToAssign = allContent.find((c) => c.id === contentId);
    if (!contentToAssign) return;

    // OPTIMISTIC UPDATE: Add to assigned immediately
    setAssignedItems((prev) => [...prev, contentToAssign]);

    try {
      await assignMutation.mutateAsync({
        tagId,
        contentIds: [contentId],
      });
      // Success - local state already updated
    } catch (error) {
      // ROLLBACK on error: Remove from assigned
      setAssignedItems((prev) => prev.filter((c) => c.id !== contentId));
    }
  };

  // Handle unassign with OPTIMISTIC UI UPDATE
  const handleUnassignContent = async (contentId: number) => {
    // Find the content to remove (for rollback)
    const contentToRemove = assignedItems.find((c) => c.id === contentId);
    if (!contentToRemove) return;

    // OPTIMISTIC UPDATE: Remove from assigned immediately
    setAssignedItems((prev) => prev.filter((c) => c.id !== contentId));

    try {
      await unassignMutation.mutateAsync({
        tagId,
        contentIds: [contentId],
      });
      // Success - local state already updated
    } catch (error) {
      // ROLLBACK on error: Add back to assigned
      setAssignedItems((prev) => [...prev, contentToRemove]);
    }
  };

  const isOperationPending = assignMutation.isPending || unassignMutation.isPending;
  const isLoading = isLoadingAssigned || isLoadingAll;

  // Custom header with tag color indicator
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        {t('tags.contentModal.title', 'Manage Content for Tag')}
      </h2>
      <div className="flex items-center gap-2 mt-1">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: tagColor }}
        />
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {tagName}
        </p>
      </div>
    </div>
  );

  // Footer with close button
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end">
        <button
          onClick={onClose}
          disabled={isOperationPending}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
        >
          {t('tags.contentModal.close', 'Close')}
        </button>
      </div>
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
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-6 h-full">
            {/* Left Column - Available Content */}
            <div className="border-r border-gray-200 dark:border-gray-700 pr-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                {t('tags.contentModal.availableContent', 'Available Content')} ({availableContent.length})
              </h4>

              {availableContent.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <FileText className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">{t('tags.contentModal.allContentAssigned', 'All content is already assigned to this tag')}</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[calc(85vh-280px)] overflow-y-auto pr-2">
                  {availableContent.map((content) => (
                    <div
                      key={content.id}
                      className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer bg-white dark:bg-gray-800"
                      onClick={() => handleAssignContent(content.id)}
                    >
                      <div className="flex gap-3">
                        {/* Thumbnail */}
                        <div className="w-14 h-14 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
                          {content.thumbnail_url ? (
                            <img
                              src={content.thumbnail_url}
                              alt={content.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <ContentTypeIcon type={content.content_type} className="w-6 h-6 text-gray-400" />
                            </div>
                          )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {content.title}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {content.content_type} • {content.duration}s
                          </p>
                        </div>

                        {/* Assign Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAssignContent(content.id);
                          }}
                          disabled={assignMutation.isPending}
                          className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-all self-center"
                          title={t('tags.contentModal.add', 'Add')}
                        >
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Right Column - Assigned Content */}
            <div className="pl-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: tagColor }}
                />
                {t('tags.contentModal.assignedContent', 'Assigned Content')} ({assignedItems.length})
              </h4>

              {assignedItems.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <FileText className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">{t('tags.contentModal.noAssignedContent', 'No content assigned to this tag yet')}</p>
                  <p className="text-xs mt-1">{t('tags.contentModal.clickToAdd', 'Click content on the left to add')}</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[calc(85vh-280px)] overflow-y-auto pr-2">
                  {assignedItems.map((content) => (
                    <div
                      key={content.id}
                      className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 transition-colors bg-white dark:bg-gray-800"
                    >
                      <div className="flex gap-3">
                        {/* Thumbnail */}
                        <div className="w-14 h-14 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
                          {content.thumbnail_url ? (
                            <img
                              src={content.thumbnail_url}
                              alt={content.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <ContentTypeIcon type={content.content_type} className="w-6 h-6 text-gray-400" />
                            </div>
                          )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {content.title}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {content.content_type} • {content.duration}s
                          </p>
                        </div>

                        {/* Remove Button */}
                        <button
                          onClick={() => handleUnassignContent(content.id)}
                          disabled={unassignMutation.isPending}
                          className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all self-center"
                          title={t('tags.contentModal.remove', 'Remove')}
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
