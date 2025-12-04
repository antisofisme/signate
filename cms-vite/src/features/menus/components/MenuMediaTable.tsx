/**
 * Menu Media Table Component
 * Table-based layout for managing menu media with pagination
 * Includes duplicate grouping (tree view) for files with same hash
 */

import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Upload,
  Trash2,
  FileImage,
  Eye,
  Copy,
  Check,
  Edit,
  Download,
  Filter,
  ChevronDown,
  ChevronRight,
  UtensilsCrossed,
} from 'lucide-react';
import { toast } from '@/shared/utils/toast';
import { usePagination, useTableSort } from '@/shared/hooks';
import {
  Pagination,
  TableSkeleton,
  EmptyState,
  ErrorDisplay,
  ConfirmDialog,
  Button,
  TABLE_STYLES,
  SortableTableHeader,
} from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import {
  useMenuMediaList,
  useDeleteMenuMedia,
  useDuplicateMenuMedia,
} from '../hooks/useMenuMedia';
import type { MenuMedia, MenuMediaFilters, MenuMediaDuplicateGroup, MenuMediaDuplicateUsage } from '../types/menu';
import { MenuMediaUploadModal } from './MenuMediaUploadModal';
import { MenuMediaEditModal } from './MenuMediaEditModal';
import { MenuMediaPreviewModal } from './MenuMediaPreviewModal';
// MenuMediaUploadQueuePanel removed - using unified UploadQueuePanel

// Format file size
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Get file type label
const getFileTypeLabel = (mimeType: string) => {
  if (mimeType.includes('jpeg') || mimeType.includes('jpg')) return 'JPEG';
  if (mimeType.includes('png')) return 'PNG';
  if (mimeType.includes('gif')) return 'GIF';
  if (mimeType.includes('webp')) return 'WebP';
  return mimeType.split('/')[1]?.toUpperCase() || 'Image';
};

interface MenuMediaTableProps {
  showUploadModal?: boolean;
  onCloseUploadModal?: () => void;
  showFilters?: boolean;
}

