/**
 * Playlists Management Page
 * Complete interface for managing playlists
 */

import { useState } from 'react';
import { Plus, Pencil, Trash2, Clock, FileText, Loader2, List, Monitor } from 'lucide-react';
import {
  usePlaylistList,
  useCreatePlaylist,
  useUpdatePlaylist,
  useDeletePlaylist,
} from '@/features/playlists/hooks/usePlaylist';
import type { Playlist, CreatePlaylistRequest, UpdatePlaylistRequest } from '@/features/playlists/types/playlist';
import PlaylistContentModal from '@/features/playlists/components/PlaylistContentModal';
import PlaylistAssignmentModal from '@/features/playlists/components/PlaylistAssignmentModal';

// Delete Confirmation Modal
interface DeleteConfirmModalProps {
  isOpen: boolean;
  playlist: Playlist | null;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function DeleteConfirmModal({
  isOpen,
  playlist,
  onClose,
  onConfirm,
  isLoading,
}: DeleteConfirmModalProps) {
  if (!isOpen || !playlist) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Hapus Playlist?
        </h3>
        <p className="text-gray-700 dark:text-gray-300 mb-2">
          Apakah Anda yakin ingin menghapus playlist:
        </p>
        <p className="text-gray-900 dark:text-white font-semibold mb-2">
          {playlist.name}
        </p>
        {playlist.content_count > 0 && (
          <p className="text-amber-600 dark:text-amber-400 text-sm mb-4">
            Playlist ini berisi {playlist.content_count} konten.
          </p>
        )}
        <p className="text-red-600 dark:text-red-400 text-sm mb-6">
          Tindakan ini tidak dapat dibatalkan.
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

// Playlist Form Modal (Create/Edit)
interface PlaylistFormModalProps {
  playlist?: Playlist;
  onClose: () => void;
  onSubmit: (data: CreatePlaylistRequest | UpdatePlaylistRequest) => void;
  isLoading: boolean;
}

function PlaylistFormModal({ playlist, onClose, onSubmit, isLoading }: PlaylistFormModalProps) {
  const [formData, setFormData] = useState({
    name: playlist?.name || '',
    description: playlist?.description || '',
    is_active: playlist?.is_active ?? true,
    priority: playlist?.priority || 0,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            {playlist ? 'Edit Playlist' : 'Buat Playlist Baru'}
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Nama Playlist <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Nama playlist"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Deskripsi
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Deskripsi playlist (opsional)"
              />
            </div>

            {/* Priority */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Prioritas
              </label>
              <input
                type="number"
                min="0"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="0"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Prioritas lebih tinggi akan ditampilkan lebih dulu (0 = terendah)
              </p>
            </div>

            {/* Active Status */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="is_active" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Aktif
              </label>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
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
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Menyimpan...
                  </>
                ) : (
                  <>
                    {playlist ? 'Update' : 'Buat Playlist'}
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

// Main Playlists Page
export default function PlaylistsPage() {
  // State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingPlaylist, setEditingPlaylist] = useState<Playlist | null>(null);
  const [deletingPlaylist, setDeletingPlaylist] = useState<Playlist | null>(null);
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [contentModalPlaylist, setContentModalPlaylist] = useState<Playlist | null>(null);
  const [assignmentModalPlaylist, setAssignmentModalPlaylist] = useState<Playlist | null>(null);

  // Hooks
  const { data: playlistsData, isLoading } = usePlaylistList({ is_active: filterActive });
  const createMutation = useCreatePlaylist();
  const updateMutation = useUpdatePlaylist();
  const deleteMutation = useDeletePlaylist();

  // Handlers
  const handleCreate = (data: CreatePlaylistRequest) => {
    createMutation.mutate(data, {
      onSuccess: () => {
        setShowCreateModal(false);
      },
    });
  };

  const handleUpdate = (data: UpdatePlaylistRequest) => {
    if (!editingPlaylist) return;
    updateMutation.mutate(
      { id: editingPlaylist.id, data },
      {
        onSuccess: () => {
          setEditingPlaylist(null);
        },
      }
    );
  };

  const handleDelete = () => {
    if (!deletingPlaylist) return;
    deleteMutation.mutate(deletingPlaylist.id, {
      onSuccess: () => {
        setDeletingPlaylist(null);
      },
    });
  };

  const formatDuration = (seconds: number): string => {
    if (seconds === 0) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    const parts = [];
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    if (secs > 0) parts.push(`${secs}s`);

    return parts.join(' ');
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Playlist Management
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Kelola playlist konten untuk perangkat Anda
        </p>
      </div>

      {/* Actions & Filters */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setFilterActive(undefined)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              filterActive === undefined
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            Semua
          </button>
          <button
            onClick={() => setFilterActive(true)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              filterActive === true
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            Aktif
          </button>
          <button
            onClick={() => setFilterActive(false)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              filterActive === false
                ? 'bg-gray-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            Nonaktif
          </button>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Buat Playlist
        </button>
      </div>

      {/* Playlists Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : !playlistsData || playlistsData.items.length === 0 ? (
          <div className="text-center py-12">
            <List className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Belum ada playlist
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Mulai dengan membuat playlist pertama Anda
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 inline-flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Buat Playlist
            </button>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Nama Playlist
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Prioritas
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Konten
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Durasi
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Aksi
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {playlistsData.items.map((playlist) => (
                <tr key={playlist.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {playlist.name}
                      </div>
                      {playlist.description && (
                        <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          {playlist.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        playlist.is_active
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {playlist.is_active ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      {playlist.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center text-sm text-gray-900 dark:text-white">
                      <FileText className="w-4 h-4 mr-2 text-gray-400" />
                      {playlist.content_count} item
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center text-sm text-gray-900 dark:text-white">
                      <Clock className="w-4 h-4 mr-2 text-gray-400" />
                      {formatDuration(playlist.total_duration)}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setContentModalPlaylist(playlist)}
                        className="p-2 text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg"
                        title="Manage Content"
                      >
                        <List className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setAssignmentModalPlaylist(playlist)}
                        className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg"
                        title="Manage Assignments"
                      >
                        <Monitor className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setEditingPlaylist(playlist)}
                        className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"
                        title="Edit"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setDeletingPlaylist(playlist)}
                        className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                        title="Hapus"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Total Count */}
      {playlistsData && playlistsData.total > 0 && (
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          Total: {playlistsData.total} playlist
        </div>
      )}

      {/* Modals */}
      {showCreateModal && (
        <PlaylistFormModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreate}
          isLoading={createMutation.isPending}
        />
      )}

      {editingPlaylist && (
        <PlaylistFormModal
          playlist={editingPlaylist}
          onClose={() => setEditingPlaylist(null)}
          onSubmit={handleUpdate}
          isLoading={updateMutation.isPending}
        />
      )}

      {deletingPlaylist && (
        <DeleteConfirmModal
          isOpen={true}
          playlist={deletingPlaylist}
          onClose={() => setDeletingPlaylist(null)}
          onConfirm={handleDelete}
          isLoading={deleteMutation.isPending}
        />
      )}

      {/* Content Management Modal */}
      {contentModalPlaylist && (
        <PlaylistContentModal
          playlistId={contentModalPlaylist.id}
          playlistName={contentModalPlaylist.name}
          isOpen={true}
          onClose={() => setContentModalPlaylist(null)}
        />
      )}

      {/* Assignment Management Modal */}
      {assignmentModalPlaylist && (
        <PlaylistAssignmentModal
          playlistId={assignmentModalPlaylist.id}
          playlistName={assignmentModalPlaylist.name}
          isOpen={true}
          onClose={() => setAssignmentModalPlaylist(null)}
        />
      )}
    </div>
  );
}
