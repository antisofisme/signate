/**
 * Playlists Page
 *
 * LAYER 1: PRESENTATION
 * Main page for playlist management - orchestration only
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  usePlaylistList,
  useCreatePlaylist,
  useUpdatePlaylist,
  useDeletePlaylist,
  useDuplicatePlaylist,
} from '../hooks/usePlaylist';
import { PlaylistList } from '../components/PlaylistList';
import { PlaylistForm } from '../components/PlaylistForm';
import { ConfirmDialog, AccessDenied, ErrorDisplay, PageSkeleton } from '@/shared/components';
import PlaylistContentModal from '../components/PlaylistContentModal';
import PlaylistAssignmentModal from '../components/PlaylistAssignmentModal';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import type { Playlist, CreatePlaylistRequest, UpdatePlaylistRequest } from '../types/playlist';

export default function PlaylistsPage() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canRead, isLoading: loadingReadPerm } = useCanPerformAction('playlists', 'read');
  const { hasPermission: canCreate } = useCanPerformAction('playlists', 'create');
  const { hasPermission: canUpdate } = useCanPerformAction('playlists', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('playlists', 'delete');

  // Show loading state while checking permissions
  if (loadingReadPerm) {
    return <PageSkeleton />;
  }

  // Show access denied if no read permission
  if (!canRead) {
    return <AccessDenied />;
  }
  // State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingPlaylist, setEditingPlaylist] = useState<Playlist | null>(null);
  const [deletingPlaylist, setDeletingPlaylist] = useState<Playlist | null>(null);
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [contentModalPlaylist, setContentModalPlaylist] = useState<Playlist | null>(null);
  const [assignmentModalPlaylist, setAssignmentModalPlaylist] = useState<Playlist | null>(null);

  // Hooks
  const { data: playlistsData, isLoading, error, refetch } = usePlaylistList({ is_active: filterActive });
  const createMutation = useCreatePlaylist();
  const updateMutation = useUpdatePlaylist();
  const deleteMutation = useDeletePlaylist();
  const duplicateMutation = useDuplicatePlaylist();

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

  const handleDuplicate = (playlist: Playlist) => {
    duplicateMutation.mutate({ id: playlist.id });
  };

  return (
    <>
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

        {canCreate && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <span>+</span>
            {t('playlists.createPlaylist')}
          </button>
        )}
      </div>

      {/* Content */}
      <div className="space-y-6">
        {/* Error State */}
        {error && (
          <ErrorDisplay
            error={error}
            onRetry={refetch}
            title={t('playlists.messages.loadError')}
          />
        )}

        {/* Playlists List */}
        {!error && (
          <PlaylistList
            playlists={playlistsData?.items || []}
            isLoading={isLoading}
            onEdit={canUpdate ? setEditingPlaylist : undefined}
            onDelete={canDelete ? setDeletingPlaylist : undefined}
            onDuplicate={canCreate ? handleDuplicate : undefined}
            onManageContent={setContentModalPlaylist}
            onManageAssignments={setAssignmentModalPlaylist}
            onCreateNew={canCreate ? () => setShowCreateModal(true) : undefined}
          />
        )}

        {/* Total Count */}
        {!error && playlistsData && playlistsData.total > 0 && (
          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            {t('playlists.messages.totalPlaylists', { count: playlistsData.total })}
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreateModal && (
        <PlaylistForm
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreate}
          isLoading={createMutation.isPending}
        />
      )}

      {editingPlaylist && (
        <PlaylistForm
          playlist={editingPlaylist}
          onClose={() => setEditingPlaylist(null)}
          onSubmit={handleUpdate}
          isLoading={updateMutation.isPending}
        />
      )}

      {deletingPlaylist && (
        <ConfirmDialog
          open={true}
          onOpenChange={(open) => !open && setDeletingPlaylist(null)}
          title={t('playlists.deletePlaylist')}
          description={t('playlists.messages.confirmDelete', { name: deletingPlaylist.name })}
          variant="danger"
          confirmLabel={t('common.delete')}
          cancelLabel={t('common.cancel')}
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
    </>
  );
}
