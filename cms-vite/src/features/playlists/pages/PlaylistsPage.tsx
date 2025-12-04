/**
 * Playlists Page
 *
 * LAYER 1: PRESENTATION
 * Main page for playlist management - orchestration only
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus } from 'lucide-react';
import {
  usePlaylistList,
  useCreatePlaylist,
  useUpdatePlaylist,
  useDeletePlaylist,
  useDuplicatePlaylist,
} from '../hooks/usePlaylist';
import { useTableSort } from '@/shared/hooks';
import { PlaylistList } from '../components/PlaylistList';
import { PlaylistForm } from '../components/PlaylistForm';
import {
  ConfirmDialog,
  AccessDenied,
  ErrorDisplay,
  PageSkeleton,
  Button,
  PageToolbar,
  PageStats,
  FilterButtonGroup,
} from '@/shared/components';
import PlaylistManagementModal from '../components/PlaylistManagementModal';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import type { Playlist, CreatePlaylistRequest, UpdatePlaylistRequest } from '../types/playlist';

// Filter options for status
const FILTER_OPTIONS = [
  { id: 'all', label: 'Semua' },
  { id: 'active', label: 'Aktif' },
  { id: 'inactive', label: 'Nonaktif' },
];

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
  const [activeFilter, setActiveFilter] = useState('all');
  const [managementPlaylist, setManagementPlaylist] = useState<Playlist | null>(null);

  // Sorting - URL state persistence
  const { sortConfig, onSortChange, sortParams } = useTableSort({
    defaultSort: { key: 'name', direction: 'asc' },
  });

  // Convert filter to API param
  const filterActive = activeFilter === 'all' ? undefined : activeFilter === 'active';

  // Hooks with sorting
  const { data: playlistsData, isLoading, error, refetch } = usePlaylistList({
    is_active: filterActive,
    ...sortParams,
  });
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

  // Calculate stats
  const playlists = playlistsData?.items || [];
  const activeCount = playlists.filter(p => p.is_active).length;
  const inactiveCount = playlists.filter(p => !p.is_active).length;

  return (
    <>
      {/* Toolbar: Filter kiri, Buttons kanan */}
      <PageToolbar>
        <PageToolbar.Left>
          <FilterButtonGroup
            options={FILTER_OPTIONS}
            activeFilter={activeFilter}
            onChange={setActiveFilter}
          />
        </PageToolbar.Left>
        <PageToolbar.Right>
          {canCreate && (
            <Button
              variant="primary"
              onClick={() => setShowCreateModal(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              {t('playlists.createPlaylist')}
            </Button>
          )}
        </PageToolbar.Right>
      </PageToolbar>

      {/* Stats: langsung di atas tabel */}
      <PageStats
        total={playlistsData?.total || 0}
        totalLabel="playlists"
        stats={[
          { label: 'active', value: activeCount, color: 'text-green-600 dark:text-green-400' },
          { label: 'inactive', value: inactiveCount, color: 'text-gray-500' },
        ]}
      />

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
            playlists={playlists}
            isLoading={isLoading}
            onEdit={canUpdate ? setEditingPlaylist : undefined}
            onDelete={canDelete ? setDeletingPlaylist : undefined}
            onDuplicate={canCreate ? handleDuplicate : undefined}
            onManage={setManagementPlaylist}
            onCreateNew={canCreate ? () => setShowCreateModal(true) : undefined}
            sortConfig={sortConfig}
            onSortChange={onSortChange}
          />
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

      {/* Playlist Management Modal */}
      {managementPlaylist && (
        <PlaylistManagementModal
          playlistId={managementPlaylist.id}
          playlistName={managementPlaylist.name}
          isOpen={true}
          onClose={() => setManagementPlaylist(null)}
        />
      )}
    </>
  );
}
