/**
 * Deleted Content Table Component
 *
 * LAYER 1: PRESENTATION
 * Displays soft-deleted content (Recycle Bin) with restore/permanent delete options
 * Includes bulk selection and bulk permanent delete functionality
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Trash2,
  RotateCcw,
  FileImage,
  FileVideo,
  FileAudio,
  Eye,
} from 'lucide-react';
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
  useDeletedContentList,
  useRestoreContent,
  usePermanentDeleteContent,
  useBulkPermanentDeleteContent,
} from '../hooks/useContent';
import type { Content, ContentType, ContentFilters } from '../types/content';
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

  const [filters, setFilters] = useState<ContentFilters>({});
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [contentToRestore, setContentToRestore] = useState<Content | null>(null);
  const [contentToDelete, setContentToDelete] = useState<Content | null>(null);

  // Selection state for bulk operations
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  // Hooks
  const { data: contentData, isLoading, error } = useDeletedContentList({
    ...filters,
    skip: pagination.skip,
    limit: pagination.limit,
  });
  const restoreMutation = useRestoreContent();
  const permanentDeleteMutation = usePermanentDeleteContent();
  const bulkPermanentDeleteMutation = useBulkPermanentDeleteContent();

  // Selection handlers
  const toggleSelect = (id: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === contentData?.data.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(contentData?.data.map((c) => c.id) || []));
    }
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
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
      setSelectedIds(new Set());
      setShowBulkDeleteConfirm(false);
    }
  };

  // Computed pagination values
  const total = contentData?.pagination?.total || 0;
  const totalPages = pagination.getTotalPages(total);

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
          <TableSkeleton columns={7} rows={10} />
        </div>
      )}

      {/* Table */}
      {!isLoading && !error && contentData && contentData.data.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full table-fixed divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  {/* Checkbox column */}
                  <th className="px-4 py-3 text-center w-12">
                    <input
                      type="checkbox"
                      checked={selectedIds.size > 0 && selectedIds.size === contentData?.data.length}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500 dark:focus:ring-red-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-[30%]">
                    {t('contents.table.content')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-20">
                    {t('contents.table.type')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                    {t('contents.table.size')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">
                    {t('contents.deleted.deletedAt')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">
                    {t('contents.table.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {contentData.data.map((content) => (
                  <tr
                    key={content.id}
                    className={`hover:bg-gray-50 dark:hover:bg-gray-700 ${
                      selectedIds.has(content.id) ? 'bg-red-50 dark:bg-red-900/10' : ''
                    }`}
                  >
                    {/* Checkbox */}
                    <td className="px-4 py-3 text-center">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(content.id)}
                        onChange={() => toggleSelect(content.id)}
                        className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500 dark:focus:ring-red-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center min-w-0">
                        {content.thumbnail_url ? (
                          <img
                            src={content.thumbnail_url}
                            alt={content.title}
                            className="w-10 h-10 rounded object-cover mr-3 flex-shrink-0 opacity-60"
                          />
                        ) : (
                          <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center mr-3 flex-shrink-0 opacity-60">
                            {getContentTypeIcon(content.content_type)}
                          </div>
                        )}
                        <div className="min-w-0 flex-1">
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
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 capitalize">
                        {getContentTypeIcon(content.content_type)}
                        <span className="hidden sm:inline">{content.content_type}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {formatFileSize(content.file_size)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {content.deleted_at
                        ? new Date(content.deleted_at).toLocaleDateString()
                        : '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <div className="flex items-center gap-1">
                        <Button
                          variant="icon"
                          size="sm"
                          onClick={() => handlePreview(content)}
                          title={t('contents.actions.preview')}
                          className="!text-blue-600 hover:!text-blue-700 dark:!text-blue-400"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {canUpdate && (
                          <Button
                            variant="icon"
                            size="sm"
                            onClick={() => setContentToRestore(content)}
                            title={t('contents.deleted.restore')}
                            className="!text-green-600 hover:!text-green-700 dark:!text-green-400"
                          >
                            <RotateCcw className="w-4 h-4" />
                          </Button>
                        )}
                        {canDelete && (
                          <Button
                            variant="icon"
                            size="sm"
                            onClick={() => setContentToDelete(content)}
                            title={t('contents.deleted.deletePermanently')}
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
