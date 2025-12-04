/**
 * Menu Media Gallery View Component
 * Masonry layout with sidebar detail panel
 * Uses CSS columns for masonry effect (no external library)
 * Supports duplicate grouping like Table view
 */

import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Search,
  SortAsc,
  SortDesc,
  FileImage,
  Copy,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { EmptyState, ErrorDisplay } from '@/shared/components';
import { useMenuMediaList, useDuplicateMenuMedia } from '../hooks/useMenuMedia';
import type { MenuMedia, MenuMediaFilters, MenuMediaDuplicateGroup } from '../types/menu';
import { MenuMediaGalleryCard } from './MenuMediaGalleryCard';
import { MenuMediaDetailSidebar } from './MenuMediaDetailSidebar';
import { MenuMediaUploadModal } from './MenuMediaUploadModal';
// MenuMediaUploadQueuePanel removed - using unified UploadQueuePanel

// Sort options
type SortOption = 'newest' | 'oldest' | 'name_asc' | 'name_desc' | 'size_desc' | 'size_asc';

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'newest', label: 'Newest First' },
  { value: 'oldest', label: 'Oldest First' },
  { value: 'name_asc', label: 'Name (A-Z)' },
  { value: 'name_desc', label: 'Name (Z-A)' },
  { value: 'size_desc', label: 'Largest First' },
  { value: 'size_asc', label: 'Smallest First' },
];

interface MenuMediaGalleryViewProps {
  showUploadModal?: boolean;
  onCloseUploadModal?: () => void;
}

