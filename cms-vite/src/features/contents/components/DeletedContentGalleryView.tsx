/**
 * Deleted Content Gallery View Component
 * Masonry layout for Recycle Bin items
 * Visual indicator: reduced opacity, trash overlay
 * Actions: Restore, Permanent Delete
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
  Trash2,
  RotateCcw,
  Eye,
  Play,
} from 'lucide-react';
import { Button, EmptyState, ErrorDisplay, ConfirmDialog } from '@/shared/components';
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

// Sort options
type SortOption = 'newest' | 'oldest' | 'name_asc' | 'name_desc';

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'newest', label: 'Deleted Recently' },
  { value: 'oldest', label: 'Deleted Oldest' },
  { value: 'name_asc', label: 'Name (A-Z)' },
  { value: 'name_desc', label: 'Name (Z-A)' },
];

// Get content type icon
function getContentTypeIcon(type: ContentType, className = 'w-4 h-4') {
  switch (type) {
    case 'image':
      return <FileImage className={className} />;
    case 'video':
      return <FileVideo className={className} />;
    case 'audio':
      return <FileAudio className={className} />;
  }
}

// Format duration as mm:ss
function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function DeletedContentGalleryView() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canUpdate } = useCanPerformAction('contents', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('contents', 'delete');

  // State
  const [filters] = useState<ContentFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // Modal states
  const [previewContent, setPreviewContent] = useState<Content | null>(null);
  const [contentToRestore, setContentToRestore] = useState<Content | null>(null);
  const [contentToDelete, setContentToDelete] = useState<Content | null>(null);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  // Fetch deleted content
  const { data: contentData, isLoading, error } = useDeletedContentList({
    ...filters,
    limit: 100,
  });

  // Mutations
  const restoreMutation = useRestoreContent();
  const permanentDeleteMutation = usePermanentDeleteContent();
  const bulkPermanentDeleteMutation = useBulkPermanentDeleteContent();

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
          content.original_filename.toLowerCase().includes(query)
      );
    }

    // Sort
    switch (sortBy) {
      case 'newest':
        result.sort((a, b) => {
          const dateA = a.deleted_at ? new Date(a.deleted_at).getTime() : 0;
          const dateB = b.deleted_at ? new Date(b.deleted_at).getTime() : 0;
          return dateB - dateA;
        });
        break;
      case 'oldest':
        result.sort((a, b) => {
          const dateA = a.deleted_at ? new Date(a.deleted_at).getTime() : 0;
          const dateB = b.deleted_at ? new Date(b.deleted_at).getTime() : 0;
          return dateA - dateB;
        });
        break;
      case 'name_asc':
        result.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case 'name_desc':
        result.sort((a, b) => b.title.localeCompare(a.title));
        break;
    }

    return result;
  }, [contentData?.data, searchQuery, sortBy]);

  // Selection handlers
  const toggleSelect = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
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

  const handleSelectAll = () => {
    if (selectedIds.size === filteredAndSortedContent.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredAndSortedContent.map((c) => c.id)));
    }
  };

  // Action handlers
  const handleRestore = async () => {
    if (contentToRestore) {
      await restoreMutation.mutateAsync(contentToRestore.id);
      setContentToRestore(null);
      // Remove from selection if restored
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(contentToRestore.id);
        return newSet;
      });
    }
  };

  const handlePermanentDelete = async () => {
    if (contentToDelete) {
      await permanentDeleteMutation.mutateAsync(contentToDelete.id);
      setContentToDelete(null);
      // Remove from selection if deleted
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(contentToDelete.id);
        return newSet;
      });
    }
  };

  const handleBulkPermanentDelete = async () => {
    await bulkPermanentDeleteMutation.mutateAsync(Array.from(selectedIds));
    setSelectedIds(new Set());
    setShowBulkDeleteConfirm(false);
  };

  // Determine if content has thumbnail
  const getThumbnailUrl = (content: Content) => {
    if (content.thumbnail_url) return content.thumbnail_url;
    if (content.content_type === 'image') return content.file_url;
    return null;
  };

  // Get gradient for non-image content
  const getGradientClass = (type: ContentType) => {
    switch (type) {
      case 'video':
        return 'bg-gradient-to-br from-slate-700 to-slate-900';
      case 'audio':
        return 'bg-gradient-to-br from-purple-600 to-purple-900';
      default:
        return 'bg-gradient-to-br from-gray-600 to-gray-800';
    }
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder={t('contents.gallery.searchPlaceholder', 'Search deleted content...')}
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
                {t(`contents.deleted.sort.${option.value}`, option.label)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats and Selection */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {filteredAndSortedContent.length > 0
            ? t('contents.deleted.showingItems', {
                count: filteredAndSortedContent.length,
                total: contentData?.pagination?.total || 0,
              })
            : t('contents.deleted.noItems')}
        </div>

        {filteredAndSortedContent.length > 0 && (
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={selectedIds.size > 0 && selectedIds.size === filteredAndSortedContent.length}
              onChange={handleSelectAll}
              className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500"
            />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {t('contents.selection.selectAll', 'Select all')}
            </span>
          </div>
        )}
      </div>

      {/* Bulk Action Bar */}
      {selectedIds.size > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-red-700 dark:text-red-300">
              {t('contents.selection.itemsSelected', { count: selectedIds.size })}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedIds(new Set())}
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

      {/* Gallery Content */}
      <div className="min-h-[400px]">
        {/* Loading */}
        {isLoading && (
          <div className="masonry-grid animate-pulse">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="masonry-item bg-gray-200 dark:bg-gray-700 rounded-lg"
                style={{ height: `${150 + Math.random() * 100}px` }}
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
            icon={Trash2}
            title={t('contents.deleted.empty.title', 'Recycle Bin is Empty')}
            description={
              searchQuery
                ? t('contents.gallery.noSearchResults', 'Try adjusting your search')
                : t('contents.deleted.empty.description', 'Deleted content will appear here for recovery')
            }
          />
        )}

        {/* Masonry Grid */}
        {!isLoading && !error && filteredAndSortedContent.length > 0 && (
          <div className="masonry-grid">
            {filteredAndSortedContent.map((content) => {
              const thumbnailUrl = getThumbnailUrl(content);

              return (
                <div
                  key={content.id}
                  className={`masonry-item relative group cursor-pointer rounded-lg overflow-hidden transition-all duration-200 ${
                    selectedIds.has(content.id)
                      ? 'ring-2 ring-red-500 ring-offset-2 dark:ring-offset-gray-900'
                      : 'hover:ring-2 hover:ring-gray-300 dark:hover:ring-gray-600'
                  }`}
                >
                  {/* Content Display with Deleted Overlay */}
                  <div className="relative">
                    {thumbnailUrl ? (
                      <img
                        src={thumbnailUrl}
                        alt={content.title}
                        className="w-full h-auto object-cover opacity-60 grayscale"
                        loading="lazy"
                      />
                    ) : (
                      <div className={`w-full aspect-video flex items-center justify-center opacity-60 grayscale ${getGradientClass(content.content_type)}`}>
                        {getContentTypeIcon(content.content_type, 'w-12 h-12 text-white/50')}
                      </div>
                    )}

                    {/* Deleted Overlay */}
                    <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                      <div className="bg-red-500/80 rounded-full p-3">
                        <Trash2 className="w-6 h-6 text-white" />
                      </div>
                    </div>
                  </div>

                  {/* Content Type Badge - Top Left */}
                  <div className="absolute top-2 left-2 p-1.5 bg-black/50 rounded-md">
                    {getContentTypeIcon(content.content_type, 'w-4 h-4 text-white')}
                  </div>

                  {/* Checkbox - Top Left, below type badge */}
                  <div
                    className="absolute top-12 left-2"
                    onClick={(e) => toggleSelect(content.id, e)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.has(content.id)}
                      onChange={() => {}}
                      className="w-5 h-5 text-red-600 bg-white/90 border-2 border-white rounded focus:ring-red-500 cursor-pointer"
                    />
                  </div>

                  {/* Play Icon for video/audio */}
                  {(content.content_type === 'video' || content.content_type === 'audio') && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="w-12 h-12 bg-black/30 rounded-full flex items-center justify-center">
                        <Play className="w-6 h-6 text-white/50 ml-1" fill="white" fillOpacity={0.5} />
                      </div>
                    </div>
                  )}

                  {/* Duration Badge - Bottom Right */}
                  {(content.content_type === 'video' || content.content_type === 'audio') && content.duration > 0 && (
                    <div className="absolute bottom-2 right-2 px-2 py-0.5 bg-black/70 text-white/70 text-xs rounded">
                      {formatDuration(content.duration)}
                    </div>
                  )}

                  {/* Hover Overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                    {/* Actions - Top Right */}
                    <div className="absolute top-2 right-2 flex gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setPreviewContent(content);
                        }}
                        className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-white dark:hover:bg-gray-700 transition-colors"
                        title={t('contents.actions.preview')}
                      >
                        <Eye className="w-4 h-4 text-blue-600" />
                      </button>
                      {canUpdate && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setContentToRestore(content);
                          }}
                          className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-green-50 dark:hover:bg-green-900/50 transition-colors"
                          title={t('contents.deleted.restore')}
                        >
                          <RotateCcw className="w-4 h-4 text-green-600" />
                        </button>
                      )}
                      {canDelete && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setContentToDelete(content);
                          }}
                          className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-red-50 dark:hover:bg-red-900/50 transition-colors"
                          title={t('contents.deleted.deletePermanently')}
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </button>
                      )}
                    </div>

                    {/* File Info - Bottom */}
                    <div className="absolute bottom-0 left-0 right-0 p-3">
                      <p className="text-white/80 text-sm font-medium truncate line-through" title={content.title}>
                        {content.title}
                      </p>
                      <div className="flex items-center gap-2 text-white/60 text-xs mt-1">
                        <span>{formatFileSize(content.file_size)}</span>
                        {content.deleted_at && (
                          <span>
                            {t('contents.deleted.deletedOn', 'Deleted')}: {new Date(content.deleted_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {previewContent && (
        <ContentPreviewModal
          isOpen={!!previewContent}
          content={previewContent}
          onClose={() => setPreviewContent(null)}
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

      {/* CSS for Masonry */}
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
      `}</style>
    </div>
  );
}
