/**
 * Content Table Component
 *
 * LAYER 1: PRESENTATION
 * Content management table with upload, filter, and preview
 */

import { useState, useCallback, useMemo, memo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Trash2,
  Loader2,
  FileImage,
  FileVideo,
  FileAudio,
  Eye,
  Download,
  Pencil,
  Filter,
  ChevronDown,
  ChevronRight,
  Copy,
  List,
  ListMusic,
  Tag,
  Monitor,
  Play,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  User,
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
  DateCell,
} from '@/shared/components';
import { getApiErrorMessage } from '@/shared/utils/types';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import {
  useContentList,
  useDeleteContent,
  useBulkDeleteContent,
  useDuplicateContent,
} from '../hooks/useContent';
import { useTags } from '@/features/tags/hooks/useTags';
import type { Content, ContentType, ContentFilters, DuplicateGroup, ContentUsage, TranscodingStatus } from '../types/content';
import { formatFileSize, downloadContent } from '../api/contentApi';
import { UploadModal } from './UploadModal';
import { EditContentModal } from './EditContentModal';
import { BulkEditModal } from './BulkEditModal';
import { BulkTagModal } from './BulkTagModal';
import { ContentTagAssignmentModal } from './ContentTagAssignmentModal';
import { ContentPlaylistAssignmentModal } from './ContentPlaylistAssignmentModal';
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

// Get file type label from mime type (like MenuMediaTable)
function getFileTypeLabel(mimeType: string): string {
  if (mimeType.includes('jpeg') || mimeType.includes('jpg')) return 'JPEG';
  if (mimeType.includes('png')) return 'PNG';
  if (mimeType.includes('gif')) return 'GIF';
  if (mimeType.includes('webp')) return 'WebP';
  if (mimeType.includes('mp4')) return 'MP4';
  if (mimeType.includes('webm')) return 'WebM';
  if (mimeType.includes('avi')) return 'AVI';
  if (mimeType.includes('mov') || mimeType.includes('quicktime')) return 'MOV';
  if (mimeType.includes('mkv')) return 'MKV';
  if (mimeType.includes('mp3') || mimeType.includes('mpeg')) return 'MP3';
  if (mimeType.includes('wav')) return 'WAV';
  if (mimeType.includes('ogg')) return 'OGG';
  if (mimeType.includes('flac')) return 'FLAC';
  return mimeType.split('/')[1]?.toUpperCase() || 'File';
}

// Transcoding status badge component for video/audio content
function TranscodingBadge({
  contentType,
  status,
  progress,
}: {
  contentType: ContentType;
  status: TranscodingStatus;
  progress: number;
}) {
  const { t } = useTranslation();

  // Only show for video and audio content
  if (contentType === 'image') {
    return <span className="text-gray-400 dark:text-gray-500">-</span>;
  }

  switch (status) {
    case 'pending':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300">
          <Clock className="w-3 h-3" />
          {t('contents.transcoding.pending', 'Pending')}
        </span>
      );
    case 'processing':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
          <Loader2 className="w-3 h-3 animate-spin" />
          {progress > 0 ? `${progress}%` : t('contents.transcoding.processing', 'Processing')}
        </span>
      );
    case 'completed':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300">
          <CheckCircle className="w-3 h-3" />
          {t('contents.transcoding.ready', 'Ready')}
        </span>
      );
    case 'failed':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300">
          <XCircle className="w-3 h-3" />
          {t('contents.transcoding.failed', 'Failed')}
        </span>
      );
    default:
      return <span className="text-gray-400 dark:text-gray-500">-</span>;
  }
}

interface ContentTableProps {
  showUploadModal?: boolean;
  onCloseUploadModal?: () => void;
  showFilters?: boolean;
}

