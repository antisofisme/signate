/**
 * Content Gallery View Component
 * Masonry layout with sidebar detail panel
 * Uses CSS columns for masonry effect (no external library)
 * Supports duplicate grouping, bulk selection, and filtering
 */

import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Search,
  SortAsc,
  SortDesc,
  FileImage,
  FileVideo,
  FileAudio,
  Copy,
  ChevronDown,
  ChevronRight,
  Edit,
  Trash2,
  Tag,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button, EmptyState, ErrorDisplay, ConfirmDialog } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import {
  useContentList,
  useDuplicateContent,
  useBulkDeleteContent,
} from '../hooks/useContent';
import type { Content, ContentType, ContentFilters, DuplicateGroup, ContentUsage } from '../types/content';
import { formatFileSize } from '../api/contentApi';
import { ContentGalleryCard } from './ContentGalleryCard';
import { ContentDetailSidebar } from './ContentDetailSidebar';
import { UploadModal } from './UploadModal';
import { BulkEditModal } from './BulkEditModal';
import { BulkTagModal } from './BulkTagModal';

// Sort options
type SortOption = 'newest' | 'oldest' | 'name_asc' | 'name_desc' | 'size_desc' | 'size_asc' | 'duration_desc' | 'duration_asc';

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'newest', label: 'Newest First' },
  { value: 'oldest', label: 'Oldest First' },
  { value: 'name_asc', label: 'Name (A-Z)' },
  { value: 'name_desc', label: 'Name (Z-A)' },
  { value: 'size_desc', label: 'Largest First' },
  { value: 'size_asc', label: 'Smallest First' },
  { value: 'duration_desc', label: 'Longest First' },
  { value: 'duration_asc', label: 'Shortest First' },
];

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

interface ContentGalleryViewProps {
  showUploadModal?: boolean;
  onCloseUploadModal?: () => void;
  showFilters?: boolean;
}

