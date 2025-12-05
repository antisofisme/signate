/**
 * Deleted Content Table Component
 *
 * LAYER 1: PRESENTATION
 * Displays soft-deleted content (Recycle Bin) with restore/permanent delete options
 * Includes bulk selection, bulk permanent delete, and duplicate grouping
 */

import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Trash2,
  RotateCcw,
  FileImage,
  FileVideo,
  FileAudio,
  Eye,
  ChevronDown,
  ChevronRight,
  Copy,
} from 'lucide-react';
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
  useDeletedContentList,
  useRestoreContent,
  usePermanentDeleteContent,
  useBulkPermanentDeleteContent,
  useDeletedDuplicateContent,
} from '../hooks/useContent';
import type { Content, ContentType, ContentFilters, DuplicateGroup } from '../types/content';
import { formatFileSize } from '../api/contentApi';
import { ContentPreviewModal } from './ContentPreviewModal';

// Get content type icon
function getContentTypeIcon(type: ContentType) {
  switch (type) {
    case 'image':
      return <FileImage className="w-4 h-4" />;
    case 'video':
      return <FileVideo className="w-4 h-4" />;
    case 'audio':
      return <FileAudio className="w-4 h-4" />;
  }
}

export function DeletedContentTable() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canUpdate } = useCanPerformAction('contents', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('contents', 'delete');

  // Standardized pagination hook
  const pagination = usePagination({ pageSize: 20 });

  // Sorting - URL state persistence
  const { sortConfig, onSortChange, sortParams } = useTableSort({
    defaultSort: { key: 'deleted_at', direction: 'desc' },
  });

  const [filters, setFilters] = useState<ContentFilters>({});
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [contentToRestore, setContentToRestore] = useState<Content | null>(null);
  const [contentToDelete, setContentToDelete] = useState<Content | null>(null);
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

  // Hooks
  const { data: contentData, isLoading, error } = useDeletedContentList({
    ...filters,
    ...sortParams,
    skip: pagination.skip,
    limit: pagination.limit,
  });
  const { data: duplicateData } = useDeletedDuplicateContent();
  const restoreMutation = useRestoreContent();
  const permanentDeleteMutation = usePermanentDeleteContent();
  const bulkPermanentDeleteMutation = useBulkPermanentDeleteContent();

  // Build duplicate lookup map
  const duplicateMap = useMemo(() => {
    const map = new Map<number, { hash: string; group: DuplicateGroup }>();
    const groups: DuplicateGroup[] = Array.isArray(duplicateData)
      ? duplicateData
      : (duplicateData?.data || []);

    groups.forEach((group: DuplicateGroup) => {
      group.contents.forEach((item) => {
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
  const handlePreview = (content: Content) => {
    setSelectedContent(content);
    setShowPreview(true);
  };

  const handleRestore = async () => {
    if (contentToRestore) {
      await restoreMutation.mutateAsync(contentToRestore.id);
      setContentToRestore(null);
    }
  };

  const handlePermanentDelete = async () => {
    if (contentToDelete) {
      await permanentDeleteMutation.mutateAsync(contentToDelete.id);
      setContentToDelete(null);
    }
  };

  const handleBulkPermanentDelete = async () => {
    if (selectedIds.size > 0) {
      await bulkPermanentDeleteMutation.mutateAsync(Array.from(selectedIds));
      clearSelection();
      setShowBulkDeleteConfirm(false);
    }
  };

  // Render a single content row
  const renderContentRow = (content: Content, isChild: boolean = false) => (
    <tr
      key={isChild ? `dup-${content.id}` : content.id}
      className={`${TABLE_STYLES.tr} ${
        isSelected(content.id) ? 'bg-red-50 dark:bg-red-900/10' : ''
      } ${isChild ? 'bg-gray-50/50 dark:bg-gray-800/50' : ''}`}
    >
      {/* Checkbox */}
      <td className={`${TABLE_STYLES.td} text-center`}>
        <div className="flex items-center justify-center">
          {isChild && (
            <div className="w-4 border-l-2 border-b-2 border-orange-300 dark:border-orange-700 h-4 mr-1" />
          )}
          <input
            type="checkbox"
            checked={isSelected(content.id)}
            onChange={() => toggleSelection(content.id)}
            className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500 dark:focus:ring-red-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
          />
        </div>
      </td>
      <td className="px-3 py-4 overflow-hidden">
        <div className={`flex items-center min-w-0 ${isChild ? 'pl-4' : ''}`}>
          {content.thumbnail_url ? (
            <img
              src={content.thumbnail_url}
              alt={content.title}
              className="w-10 h-10 rounded object-cover mr-2 flex-shrink-0 opacity-60"
            />
          ) : (
            <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center mr-2 flex-shrink-0 opacity-60">
              {getContentTypeIcon(content.content_type)}
            </div>
          )}
          <div className="min-w-0 flex-1 overflow-hidden">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate line-through" title={content.title}>
              {content.title}
            </p>
            {content.description && (
              <p className="text-xs text-gray-400 dark:text-gray-500 truncate" title={content.description}>
                {content.description}
              </p>
            )}
          </div>
        </div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
        {formatFileSize(content.file_size)}
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex flex-col">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 capitalize">
            {content.content_type}
          </span>
          {content.resolution && (
            <span className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
              {content.resolution}
            </span>
          )}
        </div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
        {content.duration ? `${content.duration}s` : '-'}
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex flex-col">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {content.deleted_at
              ? new Date(content.deleted_at).toLocaleDateString()
              : '-'}
          </span>
          {content.deleted_by_name && (
            <span className="text-xs text-gray-400 dark:text-gray-500 truncate" title={content.deleted_by_name}>
              {content.deleted_by_name}
            </span>
          )}
        </div>
      </td>
      <td className={TABLE_STYLES.td}>
        <div className="flex items-center gap-1">
          <button
            onClick={() => handlePreview(content)}
            className={ACTION_BUTTON.VIEW}
            title={t('contents.actions.preview')}
          >
            <Eye className="w-4 h-4" />
          </button>
          {canUpdate && (
            <button
              onClick={() => setContentToRestore(content)}
              className={ACTION_BUTTON.RESTORE}
              title={t('contents.deleted.restore')}
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
          {canDelete && (
            <button
              onClick={() => setContentToDelete(content)}
              className={ACTION_BUTTON.DELETE}
              title={t('contents.deleted.deletePermanently')}
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
    if (!contentData?.data) return null;

    const renderedGroups = new Set<string>();
    const rows: React.ReactNode[] = [];

    contentData.data.forEach((content) => {
      const dupInfo = duplicateMap.get(content.id);

      // If this content is part of a duplicate group
      if (dupInfo && !renderedGroups.has(dupInfo.hash)) {
        renderedGroups.add(dupInfo.hash);
        const group = dupInfo.group;
        const isExpanded = expandedGroups.has(dupInfo.hash);

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
                {group.thumbnail_url ? (
                  <img
                    src={group.thumbnail_url}
                    alt="Duplicate group"
                    className="w-10 h-10 rounded object-cover flex-shrink-0 opacity-60"
                  />
                ) : (
                  <div className="w-10 h-10 bg-orange-200 dark:bg-orange-800 rounded flex items-center justify-center flex-shrink-0">
                    {getContentTypeIcon(group.content_type)}
                  </div>
                )}
                <div className="min-w-0 overflow-hidden">
                  <div className="flex items-center gap-2">
                    <Copy className="w-4 h-4 text-orange-600 flex-shrink-0" />
                    <span className="font-medium text-orange-800 dark:text-orange-200 truncate">
                      {t('contents.duplicates.count', { count: group.duplicate_count })}
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
              <span className="px-2 py-0.5 text-xs font-medium rounded bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 capitalize">
                {group.content_type}
              </span>
            </td>
            <td className="px-4 py-3 whitespace-nowrap text-sm text-orange-700 dark:text-orange-300">
              -
            </td>
            <td className="px-4 py-3 whitespace-nowrap text-sm text-orange-700 dark:text-orange-300">
              -
            </td>
            <td className="px-4 py-3 whitespace-nowrap text-sm text-orange-600 dark:text-orange-400">
              {isExpanded ? t('contents.duplicates.clickToCollapse') : t('contents.duplicates.clickToExpand')}
            </td>
          </tr>
        );

        // If expanded, render all children from the group
        if (isExpanded) {
          group.contents.forEach((dupItem) => {
            // Find the full content data
            const fullContent = contentData.data.find((c) => c.id === dupItem.id);
            if (!fullContent) return;
            rows.push(renderContentRow(fullContent, true));
          });
        }
      }
      // Skip content that's already rendered as part of a group
      else if (dupInfo) {
        return;
      }
      // Regular content (not a duplicate)
      else {
        rows.push(renderContentRow(content));
      }
    });

    return rows;
  };

  // Computed pagination values
  const total = contentData?.pagination?.total || 0;
  const totalPages = pagination.getTotalPages(total);

  // Calculate duplicate stats
  const duplicateStats = useMemo(() => {
    const groups: DuplicateGroup[] = Array.isArray(duplicateData)
      ? duplicateData
      : (duplicateData?.data || []);
    return {
      totalGroups: groups.length,
      totalDuplicates: groups.reduce<number>((sum, g) => sum + g.duplicate_count, 0),
    };
  }, [duplicateData]);

  return (
    <div className="space-y-4">
      {/* Bulk Action Bar - Show when items are selected */}
      {selectedIds.size > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-red-700 dark:text-red-300">
              {t('contents.selection.itemsSelected', { count: selectedIds.size })}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearSelection}
              className="text-red-600 hover:text-red-700"
            >
              {t('contents.selection.clearSelection')}
            </Button>
          </div>
          {canDelete && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowBulkDeleteConfirm(true)}
              leftIcon={<Trash2 className="w-4 h-4" />}
            >
              {t('contents.deleted.deletePermanentlyCount', { count: selectedIds.size })}
            </Button>
          )}
        </div>
      )}

      {/* Stats */}
      {contentData && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {contentData.data.length > 0
            ? t('contents.deleted.showingItems', { count: contentData.data.length, total: contentData.pagination.total })
            : t('contents.deleted.noItems')}
          {duplicateStats.totalGroups > 0 && (
            <span className="ml-2 text-orange-600 dark:text-orange-400">
              ({duplicateStats.totalGroups} {t('contents.duplicates.groups', 'duplicate group')}{duplicateStats.totalGroups > 1 ? 's' : ''})
            </span>
          )}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && (!contentData || contentData.data.length === 0) && (
        <EmptyState
          icon={Trash2}
          title={t('contents.deleted.empty.title', 'Recycle Bin is Empty')}
          description={t('contents.deleted.empty.description', 'Deleted content will appear here for recovery')}
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
          <TableSkeleton columns={8} rows={10} />
        </div>
      )}

      {/* Table */}
      {!isLoading && !error && contentData && contentData.data.length > 0 && (
        <div className={TABLE_STYLES.container}>
          <div className="overflow-x-auto">
            <table className={`${TABLE_STYLES.table} table-fixed`}>
              <thead className={TABLE_STYLES.thead}>
                <tr>
                  {/* Checkbox column */}
                  <th className="w-10 px-2 py-3 text-center whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedIds.size > 0 && selectedIds.size === contentData?.data.length}
                      onChange={() => toggleSelectAll(contentData?.data || [])}
                      className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500 dark:focus:ring-red-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                    />
                  </th>
                  <th className="w-72 px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <SortableTableHeader columnKey="original_filename" sortConfig={sortConfig} onSortChange={onSortChange}>
                      {t('contents.table.content')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    <SortableTableHeader columnKey="file_size" sortConfig={sortConfig} onSortChange={onSortChange}>
                      {t('contents.table.size')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-24 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    <SortableTableHeader columnKey="content_type" sortConfig={sortConfig} onSortChange={onSortChange}>
                      {t('contents.table.type')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-16 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    <SortableTableHeader columnKey="duration" sortConfig={sortConfig} onSortChange={onSortChange}>
                      {t('contents.table.duration')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-28 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    <SortableTableHeader columnKey="deleted_at" sortConfig={sortConfig} onSortChange={onSortChange}>
                      {t('contents.deleted.deletedAt')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-24 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    {t('contents.table.actions')}
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

      {/* Preview Modal */}
      {selectedContent && (
        <ContentPreviewModal
          isOpen={showPreview}
          content={selectedContent}
          onClose={() => {
            setShowPreview(false);
            setSelectedContent(null);
          }}
        />
      )}

      {/* Restore Confirmation Dialog */}
      <ConfirmDialog
        open={!!contentToRestore}
        onOpenChange={(open) => !open && setContentToRestore(null)}
        title={t('contents.deleted.dialogs.restoreTitle')}
        description={t('contents.deleted.dialogs.restoreMessage', { name: contentToRestore?.title })}
        variant="info"
        confirmLabel={t('contents.deleted.restore')}
        onConfirm={handleRestore}
        isLoading={restoreMutation.isPending}
      />

      {/* Permanent Delete Confirmation Dialog */}
      <ConfirmDialog
        open={!!contentToDelete}
        onOpenChange={(open) => !open && setContentToDelete(null)}
        title={t('contents.deleted.dialogs.permanentDeleteTitle')}
        description={t('contents.deleted.dialogs.permanentDeleteMessage', { name: contentToDelete?.title })}
        variant="danger"
        confirmLabel={t('contents.deleted.deletePermanently')}
        onConfirm={handlePermanentDelete}
        isLoading={permanentDeleteMutation.isPending}
      />

      {/* Bulk Permanent Delete Confirmation Dialog */}
      <ConfirmDialog
        open={showBulkDeleteConfirm}
        onOpenChange={setShowBulkDeleteConfirm}
        title={t('contents.deleted.dialogs.bulkPermanentDeleteTitle')}
        description={t('contents.deleted.dialogs.bulkPermanentDeleteMessage', { count: selectedIds.size })}
        variant="danger"
        confirmLabel={t('contents.deleted.deletePermanentlyCount', { count: selectedIds.size })}
        onConfirm={handleBulkPermanentDelete}
        isLoading={bulkPermanentDeleteMutation.isPending}
      />
    </div>
  );
}
