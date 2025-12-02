/**
 * Content Table Component
 *
 * LAYER 1: PRESENTATION
 * Content management table with upload, filter, and preview
 */

import { useState, useMemo } from 'react';
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
  ChevronDown,
  ChevronRight,
  Copy,
  List,
  Tag,
  Monitor,
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
  TABLE_STYLES,
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
import type { Content, ContentType, ContentFilters, DuplicateGroup, ContentUsage } from '../types/content';
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
  const { data: duplicateData } = useDuplicateContent();
  const { data: tagsData } = useTags();
  const deleteMutation = useDeleteContent();
  const bulkDeleteMutation = useBulkDeleteContent();

  // State for expanded duplicate groups
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Build duplicate lookup map
  const duplicateMap = useMemo(() => {
    const map = new Map<number, { hash: string; usage: ContentUsage; group: DuplicateGroup }>();
    const groups = Array.isArray(duplicateData) ? duplicateData : (duplicateData as any)?.data || [];

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
    return usage.playlists.length > 0 || usage.tags.length > 0 || usage.devices.length > 0;
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

  const handleFilterChange = (key: keyof ContentFilters, value: any) => {
    console.log('[ContentTable] Filter change:', key, '=', value);
    setFilters((prev) => {
      const newFilters = { ...prev, [key]: value };
      console.log('[ContentTable] New filters:', newFilters);
      return newFilters;
    });
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

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) {
      toast.error(t('contents.messages.selectAtLeastOne'));
      return;
    }
    if (confirm(t('contents.dialogs.bulkDeleteMessage', { count: selectedIds.size }))) {
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
          {t('contents.actions.filters')}
        </Button>
        {canCreate && (
          <Button
            variant="primary"
            onClick={() => setShowUploadModal(true)}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            {t('contents.actions.upload')}
          </Button>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg space-y-4">
          <div className="grid grid-cols-4 gap-4">
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

      {/* Content Stats */}
      {contentData && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {t('contents.stats.showingItems', { count: contentData.data.length, total: contentData.pagination.total })}
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
                  leftIcon={<Edit className="w-4 h-4" />}
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
          <TableSkeleton columns={7} rows={10} />
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
                    <th className="px-4 py-3 text-center w-12">
                      <input
                        type="checkbox"
                        checked={selectedIds.size > 0 && selectedIds.size === contentData?.data.length}
                        onChange={toggleSelectAll}
                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                    </th>
                    <th className={`${TABLE_STYLES.th} w-[35%]`}>
                      {t('contents.table.content')}
                    </th>
                    <th className={`${TABLE_STYLES.th} w-20`}>
                      {t('contents.table.status')}
                    </th>
                    <th className={`${TABLE_STYLES.th} w-20`}>
                      {t('contents.table.type')}
                    </th>
                    <th className={`${TABLE_STYLES.th} w-24`}>
                      {t('contents.table.size')}
                    </th>
                    <th className={`${TABLE_STYLES.th} w-20`}>
                      {t('contents.table.duration')}
                    </th>
                    <th className={`${TABLE_STYLES.th} w-32`}>
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
                            <td className="px-4 py-3 text-center">
                              {isExpanded ? (
                                <ChevronDown className="w-4 h-4 text-orange-600" />
                              ) : (
                                <ChevronRight className="w-4 h-4 text-orange-600" />
                              )}
                            </td>
                            <td className="px-4 py-3" colSpan={2}>
                              <div className="flex items-center gap-3">
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
                                <div>
                                  <div className="flex items-center gap-2">
                                    <Copy className="w-4 h-4 text-orange-600" />
                                    <span className="font-medium text-orange-800 dark:text-orange-200">
                                      {t('contents.duplicates.count', { count: group.duplicate_count })}
                                    </span>
                                  </div>
                                  <span className="text-xs text-orange-600 dark:text-orange-400 font-mono">
                                    {t('contents.duplicates.hash')}: {group.file_hash.slice(0, 16)}...
                                  </span>
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-orange-700 dark:text-orange-300">
                              {formatFileSize(group.file_size)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-orange-700 dark:text-orange-300">
                              -
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span className="px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                                {t('contents.duplicates.sameFile')}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm text-orange-600 dark:text-orange-400">
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
                                      checked={selectedIds.has(fullContent.id)}
                                      onChange={(e) => {
                                        e.stopPropagation();
                                        toggleSelection(fullContent.id);
                                      }}
                                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                                    />
                                  </div>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex items-center min-w-0 pl-4">
                                    {fullContent.thumbnail_url ? (
                                      <img
                                        src={fullContent.thumbnail_url}
                                        alt={fullContent.title}
                                        className="w-8 h-8 rounded object-cover mr-3 flex-shrink-0"
                                      />
                                    ) : (
                                      <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center mr-3 flex-shrink-0">
                                        {getContentTypeIcon(fullContent.content_type)}
                                      </div>
                                    )}
                                    <div className="min-w-0 flex-1">
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
                                <td className="px-4 py-3 whitespace-nowrap">
                                  {/* Usage indicators */}
                                  <div className="flex flex-col gap-0.5">
                                    {itemUsage.playlists.length > 0 && (
                                      <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
                                        <List className="w-3 h-3" />
                                        <span>{t('contents.usage.playlists', { count: itemUsage.playlists.length })}</span>
                                      </div>
                                    )}
                                    {itemUsage.tags.length > 0 && (
                                      <div className="flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400">
                                        <Tag className="w-3 h-3" />
                                        <span>{t('contents.usage.tags', { count: itemUsage.tags.length })}</span>
                                      </div>
                                    )}
                                    {itemUsage.devices.length > 0 && (
                                      <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                                        <Monitor className="w-3 h-3" />
                                        <span>{t('contents.usage.devices', { count: itemUsage.devices.length })}</span>
                                      </div>
                                    )}
                                    {!itemHasUsage && (
                                      <span className="text-xs text-gray-400">{t('contents.usage.notUsed')}</span>
                                    )}
                                  </div>
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                  {formatFileSize(fullContent.file_size)}
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                  {fullContent.duration}s
                                </td>
                                <td className="px-4 py-3 whitespace-nowrap text-sm">
                                  <div className="flex items-center gap-1">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handlePreview(fullContent);
                                      }}
                                      className={TABLE_STYLES.actionBtnBlue}
                                      title={t('contents.actions.preview')}
                                    >
                                      <Eye className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleDownload(fullContent);
                                      }}
                                      className={TABLE_STYLES.actionBtnGray}
                                      title={t('contents.actions.download')}
                                    >
                                      <Download className="w-4 h-4" />
                                    </button>
                                    {canUpdate && (
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleEdit(fullContent);
                                        }}
                                        className={TABLE_STYLES.actionBtnGreen}
                                        title={t('contents.actions.edit')}
                                      >
                                        <Edit className="w-4 h-4" />
                                      </button>
                                    )}
                                    {canDelete && (
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setContentToDelete(fullContent);
                                        }}
                                        className={TABLE_STYLES.actionBtnRed}
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
                                checked={selectedIds.has(content.id)}
                                onChange={() => toggleSelection(content.id)}
                                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                              />
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center min-w-0">
                                {content.thumbnail_url ? (
                                  <img
                                    src={content.thumbnail_url}
                                    alt={content.title}
                                    className="w-10 h-10 rounded object-cover mr-3 flex-shrink-0"
                                  />
                                ) : (
                                  <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center mr-3 flex-shrink-0">
                                    {getContentTypeIcon(content.content_type)}
                                  </div>
                                )}
                                <div className="min-w-0 flex-1">
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
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span className="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                                {getFileTypeLabel(content.mime_type)}
                              </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {formatFileSize(content.file_size)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {content.duration}s
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() => handlePreview(content)}
                                  className={TABLE_STYLES.actionBtnBlue}
                                  title={t('contents.actions.preview')}
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleDownload(content)}
                                  className={TABLE_STYLES.actionBtnGray}
                                  title={t('contents.actions.download')}
                                >
                                  <Download className="w-4 h-4" />
                                </button>
                                {canUpdate && (
                                  <button
                                    onClick={() => handleEdit(content)}
                                    className={TABLE_STYLES.actionBtnGreen}
                                    title={t('contents.actions.edit')}
                                  >
                                    <Edit className="w-4 h-4" />
                                  </button>
                                )}
                                {canDelete && (
                                  <button
                                    onClick={() => setContentToDelete(content)}
                                    className={TABLE_STYLES.actionBtnRed}
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
        onClose={() => setShowUploadModal(false)}
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
    </div>
  );
}
