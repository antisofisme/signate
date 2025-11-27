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
import { TagList } from '../components/TagList';
import { TagForm } from '../components/TagForm';
import { ConfirmDialog, AccessDenied, PageSkeleton } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import type { Tag, TagSortBy, CreateTagRequest, UpdateTagRequest } from '../types/tag';

export default function TagsPage() {
  const { t } = useTranslation();
  const [sortBy, setSortBy] = useState<TagSortBy>('newest');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [deletingTag, setDeletingTag] = useState<Tag | null>(null);

  // Permission checks
  const { hasPermission: canRead, isLoading: isLoadingReadPermission } = useCanPerformAction('tags', 'view');
  const { hasPermission: canCreate } = useCanPerformAction('tags', 'create');
  const { hasPermission: canUpdate } = useCanPerformAction('tags', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('tags', 'delete');

  // React Query hooks
  const { data: tags = [], isLoading } = useTags({ sort_by: sortBy });
  const createTagMutation = useCreateTag();
  const updateTagMutation = useUpdateTag();
  const deleteTagMutation = useDeleteTag();

  // Show loading while checking permissions
  if (isLoadingReadPermission) {
    return <PageSkeleton />;
  }

  // Check read permission
  if (!canRead) {
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
      await deleteTagMutation.mutateAsync({ id: deletingTag.id });
      setDeletingTag(null);
    } catch (error) {
      // Error handled by mutation
    }
  };

  return (
    <>
      {/* Toolbar */}
      <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1 w-full sm:w-auto">
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

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as TagSortBy)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="newest">{t('tags.sortNewest')}</option>
            <option value="oldest">{t('tags.sortOldest')}</option>
            <option value="name_asc">{t('tags.sortNameAsc')}</option>
            <option value="name_desc">{t('tags.sortNameDesc')}</option>
          </select>
        </div>

        {/* Create Button */}
        {canCreate && (
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            {t('tags.createTag')}
          </button>
        )}
      </div>

      {/* Content */}
      <div className="space-y-6">
        <TagList
          tags={filteredTags}
          isLoading={isLoading}
          searchQuery={searchQuery}
          onEdit={canUpdate ? setEditingTag : undefined}
          onDelete={canDelete ? setDeletingTag : undefined}
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
    </>
  );
}
