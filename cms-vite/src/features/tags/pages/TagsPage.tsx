/**
 * Tags Page
 *
 * LAYER 1: PRESENTATION
 * Main page for tag management - orchestration only
 */

import { useState } from 'react';
import { Plus, Search } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useTags, useCreateTag, useUpdateTag, useDeleteTag } from '../hooks/useTags';
import { useTableSort } from '@/shared/hooks';
import { TagList } from '../components/TagList';
import { TagForm } from '../components/TagForm';
import TagManagementModal from '../components/TagManagementModal';
import {
  ConfirmDialog,
  AccessDenied,
  PageSkeleton,
  Button,
  PageToolbar,
  PageStats,
} from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import type { Tag, CreateTagRequest, UpdateTagRequest } from '../types/tag';

export default function TagsPage() {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [deletingTag, setDeletingTag] = useState<Tag | null>(null);
  const [contentManagementTag, setContentManagementTag] = useState<Tag | null>(null);

  // Sorting - URL state persistence
  const { sortConfig, onSortChange, sortParams } = useTableSort({
    defaultSort: { key: 'created_at', direction: 'desc' },
  });

  // Permission checks
  const { hasPermission: canView, isLoading: isCheckingPermission } = useCanPerformAction('tags', 'read');
  const { hasPermission: canCreate } = useCanPerformAction('tags', 'create');
  const { hasPermission: canUpdate } = useCanPerformAction('tags', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('tags', 'delete');

  // React Query hooks with sorting
  const { data: tags = [], isLoading } = useTags(sortParams);
  const createTagMutation = useCreateTag();
  const updateTagMutation = useUpdateTag();
  const deleteTagMutation = useDeleteTag();

  // Show loading while checking permissions
  if (isCheckingPermission) {
    return <PageSkeleton />;
  }

  // Check read permission
  if (!canView) {
    return <AccessDenied />;
  }

  // Filter tags by search query
  const filteredTags = tags.filter((tag) =>
    tag.tag_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Handle create
  const handleCreateSubmit = async (data: CreateTagRequest) => {
    try {
      await createTagMutation.mutateAsync(data);
      setIsCreateModalOpen(false);
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle update
  const handleUpdateSubmit = async (data: UpdateTagRequest) => {
    if (!editingTag) return;
    try {
      await updateTagMutation.mutateAsync({ id: editingTag.id, data });
      setEditingTag(null);
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle delete
  const handleDeleteConfirm = async () => {
    if (!deletingTag) return;
    try {
      // Always use force=true since backend now handles cleanup of all relationships
      await deleteTagMutation.mutateAsync({ id: deletingTag.id, force: true });
      setDeletingTag(null);
    } catch (error) {
      // Error handled by mutation
    }
  };

  return (
    <>
      {/* Toolbar: Search kiri, Buttons kanan */}
      <PageToolbar>
        <PageToolbar.Left>
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="search"
              placeholder={t('tags.searchPlaceholder')}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </PageToolbar.Left>
        <PageToolbar.Right>
          {canCreate && (
            <Button
              variant="primary"
              onClick={() => setIsCreateModalOpen(true)}
              leftIcon={<Plus className="h-4 w-4" />}
            >
              {t('tags.createTag')}
            </Button>
          )}
        </PageToolbar.Right>
      </PageToolbar>

      {/* Stats: langsung di atas list */}
      <PageStats
        total={tags.length}
        totalLabel="tags"
      />

      {/* Content */}
      <div className="space-y-6">
        <TagList
          tags={filteredTags}
          isLoading={isLoading}
          searchQuery={searchQuery}
          onEdit={canUpdate ? setEditingTag : undefined}
          onDelete={canDelete ? setDeletingTag : undefined}
          onManageContent={setContentManagementTag}
          sortConfig={sortConfig}
          onSortChange={onSortChange}
        />
      </div>

      {/* Modals */}
      {isCreateModalOpen && (
        <TagForm
          onClose={() => setIsCreateModalOpen(false)}
          onSubmit={handleCreateSubmit}
          isLoading={createTagMutation.isPending}
        />
      )}

      {editingTag && (
        <TagForm
          tag={editingTag}
          onClose={() => setEditingTag(null)}
          onSubmit={handleUpdateSubmit}
          isLoading={updateTagMutation.isPending}
        />
      )}

      {deletingTag && (
        <ConfirmDialog
          open={!!deletingTag}
          onOpenChange={(open) => !open && setDeletingTag(null)}
          title={t('tags.deleteTitle')}
          description={`${t('tags.deleteMessage')} "${deletingTag.tag_name}"?`}
          variant="danger"
          confirmLabel={t('tags.delete')}
          cancelLabel={t('tags.cancel')}
          onConfirm={handleDeleteConfirm}
          isLoading={deleteTagMutation.isPending}
        />
      )}

      {contentManagementTag && (
        <TagManagementModal
          tagId={contentManagementTag.id}
          tagName={contentManagementTag.tag_name}
          tagColor={contentManagementTag.color}
          isOpen={!!contentManagementTag}
          onClose={() => setContentManagementTag(null)}
        />
      )}
    </>
  );
}
