/**
 * Menu Media Deleted Table Component (Recycle Bin)
 * Table for managing soft-deleted menu media with duplicate grouping
 */

import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Trash2,
  FileImage,
  Eye,
  RotateCcw,
  Clock,
  Loader2,
  XCircle,
  ChevronDown,
  ChevronRight,
  Copy,
} from 'lucide-react';
import { toast } from '@/shared/utils/toast';
import { usePagination, useTableSort, useTableSelection } from '@/shared/hooks';
import {
  Pagination,
  TableSkeleton,
  EmptyState,
  ErrorDisplay,
  ConfirmDialog,
  Button,
  TABLE_STYLES,
  ACTION_BUTTON,
  SortableTableHeader,
} from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import {
  useDeletedMenuMediaList,
  useRestoreMenuMedia,
  usePermanentDeleteMenuMedia,
  useBulkPermanentDeleteMenuMedia,
  useDeletedDuplicateMenuMedia,
} from '../hooks/useMenuMedia';
import type { MenuMedia, MenuMediaFilters, MenuMediaDuplicateGroup } from '../types/menu';
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

// Get file type label
const getFileTypeLabel = (mimeType: string) => {
  if (mimeType.includes('jpeg') || mimeType.includes('jpg')) return 'JPEG';
  if (mimeType.includes('png')) return 'PNG';
  if (mimeType.includes('gif')) return 'GIF';
  if (mimeType.includes('webp')) return 'WebP';
  return mimeType.split('/')[1]?.toUpperCase() || 'Image';
};

// Processing status badge component
function ProcessingBadge({ status }: { status?: string }) {
  if (!status || status === 'completed') return null;

  switch (status) {
    case 'pending':
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium rounded bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300">
          <Clock className="w-3 h-3" />
        </span>
      );
    case 'processing':
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium rounded bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
          <Loader2 className="w-3 h-3 animate-spin" />
        </span>
      );
    case 'failed':
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium rounded bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300">
          <XCircle className="w-3 h-3" />
        </span>
      );
    default:
      return null;
  }
}