export function MenuMediaTable({
  showUploadModal: showUploadModalProp = false,
  onCloseUploadModal,
  showFilters: showFiltersProp = false
}: MenuMediaTableProps) {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canCreate } = useCanPerformAction('menus', 'create');
  const { hasPermission: canUpdate } = useCanPerformAction('menus', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('menus', 'delete');

  // Pagination
  const pagination = usePagination({ pageSize: 20 });

  // Sorting - URL state persistence
  const { sortConfig, onSortChange, sortParams } = useTableSort({
    defaultSort: { key: 'created_at', direction: 'desc' },
  });

  // State
  const [filters, setFilters] = useState<MenuMediaFilters>({});
  // Use prop if provided, otherwise use local state
  const showFilters = showFiltersProp;
  const showUploadModal = showUploadModalProp;
  const [selectedMedia, setSelectedMedia] = useState<MenuMedia | null>(null);
  const [mediaToDelete, setMediaToDelete] = useState<MenuMedia | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Queries - merge filters with pagination and sorting
  const { data: mediaData, isLoading, error } = useMenuMediaList({
    ...filters,
    ...sortParams,
    skip: pagination.skip,
    limit: pagination.limit,
  });
  const { data: duplicateData } = useDuplicateMenuMedia();
  const deleteMutation = useDeleteMenuMedia();

  // Build duplicate lookup map
  const duplicateMap = useMemo(() => {
    const map = new Map<number, { hash: string; usage: MenuMediaDuplicateUsage; group: MenuMediaDuplicateGroup }>();
    const groups = duplicateData?.duplicates || [];

    groups.forEach((group: MenuMediaDuplicateGroup) => {
      group.media.forEach((item) => {
        map.set(item.id, {
          hash: group.file_hash,
          usage: item.usage,
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

  // Check if media has usage
  const hasUsage = (usage: MenuMediaDuplicateUsage): boolean => {
    return usage.used_count > 0;
  };

  // Handlers
  const handleCopyUrl = async (media: MenuMedia) => {
    try {
      await navigator.clipboard.writeText(media.url || '');
      setCopiedId(media.id);
      toast.success(t('menus.media.messages.urlCopied', 'URL copied to clipboard'));
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      toast.error(t('menus.media.messages.urlCopyFailed', 'Failed to copy URL'));
    }
  };

  const handleDownload = async (media: MenuMedia) => {
    if (!media.url) return;
    const link = document.createElement('a');
    link.href = media.url;
    link.download = media.original_filename;
    link.click();
    toast.success(t('menus.media.messages.downloadStarted', 'Download started'));
  };

  const handleDelete = async () => {
    if (mediaToDelete) {
      await deleteMutation.mutateAsync(mediaToDelete.id);
      setMediaToDelete(null);
    }
  };

  const handlePreview = (media: MenuMedia) => {
    setSelectedMedia(media);
    setShowPreview(true);
  };

  const handleEdit = (media: MenuMedia) => {
    setSelectedMedia(media);
    setShowEditModal(true);
  };

  const handleFilterChange = (key: keyof MenuMediaFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    pagination.resetPage();
  };

  const clearFilters = () => {
    setFilters({});
    pagination.resetPage();
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

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) {
      toast.error(t('menus.media.messages.selectAtLeastOne', 'Please select at least one image'));
      return;
    }
    if (confirm(t('menus.media.dialogs.bulkDeleteMessage', { count: selectedIds.size }) || `Delete ${selectedIds.size} images?`)) {
      for (const id of selectedIds) {
        await deleteMutation.mutateAsync(id);
      }
      setSelectedIds(new Set());
    }
  };

  // Computed values
  const total = mediaData?.total || 0;
  const totalPages = pagination.getTotalPages(total);

  // Render table row for a media item
  const renderMediaRow = (media: MenuMedia, isChild: boolean = false, usage?: MenuMediaDuplicateUsage) => {
    const itemHasUsage = usage ? hasUsage(usage) : false;

    return (
      <tr
        key={isChild ? `dup-${media.id}` : media.id}
        className={`${TABLE_STYLES.tr} ${isChild ? 'bg-gray-50/50 dark:bg-gray-800/50' : ''}`}
      >
        <td className={`${TABLE_STYLES.td} text-center`}>
          <div className="flex items-center justify-center">
            {isChild && (
              <div className="w-4 border-l-2 border-b-2 border-orange-300 dark:border-orange-700 h-4 mr-1" />
            )}
            <input
              type="checkbox"
              checked={selectedIds.has(media.id)}
              onChange={(e) => {
                e.stopPropagation();
                toggleSelection(media.id);
              }}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
          </div>
        </td>
        <td className={TABLE_STYLES.td}>
          <div className={`flex items-center min-w-0 ${isChild ? 'pl-4' : ''}`}>
            <img
              src={media.url}
              alt={media.alt_text || media.original_filename}
              className="w-10 h-10 rounded object-cover mr-3 flex-shrink-0"
            />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate" title={media.title || media.original_filename}>
                {media.title || media.original_filename}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                {media.original_filename}
              </p>
            </div>
          </div>
        </td>
        <td className={TABLE_STYLES.td}>
          {/* Usage indicators for duplicates */}
          {isChild && usage ? (
            <div className="flex flex-col gap-0.5">
              {usage.used_count > 0 && (
                <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
                  <UtensilsCrossed className="w-3 h-3" />
                  <span>{usage.used_count} menu item{usage.used_count > 1 ? 's' : ''}</span>
                </div>
              )}
              {!itemHasUsage && (
                <span className="text-xs text-gray-400">Not used</span>
              )}
            </div>
          ) : (
            <span className="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
              {getFileTypeLabel(media.mime_type)}
            </span>
          )}
        </td>
        <td className={TABLE_STYLES.td}>
          {formatFileSize(media.file_size)}
        </td>
        <td className={TABLE_STYLES.td}>
          <div className="flex items-center gap-2">
            {media.width && media.height ? (
              <span>{media.width}x{media.height}</span>
            ) : (
              <span className="text-gray-400">-</span>
            )}
            {isChild && !itemHasUsage && (
              <span className="w-2 h-2 rounded-full bg-green-400" title="Safe to delete" />
            )}
          </div>
        </td>
        <td className={TABLE_STYLES.td}>
          <div className="flex items-center gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handlePreview(media);
              }}
              className={TABLE_STYLES.actionBtnBlue}
              title={t('menus.media.actions.preview', 'Preview')}
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDownload(media);
              }}
              className={TABLE_STYLES.actionBtnGray}
              title={t('menus.media.actions.download', 'Download')}
            >
              <Download className="w-4 h-4" />
            </button>
            {canUpdate && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleEdit(media);
                }}
                className={TABLE_STYLES.actionBtnGreen}
                title={t('menus.media.actions.edit', 'Edit')}
              >
                <Edit className="w-4 h-4" />
              </button>
            )}
            {canDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setMediaToDelete(media);
                }}
                className={TABLE_STYLES.actionBtnRed}
                title={t('menus.media.actions.delete', 'Delete')}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </td>
      </tr>
    );
  };

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

        // Get first media item for thumbnail
        const firstMedia = mediaData.items.find((m) => duplicateMap.get(m.id)?.hash === dupInfo.hash);

        // Render group header row
        rows.push(
          <tr
            key={`group-${dupInfo.hash}`}
            className={`${TABLE_STYLES.tr} bg-orange-50 dark:bg-orange-900/20 cursor-pointer`}
            onClick={() => toggleGroupExpand(dupInfo.hash)}
          >
            <td className={`${TABLE_STYLES.td} text-center`}>
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-orange-600" />
              ) : (
                <ChevronRight className="w-4 h-4 text-orange-600" />
              )}
            </td>
            <td className={TABLE_STYLES.td} colSpan={2}>
              <div className="flex items-center gap-3">
                {firstMedia?.url ? (
                  <img
                    src={firstMedia.url}
                    alt="Duplicate group"
                    className="w-10 h-10 rounded object-cover flex-shrink-0"
                  />
                ) : (
                  <div className="w-10 h-10 bg-orange-200 dark:bg-orange-800 rounded flex items-center justify-center flex-shrink-0">
                    <FileImage className="w-4 h-4" />
                  </div>
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <Copy className="w-4 h-4 text-orange-600" />
                    <span className="font-medium text-orange-800 dark:text-orange-200">
                      {group.duplicate_count} Duplicate Files
                    </span>
                  </div>
                  <span className="text-xs text-orange-600 dark:text-orange-400 font-mono">
                    Hash: {group.file_hash.slice(0, 16)}...
                  </span>
                </div>
              </div>
            </td>
            <td className={`${TABLE_STYLES.td} text-orange-700 dark:text-orange-300`}>
              {formatFileSize(group.file_size)}
            </td>
            <td className={TABLE_STYLES.td}>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                Same File
              </span>
            </td>
            <td className={`${TABLE_STYLES.td} text-orange-600 dark:text-orange-400`}>
              Click to {isExpanded ? 'collapse' : 'expand'}
            </td>
          </tr>
        );

        // If expanded, render all children from the group
        if (isExpanded) {
          group.media.forEach((dupItem) => {
            // Find the full media data
            const fullMedia = mediaData.items.find((m) => m.id === dupItem.id);
            if (!fullMedia) return;

            rows.push(renderMediaRow(fullMedia, true, dupItem.usage));
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

  return (
    <div className="space-y-4">
      {/* Filters - controlled by parent */}
      {showFilters && (
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('menus.media.filters.search', 'Search')}
              </label>
              <input
                type="text"
                placeholder={t('menus.media.filters.searchPlaceholder', 'Search by filename...')}
                value={filters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value || undefined)}
                className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
            <div className="flex items-end">
              <Button variant="ghost" onClick={clearFilters}>
                {t('menus.media.actions.clearFilters', 'Clear Filters')}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      {mediaData && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {t('menus.media.stats.showingImages', { count: mediaData.items.length, total }) || `Showing ${mediaData.items.length} of ${total} images`}
          {duplicateData && duplicateData.total_groups > 0 && (
            <span className="ml-2 text-orange-600 dark:text-orange-400">
              ({duplicateData.total_groups} duplicate group{duplicateData.total_groups > 1 ? 's' : ''})
            </span>
          )}
        </div>
      )}

      {/* Bulk Actions Toolbar */}
      {selectedIds.size > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-center justify-between">
          <p className="text-sm font-medium text-blue-900 dark:text-blue-300">
            {t('menus.media.selection.itemsSelected', { count: selectedIds.size }) || `${selectedIds.size} item(s) selected`}
          </p>
          <div className="flex gap-2">
            {canDelete && (
              <Button
                variant="danger"
                onClick={handleBulkDelete}
                leftIcon={<Trash2 className="w-4 h-4" />}
              >
                {t('menus.media.actions.deleteSelected', 'Delete Selected')}
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && (!mediaData || mediaData.items.length === 0) && (
        <EmptyState
          icon={FileImage}
          title={t('menus.media.empty.title', 'No images found')}
          description={t('menus.media.empty.description', 'Upload your first image to get started')}
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
        <div className={TABLE_STYLES.container}>
          <div className="overflow-x-auto">
            <table className={`${TABLE_STYLES.table} table-fixed`}>
              <thead className={TABLE_STYLES.thead}>
                <tr>
                  <th className={`${TABLE_STYLES.th} text-center w-12`}>
                    <input
                      type="checkbox"
                      checked={selectedIds.size > 0 && selectedIds.size === mediaData.items.length}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                  </th>
                  <th className={`${TABLE_STYLES.th} w-[40%]`}>
                    <SortableTableHeader
                      columnKey="original_filename"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('menus.media.table.image', 'Image')}
                    </SortableTableHeader>
                  </th>
                  <th className={`${TABLE_STYLES.th} w-24`}>
                    <SortableTableHeader
                      columnKey="mime_type"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('menus.media.table.type', 'Type')}
                    </SortableTableHeader>
                  </th>
                  <th className={`${TABLE_STYLES.th} w-24`}>
                    <SortableTableHeader
                      columnKey="file_size"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('menus.media.table.size', 'Size')}
                    </SortableTableHeader>
                  </th>
                  <th className={`${TABLE_STYLES.th} w-28`}>
                    <SortableTableHeader
                      columnKey="width"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('menus.media.table.dimensions', 'Dimensions')}
                    </SortableTableHeader>
                  </th>
                  <th className={`${TABLE_STYLES.th} w-32`}>
                    {t('menus.media.table.actions', 'Actions')}
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

      {/* Upload Modal */}
      <MenuMediaUploadModal
        isOpen={showUploadModal}
        onClose={onCloseUploadModal || (() => {})}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!mediaToDelete}
        onOpenChange={(open) => !open && setMediaToDelete(null)}
        title={t('menus.media.dialogs.deleteTitle', 'Delete Image')}
        description={t('menus.media.dialogs.deleteMessage', { name: mediaToDelete?.original_filename }) || `Are you sure you want to delete "${mediaToDelete?.original_filename}"?`}
        variant="danger"
        confirmLabel={t('menus.media.actions.delete', 'Delete')}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
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

      {/* Edit Modal */}
      <MenuMediaEditModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedMedia(null);
        }}
        media={selectedMedia}
      />

      {/* Upload Queue Panel - Now using unified UploadQueuePanel in main.tsx */}
    </div>
  );
}
