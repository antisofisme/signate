/**
 * Content Table Component
 *
 * LAYER 1: PRESENTATION
 * Content management table with upload, filter, and preview
 */

import { useState } from 'react';
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
  X,
} from 'lucide-react';
import {
  useContentList,
  useDeleteContent,
  useBulkDeleteContent,
} from '../hooks/useContent';
import type { Content, ContentType, ContentFilters } from '../types/content';
import { formatFileSize, downloadContent } from '../services/contentApi';
import { UploadModal } from './UploadModal';
import { toast } from 'sonner';

// Delete Confirmation Modal
interface DeleteConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  itemName: string;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function DeleteConfirmModal({
  isOpen,
  title,
  message,
  itemName,
  onClose,
  onConfirm,
  isLoading,
}: DeleteConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {title}
        </h3>
        <p className="text-gray-700 dark:text-gray-300 mb-2">{message}</p>
        <p className="text-gray-900 dark:text-white font-semibold mb-6">
          {itemName}
        </p>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// Preview Modal
interface PreviewModalProps {
  isOpen: boolean;
  content: Content | null;
  onClose: () => void;
}

function PreviewModal({ isOpen, content, onClose }: PreviewModalProps) {
  if (!isOpen || !content) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {content.title}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mb-4">
          {content.content_type === 'image' && (
            <img
              src={content.file_url}
              alt={content.title}
              className="w-full rounded-lg"
            />
          )}
          {content.content_type === 'video' && (
            <video src={content.file_url} controls className="w-full rounded-lg" />
          )}
          {content.content_type === 'audio' && (
            <audio src={content.file_url} controls className="w-full" />
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          {/* Basic Info */}
          <div>
            <p className="text-gray-500 dark:text-gray-400">Type</p>
            <p className="text-gray-900 dark:text-white font-medium capitalize">
              {content.content_type}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">File Size</p>
            <p className="text-gray-900 dark:text-white font-medium">
              {formatFileSize(content.file_size)}
            </p>
          </div>

          {/* Filename & MIME Type */}
          <div className="col-span-2">
            <p className="text-gray-500 dark:text-gray-400">Original Filename</p>
            <p className="text-gray-900 dark:text-white font-medium break-all">
              {content.original_filename}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">MIME Type</p>
            <p className="text-gray-900 dark:text-white font-medium">
              {content.mime_type}
            </p>
          </div>

          {/* Display Duration */}
          <div>
            <p className="text-gray-500 dark:text-gray-400">Display Duration</p>
            <p className="text-gray-900 dark:text-white font-medium">
              {content.duration}s
            </p>
          </div>

          {/* Resolution & Dimensions */}
          <div>
            <p className="text-gray-500 dark:text-gray-400">Resolution</p>
            <p className="text-gray-900 dark:text-white font-medium">
              {content.resolution || 'N/A'}
            </p>
          </div>

          {/* Status */}
          <div>
            <p className="text-gray-500 dark:text-gray-400">Upload Status</p>
            <p className="text-gray-900 dark:text-white font-medium capitalize">
              {content.upload_status}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">Transcoding Status</p>
            <p className="text-gray-900 dark:text-white font-medium capitalize">
              {content.transcoding_status}
            </p>
          </div>

          {/* Upload Info */}
          <div>
            <p className="text-gray-500 dark:text-gray-400">Uploaded At</p>
            <p className="text-gray-900 dark:text-white font-medium">
              {new Date(content.created_at).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">Uploaded By</p>
            <p className="text-gray-900 dark:text-white font-medium">
              User ID: {content.uploaded_by || 'N/A'}
            </p>
          </div>

          {/* Description */}
          {content.description && (
            <div className="col-span-2">
              <p className="text-gray-500 dark:text-gray-400">Description</p>
              <p className="text-gray-900 dark:text-white">{content.description}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

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
  const [filters, setFilters] = useState<ContentFilters>({
    skip: 0,
    limit: 20,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [contentToDelete, setContentToDelete] = useState<Content | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  // Hooks
  const { data: contentData, isLoading } = useContentList(filters);
  const deleteMutation = useDeleteContent();
  const bulkDeleteMutation = useBulkDeleteContent();

  // Handlers
  const handleDownload = async (content: Content) => {
    try {
      await downloadContent(content.id, content.original_filename);
      toast.success('Download started');
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Failed to download file';
      toast.error(message);
    }
  };

  const handleFilterChange = (key: keyof ContentFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value, skip: 0 }));
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
    setFilters({ skip: 0, limit: 20 });
  };

  // Pagination handlers
  const handleNextPage = () => {
    if (contentData?.pagination.has_next) {
      setFilters((prev) => ({
        ...prev,
        skip: (prev.skip || 0) + (prev.limit || 20),
      }));
    }
  };

  const handlePrevPage = () => {
    if (contentData?.pagination.has_prev) {
      setFilters((prev) => ({
        ...prev,
        skip: Math.max(0, (prev.skip || 0) - (prev.limit || 20)),
      }));
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Content Library
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your media files (images, videos, audio)
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            Filters
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Upload Content
          </button>
        </div>
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
              <button
                onClick={clearFilters}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                Clear Filters
              </button>
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

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : contentData && contentData.data.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
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
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handlePreview(content)}
                            className="text-blue-600 hover:text-blue-700 dark:text-blue-400"
                            title="Preview"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDownload(content)}
                            className="text-gray-600 hover:text-gray-700 dark:text-gray-400"
                            title="Download"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setContentToDelete(content)}
                            className="text-red-600 hover:text-red-700 dark:text-red-400"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="bg-gray-50 dark:bg-gray-900 px-6 py-3 flex items-center justify-between">
              <div className="text-sm text-gray-700 dark:text-gray-300">
                Page {contentData.pagination.page} of{' '}
                {contentData.pagination.total_pages}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handlePrevPage}
                  disabled={!contentData.pagination.has_prev}
                  className="px-3 py-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={handleNextPage}
                  disabled={!contentData.pagination.has_next}
                  className="px-3 py-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-12">
            <FileImage className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-600 mb-4" />
            <p className="text-gray-500 dark:text-gray-400">No content found</p>
            <button
              onClick={() => setShowUploadModal(true)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Upload Your First Content
            </button>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!contentToDelete}
        title="Delete Content"
        message="Are you sure you want to delete this content? This action cannot be undone."
        itemName={contentToDelete?.title || ''}
        onClose={() => setContentToDelete(null)}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />

      {/* Preview Modal */}
      <PreviewModal
        isOpen={showPreview}
        content={selectedContent}
        onClose={() => {
          setShowPreview(false);
          setSelectedContent(null);
        }}
      />
    </div>
  );
}