export function ContentGalleryView({ showUploadModal = false, onCloseUploadModal, showFilters = false }: ContentGalleryViewProps) {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canUpdate } = useCanPerformAction('contents', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('contents', 'delete');

  // State
  const [filters, setFilters] = useState<ContentFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [contentTypeFilter, setContentTypeFilter] = useState<ContentType | ''>('');
  const [statusFilter, setStatusFilter] = useState<'' | 'active' | 'inactive'>('');
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Bulk selection state
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [showBulkEditModal, setShowBulkEditModal] = useState(false);
  const [showBulkTagModal, setShowBulkTagModal] = useState(false);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  // Fetch content with max allowed limit
  const { data: contentData, isLoading, error } = useContentList({
    ...filters,
    limit: 100, // Backend max limit
  });

  // Fetch duplicate data
  const { data: duplicateData } = useDuplicateContent();

  // Mutations
  const bulkDeleteMutation = useBulkDeleteContent();

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

  // Filter and sort content client-side
  const filteredAndSortedContent = useMemo(() => {
    if (!contentData?.data) return [];

    let result = [...contentData.data];

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (content) =>
          content.title.toLowerCase().includes(query) ||
          content.original_filename.toLowerCase().includes(query) ||
          content.description?.toLowerCase().includes(query)
      );
    }

    // Filter by content type
    if (contentTypeFilter) {
      result = result.filter((content) => content.content_type === contentTypeFilter);
    }

    // Filter by status
    if (statusFilter) {
      result = result.filter((content) =>
        statusFilter === 'active' ? content.is_active : !content.is_active
      );
    }

    // Sort
    switch (sortBy) {
      case 'newest':
        result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        break;
      case 'oldest':
        result.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        break;
      case 'name_asc':
        result.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case 'name_desc':
        result.sort((a, b) => b.title.localeCompare(a.title));
        break;
      case 'size_desc':
        result.sort((a, b) => b.file_size - a.file_size);
        break;
      case 'size_asc':
        result.sort((a, b) => a.file_size - b.file_size);
        break;
      case 'duration_desc':
        result.sort((a, b) => b.duration - a.duration);
        break;
      case 'duration_asc':
        result.sort((a, b) => a.duration - b.duration);
        break;
    }

    return result;
  }, [contentData?.data, searchQuery, contentTypeFilter, statusFilter, sortBy]);

  // Handle content selection (for sidebar)
  const handleSelectContent = (content: Content) => {
    // If clicking same content, close sidebar; otherwise select and open
    if (selectedContent?.id === content.id) {
      setIsSidebarOpen(false);
    } else {
      setSelectedContent(content);
      setIsSidebarOpen(true);
    }
  };

  // Handle sidebar close
  const handleCloseSidebar = () => {
    setIsSidebarOpen(false);
  };

  // Handle checkbox selection (for bulk actions)
  const handleCheckboxChange = (id: number, checked: boolean) => {
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(id);
      } else {
        newSet.delete(id);
      }
      return newSet;
    });
  };

  // Select all visible content
  const handleSelectAll = () => {
    if (selectedIds.size === filteredAndSortedContent.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredAndSortedContent.map((c) => c.id)));
    }
  };

  // Handle content update from sidebar
  const handleContentUpdate = (updatedContent: Content) => {
    setSelectedContent(updatedContent);
  };

  // Handle content delete from sidebar
  const handleContentDelete = () => {
    setSelectedContent(null);
    setIsSidebarOpen(false);
  };

  // Bulk operations
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
    await bulkDeleteMutation.mutateAsync(Array.from(selectedIds));
    setSelectedIds(new Set());
    setShowBulkDeleteConfirm(false);
    // Close sidebar if selected content was deleted
    if (selectedContent && selectedIds.has(selectedContent.id)) {
      setSelectedContent(null);
    }
  };

  const getSelectedContent = (): Content[] => {
    return contentData?.data.filter((c) => selectedIds.has(c.id)) || [];
  };

  // Clear filters
  const clearFilters = () => {
    setSearchQuery('');
    setContentTypeFilter('');
    setStatusFilter('');
  };

  // Calculate duplicate group count
  const duplicateGroupCount = useMemo(() => {
    const groups = Array.isArray(duplicateData) ? duplicateData : (duplicateData as any)?.data || [];
    return groups.length;
  }, [duplicateData]);

  return (
    <div className="flex flex-col lg:flex-row gap-4 lg:gap-6 h-auto lg:h-[calc(100vh-280px)] min-h-[300px] lg:min-h-[500px]">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div className="flex items-center gap-4 mb-4 flex-wrap">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder={t('contents.gallery.searchPlaceholder', 'Search content...')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
              className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {t(`contents.gallery.sort.${option.value}`, option.label)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg mb-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('contents.filters.contentType')}
                </label>
                <select
                  value={contentTypeFilter}
                  onChange={(e) => setContentTypeFilter(e.target.value as ContentType | '')}
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
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as '' | 'active' | 'inactive')}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                >
                  <option value="">{t('contents.filters.allStatus')}</option>
                  <option value="active">{t('contents.filters.active')}</option>
                  <option value="inactive">{t('contents.filters.inactive')}</option>
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

        {/* Stats and Bulk Actions */}
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {t('contents.gallery.itemsFound', {
              count: filteredAndSortedContent.length,
              defaultValue: '{{count}} items found',
            })}
            {(searchQuery || contentTypeFilter || statusFilter) && ` (${t('contents.gallery.filtered', 'filtered')})`}
            {duplicateGroupCount > 0 && (
              <span className="ml-2 text-orange-600 dark:text-orange-400">
                ({duplicateGroupCount} {t('contents.duplicates.groups', 'duplicate group(s)')})
              </span>
            )}
          </div>

          {/* Bulk selection checkbox */}
          {filteredAndSortedContent.length > 0 && (
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selectedIds.size > 0 && selectedIds.size === filteredAndSortedContent.length}
                onChange={handleSelectAll}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {t('contents.selection.selectAll', 'Select all')}
              </span>
            </div>
          )}
        </div>

        {/* Bulk Actions Toolbar */}
        {selectedIds.size > 0 && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-center justify-between mb-4">
            <p className="text-sm font-medium text-blue-900 dark:text-blue-300">
              {t('contents.selection.itemsSelected', { count: selectedIds.size })}
            </p>
            <div className="flex gap-2">
              {canUpdate && (
                <>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleBulkEdit}
                    leftIcon={<Edit className="w-4 h-4" />}
                  >
                    {t('contents.actions.bulkEdit')}
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleBulkTag}
                    leftIcon={<Tag className="w-4 h-4" />}
                    className="!bg-purple-600 hover:!bg-purple-700 !text-white"
                  >
                    {t('contents.actions.bulkTag')}
                  </Button>
                </>
              )}
              {canDelete && (
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => setShowBulkDeleteConfirm(true)}
                  leftIcon={<Trash2 className="w-4 h-4" />}
                >
                  {t('contents.actions.deleteSelected')}
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Gallery Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Loading */}
          {isLoading && (
            <div className="masonry-grid animate-pulse">
              {Array.from({ length: 12 }).map((_, i) => (
                <div
                  key={i}
                  className="masonry-item bg-gray-200 dark:bg-gray-700 rounded-lg"
                  style={{ height: `${150 + Math.random() * 150}px` }}
                />
              ))}
            </div>
          )}

          {/* Error */}
          {error && (
            <ErrorDisplay error={error} onRetry={() => window.location.reload()} />
          )}

          {/* Empty State */}
          {!isLoading && !error && filteredAndSortedContent.length === 0 && (
            <EmptyState
              icon={FileImage}
              title={t('contents.empty.title', 'No content found')}
              description={
                searchQuery || contentTypeFilter || statusFilter
                  ? t('contents.gallery.noSearchResults', 'Try adjusting your filters')
                  : t('contents.empty.description', 'Upload your first media file to get started')
              }
            />
          )}

          {/* Masonry Grid with Duplicate Grouping */}
          {!isLoading && !error && filteredAndSortedContent.length > 0 && (
            <div className="masonry-grid">
              {(() => {
                const renderedGroups = new Set<string>();
                const elements: React.ReactNode[] = [];

                filteredAndSortedContent.forEach((content) => {
                  const dupInfo = duplicateMap.get(content.id);

                  // If this content is part of a duplicate group
                  if (dupInfo && !renderedGroups.has(dupInfo.hash)) {
                    renderedGroups.add(dupInfo.hash);
                    const group = dupInfo.group;
                    const isExpanded = expandedGroups.has(dupInfo.hash);

                    // Get all content items in this group that exist in current filtered list
                    const groupContentIds = new Set(group.contents.map((c) => c.id));
                    const groupContentItems = filteredAndSortedContent.filter((c) =>
                      groupContentIds.has(c.id)
                    );

                    // Only show as group if more than 1 item visible
                    if (groupContentItems.length <= 1) {
                      // Render as regular card
                      elements.push(
                        <ContentGalleryCard
                          key={content.id}
                          content={content}
                          isSelected={selectedIds.has(content.id)}
                          showCheckbox={selectedIds.size > 0}
                          onSelect={() => handleSelectContent(content)}
                          onCheckboxChange={(checked) => handleCheckboxChange(content.id, checked)}
                        />
                      );
                      return;
                    }

                    // Render duplicate group card
                    elements.push(
                      <div key={`group-${dupInfo.hash}`} className="masonry-item">
                        {/* Group Header Card */}
                        <div
                          className="bg-orange-50 dark:bg-orange-900/30 border-2 border-orange-300 dark:border-orange-700 rounded-lg p-3 cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-900/50 transition-colors"
                          onClick={() => toggleGroupExpand(dupInfo.hash)}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            {isExpanded ? (
                              <ChevronDown className="w-4 h-4 text-orange-600" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-orange-600" />
                            )}
                            <Copy className="w-4 h-4 text-orange-600" />
                            <span className="font-medium text-orange-800 dark:text-orange-200 text-sm">
                              {t('contents.duplicates.count', { count: groupContentItems.length })}
                            </span>
                          </div>

                          {/* Preview thumbnails */}
                          <div className="flex gap-1 mb-2">
                            {groupContentItems.slice(0, 3).map((c) => (
                              <div key={c.id} className="w-12 h-12 rounded overflow-hidden">
                                {c.thumbnail_url || c.content_type === 'image' ? (
                                  <img
                                    src={c.thumbnail_url || c.file_url}
                                    alt=""
                                    className="w-full h-full object-cover"
                                  />
                                ) : (
                                  <div className="w-full h-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                                    {getContentTypeIcon(c.content_type)}
                                  </div>
                                )}
                              </div>
                            ))}
                            {groupContentItems.length > 3 && (
                              <div className="w-12 h-12 bg-orange-200 dark:bg-orange-800 rounded flex items-center justify-center text-xs font-medium text-orange-700 dark:text-orange-300">
                                +{groupContentItems.length - 3}
                              </div>
                            )}
                          </div>

                          <div className="text-xs text-orange-600 dark:text-orange-400">
                            {t('contents.duplicates.clickToExpand', 'Click to expand')}
                          </div>
                        </div>

                        {/* Expanded: Show all items in group */}
                        {isExpanded && (
                          <div className="mt-2 space-y-2 pl-2 border-l-2 border-orange-300 dark:border-orange-700">
                            {groupContentItems.map((c) => (
                              <ContentGalleryCard
                                key={c.id}
                                content={c}
                                isSelected={selectedIds.has(c.id)}
                                showCheckbox={selectedIds.size > 0}
                                onSelect={() => handleSelectContent(c)}
                                onCheckboxChange={(checked) => handleCheckboxChange(c.id, checked)}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  }
                  // Skip if already rendered as part of group
                  else if (dupInfo) {
                    return;
                  }
                  // Regular content (not duplicate)
                  else {
                    elements.push(
                      <ContentGalleryCard
                        key={content.id}
                        content={content}
                        isSelected={selectedIds.has(content.id)}
                        showCheckbox={selectedIds.size > 0}
                        onSelect={() => handleSelectContent(content)}
                        onCheckboxChange={(checked) => handleCheckboxChange(content.id, checked)}
                      />
                    );
                  }
                });

                return elements;
              })()}
            </div>
          )}
        </div>
      </div>

      {/* Sidebar Detail Panel */}
      <ContentDetailSidebar
        content={selectedContent}
        usage={selectedContent ? duplicateMap.get(selectedContent.id)?.usage : undefined}
        isOpen={isSidebarOpen}
        onUpdate={handleContentUpdate}
        onDelete={handleContentDelete}
        onClose={handleCloseSidebar}
      />

      {/* Upload Modal */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => onCloseUploadModal?.()}
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

      {/* Bulk Delete Confirmation */}
      <ConfirmDialog
        open={showBulkDeleteConfirm}
        onOpenChange={setShowBulkDeleteConfirm}
        title={t('contents.dialogs.bulkDeleteTitle', 'Delete Selected Content')}
        description={t('contents.dialogs.bulkDeleteMessage', {
          count: selectedIds.size,
          defaultValue: 'Are you sure you want to delete {{count}} item(s)? They will be moved to the recycle bin.',
        })}
        variant="danger"
        confirmLabel={t('contents.actions.delete')}
        onConfirm={handleBulkDelete}
        isLoading={bulkDeleteMutation.isPending}
      />

      {/* CSS for Masonry and Animation */}
      <style>{`
        .masonry-grid {
          column-count: 4;
          column-gap: 16px;
        }
        .masonry-item {
          break-inside: avoid;
          margin-bottom: 16px;
        }
        @media (max-width: 1536px) {
          .masonry-grid {
            column-count: 3;
          }
        }
        @media (max-width: 1280px) {
          .masonry-grid {
            column-count: 2;
          }
        }
        @media (max-width: 768px) {
          .masonry-grid {
            column-count: 1;
          }
        }
        @keyframes slide-in-right {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        .animate-slide-in-right {
          animation: slide-in-right 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
