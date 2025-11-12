/**
 * Tags Page
 *
 * LAYER 1: PRESENTATION
 * Main page for tag management - orchestration only
 */

import { useState } from 'react';
import { Plus, Search } from 'lucide-react';
import { useTags, useCreateTag, useUpdateTag, useDeleteTag } from '../hooks/useTags';
import { TagList } from '../components/TagList';
import { TagForm } from '../components/TagForm';
import { DeleteConfirmModal } from '@/shared/components/DeleteConfirmModal';
import type { Tag, TagSortBy, CreateTagRequest, UpdateTagRequest } from '../types/tag';

export default function TagsPage() {
  const [sortBy, setSortBy] = useState<TagSortBy>('newest');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [deletingTag, setDeletingTag] = useState<Tag | null>(null);

  // React Query hooks
  const { data: tags = [], isLoading } = useTags({ sort_by: sortBy });
  const createTagMutation = useCreateTag();
  const updateTagMutation = useUpdateTag();
  const deleteTagMutation = useDeleteTag();

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
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Tags</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Kelola tags untuk mengorganisir devices dan content
        </p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1 w-full sm:w-auto">
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="search"
              placeholder="Cari tags..."
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
            <option value="newest">Terbaru</option>
            <option value="oldest">Terlama</option>
            <option value="name_asc">Nama A-Z</option>
            <option value="name_desc">Nama Z-A</option>
          </select>
        </div>

        {/* Create Button */}
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Buat Tag
        </button>
      </div>

      {/* Tag List */}
      <TagList
        tags={filteredTags}
        isLoading={isLoading}
        searchQuery={searchQuery}
        onEdit={setEditingTag}
        onDelete={setDeletingTag}
      />

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
        <DeleteConfirmModal
          isOpen={!!deletingTag}
          title="Hapus Tag?"
          message="Apakah Anda yakin ingin menghapus tag:"
          itemName={deletingTag.tag_name}
          onClose={() => setDeletingTag(null)}
          onConfirm={handleDeleteConfirm}
          isLoading={deleteTagMutation.isPending}
        />
      )}
    </div>
  );
}
