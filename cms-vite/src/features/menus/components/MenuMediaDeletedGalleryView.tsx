/**
 * Menu Media Deleted Gallery View Component
 * Masonry layout for soft-deleted menu media (Recycle Bin)
 * Supports restore and permanent delete operations
 */

import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Search,
  SortAsc,
  SortDesc,
  Trash2,
  RotateCcw,
  Eye,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button, EmptyState, ErrorDisplay, ConfirmDialog } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import {
  useDeletedMenuMediaList,
  useRestoreMenuMedia,
  usePermanentDeleteMenuMedia,
  useBulkPermanentDeleteMenuMedia,
} from '../hooks/useMenuMedia';
import type { MenuMedia } from '../types/menu';
import { MenuMediaPreviewModal } from './MenuMediaPreviewModal';

// Sort options
type SortOption = 'newest' | 'oldest' | 'name_asc' | 'name_desc' | 'size_desc' | 'size_asc';

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'newest', label: 'Recently Deleted' },
  { value: 'oldest', label: 'Oldest First' },
  { value: 'name_asc', label: 'Name (A-Z)' },
  { value: 'name_desc', label: 'Name (Z-A)' },
  { value: 'size_desc', label: 'Largest First' },
  { value: 'size_asc', label: 'Smallest First' },
];