export function MenuMediaGalleryView({
  showUploadModal: showUploadModalProp = false,
  onCloseUploadModal
}: MenuMediaGalleryViewProps) {
  const { t } = useTranslation();

  // State
  const [filters, setFilters] = useState<MenuMediaFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [selectedMedia, setSelectedMedia] = useState<MenuMedia | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const showUploadModal = showUploadModalProp;
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Fetch media with max allowed limit (backend allows max 100)
  const { data: mediaData, isLoading, error } = useMenuMediaList({
    ...filters,
    limit: 100, // Backend max limit is 100
  });

  // Fetch duplicate data
  const { data: duplicateData } = useDuplicateMenuMedia();

  // Build duplicate lookup map
  const duplicateMap = useMemo(() => {
    const map = new Map<number, { hash: string; group: MenuMediaDuplicateGroup }>();
    const groups = duplicateData?.duplicates || [];

    groups.forEach((group) => {
      group.media.forEach((item) => {
        map.set(item.id, { hash: group.file_hash, group });
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

  // Filter and sort media client-side
  const filteredAndSortedMedia = useMemo(() => {
    if (!mediaData?.items) return [];

    let result = [...mediaData.items];

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (media) =>
          media.original_filename.toLowerCase().includes(query) ||
          media.title?.toLowerCase().includes(query) ||
          media.alt_text?.toLowerCase().includes(query)
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
        result.sort((a, b) => (a.title || a.original_filename).localeCompare(b.title || b.original_filename));
        break;
      case 'name_desc':
        result.sort((a, b) => (b.title || b.original_filename).localeCompare(a.title || a.original_filename));
        break;
      case 'size_desc':
        result.sort((a, b) => b.file_size - a.file_size);
        break;
      case 'size_asc':
        result.sort((a, b) => a.file_size - b.file_size);
        break;
    }

    return result;
  }, [mediaData?.items, searchQuery, sortBy]);

  // Handle media selection - toggle sidebar when clicking media
  const handleSelectMedia = (media: MenuMedia) => {
    if (selectedMedia?.id === media.id) {
      // Clicking same media - close sidebar
      setIsSidebarOpen(false);
    } else {
      // Clicking different media - select and open sidebar
      setSelectedMedia(media);
      setIsSidebarOpen(true);
    }
  };

  // Handle sidebar close
  const handleCloseSidebar = () => {
    setIsSidebarOpen(false);
  };

  // Handle media update from sidebar
  const handleMediaUpdate = (updatedMedia: MenuMedia) => {
    setSelectedMedia(updatedMedia);
  };

  // Handle media delete from sidebar
  const handleMediaDelete = () => {
    setSelectedMedia(null);
  };

  return (
    <div className="flex gap-6 h-[calc(100vh-280px)] min-h-[500px]">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div className="flex items-center gap-4 mb-4">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder={t('menus.media.gallery.searchPlaceholder', 'Search images...')}
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
                  {t(`menus.media.gallery.sort.${option.value}`, option.label)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Stats */}
        <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {t('menus.media.gallery.imagesFound', { count: filteredAndSortedMedia.length, defaultValue: '{{count}} images found' })}
          {searchQuery && ` (${t('menus.media.gallery.filtered', 'filtered')})`}
          {duplicateData && duplicateData.total_groups > 0 && (
            <span className="ml-2 text-orange-600 dark:text-orange-400">
              ({duplicateData.total_groups} duplicate group{duplicateData.total_groups > 1 ? 's' : ''})
            </span>
          )}
        </div>

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
          {!isLoading && !error && filteredAndSortedMedia.length === 0 && (
            <EmptyState
              icon={FileImage}
              title={t('menus.media.empty.title', 'No images found')}
              description={
                searchQuery
                  ? t('menus.media.gallery.noSearchResults', 'Try adjusting your search')
                  : t('menus.media.empty.description', 'Upload your first image to get started')
              }
            />
          )}

          {/* Masonry Grid with Duplicate Grouping */}
          {!isLoading && !error && filteredAndSortedMedia.length > 0 && (
            <div className="masonry-grid">
              {(() => {
                const renderedGroups = new Set<string>();
                const elements: React.ReactNode[] = [];

                filteredAndSortedMedia.forEach((media) => {
                  const dupInfo = duplicateMap.get(media.id);

                  // If this media is part of a duplicate group
                  if (dupInfo && !renderedGroups.has(dupInfo.hash)) {
                    renderedGroups.add(dupInfo.hash);
                    const group = dupInfo.group;
                    const isExpanded = expandedGroups.has(dupInfo.hash);

                    // Get all media items in this group that exist in current filtered list
                    const groupMediaIds = new Set(group.media.map((m) => m.id));
                    const groupMediaItems = filteredAndSortedMedia.filter((m) =>
                      groupMediaIds.has(m.id)
                    );

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
                              {group.duplicate_count} Duplicates
                            </span>
                          </div>

                          {/* Preview thumbnails */}
                          <div className="flex gap-1 mb-2">
                            {groupMediaItems.slice(0, 3).map((m) => (
                              <img
                                key={m.id}
                                src={m.url}
                                alt=""
                                className="w-12 h-12 object-cover rounded"
                              />
                            ))}
                            {groupMediaItems.length > 3 && (
                              <div className="w-12 h-12 bg-orange-200 dark:bg-orange-800 rounded flex items-center justify-center text-xs font-medium text-orange-700 dark:text-orange-300">
                                +{groupMediaItems.length - 3}
                              </div>
                            )}
                          </div>

                          <div className="text-xs text-orange-600 dark:text-orange-400">
                            Click to {isExpanded ? 'collapse' : 'expand'}
                          </div>
                        </div>

                        {/* Expanded: Show all items in group */}
                        {isExpanded && (
                          <div className="mt-2 space-y-2 pl-2 border-l-2 border-orange-300 dark:border-orange-700">
                            {groupMediaItems.map((m) => (
                              <div
                                key={m.id}
                                className={`relative rounded-lg overflow-hidden cursor-pointer transition-all ${
                                  selectedMedia?.id === m.id
                                    ? 'ring-2 ring-blue-500'
                                    : 'hover:ring-2 hover:ring-gray-300 dark:hover:ring-gray-600'
                                }`}
                                onClick={() => handleSelectMedia(m)}
                              >
                                <img
                                  src={m.url}
                                  alt={m.alt_text || m.original_filename}
                                  className="w-full h-auto object-cover"
                                />
                                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
                                  <p className="text-white text-xs truncate">
                                    {m.title || m.original_filename}
                                  </p>
                                </div>
                              </div>
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
                  // Regular media (not duplicate)
                  else {
                    elements.push(
                      <MenuMediaGalleryCard
                        key={media.id}
                        media={media}
                        isSelected={selectedMedia?.id === media.id}
                        onSelect={() => handleSelectMedia(media)}
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

      {/* Sidebar Detail Panel - Expand/Collapse with animation */}
      <MenuMediaDetailSidebar
        media={selectedMedia}
        isOpen={isSidebarOpen}
        onUpdate={handleMediaUpdate}
        onDelete={handleMediaDelete}
        onClose={handleCloseSidebar}
      />

      {/* Upload Modal */}
      <MenuMediaUploadModal
        isOpen={showUploadModal}
        onClose={onCloseUploadModal || (() => {})}
      />

      {/* Upload Queue Panel - Now using unified UploadQueuePanel in main.tsx */}

      {/* CSS for Masonry and Sidebar Animation */}
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
        /* Sidebar slide-in animation */
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