export function MenuMediaDeletedTable() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canDelete } = useCanPerformAction('menus', 'delete');

  // Pagination
  const pagination = usePagination({ pageSize: 20 });

  // Sorting - URL state persistence
  const { sortConfig, onSortChange, sortParams } = useTableSort({
    defaultSort: { key: 'deleted_at', direction: 'desc' },
  });

  // State
  const [filters, setFilters] = useState<MenuMediaFilters>({});
  const [selectedMedia, setSelectedMedia] = useState<MenuMedia | null>(null);
  const [mediaToRestore, setMediaToRestore] = useState<MenuMedia | null>(null);
  const [mediaToDelete, setMediaToDelete] = useState<MenuMedia | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  // State for expand/collapse groups
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Selection hook (replaces manual selection state)
  const {
    selectedIds,
    isSelected,
    toggleSelection,
    toggleSelectAll,
    clearSelection,
  } = useTableSelection<number>();

  // Queries
  const { data: mediaData, isLoading, error } = useDeletedMenuMediaList({
    ...filters,
    ...sortParams,
    skip: pagination.skip,
    limit: pagination.limit,
  });
  const { data: duplicateData } = useDeletedDuplicateMenuMedia();
  const restoreMutation = useRestoreMenuMedia();
  const permanentDeleteMutation = usePermanentDeleteMenuMedia();
  const bulkPermanentDeleteMutation = useBulkPermanentDeleteMenuMedia();

  // Build duplicate lookup map
  const duplicateMap = useMemo(() => {
    const map = new Map<number, { hash: string; group: MenuMediaDuplicateGroup }>();
    const groups: MenuMediaDuplicateGroup[] = duplicateData?.duplicates || [];

    groups.forEach((group: MenuMediaDuplicateGroup) => {
      group.media.forEach((item) => {
        map.set(item.id, {
          hash: group.file_hash,
          group,
        });
      });
    });
    return map;
  }, [duplicateData]);

  // Toggle group expansion
  const toggleGroupExpand = (hash: string) => {
    setExpandedGroups((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(hash)) {
        newSet.delete(hash);
      } else {
        newSet.add(hash);
      }
      return newSet;
    });
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

  const handlePreview = (media: MenuMedia) => {
    setSelectedMedia(media);
    setShowPreview(true);
  };

  const handleBulkPermanentDelete = async () => {
    if (selectedIds.size === 0) {
      toast.error(t('menus.media.messages.selectAtLeastOne'));
      return;
    }
    await bulkPermanentDeleteMutation.mutateAsync(Array.from(selectedIds));
    clearSelection();
    setShowBulkDeleteConfirm(false);
  };

  // Render a single media row
  const renderMediaRow = (media: MenuMedia, isChild: boolean = false) => (
    <tr
      key={isChild ? `dup-${media.id}` : media.id}
      className={`${TABLE_STYLES.tr} hover:!bg-red-50 dark:hover:!bg-red-900/10 ${
        isChild ? 'bg-gray-50/50 dark:bg-gray-800/50' : ''
      }`}
    >
      <td className="px-2 py-3 text-center whitespace-nowrap">
        <div className="flex items-center justify-center">
          {isChild && (
            <div className="w-4 border-l-2 border-b-2 border-orange-300 dark:border-orange-700 h-4 mr-1" />
          )}
          <input
            type="checkbox"
            checked={isSelected(media.id)}
            onChange={() => toggleSelection(media.id)}
            className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500"
          />
        </div>
      </td>
      <td className="px-3 py-4 overflow-hidden">
        <div className={`flex items-center min-w-0 ${isChild ? 'pl-4' : ''}`}>
          <div className="relative mr-2 flex-shrink-0">
            <img
              src={media.url}
              alt={media.alt_text || media.original_filename}
              className="w-10 h-10 rounded object-cover opacity-60"
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <Trash2 className="w-4 h-4 text-red-500" />
            </div>
          </div>
          <div className="min-w-0 flex-1 overflow-hidden">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate line-through" title={media.title || media.original_filename}>
              {media.title || media.original_filename}
            </p>
            <p className="text-xs text-gray-400 truncate">
              {media.original_filename}
            </p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap text-gray-500 dark:text-gray-400">
        {formatFileSize(media.file_size)}
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex flex-col">
          <div className="flex items-center gap-1">
            <span className="px-2 py-0.5 text-xs font-medium rounded bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
              {getFileTypeLabel(media.mime_type)}
            </span>
            {media.is_animated && (
              <span className="px-1.5 py-0.5 text-xs font-medium rounded bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300" title="Animated">
                GIF
              </span>
            )}
            <ProcessingBadge status={media.processing_status} />
          </div>
          {media.width && media.height && (
            <span className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {media.width}x{media.height}
            </span>
          )}
        </div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex flex-col">
          <span className="text-sm text-red-600 dark:text-red-400">
            {formatDate(media.deleted_at)}
          </span>
          {media.deleted_by_name && (
            <span className="text-xs text-gray-400 dark:text-gray-500 truncate" title={media.deleted_by_name}>
              {media.deleted_by_name}
            </span>
          )}
        </div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex items-center gap-1">
          <button
            onClick={() => handlePreview(media)}
            className={ACTION_BUTTON.VIEW}
            title={t('menus.media.actions.preview')}
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => setMediaToRestore(media)}
            className={ACTION_BUTTON.RESTORE}
            title={t('menus.media.actions.restore')}
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          {canDelete && (
            <button
              onClick={() => setMediaToDelete(media)}
              className={ACTION_BUTTON.DELETE}
              title={t('menus.media.actions.permanentlyDelete')}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </td>
    </tr>
  );

  // Render table rows with duplicate grouping
  const renderTableRows = () => {
    if (!mediaData?.items) return null;

    const renderedGroups = new Set<string>();
    const rows: React.ReactNode[] = [];

    mediaData.items.forEach((media) => {
      const dupInfo = duplicateMap.get(media.id);

      // If this media is part of a duplicate group
      if (dupInfo && !renderedGroups.has(dupInfo.hash)) {
        renderedGroups.add(dupInfo.hash);
        const group = dupInfo.group;
        const isExpanded = expandedGroups.has(dupInfo.hash);

        // Get first media for thumbnail
        const firstMedia = mediaData.items.find((m) => duplicateMap.get(m.id)?.hash === dupInfo.hash);

        // Render group header row
        rows.push(
          <tr
            key={`group-${dupInfo.hash}`}
            className="bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/30 cursor-pointer"
            onClick={() => toggleGroupExpand(dupInfo.hash)}
          >
            <td className="px-2 py-3 text-center whitespace-nowrap">
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-orange-600" />
              ) : (
                <ChevronRight className="w-4 h-4 text-orange-600" />
              )}
            </td>
            <td className="px-3 py-3 overflow-hidden">
              <div className="flex items-center gap-3 min-w-0">
                {firstMedia?.url ? (
                  <img
                    src={firstMedia.url}
                    alt="Duplicate group"
                    className="w-10 h-10 rounded object-cover flex-shrink-0 opacity-60"
                  />
                ) : (
                  <div className="w-10 h-10 bg-orange-200 dark:bg-orange-800 rounded flex items-center justify-center flex-shrink-0">
                    <FileImage className="w-4 h-4" />
                  </div>
                )}
                <div className="min-w-0 overflow-hidden">
                  <div className="flex items-center gap-2">
                    <Copy className="w-4 h-4 text-orange-600 flex-shrink-0" />
                    <span className="font-medium text-orange-800 dark:text-orange-200 truncate">
                      {group.duplicate_count} Duplicates
                    </span>
                  </div>
                  <span className="text-xs text-orange-600 dark:text-orange-400 font-mono truncate block">
                    {group.file_hash.slice(0, 12)}...
                  </span>
                </div>
              </div>
            </td>
            <td className="px-4 py-3 whitespace-nowrap text-sm text-orange-700 dark:text-orange-300">
              {formatFileSize(group.file_size)}
            </td>
            <td className="px-4 py-3 whitespace-nowrap">
              <span className="px-2 py-0.5 text-xs font-medium rounded bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                Same File
              </span>
            </td>
            <td className="px-4 py-3 whitespace-nowrap text-sm text-orange-700 dark:text-orange-300">
              -
            </td>
            <td className="px-4 py-3 whitespace-nowrap text-sm text-orange-600 dark:text-orange-400">
              {isExpanded ? 'Collapse' : 'Expand'}
            </td>
          </tr>
        );

        // If expanded, render all children from the group
        if (isExpanded) {
          group.media.forEach((dupItem) => {
            // Find the full media data
            const fullMedia = mediaData.items.find((m) => m.id === dupItem.id);
            if (!fullMedia) return;
            rows.push(renderMediaRow(fullMedia, true));
          });
        }
      }
      // Skip media that's already rendered as part of a group
      else if (dupInfo) {
        return;
      }
      // Regular media (not a duplicate)
      else {
        rows.push(renderMediaRow(media));
      }
    });

    return rows;
  };

  // Computed values
  const total = mediaData?.total || 0;
  const totalPages = pagination.getTotalPages(total);

  // Calculate duplicate stats
  const duplicateStats = useMemo(() => {
    const groups = duplicateData?.duplicates || [];
    return {
      totalGroups: groups.length,
      totalDuplicates: groups.reduce((sum: number, g: MenuMediaDuplicateGroup) => sum + g.duplicate_count, 0),
    };
  }, [duplicateData]);

  return (
    <div className="space-y-4">
      {/* Stats */}
      {mediaData && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {t('menus.media.stats.showingDeleted', { count: mediaData.items.length, total })}
          {duplicateStats.totalGroups > 0 && (
            <span className="ml-2 text-orange-600 dark:text-orange-400">
              ({duplicateStats.totalGroups} duplicate group{duplicateStats.totalGroups > 1 ? 's' : ''})
            </span>
          )}
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
          <TableSkeleton columns={7} rows={10} />
        </div>
      )}

      {/* Table */}
      {!isLoading && !error && mediaData && mediaData.items.length > 0 && (
        <div className={TABLE_STYLES.container}>
          <div className="overflow-x-auto">
            <table className={`${TABLE_STYLES.table} table-fixed`}>
              <thead className={TABLE_STYLES.thead}>
                <tr>
                  <th className="w-10 px-2 py-3 text-center whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedIds.size > 0 && selectedIds.size === mediaData.items.length}
                      onChange={() => toggleSelectAll(mediaData?.items || [])}
                      className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500"
                    />
                  </th>
                  <th className="w-72 px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <SortableTableHeader columnKey="original_filename" sortConfig={sortConfig} onSortChange={onSortChange}>
                      {t('menus.media.table.image')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    <SortableTableHeader columnKey="file_size" sortConfig={sortConfig} onSortChange={onSortChange}>
                      {t('menus.media.table.size')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-28 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    <SortableTableHeader columnKey="mime_type" sortConfig={sortConfig} onSortChange={onSortChange}>
                      {t('menus.media.table.type')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-28 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    <SortableTableHeader columnKey="deleted_at" sortConfig={sortConfig} onSortChange={onSortChange}>
                      {t('menus.media.table.deletedAt')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-24 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    {t('menus.media.table.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className={TABLE_STYLES.tbody}>
                {renderTableRows()}
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
