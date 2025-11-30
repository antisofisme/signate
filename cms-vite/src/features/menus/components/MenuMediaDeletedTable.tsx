/**
 * Menu Media Deleted Table Component (Recycle Bin)
 * Table for managing soft-deleted menu media
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Trash2,
  FileImage,
  Eye,
  RotateCcw,
} from 'lucide-react';
import { toast } from 'sonner';
import { usePagination } from '@/shared/hooks';
import {
  Pagination,
  TableSkeleton,
  EmptyState,
  ErrorDisplay,
  ConfirmDialog,
  Button,
} from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import {
  useDeletedMenuMediaList,
  useRestoreMenuMedia,
  usePermanentDeleteMenuMedia,
  useBulkPermanentDeleteMenuMedia,
} from '../hooks/useMenuMedia';
import type { MenuMedia, MenuMediaFilters } from '../types/menu';
import { MenuMediaPreviewModal } from './MenuMediaPreviewModal';

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
    hour: '2-digit',
    minute: '2-digit',
  });
};

export function MenuMediaDeletedTable() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canDelete } = useCanPerformAction('menus', 'delete');

  // Pagination
  const pagination = usePagination({ pageSize: 20 });

  // State
  const [filters, setFilters] = useState<MenuMediaFilters>({});
  const [selectedMedia, setSelectedMedia] = useState<MenuMedia | null>(null);
  const [mediaToRestore, setMediaToRestore] = useState<MenuMedia | null>(null);
  const [mediaToDelete, setMediaToDelete] = useState<MenuMedia | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  // Queries
  const { data: mediaData, isLoading, error } = useDeletedMenuMediaList({
    ...filters,
    skip: pagination.skip,
    limit: pagination.limit,
  });
  const restoreMutation = useRestoreMenuMedia();
  const permanentDeleteMutation = usePermanentDeleteMenuMedia();
  const bulkPermanentDeleteMutation = useBulkPermanentDeleteMenuMedia();

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

  const handlePreview = (media: MenuMedia) => {
    setSelectedMedia(media);
    setShowPreview(true);
  };

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

  const toggleSelectAll = () => {
    if (selectedIds.size === mediaData?.items.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(mediaData?.items.map((m) => m.id) || []));
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

  // Computed values
  const total = mediaData?.total || 0;
  const totalPages = pagination.getTotalPages(total);

  return (
    <div className="space-y-4">
      {/* Stats */}
      {mediaData && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {t('menus.media.stats.showingDeleted', { count: mediaData.items.length, total })}
        </div>
      )}

      {/* Bulk Actions Toolbar */}
      {selectedIds.size > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center justify-between">
          <p className="text-sm font-medium text-red-900 dark:text-red-300">
            {t('menus.media.selection.itemsSelected', { count: selectedIds.size })}
          </p>
          <div className="flex gap-2">
            {canDelete && (
              <Button
                variant="danger"
                onClick={() => setShowBulkDeleteConfirm(true)}
                leftIcon={<Trash2 className="w-4 h-4" />}
              >
                {t('menus.media.actions.permanentlyDelete')}
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && (!mediaData || mediaData.items.length === 0) && (
        <EmptyState
          icon={Trash2}
          title={t('menus.media.empty.recycleBinTitle')}
          description={t('menus.media.empty.recycleBinDescription')}
        />
      )}

      {/* Error State */}
      {error && (
        <ErrorDisplay
          error={error}
          onRetry={() => window.location.reload()}
        />
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <TableSkeleton columns={6} rows={10} />
        </div>
      )}

      {/* Table */}
      {!isLoading && !error && mediaData && mediaData.items.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full table-fixed divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-4 py-3 text-center w-12">
                    <input
                      type="checkbox"
                      checked={selectedIds.size > 0 && selectedIds.size === mediaData.items.length}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500"
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-[35%]">
                    {t('menus.media.table.image')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                    {t('menus.media.table.size')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-28">
                    {t('menus.media.table.dimensions')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-36">
                    {t('menus.media.table.deletedAt')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-28">
                    {t('menus.media.table.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {mediaData.items.map((media) => (
                  <tr key={media.id} className="hover:bg-red-50 dark:hover:bg-red-900/10">
                    <td className="px-4 py-3 text-center">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(media.id)}
                        onChange={() => toggleSelection(media.id)}
                        className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center min-w-0">
                        <div className="relative">
                          <img
                            src={media.url}
                            alt={media.alt_text || media.original_filename}
                            className="w-10 h-10 rounded object-cover mr-3 flex-shrink-0 opacity-60"
                          />
                          <div className="absolute inset-0 flex items-center justify-center">
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </div>
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate line-through" title={media.title || media.original_filename}>
                            {media.title || media.original_filename}
                          </p>
                          <p className="text-xs text-gray-400 truncate">
                            {media.original_filename}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {formatFileSize(media.file_size)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {media.width}x{media.height}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-red-600 dark:text-red-400">
                      {formatDate(media.deleted_at)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <div className="flex items-center gap-1">
                        <Button
                          variant="icon"
                          size="sm"
                          onClick={() => handlePreview(media)}
                          title={t('menus.media.actions.preview')}
                          className="!text-blue-600 hover:!text-blue-700 dark:!text-blue-400"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="icon"
                          size="sm"
                          onClick={() => setMediaToRestore(media)}
                          title={t('menus.media.actions.restore')}
                          className="!text-green-600 hover:!text-green-700 dark:!text-green-400"
                        >
                          <RotateCcw className="w-4 h-4" />
                        </Button>
                        {canDelete && (
                          <Button
                            variant="icon"
                            size="sm"
                            onClick={() => setMediaToDelete(media)}
                            title={t('menus.media.actions.permanentlyDelete')}
                            className="!text-red-600 hover:!text-red-700 dark:!text-red-400"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <Pagination
            currentPage={pagination.currentPage}
            totalPages={totalPages}
            totalItems={total}
            pageSize={pagination.pageSize}
            onPageChange={pagination.goToPage}
            className="px-6 bg-gray-50 dark:bg-gray-900"
          />
        </div>
      )}

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
      {selectedMedia && (
        <MenuMediaPreviewModal
          isOpen={showPreview}
          media={selectedMedia}
          onClose={() => {
            setShowPreview(false);
            setSelectedMedia(null);
          }}
        />
      )}
    </div>
  );
}
