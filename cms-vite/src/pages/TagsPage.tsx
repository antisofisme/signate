/**
 * Tags Management Page
 * Complete CRUD interface for managing tags
 */

import { useState } from 'react';
import { Plus, Pencil, Trash2, Search, Loader2, Tag as TagIcon } from 'lucide-react';
import { useTags, useCreateTag, useUpdateTag, useDeleteTag } from '@/features/tags/hooks/useTags';
import { TagBadge } from '@/features/tags/components/TagBadge';
import type { Tag, TagSortBy, CreateTagRequest, UpdateTagRequest } from '@/features/tags/types/tag';

const TAG_COLORS = [
  { label: 'Blue', value: '#3B82F6' },
  { label: 'Red', value: '#EF4444' },
  { label: 'Green', value: '#10B981' },
  { label: 'Yellow', value: '#F59E0B' },
  { label: 'Purple', value: '#8B5CF6' },
  { label: 'Pink', value: '#EC4899' },
  { label: 'Gray', value: '#6B7280' },
];

// Delete Confirmation Modal
interface DeleteConfirmModalProps {
  isOpen: boolean;
  tag: Tag | null;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function DeleteConfirmModal({
  isOpen,
  tag,
  onClose,
  onConfirm,
  isLoading,
}: DeleteConfirmModalProps) {
  if (!isOpen || !tag) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Hapus Tag?
        </h3>
        <p className="text-gray-700 dark:text-gray-300 mb-2">
          Apakah Anda yakin ingin menghapus tag:
        </p>
        <p className="text-gray-900 dark:text-white font-semibold mb-2">
          {tag.tag_name}
        </p>
        <p className="text-red-600 dark:text-red-400 text-sm mb-6">
          Tag yang sedang digunakan tidak dapat dihapus.
        </p>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
          >
            Batal
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Menghapus...
              </>
            ) : (
              'Hapus'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// Tag Modal (Create/Edit)
interface TagModalProps {
  tag?: Tag;
  onClose: () => void;
  onSubmit: (data: any) => void;
  isLoading: boolean;
}

function TagModal({ tag, onClose, onSubmit, isLoading }: TagModalProps) {
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
          {tag ? 'Edit Tag' : 'Buat Tag Baru'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Nama Tag *
            </label>
            <input
              type="text"
              value={formData.tag_name}
              onChange={(e) => setFormData({ ...formData, tag_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="e.g., Urgent, Lobby, Promo"
              required
            />
          </div>

          {/* Color */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Warna
            </label>
            <select
              value={formData.color}
              onChange={(e) => setFormData({ ...formData, color: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {TAG_COLORS.map((color) => (
                <option key={color.value} value={color.value}>
                  {color.label}
                </option>
              ))}
            </select>
            <div className="mt-2 flex items-center gap-2">
              <div
                className="w-8 h-8 rounded border-2"
                style={{ backgroundColor: formData.color }}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">Preview</span>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Deskripsi
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Deskripsi opsional"
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
              Batal
            </button>
            <button
              type="submit"
              disabled={isLoading || !formData.tag_name.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {tag ? 'Updating...' : 'Creating...'}
                </>
              ) : (
                <>{tag ? 'Update' : 'Buat'}</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function TagsPage() {
  const [sortBy, setSortBy] = useState<TagSortBy>('newest');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [deletingTag, setDeletingTag] = useState<Tag | null>(null);

  // React Query hooks
  const { data: tags = [], isLoading, error } = useTags({ sort_by: sortBy });
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

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Tag
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Deskripsi
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Dibuat
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Aksi
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                  Loading...
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-red-600 dark:text-red-400">
                  Error loading tags
                </td>
              </tr>
            ) : filteredTags.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                  <TagIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  {searchQuery ? 'Tidak ada tag yang cocok' : 'Belum ada tag'}
                </td>
              </tr>
            ) : (
              filteredTags.map((tag) => (
                <tr key={tag.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <TagBadge tag={tag} />
                  </td>
                  <td className="px-6 py-4 text-gray-700 dark:text-gray-300">
                    {tag.description || '-'}
                  </td>
                  <td className="px-6 py-4 text-gray-600 dark:text-gray-400">
                    {new Date(tag.created_at).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setEditingTag(tag)}
                        className="p-1.5 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
                        title="Edit"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setDeletingTag(tag)}
                        className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {isCreateModalOpen && (
        <TagModal
          onClose={() => setIsCreateModalOpen(false)}
          onSubmit={handleCreateSubmit}
          isLoading={createTagMutation.isPending}
        />
      )}

      {editingTag && (
        <TagModal
          tag={editingTag}
          onClose={() => setEditingTag(null)}
          onSubmit={handleUpdateSubmit}
          isLoading={updateTagMutation.isPending}
        />
      )}

      <DeleteConfirmModal
        isOpen={!!deletingTag}
        tag={deletingTag}
        onClose={() => setDeletingTag(null)}
        onConfirm={handleDeleteConfirm}
        isLoading={deleteTagMutation.isPending}
      />
    </div>
  );
}
