/**
 * Direct Content Assignment Tab
 *
 * Priority 1 - Highest priority content assignment with drag & drop reordering
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Trash2, Loader2, Star, Image, Video, Music, ArrowRight, GripVertical, FileText, Tag, List, Info } from 'lucide-react';
import { toast } from '@/shared/utils/toast';
import { useQueryClient } from '@tanstack/react-query';
import {
  useDeviceContents,
  useAssignContent,
  useUnassignContent,
  assignmentKeys
} from '../../../hooks/useDeviceAssignments';  // Use all from same file!
import { deviceAssignmentsApi } from '../../../api/deviceAssignmentsApi';
import { useContentList } from '@/shared/hooks/useSharedContents';
import type { Device } from '../../../types/device';
import type { Content } from '@/features/contents/types/content';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface DirectContentAssignmentTabProps {
  device: Device;
}

// Sortable Item Component
interface SortableItemProps {
  assigned: any;
  content: Content | undefined;
  Icon: any;
  onUnassign: (contentId: number) => void;
  isUnassigning: boolean;
}

function SortableItem({ assigned, content, Icon, onUnassign, isUnassigning }: SortableItemProps) {
  const { t } = useTranslation();
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: assigned.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  if (!content) return null;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 transition-colors bg-white dark:bg-gray-800"
    >
      <div className="flex gap-3">
        {/* Drag Handle */}
        <div
          {...attributes}
          {...listeners}
          className="flex-shrink-0 w-8 h-16 flex items-center justify-center cursor-grab active:cursor-grabbing"
        >
          <GripVertical className="w-5 h-5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" />
        </div>

        {/* Priority Badge */}
        <div className="flex-shrink-0 w-12 h-16 flex items-center justify-center">
          <div className="flex flex-col items-center gap-1">
            <Star className="w-3 h-3 text-yellow-500" />
            <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
              {assigned.priority}
            </span>
          </div>
        </div>

        {/* Thumbnail */}
        <div className="w-16 h-16 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
          {content.thumbnail_url ? (
            <img
              src={content.thumbnail_url}
              alt={content.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Icon className="w-6 h-6 text-gray-400" />
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
            {assigned.content_name}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {assigned.content_type}
          </p>
        </div>

        {/* Remove Button */}
        <button
          onClick={() => onUnassign(assigned.content_id)}
          disabled={isUnassigning}
          className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all"
          title={t('devices.modals.removeFromDevice')}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export function DirectContentAssignmentTab({ device }: DirectContentAssignmentTabProps) {
  const { t } = useTranslation();
  const [priority, setPriority] = useState<number>(1);
  const [sortedItems, setSortedItems] = useState<any[]>([]);
  const queryClient = useQueryClient();

  // Fetch assigned content for this device
  const { data: assignedData, isLoading: loadingAssigned } = useDeviceContents(device.id, true);

  // Fetch all available content
  const { data: allContentData, isLoading: loadingAllContent } = useContentList();

  // Mutations
  const assignContent = useAssignContent();
  const unassignContent = useUnassignContent();

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Filter content by source type
  const allItems = assignedData?.items || [];
  const assignedContents = allItems.filter((item: any) => item.source === 'direct');
  const tagBasedContents = allItems.filter((item: any) => item.source === 'tag');
  const playlistBasedContents = allItems.filter((item: any) => item.source === 'playlist');
  const allContents = allContentData?.data || [];

  // Total inherited content (from tags + playlists)
  const totalInheritedContent = tagBasedContents.length + playlistBasedContents.length;

  // Update sorted items when assigned content changes
  // Only sync when assignedData changes (not on every render)
  useEffect(() => {
    if (!assignedData) return;

    // Filter to only DIRECT assignments and sort by priority DESC
    const newItems = (assignedData.items || []).filter(
      (item: any) => item.source === 'direct'
    );

    // Only update if items actually changed (deep comparison)
    const itemsChanged = JSON.stringify(newItems) !== JSON.stringify(sortedItems);

    if (itemsChanged) {
      setSortedItems(newItems);
    }
  }, [assignedData]); // Use assignedData, not assignedContents

  // Only filter out DIRECT assignments - user can still add content that's in tag/playlist
  const directAssignedContentIds = assignedContents.map((item: any) => item.content_id);
  const availableContents = allContents.filter(
    (content) => !directAssignedContentIds.includes(content.id)
  );

  // Create a map of content -> inherited sources (tag/playlist) for indicators
  const contentInheritedSources = new Map<number, { tags: string[], playlists: string[] }>();
  tagBasedContents.forEach((item: any) => {
    const existing = contentInheritedSources.get(item.content_id) || { tags: [], playlists: [] };
    if (item.source_name && !existing.tags.includes(item.source_name)) {
      existing.tags.push(item.source_name);
    }
    contentInheritedSources.set(item.content_id, existing);
  });
  playlistBasedContents.forEach((item: any) => {
    const existing = contentInheritedSources.get(item.content_id) || { tags: [], playlists: [] };
    if (item.source_name && !existing.playlists.includes(item.source_name)) {
      existing.playlists.push(item.source_name);
    }
    contentInheritedSources.set(item.content_id, existing);
  });

  // Get content type icon
  const getContentIcon = (type: string) => {
    switch (type) {
      case 'image':
        return Image;
      case 'video':
        return Video;
      case 'audio':
        return Music;
      default:
        return FileText;
    }
  };

  // Get content details by ID
  const getContentDetails = (contentId: number) => {
    return allContents.find((c) => c.id === contentId);
  };

  // Handle assign with priority
  const handleAssign = async (contentId: number) => {
    try {
      await assignContent.mutateAsync({
        deviceId: device.id,
        data: {
          content_id: contentId,
          priority,
        },
      });
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle unassign
  const handleUnassign = async (contentId: number) => {
    try {
      await unassignContent.mutateAsync({ deviceId: device.id, contentId });
      // Update sorted items after unassign
      setSortedItems((prev) => prev.filter((item) => item.content_id !== contentId));
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle drag end - reorder and update priorities
  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) return;

    const oldIndex = sortedItems.findIndex((item) => item.id === active.id);
    const newIndex = sortedItems.findIndex((item) => item.id === over.id);

    if (oldIndex === -1 || newIndex === -1) return;

    // Store original order for rollback
    const originalOrder = [...sortedItems];

    // Optimistic update - reorder array immediately
    const newOrder = arrayMove(sortedItems, oldIndex, newIndex);

    // Update local state with new priorities
    const updatedOrder = newOrder.map((item, index) => ({
      ...item,
      priority: 100 - index, // Recalculate priority based on position
    }));

    // Optimistic UI update
    setSortedItems(updatedOrder);

    // Update backend - only items that changed
    const itemsToUpdate = updatedOrder.filter((item, index) => {
      const originalItem = originalOrder.find(o => o.id === item.id);
      return item.priority !== originalItem?.priority;
    });

    if (itemsToUpdate.length === 0) {
      return;
    }

    try {
      // Sequential backend updates
      for (const item of itemsToUpdate) {
        await deviceAssignmentsApi.assignContentToDevice(device.id, {
          content_id: item.content_id,
          priority: item.priority,
        });
      }

      // After ALL backend updates complete, refetch to sync with server
      // This ensures modal re-open will show correct order
      await queryClient.refetchQueries({
        queryKey: assignmentKeys.contents(device.id),
        exact: true
      });

      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['devices', 'detail', device.id] });
      queryClient.invalidateQueries({ queryKey: ['devices', 'list'] });

      toast.success(t('devices.modals.priorityUpdatedSuccess'));
    } catch (error) {
      // Rollback on error
      setSortedItems(originalOrder);

      // Force refetch to sync with actual backend state
      await queryClient.refetchQueries({
        queryKey: assignmentKeys.contents(device.id),
        exact: true
      });

      toast.error(t('devices.modals.priorityUpdateFailed'));
      console.error('Failed to update priorities:', error);
    }
  };

  const isLoading = loadingAssigned || loadingAllContent;

  return (
    <div className="p-6 min-h-[600px]">
      {/* Priority Selector */}
      <div className="mb-4 flex items-center justify-between bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
        <p className="text-sm text-blue-700 dark:text-blue-300">
          <strong>{t('devices.modals.priority1Highest')}:</strong> {t('devices.modals.priority1Info')}
        </p>
        <div className="flex items-center gap-2 ml-4">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1 whitespace-nowrap">
            <Star className="w-4 h-4" />
            {t('devices.modals.priorityLabel')}:
          </label>
          <input
            type="number"
            min="1"
            max="100"
            value={priority}
            onChange={(e) => setPriority(parseInt(e.target.value) || 1)}
            className="w-20 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
      </div>

      {/* Inherited Content Info (from Tags + Playlists) */}
      {totalInheritedContent > 0 && (
        <div className="mb-4 flex items-center gap-3 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
          <Info className="w-4 h-4 text-gray-500 dark:text-gray-400 flex-shrink-0" />
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
            <span className="text-gray-600 dark:text-gray-300">
              <strong>{totalInheritedContent}</strong> {t('devices.modals.inheritedContent', 'inherited content')}:
            </span>
            {tagBasedContents.length > 0 && (
              <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                <Tag className="w-3.5 h-3.5" />
                <strong>{tagBasedContents.length}</strong> dari tag
              </span>
            )}
            {playlistBasedContents.length > 0 && (
              <span className="flex items-center gap-1 text-purple-600 dark:text-purple-400">
                <List className="w-3.5 h-3.5" />
                <strong>{playlistBasedContents.length}</strong> dari playlist
              </span>
            )}
          </div>
        </div>
      )}

      {/* Content - 2 Column Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column - Available Content */}
          <div className="border-r border-gray-200 dark:border-gray-700 pr-4">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              {t('devices.modals.availableContent')} ({availableContents.length})
            </h4>
            {availableContents.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('devices.modals.allContentAssigned')}
              </p>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {availableContents.map((content: Content) => {
                  const Icon = getContentIcon(content.content_type);
                  const inheritedSources = contentInheritedSources.get(content.id);
                  const hasInherited = inheritedSources && (inheritedSources.tags.length > 0 || inheritedSources.playlists.length > 0);

                  return (
                    <div
                      key={content.id}
                      className={`group relative border rounded-lg p-3 hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer ${
                        hasInherited
                          ? 'border-amber-300 dark:border-amber-700 bg-amber-50/30 dark:bg-amber-900/10'
                          : 'border-gray-200 dark:border-gray-700'
                      }`}
                      onClick={() => handleAssign(content.id)}
                    >
                      <div className="flex gap-3">
                        {/* Thumbnail */}
                        <div className="w-16 h-16 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden relative">
                          {content.thumbnail_url ? (
                            <img
                              src={content.thumbnail_url}
                              alt={content.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <Icon className="w-6 h-6 text-gray-400" />
                            </div>
                          )}
                          {/* Duplicate indicator badge */}
                          {hasInherited && (
                            <div className="absolute -top-1 -right-1 w-5 h-5 bg-amber-500 rounded-full flex items-center justify-center">
                              <Info className="w-3 h-3 text-white" />
                            </div>
                          )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {content.title}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {content.content_type} • {content.duration}s
                          </p>
                          {/* Show inherited sources */}
                          {hasInherited && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {inheritedSources.tags.map((tagName: string) => (
                                <span
                                  key={`tag-${tagName}`}
                                  className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 rounded"
                                >
                                  <Tag className="w-2.5 h-2.5" />
                                  {tagName}
                                </span>
                              ))}
                              {inheritedSources.playlists.map((playlistName: string) => (
                                <span
                                  key={`playlist-${playlistName}`}
                                  className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 rounded"
                                >
                                  <List className="w-2.5 h-2.5" />
                                  {playlistName}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Assign Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAssign(content.id);
                          }}
                          disabled={assignContent.isPending}
                          className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-all"
                          title={t('devices.modals.assignToDevice')}
                        >
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column - Assigned Content with Drag & Drop */}
          <div className="pl-4">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <GripVertical className="w-4 h-4 text-gray-400" />
              {t('devices.modals.assignedContent')} ({sortedItems.length})
            </h4>
            {sortedItems.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('devices.modals.noContentAssigned')}</p>
            ) : (
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
              >
                <SortableContext
                  items={sortedItems.map((item) => item.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {sortedItems.map((assigned) => {
                      const content = getContentDetails(assigned.content_id);
                      const Icon = getContentIcon(assigned.content_type);
                      return (
                        <SortableItem
                          key={assigned.id}
                          assigned={assigned}
                          content={content}
                          Icon={Icon}
                          onUnassign={handleUnassign}
                          isUnassigning={unassignContent.isPending}
                        />
                      );
                    })}
                  </div>
                </SortableContext>
              </DndContext>
            )}

            {/* Tag-based Content (Read-only) */}
            {tagBasedContents.length > 0 && (
              <div className="mt-4">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <Tag className="w-4 h-4 text-amber-500" />
                  {t('devices.modals.contentFromTagsTitle', 'Dari Tag')} ({tagBasedContents.length})
                </h4>
                <div className="space-y-2 max-h-[150px] overflow-y-auto">
                  {tagBasedContents.map((assigned: any) => {
                    const content = getContentDetails(assigned.content_id);
                    const Icon = getContentIcon(assigned.content_type);
                    return (
                      <div
                        key={`tag-${assigned.id}`}
                        className="relative border border-amber-200 dark:border-amber-800 rounded-lg p-2 bg-amber-50/50 dark:bg-amber-900/20"
                      >
                        <div className="flex gap-2 items-center">
                          {/* Thumbnail */}
                          <div className="w-10 h-10 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
                            {content?.thumbnail_url ? (
                              <img
                                src={content.thumbnail_url}
                                alt={content.title}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <Icon className="w-4 h-4 text-gray-400" />
                              </div>
                            )}
                          </div>

                          {/* Info */}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                              {assigned.content_name}
                            </p>
                            <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
                              <Tag className="w-3 h-3" />
                              {assigned.source_name || 'Tag'}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Playlist-based Content (Read-only) */}
            {playlistBasedContents.length > 0 && (
              <div className="mt-4">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <List className="w-4 h-4 text-purple-500" />
                  {t('devices.modals.contentFromPlaylistsTitle', 'Dari Playlist')} ({playlistBasedContents.length})
                </h4>
                <div className="space-y-2 max-h-[150px] overflow-y-auto">
                  {playlistBasedContents.map((assigned: any) => {
                    const content = getContentDetails(assigned.content_id);
                    const Icon = getContentIcon(assigned.content_type);
                    return (
                      <div
                        key={`playlist-${assigned.id}`}
                        className="relative border border-purple-200 dark:border-purple-800 rounded-lg p-2 bg-purple-50/50 dark:bg-purple-900/20"
                      >
                        <div className="flex gap-2 items-center">
                          {/* Thumbnail */}
                          <div className="w-10 h-10 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
                            {content?.thumbnail_url ? (
                              <img
                                src={content.thumbnail_url}
                                alt={content.title}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <Icon className="w-4 h-4 text-gray-400" />
                              </div>
                            )}
                          </div>

                          {/* Info */}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                              {assigned.content_name}
                            </p>
                            <p className="text-xs text-purple-600 dark:text-purple-400 flex items-center gap-1">
                              <List className="w-3 h-3" />
                              {assigned.source_name || 'Playlist'}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
