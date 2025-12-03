/**
 * Direct Content Assignment Tab
 *
 * Priority 1 - Highest priority content assignment with drag & drop reordering
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Trash2, Loader2, Star, Image, Video, Music, ArrowRight, GripVertical, FileText } from 'lucide-react';
import { toast } from 'sonner';
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

  const assignedContents = assignedData?.items || [];
  const allContents = allContentData?.data || [];

  // Update sorted items when assigned content changes
  // Only sync when assignedData changes (not on every render)
  useEffect(() => {
    if (!assignedData) return;

    // Backend already sorts by priority DESC
    const newItems = assignedData.items || [];

    // Only update if items actually changed (deep comparison)
    const itemsChanged = JSON.stringify(newItems) !== JSON.stringify(sortedItems);

    if (itemsChanged) {
      setSortedItems(newItems);
    }
  }, [assignedData]); // Use assignedData, not assignedContents

  // Filter out already assigned content
  const availableContents = allContents.filter(
    (content) => !assignedContents.some((assigned) => assigned.content_id === content.id)
  );

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
                  return (
                    <div
                      key={content.id}
                      className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer"
                      onClick={() => handleAssign(content.id)}
                    >
                      <div className="flex gap-3">
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
                            {content.title}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {content.content_type} • {content.duration}s
                          </p>
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
                  <div className="space-y-2 max-h-[400px] overflow-y-auto">
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
          </div>
        </div>
      )}
    </div>
  );
}