// Format file size
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Format date
const formatDate = (dateString?: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

export function MenuMediaDeletedGalleryView() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canDelete } = useCanPerformAction('menus', 'delete');

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [mediaToRestore, setMediaToRestore] = useState<MenuMedia | null>(null);
  const [mediaToDelete, setMediaToDelete] = useState<MenuMedia | null>(null);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);
  const [previewMedia, setPreviewMedia] = useState<MenuMedia | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  // Fetch deleted media
  const { data: mediaData, isLoading, error } = useDeletedMenuMediaList({
    limit: 100,
  });
  const restoreMutation = useRestoreMenuMedia();
  const permanentDeleteMutation = usePermanentDeleteMenuMedia();
  const bulkPermanentDeleteMutation = useBulkPermanentDeleteMenuMedia();

  // Filter and sort media client-side
  const filteredAndSortedMedia = useMemo(() => {
    if (!mediaData?.items) return [];

    let result = [...mediaData.items];

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (media) =>
          media.original_filename.toLowerCase().includes(query) ||
          media.title?.toLowerCase().includes(query)
      );
    }

    // Sort
    switch (sortBy) {
      case 'newest':
        result.sort((a, b) => new Date(b.deleted_at || 0).getTime() - new Date(a.deleted_at || 0).getTime());
        break;
      case 'oldest':
        result.sort((a, b) => new Date(a.deleted_at || 0).getTime() - new Date(b.deleted_at || 0).getTime());
        break;
      case 'name_asc':
        result.sort((a, b) => (a.title || a.original_filename).localeCompare(b.title || b.original_filename));
        break;
      case 'name_desc':
        result.sort((a, b) => (b.title || b.original_filename).localeCompare(a.title || a.original_filename));
        break;
      case 'size_desc':
        result.sort((a, b) => b.file_size - a.file_size);
        break;
      case 'size_asc':
        result.sort((a, b) => a.file_size - b.file_size);
        break;
    }

    return result;
  }, [mediaData?.items, searchQuery, sortBy]);

  // Selection handlers
  const toggleSelection = (id: number) => {
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  // Handlers
  const handleRestore = async () => {
    if (mediaToRestore) {
      await restoreMutation.mutateAsync(mediaToRestore.id);
      setMediaToRestore(null);
    }
  };

  const handlePermanentDelete = async () => {
    if (mediaToDelete) {
      await permanentDeleteMutation.mutateAsync(mediaToDelete.id);
      setMediaToDelete(null);
    }
  };

  const handleBulkPermanentDelete = async () => {
    if (selectedIds.size === 0) {
      toast.error(t('menus.media.messages.selectAtLeastOne'));
      return;
    }
    await bulkPermanentDeleteMutation.mutateAsync(Array.from(selectedIds));
    setSelectedIds(new Set());
    setShowBulkDeleteConfirm(false);
  };

  const handlePreview = (media: MenuMedia) => {
    setPreviewMedia(media);
    setShowPreview(true);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-280px)] min-h-[500px]">
      {/* Toolbar */}
      <div className="flex items-center gap-4 mb-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder={t('menus.media.gallery.searchPlaceholder', 'Search deleted images...')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
          />
        </div>

        {/* Sort Dropdown */}
        <div className="flex items-center gap-2">
          {sortBy.includes('asc') ? (
            <SortAsc className="w-4 h-4 text-gray-500" />
          ) : (
            <SortDesc className="w-4 h-4 text-gray-500" />
          )}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-red-500"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Bulk Actions Toolbar */}
      {selectedIds.size > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4 flex items-center justify-between">
          <p className="text-sm font-medium text-red-900 dark:text-red-300">
            {t('menus.media.selection.itemsSelected', { count: selectedIds.size })}
          </p>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={clearSelection}
            >
              {t('common.cancel', 'Clear')}
            </Button>
            {canDelete && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => setShowBulkDeleteConfirm(true)}
                leftIcon={<Trash2 className="w-4 h-4" />}
              >
                {t('menus.media.actions.permanentlyDelete')}
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        {filteredAndSortedMedia.length} {t('menus.media.gallery.deletedImages', 'deleted images')}
        {searchQuery && ` (${t('menus.media.gallery.filtered', 'filtered')})`}
      </div>

      {/* Gallery Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Loading */}
        {isLoading && (
          <div className="deleted-masonry-grid animate-pulse">
            {Array.from({ length: 12 }).map((_, i) => (
              <div
                key={i}
                className="deleted-masonry-item bg-gray-200 dark:bg-gray-700 rounded-lg"
                style={{ height: `${150 + Math.random() * 100}px` }}
              />
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <ErrorDisplay error={error} onRetry={() => window.location.reload()} />
        )}

        {/* Empty State */}
        {!isLoading && !error && filteredAndSortedMedia.length === 0 && (
          <EmptyState
            icon={Trash2}
            title={t('menus.media.empty.recycleBinTitle', 'Recycle bin is empty')}
            description={
              searchQuery
                ? t('menus.media.gallery.noSearchResults', 'Try adjusting your search')
                : t('menus.media.empty.recycleBinDescription', 'Deleted images will appear here')
            }
          />
        )}

        {/* Masonry Grid */}
        {!isLoading && !error && filteredAndSortedMedia.length > 0 && (
          <div className="deleted-masonry-grid">
            {filteredAndSortedMedia.map((media) => (
              <div
                key={media.id}
                className={`deleted-masonry-item relative group rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 border-2 transition-all ${
                  selectedIds.has(media.id)
                    ? 'border-red-500 ring-2 ring-red-500/30'
                    : 'border-transparent hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                {/* Selection Checkbox */}
                <div
                  className={`absolute top-2 left-2 z-10 transition-opacity ${
                    selectedIds.size > 0 || selectedIds.has(media.id) ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.has(media.id)}
                    onChange={() => toggleSelection(media.id)}
                    className="w-5 h-5 text-red-600 bg-white border-gray-300 rounded focus:ring-red-500 cursor-pointer"
                  />
                </div>

                {/* Image with Deleted Overlay */}
                <div className="relative">
                  <img
                    src={media.url}
                    alt={media.alt_text || media.original_filename}
                    className="w-full h-auto object-cover opacity-60"
                    loading="lazy"
                  />
                  {/* Trash Icon Overlay */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="bg-red-500/20 rounded-full p-3">
                      <Trash2 className="w-8 h-8 text-red-500" />
                    </div>
                  </div>
                </div>

                {/* Info Overlay */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                  <p className="text-white text-sm font-medium truncate line-through">
                    {media.title || media.original_filename}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-gray-300 mt-1">
                    <span>{formatFileSize(media.file_size)}</span>
                    <span>•</span>
                    <span className="text-red-300">{formatDate(media.deleted_at)}</span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    variant="icon"
                    size="sm"
                    onClick={() => handlePreview(media)}
                    className="!bg-white/90 hover:!bg-white !text-gray-700"
                    title={t('menus.media.actions.preview')}
                  >
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="icon"
                    size="sm"
                    onClick={() => setMediaToRestore(media)}
                    className="!bg-green-500/90 hover:!bg-green-500 !text-white"
                    title={t('menus.media.actions.restore')}
                  >
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                  {canDelete && (
                    <Button
                      variant="icon"
                      size="sm"
                      onClick={() => setMediaToDelete(media)}
                      className="!bg-red-500/90 hover:!bg-red-500 !text-white"
                      title={t('menus.media.actions.permanentlyDelete')}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Restore Confirmation */}
      <ConfirmDialog
        open={!!mediaToRestore}
        onOpenChange={(open) => !open && setMediaToRestore(null)}
        title={t('menus.media.dialogs.restoreTitle')}
        description={t('menus.media.dialogs.restoreMessage', { name: mediaToRestore?.original_filename })}
        variant="info"
        confirmLabel={t('menus.media.actions.restore')}
        onConfirm={handleRestore}
        isLoading={restoreMutation.isPending}
      />

      {/* Permanent Delete Confirmation */}
      <ConfirmDialog
        open={!!mediaToDelete}
        onOpenChange={(open) => !open && setMediaToDelete(null)}
        title={t('menus.media.dialogs.permanentDeleteTitle')}
        description={t('menus.media.dialogs.permanentDeleteMessage', { name: mediaToDelete?.original_filename })}
        variant="danger"
        confirmLabel={t('menus.media.actions.permanentlyDelete')}
        onConfirm={handlePermanentDelete}
        isLoading={permanentDeleteMutation.isPending}
      />

      {/* Bulk Permanent Delete Confirmation */}
      <ConfirmDialog
        open={showBulkDeleteConfirm}
        onOpenChange={(open) => !open && setShowBulkDeleteConfirm(false)}
        title={t('menus.media.dialogs.bulkPermanentDeleteTitle')}
        description={t('menus.media.dialogs.bulkPermanentDeleteMessage', { count: selectedIds.size })}
        variant="danger"
        confirmLabel={t('menus.media.actions.permanentlyDeleteAll')}
        onConfirm={handleBulkPermanentDelete}
        isLoading={bulkPermanentDeleteMutation.isPending}
      />

      {/* Preview Modal */}
      {previewMedia && (
        <MenuMediaPreviewModal
          isOpen={showPreview}
          media={previewMedia}
          onClose={() => {
            setShowPreview(false);
            setPreviewMedia(null);
          }}
        />
      )}

      {/* CSS for Masonry */}
      <style>{`
        .deleted-masonry-grid {
          column-count: 4;
          column-gap: 16px;
        }
        .deleted-masonry-item {
          break-inside: avoid;
          margin-bottom: 16px;
        }
        @media (max-width: 1536px) {
          .deleted-masonry-grid {
            column-count: 3;
          }
        }
        @media (max-width: 1280px) {
          .deleted-masonry-grid {
            column-count: 2;
          }
        }
        @media (max-width: 768px) {
          .deleted-masonry-grid {
            column-count: 1;
          }
        }
      `}</style>
    </div>
  );
}