export function ContentTable({ showUploadModal = false, onCloseUploadModal, showFilters = false }: ContentTableProps) {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canUpdate } = useCanPerformAction('contents', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('contents', 'delete');

  // Standardized pagination hook
  const pagination = usePagination({ pageSize: 20 });

  // Sorting - URL state persistence
  const { sortConfig, onSortChange, sortParams } = useTableSort({
    defaultSort: { key: 'created_at', direction: 'desc' },
  });

  const [filters, setFilters] = useState<ContentFilters>({});
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [contentToDelete, setContentToDelete] = useState<Content | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  // Selection state - using shared hook
  const {
    selectedIds,
    isSelected,
    toggleSelection,
    toggleSelectAll,
    clearSelection,
    getSelectedItems,
  } = useTableSelection<number>();
  const [showEditModal, setShowEditModal] = useState(false);
  const [showBulkEditModal, setShowBulkEditModal] = useState(false);
  const [showBulkTagModal, setShowBulkTagModal] = useState(false);
  const [showTagAssignModal, setShowTagAssignModal] = useState(false);
  const [showPlaylistAssignModal, setShowPlaylistAssignModal] = useState(false);

  // Hooks - merge filters with pagination and sorting
  const { data: contentData, isLoading, error } = useContentList({
    ...filters,
    ...sortParams,
    skip: pagination.skip,
    limit: pagination.limit,
  });
  const { data: duplicateData } = useDuplicateContent();
  const { data: tagsData } = useTags();
  const deleteMutation = useDeleteContent();
  const bulkDeleteMutation = useBulkDeleteContent();

  // State for expand/collapse groups
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Build duplicate lookup map
  // Note: After API interceptor unwrap, duplicateData is the array directly (not {data: [...]})
  const duplicateMap = useMemo(() => {
    const map = new Map<number, { hash: string; usage: ContentUsage; group: DuplicateGroup }>();
    // Handle both wrapped and unwrapped response formats
    const groups: DuplicateGroup[] = Array.isArray(duplicateData)
      ? duplicateData
      : (duplicateData?.data || []);

    groups.forEach((group: DuplicateGroup) => {
      group.contents.forEach((item) => {
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

  // Check if content has usage
  const hasUsage = (usage: ContentUsage): boolean => {
    return (
      (usage.playlists?.length ?? 0) > 0 ||
      (usage.tags?.length ?? 0) > 0 ||
      (usage.devices?.length ?? 0) > 0
    );
  };

  // Handlers
  const handleDownload = async (content: Content) => {
    try {
      await downloadContent(content.id, content.original_filename);
      toast.success(t('contents.messages.downloadStarted'));
    } catch (error: unknown) {
      toast.error(getApiErrorMessage(error, t('contents.messages.downloadFailed')));
    }
  };

  // PERFORMANCE: useCallback to prevent unnecessary re-renders
  const handleFilterChange = useCallback((key: keyof ContentFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    pagination.resetPage();
  }, [pagination]);

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

  const handleEdit = (content: Content) => {
    setSelectedContent(content);
    setShowEditModal(true);
  };

  const handleBulkEdit = () => {
    if (selectedIds.size === 0) {
      toast.error(t('contents.messages.selectAtLeastOne'));
      return;
    }
    setShowBulkEditModal(true);
  };

  const handleBulkTag = () => {
    if (selectedIds.size === 0) {
      toast.error(t('contents.messages.selectAtLeastOne'));
      return;
    }
    setShowBulkTagModal(true);
  };

  const handleTagAssign = (content: Content) => {
    setSelectedContent(content);
    setShowTagAssignModal(true);
  };

  const handlePlaylistAssign = (content: Content) => {
    setSelectedContent(content);
    setShowPlaylistAssignModal(true);
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) {
      toast.error(t('contents.messages.selectAtLeastOne'));
      return;
    }
    if (confirm(t('contents.dialogs.bulkDeleteMessage', { count: selectedIds.size }))) {
      await bulkDeleteMutation.mutateAsync(Array.from(selectedIds));
      clearSelection();
    }
  };

  const getSelectedContent = (): Content[] => {
    return getSelectedItems(contentData?.data || []);
  };

  // Computed pagination values
  const total = contentData?.pagination?.total || 0;
  const totalPages = pagination.getTotalPages(total);

  return (
    <div className="space-y-4">
      {/* Filters - controlled by parent */}
      {showFilters && (
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('contents.filters.contentType')}
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
                <option value="">{t('contents.filters.allTypes')}</option>
                <option value="image">{t('contents.filters.image')}</option>
                <option value="video">{t('contents.filters.video')}</option>
                <option value="audio">{t('contents.filters.audio')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('contents.filters.status')}
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
                <option value="">{t('contents.filters.allStatus')}</option>
                <option value="true">{t('contents.filters.active')}</option>
                <option value="false">{t('contents.filters.inactive')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('contents.filters.tags')}
              </label>
              <select
                value={filters.tag_ids?.length === 1 ? filters.tag_ids[0].toString() : ''}
                onChange={(e) =>
                  handleFilterChange(
                    'tag_ids',
                    e.target.value ? [parseInt(e.target.value)] : undefined
                  )
                }
                className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              >
                <option value="">{t('contents.filters.allTags')}</option>
                {tagsData?.map((tag) => (
                  <option key={tag.id} value={tag.id}>
                    {tag.tag_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <Button variant="ghost" onClick={clearFilters}>
                {t('contents.actions.clearFilters')}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Actions Toolbar */}
      {selectedIds.size > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-center justify-between">
          <p className="text-sm font-medium text-blue-900 dark:text-blue-300">
            {t('contents.selection.itemsSelected', { count: selectedIds.size })}
          </p>
          <div className="flex gap-2">
            {canUpdate && (
              <>
                <Button
                  variant="primary"
                  onClick={handleBulkEdit}
                  leftIcon={<Pencil className="w-4 h-4" />}
                >
                  {t('contents.actions.bulkEdit')}
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleBulkTag}
                  leftIcon={<Filter className="w-4 h-4" />}
                  className="!bg-purple-600 hover:!bg-purple-700 !text-white"
                >
                  {t('contents.actions.bulkTag')}
                </Button>
              </>
            )}
            {canDelete && (
              <Button
                variant="danger"
                onClick={handleBulkDelete}
                leftIcon={<Trash2 className="w-4 h-4" />}
              >
                {t('contents.actions.deleteSelected')}
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Empty State - No box wrapper */}
      {!isLoading && !error && (!contentData || contentData.data.length === 0) && (
        <EmptyState
          icon={FileImage}
          title={t('contents.empty.title', 'No content found')}
          description={t('contents.empty.description', 'Upload your first media file to get started')}
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
        <div className={TABLE_STYLES.container}>
          <TableSkeleton columns={10} rows={10} />
        </div>
      )}

      {/* Table - Only when has data */}
      {!isLoading && !error && contentData && contentData.data.length > 0 && (
        <div className={TABLE_STYLES.container}>
          <>
            <div className="overflow-x-auto">
              <table className={`${TABLE_STYLES.table} table-fixed`}>
                <thead className={TABLE_STYLES.thead}>
                  <tr>
                    <th className="w-10 px-2 py-3 text-center">
                      <input
                        type="checkbox"
                        checked={selectedIds.size > 0 && selectedIds.size === contentData?.data.length}
                        onChange={() => toggleSelectAll(contentData?.data || [])}
                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                    </th>
                    <th className="w-72 px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      <SortableTableHeader
                        columnKey="original_filename"
                        sortConfig={sortConfig}
                        onSortChange={onSortChange}
                      >
                        {t('contents.table.content')}
                      </SortableTableHeader>
                    </th>
                    <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      <SortableTableHeader
                        columnKey="is_active"
                        sortConfig={sortConfig}
                        onSortChange={onSortChange}
                      >
                        {t('contents.table.status')}
                      </SortableTableHeader>
                    </th>
                    <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      <SortableTableHeader
                        columnKey="file_size"
                        sortConfig={sortConfig}
                        onSortChange={onSortChange}
                      >
                        {t('contents.table.size')}
                      </SortableTableHeader>
                    </th>
                    <th className="w-24 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      <SortableTableHeader
                        columnKey="content_type"
                        sortConfig={sortConfig}
                        onSortChange={onSortChange}
                      >
                        {t('contents.table.type')}
                      </SortableTableHeader>
                    </th>
                    <th className="w-16 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      <SortableTableHeader
                        columnKey="duration"
                        sortConfig={sortConfig}
                        onSortChange={onSortChange}
                      >
                        {t('contents.table.duration')}
                      </SortableTableHeader>
                    </th>
                    <th className="w-24 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      <SortableTableHeader
                        columnKey="transcoding_status"
                        sortConfig={sortConfig}
                        onSortChange={onSortChange}
                      >
                        {t('contents.table.transcoding', 'Transcoding')}
                      </SortableTableHeader>
                    </th>
                    <th className="w-28 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      <SortableTableHeader
                        columnKey="created_at"
                        sortConfig={sortConfig}
                        onSortChange={onSortChange}
                      >
                        {t('contents.table.uploaded', 'Uploaded')}
                      </SortableTableHeader>
                    </th>
                    <th className="w-44 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      {t('contents.table.actions')}
                    </th>
                  </tr>
                </thead>
                <tbody className={TABLE_STYLES.tbody}>
                  {(() => {
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
                                    className="w-10 h-10 rounded object-cover flex-shrink-0"
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
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span className="px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                                {t('contents.duplicates.sameFile')}
                              </span>
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

                            const itemUsage = dupItem.usage;
                            const itemHasUsage = hasUsage(itemUsage);

                            rows.push(
                              <tr
                                key={`dup-${dupItem.id}`}
                                className="hover:bg-gray-50 dark:hover:bg-gray-700 bg-gray-50/50 dark:bg-gray-800/50"
                              >
                                <td className="px-4 py-3 text-center">
                                  <div className="flex items-center justify-center">
                                    <div className="w-4 border-l-2 border-b-2 border-orange-300 dark:border-orange-700 h-4 mr-1" />
                                    <input
                                      type="checkbox"
                                      checked={isSelected(fullContent.id)}
                                      onChange={(e) => {
                                        e.stopPropagation();
                                        toggleSelection(fullContent.id);
                                      }}
                                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                                    />
                                  </div>
                                </td>
                                <td className="px-3 py-3 overflow-hidden">
                                  <div className="flex items-center min-w-0 pl-4">
                                    {fullContent.thumbnail_url ? (
                                      <img
                                        src={fullContent.thumbnail_url}
                                        alt={fullContent.title}
                                        className="w-8 h-8 rounded object-cover mr-2 flex-shrink-0"
                                      />
                                    ) : (
                                      <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center mr-2 flex-shrink-0">
                                        {getContentTypeIcon(fullContent.content_type)}
                                      </div>
                                    )}
                                    <div className="min-w-0 flex-1 overflow-hidden">
                                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate" title={fullContent.title}>
                                        {fullContent.title}
                                      </p>
                                      <p className="text-xs text-gray-400 truncate" title={fullContent.original_filename}>
                                        {fullContent.original_filename}
                                      </p>
                                    </div>
                                  </div>
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap">
                                  <div className="flex items-center gap-2">
                                    <span
                                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                                        fullContent.is_active
                                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                                      }`}
                                    >
                                      {fullContent.is_active ? t('contents.status.active') : t('contents.status.inactive')}
                                    </span>
                                    {!itemHasUsage && (
                                      <span className="w-2 h-2 rounded-full bg-green-400" title={t('contents.usage.safeToDelete')} />
                                    )}
                                  </div>
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                  {formatFileSize(fullContent.file_size)}
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap">
                                  <div className="flex flex-col">
                                    <span className="px-2 py-0.5 text-xs font-medium rounded bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 w-fit">
                                      {getFileTypeLabel(fullContent.mime_type)}
                                    </span>
                                    {fullContent.resolution && (
                                      <span className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                        {fullContent.resolution}
                                      </span>
                                    )}
                                    {/* Usage indicators in small text */}
                                    {itemHasUsage && (
                                      <div className="flex items-center gap-2 mt-0.5">
                                        {itemUsage.playlists.length > 0 && (
                                          <span className="text-xs text-blue-600 dark:text-blue-400" title={itemUsage.playlists.map(p => p.name).join(', ')}>
                                            <List className="w-3 h-3 inline mr-0.5" />{itemUsage.playlists.length}
                                          </span>
                                        )}
                                        {itemUsage.tags.length > 0 && (
                                          <span className="text-xs text-purple-600 dark:text-purple-400" title={itemUsage.tags.map(t => t.name).join(', ')}>
                                            <Tag className="w-3 h-3 inline mr-0.5" />{itemUsage.tags.length}
                                          </span>
                                        )}
                                        {itemUsage.devices.length > 0 && (
                                          <span className="text-xs text-green-600 dark:text-green-400" title={itemUsage.devices.map(d => d.name).join(', ')}>
                                            <Monitor className="w-3 h-3 inline mr-0.5" />{itemUsage.devices.length}
                                          </span>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                  {fullContent.duration}s
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap">
                                  <TranscodingBadge contentType={fullContent.content_type} status={fullContent.transcoding_status} progress={fullContent.transcoding_progress} />
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap">
                                  <div className="flex flex-col">
                                    <DateCell date={fullContent.created_at} />
                                    {fullContent.uploaded_by_name && (
                                      <span className="text-xs text-gray-500 dark:text-gray-400 truncate" title={fullContent.uploaded_by_name}>
                                        {fullContent.uploaded_by_name}
                                      </span>
                                    )}
                                  </div>
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm">
                                  <div className="flex items-center gap-1">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handlePreview(fullContent);
                                      }}
                                      className={ACTION_BUTTON.VIEW}
                                      title={t('contents.actions.preview')}
                                    >
                                      <Eye className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleDownload(fullContent);
                                      }}
                                      className={ACTION_BUTTON.DOWNLOAD}
                                      title={t('contents.actions.download')}
                                    >
                                      <Download className="w-4 h-4" />
                                    </button>
                                    {canUpdate && (
                                      <>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleTagAssign(fullContent);
                                          }}
                                          className={ACTION_BUTTON.ASSIGN}
                                          title={t('contents.actions.assignTag', 'Assign Tag')}
                                        >
                                          <Tag className="w-4 h-4" />
                                        </button>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handlePlaylistAssign(fullContent);
                                          }}
                                          className={ACTION_BUTTON.ASSIGN}
                                          title={t('contents.actions.assignPlaylist', 'Assign Playlist')}
                                        >
                                          <ListMusic className="w-4 h-4" />
                                        </button>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleEdit(fullContent);
                                          }}
                                          className={ACTION_BUTTON.EDIT}
                                          title={t('contents.actions.edit')}
                                        >
                                          <Pencil className="w-4 h-4" />
                                        </button>
                                      </>
                                    )}
                                    {canDelete && (
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setContentToDelete(fullContent);
                                        }}
                                        className={ACTION_BUTTON.DELETE}
                                        title={t('contents.actions.delete')}
                                      >
                                        <Trash2 className="w-4 h-4" />
                                      </button>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            );
                          });
                        }
                      }
                      // Skip content that's already rendered as part of a group
                      else if (dupInfo) {
                        return;
                      }
                      // Regular content (not a duplicate)
                      else {
                        rows.push(
                          <tr key={content.id} className={TABLE_STYLES.tr}>
                            <td className="px-4 py-3 text-center">
                              <input
                                type="checkbox"
                                checked={isSelected(content.id)}
                                onChange={() => toggleSelection(content.id)}
                                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                              />
                            </td>
                            <td className="px-3 py-3 overflow-hidden">
                              <div className="flex items-center min-w-0">
                                {content.thumbnail_url ? (
                                  <img
                                    src={content.thumbnail_url}
                                    alt={content.title}
                                    className="w-10 h-10 rounded object-cover mr-2 flex-shrink-0"
                                  />
                                ) : (
                                  <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center mr-2 flex-shrink-0">
                                    {getContentTypeIcon(content.content_type)}
                                  </div>
                                )}
                                <div className="min-w-0 flex-1 overflow-hidden">
                                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate" title={content.title}>
                                    {content.title}
                                  </p>
                                  {content.description && (
                                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate" title={content.description}>
                                      {content.description}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span
                                className={`px-2 py-1 text-xs font-medium rounded-full ${
                                  content.is_active
                                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                                }`}
                              >
                                {content.is_active ? t('contents.status.active') : t('contents.status.inactive')}
                              </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {formatFileSize(content.file_size)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <div className="flex flex-col">
                                <span className="px-2 py-0.5 text-xs font-medium rounded bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 w-fit">
                                  {getFileTypeLabel(content.mime_type)}
                                </span>
                                {content.resolution && (
                                  <span className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                    {content.resolution}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {content.duration}s
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <TranscodingBadge contentType={content.content_type} status={content.transcoding_status} progress={content.transcoding_progress} />
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <div className="flex flex-col">
                                <DateCell date={content.created_at} />
                                {content.uploaded_by_name && (
                                  <span className="text-xs text-gray-500 dark:text-gray-400 truncate" title={content.uploaded_by_name}>
                                    {content.uploaded_by_name}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() => handlePreview(content)}
                                  className={ACTION_BUTTON.VIEW}
                                  title={t('contents.actions.preview')}
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleDownload(content)}
                                  className={ACTION_BUTTON.DOWNLOAD}
                                  title={t('contents.actions.download')}
                                >
                                  <Download className="w-4 h-4" />
                                </button>
                                {canUpdate && (
                                  <>
                                    <button
                                      onClick={() => handleTagAssign(content)}
                                      className={ACTION_BUTTON.ASSIGN}
                                      title={t('contents.actions.assignTag', 'Assign Tag')}
                                    >
                                      <Tag className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={() => handlePlaylistAssign(content)}
                                      className={ACTION_BUTTON.ASSIGN}
                                      title={t('contents.actions.assignPlaylist', 'Assign Playlist')}
                                    >
                                      <ListMusic className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={() => handleEdit(content)}
                                      className={ACTION_BUTTON.EDIT}
                                      title={t('contents.actions.edit')}
                                    >
                                      <Pencil className="w-4 h-4" />
                                    </button>
                                  </>
                                )}
                                {canDelete && (
                                  <button
                                    onClick={() => setContentToDelete(content)}
                                    className={ACTION_BUTTON.DELETE}
                                    title={t('contents.actions.delete')}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      }
                    });

                    return rows;
                  })()}
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
        </div>
      )}

      {/* Upload Modal */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => onCloseUploadModal?.()}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={!!contentToDelete}
        onOpenChange={(open) => !open && setContentToDelete(null)}
        title={t('contents.dialogs.deleteTitle')}
        description={t('contents.dialogs.deleteMessage', { name: contentToDelete?.title })}
        variant="danger"
        confirmLabel={t('contents.actions.delete')}
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

      {/* Content Tag Assignment Modal */}
      <ContentTagAssignmentModal
        isOpen={showTagAssignModal}
        onClose={() => {
          setShowTagAssignModal(false);
          // Don't clear selectedContent here as it might be used for preview
        }}
        selectedContent={selectedContent ? [selectedContent] : []}
      />

      {/* Content Playlist Assignment Modal */}
      <ContentPlaylistAssignmentModal
        isOpen={showPlaylistAssignModal}
        onClose={() => {
          setShowPlaylistAssignModal(false);
          // Don't clear selectedContent here as it might be used for preview
        }}
        selectedContent={selectedContent ? [selectedContent] : []}
      />
    </div>
  );
}
