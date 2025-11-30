/**
 * Menu Items Bulk Edit Modal
 * Inline editing for multiple menu items with 2-row layout per item:
 * - Row 1: Active, Image, Name, Description, Price, Category
 * - Row 2: Variant (badges), Tags (badges), Highlight, Available, Delete
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Loader2,
  Trash2,
  Image as ImageIcon,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  Package,
  Camera,
  X,
  Check,
  Plus,
} from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { cn } from '@/lib/utils';
import { useMenuCategories } from '../hooks/useMenuCategories';
import { useDistinctVariants } from '../hooks/useDistinctVariants';
import { useMenuMedia } from '../hooks/useMenuMedia';
import {
  useBulkUpdateMenuItems,
  useDeleteMenuItem,
  useAddMenuItem,
  type BulkUpdateStatus,
} from '../hooks/useMenuItems';
import { menuApi } from '../api/menuApi';
import { VariantAutocomplete } from './VariantAutocomplete';
import { TagsInput } from './TagsInput';
import type { MenuItem, MenuItemUpdateRequest, MenuMedia } from '../types/menu';

interface MenuItemsBulkEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  menuId: number;
  menuName: string;
  items: MenuItem[];
  onSuccess?: () => void;
  canEdit?: boolean;
  canDelete?: boolean;
}

interface EditableItem {
  id: number;
  name: string;
  description: string;
  price: number | null;
  category: string;
  subcategory: string;
  tags: string;
  is_active: boolean;
  is_featured: boolean;
  is_available: boolean;
  image_url: string | null;
  media_ids: number[]; // Multiple media IDs
  mediaChanged: boolean; // Track if media was changed
  hasChanges: boolean;
  status: BulkUpdateStatus;
  isNew?: boolean; // Flag for new items not yet saved
}

export const MenuItemsBulkEditModal = ({
  isOpen,
  onClose,
  menuId,
  menuName,
  items,
  onSuccess,
  canEdit = true,
  canDelete = true,
}: MenuItemsBulkEditModalProps) => {
  const { t } = useTranslation();

  // Hooks
  const { data: categories } = useMenuCategories(menuId, isOpen);
  const { data: variantSuggestions } = useDistinctVariants(menuId, isOpen);
  const { data: mediaData, isLoading: isLoadingMedia } = useMenuMedia();
  const { bulkUpdate } = useBulkUpdateMenuItems(menuId);
  const deleteMutation = useDeleteMenuItem(menuId);
  const addMutation = useAddMenuItem(menuId);

  // State
  const [editableItems, setEditableItems] = useState<EditableItem[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [showConfirmClose, setShowConfirmClose] = useState(false);
  const [selectedItemIdForMedia, setSelectedItemIdForMedia] = useState<number | null>(null);
  const [newItemCounter, setNewItemCounter] = useState(-1); // Negative IDs for new items

  // Initialize editable items when modal opens or items change
  useEffect(() => {
    if (isOpen && items.length > 0) {
      setEditableItems(
        items.map((item) => ({
          id: item.id,
          name: item.name,
          description: item.description || '',
          price: item.price ?? null,
          category: item.category || '',
          subcategory: item.subcategory || '',
          tags: item.tags || '',
          is_active: item.is_active,
          is_featured: item.is_featured,
          is_available: item.is_available,
          image_url: item.image_url || null,
          // Pre-populate media_ids from existing item media
          media_ids: item.media?.map(m => m.id) || [],
          mediaChanged: false,
          hasChanges: false,
          status: 'idle' as BulkUpdateStatus,
        }))
      );
    }
  }, [isOpen, items]);

  // Calculate modified count
  const modifiedCount = useMemo(
    () => editableItems.filter((item) => item.hasChanges).length,
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

    // Call onSuccess if all succeeded
    if (totalFailed === 0) {
      onSuccess?.();
    }
  };

  // Handle delete
  const handleDelete = async (itemId: number) => {
    const item = editableItems.find((i) => i.id === itemId);
    if (!item) return;

    if (
      window.confirm(
        t(
          'menus.bulkEdit.confirmDelete',
          `Are you sure you want to delete "${item.name}"?`
        )
      )
    ) {
      try {
        await deleteMutation.mutateAsync(itemId);
        setEditableItems((prev) => prev.filter((i) => i.id !== itemId));
      } catch {
        // Error handled by mutation
      }
    }
  };

  // Handle cancel/close
  const handleCancel = () => {
    if (modifiedCount > 0 && !isSaving) {
      setShowConfirmClose(true);
    } else {
      onClose();
    }
  };

  const confirmClose = () => {
    setShowConfirmClose(false);
    onClose();
  };

  // Handle image click - show media picker for specific item
  const handleImageClick = useCallback((itemId: number) => {
    setSelectedItemIdForMedia(itemId);
  }, []);

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

  // Add new empty item
  const handleAddNewItem = useCallback(() => {
    const newItem: EditableItem = {
      id: newItemCounter,
      name: '',
      description: '',
      price: null,
      category: '',
      subcategory: '',
      tags: '',
      is_active: true,
      is_featured: false,
      is_available: true,
      image_url: null,
      media_ids: [],
      mediaChanged: false,
      hasChanges: false,
      status: 'idle',
      isNew: true,
    };
    setEditableItems((prev) => [...prev, newItem]);
    setNewItemCounter((prev) => prev - 1);
  }, [newItemCounter]);

  // Remove new item (not saved yet)
  const handleRemoveNewItem = useCallback((itemId: number) => {
    setEditableItems((prev) => prev.filter((i) => i.id !== itemId));
  }, []);

  // Get selected item for media picker
  const selectedItemForMedia = useMemo(
    () => editableItems.find(item => item.id === selectedItemIdForMedia),
    [editableItems, selectedItemIdForMedia]
  );

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

  const failedCount = editableItems.filter(
    (item) => item.status === 'error'
  ).length;

  // Custom header
  const customHeader = (
    <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {t('menus.bulkEdit.title', 'Bulk Edit Menu Items')}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {menuName} - {t('menus.items.itemsTotal', { count: editableItems.length, defaultValue: '{{count}} items' })}
          </p>
        </div>
        <button
          onClick={handleCancel}
          disabled={isSaving}
          className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-500 dark:text-gray-400 transition-colors disabled:opacity-50"
          aria-label="Close modal"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  );

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={handleCancel}
        maxWidth="6xl"
        showHeader={false}
        customHeader={customHeader}
        closeOnBackdropClick={!isSaving && modifiedCount === 0}
        footer={
          <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between bg-gray-50 dark:bg-gray-900">
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {modifiedCount > 0 ? (
                  <span className="text-amber-600 dark:text-amber-400 font-medium">
                    {modifiedCount}{' '}
                    {t('menus.bulkEdit.itemsModified', 'items modified')}
                  </span>
                ) : (
                  t('menus.bulkEdit.noChanges', 'No changes')
                )}
              </span>
              {failedCount > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRetryFailed}
                  disabled={isSaving}
                  leftIcon={<RefreshCw className="w-3 h-3" />}
                >
                  Retry {failedCount} failed
                </Button>
              )}
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={handleCancel}
                disabled={isSaving}
              >
                {t('common.cancel', 'Cancel')}
              </Button>
              <Button
                variant="primary"
                onClick={handleSaveAll}
                disabled={modifiedCount === 0 || isSaving || !canEdit}
                loading={isSaving}
              >
                {isSaving
                  ? t('menus.bulkEdit.saving', 'Saving...')
                  : t('menus.bulkEdit.saveAll', 'Save All Changes')}
              </Button>
            </div>
          </div>
        }
      >
        {/* Table Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {editableItems.length === 0 ? (
            <div className="text-center py-12">
              <ImageIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">
                {t('menus.bulkEdit.noItems', 'No items to edit')}
              </p>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-12">
                      {t('menus.bulkEdit.active', 'Active')}
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-16">
                      {t('menus.bulkEdit.image', 'Image')}
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-40">
                      {t('menus.bulkEdit.name', 'Name')}
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      {t('menus.bulkEdit.description', 'Description')}
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-24">
                      {t('menus.bulkEdit.price', 'Price')}
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-32">
                      {t('menus.bulkEdit.category', 'Category')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {editableItems.map((item) => (
                    <TableRowGroup
                      key={item.id}
                      item={item}
                      categories={categories?.items || []}
                      variantSuggestions={variantSuggestions || []}
                      onUpdateField={updateField}
                      onDelete={handleDelete}
                      onRemoveNew={handleRemoveNewItem}
                      onImageClick={handleImageClick}
                      disabled={!canEdit || isSaving}
                      canDelete={canDelete && !item.isNew}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Add New Item Button */}
          <div className="mt-4">
            <Button
              variant="outline"
              onClick={handleAddNewItem}
              disabled={!canEdit || isSaving}
              leftIcon={<Plus className="w-4 h-4" />}
              className="w-full border-dashed"
            >
              {t('menus.bulkEdit.addNewItem', 'Add New Item')}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Confirm Close Dialog */}
      <Modal
        isOpen={showConfirmClose}
        onClose={() => setShowConfirmClose(false)}
        maxWidth="sm"
        title={t('menus.bulkEdit.unsavedChanges', 'Unsaved Changes')}
      >
        <div className="p-4">
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {t(
              'menus.bulkEdit.confirmDiscard',
              'You have unsaved changes. Are you sure you want to discard them?'
            )}
          </p>
          <div className="flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => setShowConfirmClose(false)}
            >
              {t('common.cancel', 'Cancel')}
            </Button>
            <Button variant="danger" onClick={confirmClose}>
              {t('common.discard', 'Discard Changes')}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Media Picker Modal - Multi-Select */}
      <Modal
        isOpen={selectedItemIdForMedia !== null}
        onClose={closeMediaPicker}
        maxWidth="lg"
        title={t('menus.bulkEdit.selectImages', 'Select Images')}
      >
        <div className="p-4">
          {/* Current Item Info with selection count */}
          {selectedItemForMedia && (
            <div className="flex items-center gap-4 mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex gap-1">
                {/* Show up to 3 thumbnails */}
                {selectedItemForMedia.media_ids.slice(0, 3).map((mediaId, idx) => {
                  const media = mediaData?.items.find((m) => m.id === mediaId);
                  return media ? (
                    <div
                      key={mediaId}
                      className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden"
                      style={{ marginLeft: idx > 0 ? '-8px' : 0, zIndex: 3 - idx }}
                    >
                      <img src={media.url} alt="" className="w-full h-full object-cover" />
                    </div>
                  ) : null;
                })}
                {selectedItemForMedia.media_ids.length === 0 && (
                  <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center">
                    <ImageIcon className="w-4 h-4 text-gray-400" />
                  </div>
                )}
                {selectedItemForMedia.media_ids.length > 3 && (
                  <div className="w-10 h-10 bg-gray-300 dark:bg-gray-600 rounded flex items-center justify-center text-xs font-medium" style={{ marginLeft: '-8px' }}>
                    +{selectedItemForMedia.media_ids.length - 3}
                  </div>
                )}
              </div>
              <div className="flex-1">
                <div className="font-medium text-gray-900 dark:text-white">
                  {selectedItemForMedia.name || t('menus.bulkEdit.newItem', 'New Item')}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {selectedItemForMedia.media_ids.length > 0
                    ? t('menus.bulkEdit.selectedCount', { count: selectedItemForMedia.media_ids.length, defaultValue: '{{count}} image(s) selected' })
                    : t('menus.bulkEdit.selectMultipleImages', 'Click images to select (multi-select)')}
                </div>
              </div>
              {selectedItemForMedia.media_ids.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRemoveAllImages}
                  className="text-red-600 hover:text-red-700"
                >
                  {t('menus.bulkEdit.clearAll', 'Clear All')}
                </Button>
              )}
            </div>
          )}

          {/* Media Grid - Multi-Select with Checkboxes */}
          {isLoadingMedia ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            </div>
          ) : mediaData && mediaData.items.length > 0 ? (
            <div className="grid grid-cols-5 sm:grid-cols-6 md:grid-cols-8 gap-2 max-h-80 overflow-y-auto">
              {mediaData.items.map((media) => {
                const isSelected = selectedItemForMedia?.media_ids.includes(media.id) ?? false;
                const selectionIndex = selectedItemForMedia?.media_ids.indexOf(media.id) ?? -1;
                return (
                  <button
                    key={media.id}
                    type="button"
                    onClick={() => handleToggleMedia(media)}
                    className={cn(
                      'relative aspect-square rounded-lg overflow-hidden border-2 transition-all hover:opacity-90',
                      isSelected
                        ? 'border-blue-500 ring-2 ring-blue-200 dark:ring-blue-800'
                        : 'border-transparent hover:border-gray-300 dark:hover:border-gray-600'
                    )}
                  >
                    <img
                      src={media.url}
                      alt={media.alt_text || media.original_filename}
                      className="w-full h-full object-cover"
                    />
                    {/* Selection indicator with order number */}
                    {isSelected && (
                      <div className="absolute inset-0 bg-blue-500/30 flex items-center justify-center">
                        <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                          {selectionIndex + 1}
                        </div>
                      </div>
                    )}
                    {/* Checkbox in corner */}
                    <div className={cn(
                      'absolute top-1 right-1 w-5 h-5 rounded border-2 flex items-center justify-center',
                      isSelected
                        ? 'bg-blue-600 border-blue-600'
                        : 'bg-white/80 border-gray-400'
                    )}>
                      {isSelected && <Check className="w-3 h-3 text-white" />}
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <ImageIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">
                {t('menus.bulkEdit.noMedia', 'No images available. Upload images in the Menu Media tab.')}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between gap-3 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {selectedItemForMedia?.media_ids.length
                ? t('menus.bulkEdit.firstImagePrimary', 'First selected image will be the primary thumbnail')
                : ''}
            </div>
            <Button variant="primary" onClick={closeMediaPicker}>
              {t('common.done', 'Done')}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};

// ========== Table Row Group Component ==========

interface TableRowGroupProps {
  item: EditableItem;
  categories: Array<{ id: number; name: string }>;
  variantSuggestions: string[];
  onUpdateField: (
    itemId: number,
    field: keyof EditableItem,
    value: any
  ) => void;
  onDelete: (itemId: number) => void;
  onRemoveNew: (itemId: number) => void;
  onImageClick: (itemId: number) => void;
  disabled: boolean;
  canDelete: boolean;
}

const TableRowGroup = ({
  item,
  categories,
  variantSuggestions,
  onUpdateField,
  onDelete,
  onRemoveNew,
  onImageClick,
  disabled,
  canDelete,
}: TableRowGroupProps) => {
  const { t } = useTranslation();

  const rowClasses = cn(
    'transition-all duration-200',
    item.hasChanges && 'bg-yellow-50 dark:bg-yellow-900/20',
    item.status === 'saving' && 'opacity-50',
    item.status === 'success' && 'bg-green-50 dark:bg-green-900/20',
    item.status === 'error' && 'bg-red-50 dark:bg-red-900/20'
  );

  const borderClasses = cn(
    item.hasChanges && 'border-l-4 border-l-yellow-500',
    item.status === 'success' && 'border-l-4 border-l-green-500',
    item.status === 'error' && 'border-l-4 border-l-red-500'
  );

  // Toggle Switch Component
  const ToggleSwitch = ({ checked, onChange, disabled: isDisabled }: { checked: boolean; onChange: (val: boolean) => void; disabled?: boolean }) => (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={isDisabled}
      onClick={() => onChange(!checked)}
      className={cn(
        'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out',
        'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1',
        isDisabled && 'cursor-not-allowed opacity-50',
        checked ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
      )}
    >
      <span
        className={cn(
          'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
          checked ? 'translate-x-5' : 'translate-x-0'
        )}
      />
    </button>
  );

  return (
    <>
      {/* Row 1: Active, Image, Name, Description, Price, Category */}
      <tr className={cn(rowClasses, borderClasses)}>
        {/* Active Toggle - First column with rowSpan */}
        <td rowSpan={2} className="px-2 py-2 align-middle text-center">
          <div className="flex flex-col items-center gap-1">
            <ToggleSwitch
              checked={item.is_active}
              onChange={(val) => onUpdateField(item.id, 'is_active', val)}
              disabled={disabled}
            />
            {/* Status indicator */}
            {item.status === 'saving' && (
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
            )}
            {item.status === 'success' && (
              <CheckCircle2 className="w-4 h-4 text-green-500" />
            )}
            {item.status === 'error' && (
              <AlertCircle className="w-4 h-4 text-red-500" />
            )}
          </div>
        </td>
        {/* Image - Second column with rowSpan */}
        <td rowSpan={2} className="px-3 py-2 align-top">
          <button
            type="button"
            onClick={() => !disabled && onImageClick(item.id)}
            disabled={disabled}
            className={cn(
              'w-14 h-14 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden flex items-center justify-center relative group',
              'hover:ring-2 hover:ring-blue-500 transition-all cursor-pointer',
              disabled && 'cursor-not-allowed'
            )}
            title={t('menus.bulkEdit.changeImage', 'Click to change image')}
          >
            {item.image_url ? (
              <img
                src={item.image_url}
                alt={item.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <ImageIcon className="w-6 h-6 text-gray-400" />
            )}
            {/* Hover overlay for image change */}
            {!disabled && (
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                <Camera className="w-5 h-5 text-white" />
              </div>
            )}
          </button>
        </td>
        {/* Name */}
        <td className="px-3 py-1.5">
          <input
            type="text"
            value={item.name}
            onChange={(e) => onUpdateField(item.id, 'name', e.target.value)}
            disabled={disabled}
            className={cn(
              'w-full px-2 py-1 border rounded-md text-sm font-medium',
              'bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
              'border-gray-300 dark:border-gray-600',
              'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              disabled && 'opacity-60 cursor-not-allowed'
            )}
            placeholder={t('menus.bulkEdit.namePlaceholder', 'Item name')}
          />
        </td>
        {/* Description */}
        <td className="px-3 py-1.5">
          <input
            type="text"
            value={item.description}
            onChange={(e) => onUpdateField(item.id, 'description', e.target.value)}
            disabled={disabled}
            className={cn(
              'w-full px-2 py-1 border rounded-md text-sm',
              'bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
              'border-gray-300 dark:border-gray-600',
              'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              disabled && 'opacity-60 cursor-not-allowed'
            )}
            placeholder={t('menus.bulkEdit.descriptionPlaceholder', 'Description (optional)')}
          />
        </td>
        {/* Price - Integer only, no decimals */}
        <td className="px-3 py-1.5">
          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            value={item.price !== null ? String(Math.floor(item.price)) : ''}
            onChange={(e) => {
              // Only allow digits
              const value = e.target.value.replace(/[^0-9]/g, '');
              onUpdateField(
                item.id,
                'price',
                value ? parseInt(value, 10) : null
              );
            }}
            onKeyDown={(e) => {
              // Prevent decimal and non-numeric input
              if (e.key === '.' || e.key === ',' || e.key === '-' || e.key === '+' || e.key === 'e' || e.key === 'E') {
                e.preventDefault();
              }
            }}
            disabled={disabled}
            className={cn(
              'w-full px-2 py-1 border rounded-md text-sm',
              'bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
              'border-gray-300 dark:border-gray-600',
              'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              disabled && 'opacity-60 cursor-not-allowed'
            )}
            placeholder="0"
          />
        </td>
        {/* Category */}
        <td className="px-3 py-1.5">
          <select
            value={item.category}
            onChange={(e) => onUpdateField(item.id, 'category', e.target.value)}
            disabled={disabled}
            className={cn(
              'w-full px-2 py-1 border rounded-md text-sm',
              'bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
              'border-gray-300 dark:border-gray-600',
              'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              disabled && 'opacity-60 cursor-not-allowed'
            )}
          >
            <option value="">-- Select --</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.name}>
                {cat.name}
              </option>
            ))}
          </select>
        </td>
      </tr>

      {/* Row 2: Variant, Tags, Highlight, Available, Delete (spans 4 columns) */}
      <tr className={cn(rowClasses, 'border-b border-gray-200 dark:border-gray-700')}>
        <td colSpan={4} className="px-3 py-1.5">
          <div className="flex items-center gap-3">
            {/* Variant */}
            <div className="flex-1">
              <VariantAutocomplete
                value={item.subcategory}
                suggestions={variantSuggestions}
                onChange={(val) => onUpdateField(item.id, 'subcategory', val)}
                disabled={disabled}
                placeholder={t('menus.bulkEdit.variantPlaceholder', 'Variants...')}
              />
            </div>

            {/* Tags - Using TagsInput component */}
            <div className="flex-1">
              <TagsInput
                value={item.tags}
                onChange={(val) => onUpdateField(item.id, 'tags', val)}
                disabled={disabled}
                placeholder={t('menus.bulkEdit.tagsPlaceholder', 'Add tags...')}
              />
            </div>

            {/* Highlight (formerly Featured) */}
            <label className="flex items-center gap-1.5 cursor-pointer" title="Highlight">
              <input
                type="checkbox"
                checked={item.is_featured}
                onChange={(e) =>
                  onUpdateField(item.id, 'is_featured', e.target.checked)
                }
                disabled={disabled}
                className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-amber-500 disabled:opacity-60"
              />
              <Sparkles className={cn('w-4 h-4', item.is_featured ? 'text-amber-500' : 'text-gray-400')} />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {t('menus.bulkEdit.highlight', 'Highlight')}
              </span>
            </label>

            {/* Available */}
            <label className="flex items-center gap-1.5 cursor-pointer" title="Available">
              <input
                type="checkbox"
                checked={item.is_available}
                onChange={(e) =>
                  onUpdateField(item.id, 'is_available', e.target.checked)
                }
                disabled={disabled}
                className="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500 disabled:opacity-60"
              />
              <Package className={cn('w-4 h-4', item.is_available ? 'text-green-600' : 'text-gray-400')} />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {t('menus.bulkEdit.available', 'Avail')}
              </span>
            </label>

            {/* Delete for existing items OR Remove for new items */}
            {item.isNew ? (
              <button
                onClick={() => onRemoveNew(item.id)}
                disabled={disabled}
                className={cn(
                  'p-1.5 rounded text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700',
                  'transition-colors',
                  disabled && 'opacity-60 cursor-not-allowed'
                )}
                title={t('common.remove', 'Remove')}
              >
                <X className="w-4 h-4" />
              </button>
            ) : canDelete ? (
              <button
                onClick={() => onDelete(item.id)}
                disabled={disabled}
                className={cn(
                  'p-1.5 rounded text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30',
                  'transition-colors',
                  disabled && 'opacity-60 cursor-not-allowed'
                )}
                title={t('common.delete', 'Delete')}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            ) : null}
          </div>
        </td>
      </tr>
    </>
  );
};
