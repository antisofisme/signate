/**
 * Custom Hook for Menu Items Editor
 * Manages edit state, change tracking, and save operations
 * Used by MenuItemsManager in Edit Mode
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import { menuApi } from '../api/menuApi';
import { useMenuMedia } from './useMenuMedia';
import {
  useBulkUpdateMenuItems,
  useDeleteMenuItem,
  useAddMenuItem,
  type BulkUpdateStatus,
} from './useMenuItems';
import type {
  MenuItem,
  MenuMedia,
  EditableItem,
  MenuItemUpdateRequest,
  MenuItemMediaListResponse,
} from '../types/menu';
import { toEditableItem } from '../types/menu';

interface UseMenuItemsEditorOptions {
  menuId: number;
  items: MenuItem[];
  enabled: boolean;
}

interface UseMenuItemsEditorReturn {
  // State
  editableItems: EditableItem[];
  modifiedCount: number;
  failedCount: number;
  isSaving: boolean;
  isLoadingItemMedia: boolean;

  // Field updates
  updateField: (itemId: number, field: keyof EditableItem, value: any) => void;

  // Item management
  addNewItem: () => void;
  removeNewItem: (itemId: number) => void;

  // Save/Reset
  handleSaveAll: () => Promise<void>;
  handleRetryFailed: () => Promise<void>;
  resetChanges: () => void;

  // Media picker
  selectedItemIdForMedia: number | null;
  setSelectedItemIdForMedia: (id: number | null) => void;
  selectedItemForMedia: EditableItem | undefined;
  handleToggleMedia: (media: MenuMedia) => void;
  handleRemoveAllImages: () => void;
  closeMediaPicker: () => void;
  mediaData: { items: MenuMedia[] } | undefined;
  isLoadingMedia: boolean;
}

export function useMenuItemsEditor({
  menuId,
  items,
  enabled,
}: UseMenuItemsEditorOptions): UseMenuItemsEditorReturn {
  // Initialize editable items immediately (not via useEffect to avoid flicker)
  const initialEditableItems = useMemo(() => {
    if (!enabled || items.length === 0) return [];
    const sortedItems = [...items].sort((a, b) =>
      a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
    );
    return sortedItems.map(toEditableItem);
  }, [enabled, items]);

  // State
  const [editableItems, setEditableItems] = useState<EditableItem[]>(initialEditableItems);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingItemMedia, setIsLoadingItemMedia] = useState(false);
  const [selectedItemIdForMedia, setSelectedItemIdForMedia] = useState<number | null>(null);
  const [newItemCounter, setNewItemCounter] = useState(-1);

  // Hooks
  const { data: mediaData, isLoading: isLoadingMedia } = useMenuMedia();
  const { bulkUpdate } = useBulkUpdateMenuItems(menuId);
  const deleteMutation = useDeleteMenuItem(menuId);
  const addMutation = useAddMenuItem(menuId);

  // Sync editableItems when initialEditableItems changes (e.g., when items are refetched)
  useEffect(() => {
    if (enabled && initialEditableItems.length > 0) {
      setEditableItems(initialEditableItems);
    }
  }, [enabled, initialEditableItems]);

  // Fetch existing media for all items when enabled
  useEffect(() => {
    if (!enabled || items.length === 0) return;

    const fetchAllItemMedia = async () => {
      setIsLoadingItemMedia(true);

      // Fetch media for all items in parallel
      const mediaPromises = items.map(async (item) => {
        try {
          const response: MenuItemMediaListResponse = await menuApi.listItemMedia(menuId, item.id);
          return {
            itemId: item.id,
            mediaIds: response.items.map(m => m.menu_media_id),
          };
        } catch {
          return { itemId: item.id, mediaIds: [] };
        }
      });

      const results = await Promise.all(mediaPromises);

      // Update editable items with fetched media_ids
      setEditableItems(prev => prev.map(item => {
        const result = results.find(r => r.itemId === item.id);
        if (result && result.mediaIds.length > 0) {
          return {
            ...item,
            media_ids: result.mediaIds,
          };
        }
        return item;
      }));

      setIsLoadingItemMedia(false);
    };

    fetchAllItemMedia();
  }, [enabled, items, menuId]);

  // Calculate modified and failed counts
  const modifiedCount = useMemo(
    () => editableItems.filter((item) => item.hasChanges).length,
    [editableItems]
  );

  const failedCount = useMemo(
    () => editableItems.filter((item) => item.status === 'error').length,
    [editableItems]
  );

  // Check if item has changes compared to original
  const checkHasChanges = useCallback(
    (itemId: number, field: string, value: any) => {
      // Get current item state
      const current = editableItems.find((i) => i.id === itemId);
      if (!current) return false;

      // For new items, consider it has changes if name is not empty
      if (current.isNew) {
        const updated = { ...current, [field]: value };
        return updated.name.trim() !== '';
      }

      const original = items.find((i) => i.id === itemId);
      if (!original) return false;

      // Create updated item state
      const updated = { ...current, [field]: value };

      // Compare each field (include mediaChanged)
      return (
        updated.name !== original.name ||
        updated.description !== (original.description || '') ||
        updated.price !== (original.price ?? null) ||
        updated.category !== (original.category || '') ||
        updated.subcategory !== (original.subcategory || '') ||
        updated.variant !== (original.variant || '') ||
        updated.tags !== (original.tags || '') ||
        updated.is_active !== original.is_active ||
        updated.is_featured !== original.is_featured ||
        updated.is_available !== original.is_available ||
        updated.image_url !== (original.image_url || null) ||
        updated.mediaChanged === true
      );
    },
    [items, editableItems]
  );

  // Update field value
  const updateField = useCallback(
    (itemId: number, field: keyof EditableItem, value: any) => {
      setEditableItems((prev) =>
        prev.map((item) => {
          if (item.id !== itemId) return item;

          const hasChanges = checkHasChanges(itemId, field, value);
          return {
            ...item,
            [field]: value,
            hasChanges,
            status: 'idle' as BulkUpdateStatus,
          };
        })
      );
    },
    [checkHasChanges]
  );

  // Handle progress updates during save
  const handleProgress = useCallback(
    (progress: { id: number; status: BulkUpdateStatus }) => {
      setEditableItems((prev) =>
        prev.map((item) =>
          item.id === progress.id ? { ...item, status: progress.status } : item
        )
      );
    },
    []
  );

  // Save all modified items
  const handleSaveAll = async () => {
    const modifiedItems = editableItems.filter((item) => item.hasChanges);
    if (modifiedItems.length === 0) return;

    setIsSaving(true);

    // Separate new items from existing items
    const newItems = modifiedItems.filter((item) => item.isNew);
    const existingItems = modifiedItems.filter((item) => !item.isNew);

    let totalSuccess = 0;
    let totalFailed = 0;

    // Track created item IDs for media assignment
    const createdItemIds: Map<number, number> = new Map(); // tempId -> realId

    // Create new items first
    for (const item of newItems) {
      handleProgress({ id: item.id, status: 'saving' });
      try {
        const createdItem = await addMutation.mutateAsync({
          name: item.name,
          description: item.description || undefined,
          price: item.price ?? undefined,
          category: item.category || undefined,
          subcategory: item.subcategory || undefined,
          variant: item.variant || undefined,
          tags: item.tags || undefined,
          is_active: item.is_active,
          is_featured: item.is_featured,
          is_available: item.is_available,
          image_url: item.image_url || undefined,
        });

        // Store the mapping for media assignment
        if (createdItem && typeof createdItem === 'object' && 'id' in createdItem) {
          createdItemIds.set(item.id, (createdItem as { id: number }).id);
        }

        handleProgress({ id: item.id, status: 'success' });
        totalSuccess++;
      } catch {
        handleProgress({ id: item.id, status: 'error' });
        totalFailed++;
      }
    }

    // Update existing items
    if (existingItems.length > 0) {
      const updateData = existingItems.map((item) => ({
        id: item.id,
        data: {
          name: item.name,
          description: item.description || undefined,
          price: item.price ?? undefined,
          category: item.category || undefined,
          subcategory: item.subcategory || undefined,
          variant: item.variant || undefined,
          tags: item.tags || undefined,
          is_active: item.is_active,
          is_featured: item.is_featured,
          is_available: item.is_available,
          image_url: item.image_url || undefined,
        } as MenuItemUpdateRequest,
      }));

      const result = await bulkUpdate(updateData, handleProgress);
      totalSuccess += result.success;
      totalFailed += result.failed;
    }

    // Update media for items with media changes
    const itemsWithMediaChanges = modifiedItems.filter((item) => item.mediaChanged && item.media_ids.length > 0);
    for (const item of itemsWithMediaChanges) {
      try {
        // Use the real ID for new items, or the existing ID
        const realId = item.isNew ? createdItemIds.get(item.id) : item.id;
        if (realId && realId > 0) {
          await menuApi.bulkSetItemMedia(menuId, realId, {
            media_ids: item.media_ids,
            primary_media_id: item.media_ids[0], // First selected is primary
          });
        }
      } catch (error) {
        console.error('Failed to update media for item:', item.id, error);
        // Don't fail the whole operation for media errors
      }
    }

    setIsSaving(false);

    // Mark successful items as not changed and remove new flag
    if (totalSuccess > 0) {
      setEditableItems((prev) =>
        prev.map((item) => {
          if (item.status === 'success') {
            return { ...item, hasChanges: false, isNew: false, mediaChanged: false };
          }
          return item;
        })
      );
    }
  };

  // Retry failed items
  const handleRetryFailed = async () => {
    const failedItems = editableItems.filter((item) => item.status === 'error');
    if (failedItems.length === 0) return;

    setIsSaving(true);

    const updateData = failedItems.map((item) => ({
      id: item.id,
      data: {
        name: item.name,
        description: item.description || undefined,
        price: item.price ?? undefined,
        category: item.category || undefined,
        subcategory: item.subcategory || undefined,
        variant: item.variant || undefined,
        tags: item.tags || undefined,
        is_active: item.is_active,
        is_featured: item.is_featured,
        is_available: item.is_available,
        image_url: item.image_url || undefined,
      } as MenuItemUpdateRequest,
    }));

    await bulkUpdate(updateData, handleProgress);

    setIsSaving(false);
  };

  // Reset all changes
  const resetChanges = useCallback(() => {
    if (items.length > 0) {
      const sortedItems = [...items].sort((a, b) =>
        a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
      );
      setEditableItems(sortedItems.map(toEditableItem));
    }
    setNewItemCounter(-1);
  }, [items]);

  // Add new empty item
  const addNewItem = useCallback(() => {
    const newItem: EditableItem = {
      id: newItemCounter,
      menu_id: menuId,
      organization_id: 0, // Will be set by backend
      name: '',
      description: '',
      price: null,
      currency: 'IDR',
      image_url: null,
      media_ids: [],
      category: '',
      subcategory: '',
      variant: '',
      tags: '',
      display_order: 0,
      is_active: true,
      is_featured: false,
      is_available: true,
      hasChanges: false,
      status: 'idle',
      mediaChanged: false,
      isNew: true,
    };
    setEditableItems((prev) => [...prev, newItem]);
    setNewItemCounter((prev) => prev - 1);
  }, [newItemCounter, menuId]);

  // Remove new item (not saved yet)
  const removeNewItem = useCallback((itemId: number) => {
    setEditableItems((prev) => prev.filter((i) => i.id !== itemId));
  }, []);

  // Get selected item for media picker
  const selectedItemForMedia = useMemo(
    () => editableItems.find(item => item.id === selectedItemIdForMedia),
    [editableItems, selectedItemIdForMedia]
  );

  // Handle media toggle (multi-select)
  const handleToggleMedia = useCallback((media: MenuMedia) => {
    if (!selectedItemIdForMedia) return;

    setEditableItems((prev) =>
      prev.map((item) => {
        if (item.id !== selectedItemIdForMedia) return item;

        const currentIds = item.media_ids || [];
        const isSelected = currentIds.includes(media.id);
        let newIds: number[];

        if (isSelected) {
          // Remove from selection
          newIds = currentIds.filter((id) => id !== media.id);
        } else {
          // Add to selection
          newIds = [...currentIds, media.id];
        }

        // Update image_url to first selected media's URL
        const firstMedia = mediaData?.items.find((m) => m.id === newIds[0]);
        const newImageUrl = firstMedia?.url || null;

        const hasChanges = checkHasChanges(item.id, 'media_ids', newIds);

        return {
          ...item,
          media_ids: newIds,
          image_url: newImageUrl,
          mediaChanged: true,
          hasChanges,
          status: 'idle' as BulkUpdateStatus,
        };
      })
    );
  }, [selectedItemIdForMedia, mediaData, checkHasChanges]);

  // Handle remove all images
  const handleRemoveAllImages = useCallback(() => {
    if (!selectedItemIdForMedia) return;

    setEditableItems((prev) =>
      prev.map((item) => {
        if (item.id !== selectedItemIdForMedia) return item;

        const hasChanges = checkHasChanges(item.id, 'media_ids', []);

        return {
          ...item,
          media_ids: [],
          image_url: null,
          mediaChanged: true,
          hasChanges,
          status: 'idle' as BulkUpdateStatus,
        };
      })
    );
  }, [selectedItemIdForMedia, checkHasChanges]);

  // Close media picker
  const closeMediaPicker = useCallback(() => {
    setSelectedItemIdForMedia(null);
  }, []);

  return {
    // State
    editableItems,
    modifiedCount,
    failedCount,
    isSaving,
    isLoadingItemMedia,

    // Field updates
    updateField,

    // Item management
    addNewItem,
    removeNewItem,

    // Save/Reset
    handleSaveAll,
    handleRetryFailed,
    resetChanges,

    // Media picker
    selectedItemIdForMedia,
    setSelectedItemIdForMedia,
    selectedItemForMedia,
    handleToggleMedia,
    handleRemoveAllImages,
    closeMediaPicker,
    mediaData,
    isLoadingMedia,
  };
}
