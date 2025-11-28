/**
 * Content Table Component
 *
 * LAYER 1: PRESENTATION
 * Content management table with upload, filter, and preview
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Upload,
  Trash2,
  Loader2,
  FileImage,
  FileVideo,
  FileAudio,
  Eye,
  Download,
  Edit,
  Filter,
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
import { getApiErrorMessage } from '@/shared/utils/types';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import {
  useContentList,
  useDeleteContent,
  useBulkDeleteContent,
} from '../hooks/useContent';
import type { Content, ContentType, ContentFilters } from '../types/content';
import { formatFileSize, downloadContent } from '../api/contentApi';
import { UploadModal } from './UploadModal';
import { EditContentModal } from './EditContentModal';
import { BulkEditModal } from './BulkEditModal';
import { BulkTagModal } from './BulkTagModal';
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

export function ContentTable() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canCreate } = useCanPerformAction('contents', 'create');
  const { hasPermission: canUpdate } = useCanPerformAction('contents', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('contents', 'delete');

  // Standardized pagination hook
  const pagination = usePagination({ pageSize: 20 });

  const [filters, setFilters] = useState<ContentFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [contentToDelete, setContentToDelete] = useState<Content | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [showEditModal, setShowEditModal] = useState(false);
  const [showBulkEditModal, setShowBulkEditModal] = useState(false);
  const [showBulkTagModal, setShowBulkTagModal] = useState(false);

  // Hooks - merge filters with pagination
  const { data: contentData, isLoading, error } = useContentList({
    ...filters,
    skip: pagination.skip,
    limit: pagination.limit,
  });
  const deleteMutation = useDeleteContent();
  const bulkDeleteMutation = useBulkDeleteContent();

  // Handlers
  const handleDownload = async (content: Content) => {
    try {
      await downloadContent(content.id, content.original_filename);
      toast.success('Download started');
    } catch (error: unknown) {
      toast.error(getApiErrorMessage(error, 'Failed to download file'));
    }
  };

  const handleFilterChange = (key: keyof ContentFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    pagination.resetPage();
  };

  const handleDelete = async () => {
    if (contentToDelete) {
      await deleteMutation.mutateAsync(contentToDelete.id);
      setContentToDelete(null);
    }
  };

  const handlePreview = (content: Content) => {
    setSelectedContent(content);
    setShowPreview(true);
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
    if (selectedIds.size === contentData?.data.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(contentData?.data.map((c) => c.id) || []));
    }
  };

  const handleEdit = (content: Content) => {
    setSelectedContent(content);
    setShowEditModal(true);
  };

  const handleBulkEdit = () => {
    if (selectedIds.size === 0) {
      toast.error('Please select at least one content item');
      return;
    }
    setShowBulkEditModal(true);
  };

  const handleBulkTag = () => {
    if (selectedIds.size === 0) {
      toast.error('Please select at least one content item');
      return;
    }
    setShowBulkTagModal(true);
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) {
      toast.error('Please select at least one content item');
      return;
    }
    if (confirm(`Are you sure you want to delete ${selectedIds.size} content items?`)) {
      await bulkDeleteMutation.mutateAsync(Array.from(selectedIds));
      setSelectedIds(new Set());
    }
  };

  const getSelectedContent = (): Content[] => {
    return contentData?.data.filter((c) => selectedIds.has(c.id)) || [];
  };

  // Computed pagination values
  const total = contentData?.pagination?.total || 0;
  const totalPages = pagination.getTotalPages(total);

  return (
    <div className="space-y-4">
      {/* Action Bar - No duplicate header, title is in PageHeader */}
      <div className="flex items-center justify-end gap-2">
        <Button
          variant="secondary"
          onClick={() => setShowFilters(!showFilters)}
          leftIcon={<Filter className="w-4 h-4" />}
        >
          Filters
        </Button>
        {canCreate && (
          <Button
            variant="primary"
            onClick={() => setShowUploadModal(true)}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            Upload Content
          </Button>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Content Type
              </label>
              <select
                value={filters.content_type || ''}
                onChange={(e) =>
                  handleFilterChange(
                    'content_type',
                    e.target.value || undefined
                  )
                }
                className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              >
                <option value="">All Types</option>
                <option value="image">Image</option>
                <option value="video">Video</option>
                <option value="audio">Audio</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Status
              </label>
              <select
                value={
                  filters.is_active === undefined
                    ? ''
                    : filters.is_active
                    ? 'true'
                    : 'false'
                }
                onChange={(e) =>
                  handleFilterChange(
                    'is_active',
                    e.target.value === ''
                      ? undefined
                      : e.target.value === 'true'
                  )
                }
                className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              >
                <option value="">All Status</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button variant="ghost" onClick={clearFilters}>
                Clear Filters
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Content Stats */}
      {contentData && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Showing {contentData.data.length} of {contentData.pagination.total} items
        </div>
      )}

      {/* Bulk Actions Toolbar */}
      {selectedIds.size > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-center justify-between">
          <p className="text-sm font-medium text-blue-900 dark:text-blue-300">
            {selectedIds.size} item(s) selected
          </p>
          <div className="flex gap-2">
            {canUpdate && (
              <>
                <Button
                  variant="primary"
                  onClick={handleBulkEdit}
                  leftIcon={<Edit className="w-4 h-4" />}
                >
                  Bulk Edit
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleBulkTag}
                  leftIcon={<Filter className="w-4 h-4" />}
                  className="!bg-purple-600 hover:!bg-purple-700 !text-white"
                >
                  Bulk Tag
                </Button>
              </>
            )}
            {canDelete && (
              <Button
                variant="danger"
                onClick={handleBulkDelete}
                leftIcon={<Trash2 className="w-4 h-4" />}
              >
                Delete Selected
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {error ? (
          <ErrorDisplay
            error={error}
            onRetry={() => window.location.reload()}
          />
        ) : isLoading ? (
          <TableSkeleton columns={7} rows={10} />
        ) : contentData && contentData.data.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-center w-12">
                      <input
                        type="checkbox"
                        checked={selectedIds.size > 0 && selectedIds.size === contentData?.data.length}
                        onChange={toggleSelectAll}
                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Content
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {contentData.data.map((content) => (
                    <tr key={content.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-3 text-center">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(content.id)}
                          onChange={() => toggleSelection(content.id)}
                          className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {content.thumbnail_url ? (
                            <img
                              src={content.thumbnail_url}
                              alt={content.title}
                              className="w-10 h-10 rounded object-cover mr-3"
                            />
                          ) : (
                            <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center mr-3">
                              {getContentTypeIcon(content.content_type)}
                            </div>
                          )}
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {content.title}
                            </p>
                            {content.description && (
                              <p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-xs">
                                {content.description}
                              </p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2 text-sm text-gray-900 dark:text-white capitalize">
                          {getContentTypeIcon(content.content_type)}
                          {content.content_type}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatFileSize(content.file_size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {content.duration}s
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            content.is_active
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                          }`}
                        >
                          {content.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex items-center gap-1">
                          {canUpdate && (
                            <Button
                              variant="icon"
                              size="sm"
                              onClick={() => handleEdit(content)}
                              title="Edit"
                              className="!text-green-600 hover:!text-green-700 dark:!text-green-400"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                          )}
                          <Button
                            variant="icon"
                            size="sm"
                            onClick={() => handlePreview(content)}
                            title="Preview"
                            className="!text-blue-600 hover:!text-blue-700 dark:!text-blue-400"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="icon"
                            size="sm"
                            onClick={() => handleDownload(content)}
                            title="Download"
                            className="!text-gray-600 hover:!text-gray-700 dark:!text-gray-400"
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                          {canDelete && (
                            <Button
                              variant="icon"
                              size="sm"
                              onClick={() => setContentToDelete(content)}
                              title="Delete"
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

            {/* Pagination - Using standardized component */}
            <Pagination
              currentPage={pagination.currentPage}
              totalPages={totalPages}
              totalItems={total}
              pageSize={pagination.pageSize}
              onPageChange={pagination.goToPage}
              className="px-6 bg-gray-50 dark:bg-gray-900"
            />
          </>
        ) : (
          <EmptyState
            icon={FileImage}
            title="No content found"
            description="Upload your first media file to get started"
            action={
              canCreate && (
                <Button onClick={() => setShowUploadModal(true)}>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Content
                </Button>
              )
            }
          />
        )}
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={!!contentToDelete}
        onOpenChange={(open) => !open && setContentToDelete(null)}
        title="Delete Content"
        description={`Are you sure you want to delete "${contentToDelete?.title}"? This action cannot be undone.`}
        variant="danger"
        confirmLabel="Delete"
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />

      {/* Preview Modal */}
      {/* Content Preview Modal */}
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

      {/* Edit Content Modal */}
      <EditContentModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedContent(null);
        }}
        content={selectedContent}
      />

      {/* Bulk Edit Modal */}
      <BulkEditModal
        isOpen={showBulkEditModal}
        onClose={() => setShowBulkEditModal(false)}
        selectedContent={getSelectedContent()}
      />

      {/* Bulk Tag Modal */}
      <BulkTagModal
        isOpen={showBulkTagModal}
        onClose={() => setShowBulkTagModal(false)}
        selectedContent={getSelectedContent()}
      />
    </div>
  );
}
