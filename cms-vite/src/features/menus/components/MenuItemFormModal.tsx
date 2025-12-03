/**
 * Menu Item Form Modal Component
 * Add or Edit menu items with image selection from menu media
 * Category field uses dropdown populated from menu's categories
 */

import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { X, Image as ImageIcon, Check, Loader2, Plus, Star } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { useAddMenuItem, useUpdateMenuItem } from '../hooks/useMenuItems';
import { useMenuMedia, useBulkSetItemMedia, useItemMedia } from '../hooks/useMenuMedia';
import { useMenuCategories } from '../hooks/useMenuCategories';
import { useDistinctVariants } from '../hooks/useDistinctVariants';
import { VariantAutocomplete } from './VariantAutocomplete';
import type { MenuItem, MenuMedia } from '../types/menu';

// Form validation schema
const menuItemSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  description: z.string().max(1000).optional().nullable(),
  price: z.coerce.number().min(0).optional().nullable(),
  currency: z.string().default('IDR'),
  category: z.string().max(100).optional().nullable(),
  subcategory: z.string().max(100).optional().nullable(),
  variant: z.string().max(200).optional().nullable(),  // Item variations: Hot, Cold, Large, Small
  tags: z.string().max(200).optional().nullable(),
  is_active: z.boolean().default(true),
  is_featured: z.boolean().default(false),
  is_available: z.boolean().default(true),
});

type MenuItemFormData = z.infer<typeof menuItemSchema>;

interface MenuItemFormModalProps {
  isOpen: boolean;
  menuId: number;
  item?: MenuItem | null; // null = add mode, object = edit mode
  onClose: () => void;
  onSuccess?: () => void;
}

export const MenuItemFormModal = ({
  isOpen,
  menuId,
  item,
  onClose,
  onSuccess,
}: MenuItemFormModalProps) => {
  const { t } = useTranslation();
  const isEditMode = !!item;
  const [showMediaPicker, setShowMediaPicker] = useState(false);
  // Multi-image selection: track selected media IDs and which is primary
  const [selectedMediaIds, setSelectedMediaIds] = useState<Set<number>>(new Set());
  const [primaryMediaId, setPrimaryMediaId] = useState<number | null>(null);
  const [showCustomCategory, setShowCustomCategory] = useState(false);

  const addMutation = useAddMenuItem(menuId);
  const updateMutation = useUpdateMenuItem(menuId);
  const bulkSetMediaMutation = useBulkSetItemMedia(menuId);
  const { data: mediaData, isLoading: isLoadingMedia } = useMenuMedia();
  const { data: categoriesData, isLoading: isLoadingCategories } = useMenuCategories(menuId);
  const { data: variantSuggestions } = useDistinctVariants(menuId);

  // Fetch existing media for the item being edited
  const { data: itemMediaData, isLoading: isLoadingItemMedia } = useItemMedia(
    menuId,
    isEditMode && item ? item.id : null
  );

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    control,
    formState: { errors, isSubmitting },
  } = useForm<MenuItemFormData>({
    resolver: zodResolver(menuItemSchema),
    defaultValues: {
      name: item?.name || '',
      description: item?.description || '',
      price: item?.price || undefined,
      currency: item?.currency || 'IDR',
      category: item?.category || '',
      subcategory: item?.subcategory || '',
      variant: item?.variant || '',
      tags: item?.tags || '',
      is_active: item?.is_active ?? true,
      is_featured: item?.is_featured ?? false,
      is_available: item?.is_available ?? true,
    },
  });

  const currentCategory = watch('category');

  // Reset form when item changes
  useEffect(() => {
    if (isOpen) {
      reset({
        name: item?.name || '',
        description: item?.description || '',
        price: item?.price || undefined,
        currency: item?.currency || 'IDR',
        category: item?.category || '',
        subcategory: item?.subcategory || '',
        variant: item?.variant || '',
        tags: item?.tags || '',
        is_active: item?.is_active ?? true,
        is_featured: item?.is_featured ?? false,
        is_available: item?.is_available ?? true,
      });

      // Reset media selection when opening (will be populated from itemMediaData)
      if (!isEditMode) {
        setSelectedMediaIds(new Set());
        setPrimaryMediaId(null);
      }

      setShowMediaPicker(false);
      setShowCustomCategory(false);
    }
  }, [item, isOpen, reset, isEditMode]);

  // Initialize selected media from fetched itemMediaData (for edit mode)
  useEffect(() => {
    if (isOpen && isEditMode && itemMediaData?.items && itemMediaData.items.length > 0) {
      const mediaIds = new Set<number>();
      let primaryId: number | null = null;

      itemMediaData.items.forEach((m) => {
        // menu_media_id is the actual media ID in the menu_media table
        if (m.menu_media_id) {
          mediaIds.add(m.menu_media_id);
          if (m.is_primary) {
            primaryId = m.menu_media_id;
          }
        }
      });

      setSelectedMediaIds(mediaIds);
      setPrimaryMediaId(primaryId || (mediaIds.size > 0 ? Array.from(mediaIds)[0] : null));
    } else if (isOpen && isEditMode && itemMediaData?.items?.length === 0) {
      // Item has no media assigned
      setSelectedMediaIds(new Set());
      setPrimaryMediaId(null);
    }
  }, [isOpen, isEditMode, itemMediaData]);

  // Check if current category is in the list or custom
  useEffect(() => {
    if (categoriesData && currentCategory) {
      const isInList = categoriesData.items.some(cat => cat.name === currentCategory);
      setShowCustomCategory(!isInList && currentCategory !== '');
    }
  }, [categoriesData, currentCategory]);

  const onSubmit = async (data: MenuItemFormData) => {
    // Get primary image URL for backward compatibility
    const primaryMedia = primaryMediaId && mediaData?.items
      ? mediaData.items.find(m => m.id === primaryMediaId)
      : null;

    const payload = {
      name: data.name,
      description: data.description || undefined,
      price: data.price || undefined,
      currency: data.currency,
      category: data.category || undefined,
      subcategory: data.subcategory || undefined,
      variant: data.variant || undefined,
      tags: data.tags || undefined,
      image_url: primaryMedia?.url || undefined,
      is_active: data.is_active,
      is_featured: data.is_featured,
      is_available: data.is_available,
    };

    if (isEditMode && item) {
      // Update menu item
      await updateMutation.mutateAsync({
        itemId: item.id,
        data: payload,
      });

      // Bulk set media (replaces existing)
      if (selectedMediaIds.size > 0) {
        await bulkSetMediaMutation.mutateAsync({
          itemId: item.id,
          data: {
            media_ids: Array.from(selectedMediaIds),
            primary_media_id: primaryMediaId || undefined,
          },
        });
      }
    } else {
      // For new items, first create the item
      const newItem = await addMutation.mutateAsync(payload);

      // Then set media if any selected
      if (selectedMediaIds.size > 0 && newItem?.id) {
        await bulkSetMediaMutation.mutateAsync({
          itemId: newItem.id,
          data: {
            media_ids: Array.from(selectedMediaIds),
            primary_media_id: primaryMediaId || undefined,
          },
        });
      }
    }
    onSuccess?.();
    onClose();
  };

  // Toggle media selection (multi-select)
  const handleToggleMedia = (media: MenuMedia) => {
    setSelectedMediaIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(media.id)) {
        newSet.delete(media.id);
        // If removing primary, pick a new primary
        if (primaryMediaId === media.id) {
          setPrimaryMediaId(newSet.size > 0 ? Array.from(newSet)[0] : null);
        }
      } else {
        newSet.add(media.id);
        // If first selection, make it primary
        if (!primaryMediaId) {
          setPrimaryMediaId(media.id);
        }
      }
      return newSet;
    });
  };

  // Set a media as primary (with star icon click)
  const handleSetPrimary = (mediaId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (selectedMediaIds.has(mediaId)) {
      setPrimaryMediaId(mediaId);
    }
  };

  // Remove all selected images
  const handleRemoveAllImages = () => {
    setSelectedMediaIds(new Set());
    setPrimaryMediaId(null);
  };

  // Get selected media objects for preview
  const getSelectedMediaList = (): MenuMedia[] => {
    if (!mediaData?.items) return [];
    return mediaData.items.filter(m => selectedMediaIds.has(m.id));
  };

  const handleCategoryChange = (value: string) => {
    if (value === '__custom__') {
      setShowCustomCategory(true);
      setValue('category', '');
    } else {
      setShowCustomCategory(false);
      setValue('category', value);
    }
  };

  const isPending = isSubmitting || addMutation.isPending || updateMutation.isPending || bulkSetMediaMutation.isPending;

  // Get categories list
  const categories = categoriesData?.items || [];
  const hasCategories = categories.length > 0;

  // Footer component with sticky buttons
  const footerContent = (
    <div className="flex justify-end space-x-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <Button type="button" variant="outline" onClick={onClose}>
        {t('common.cancel', 'Cancel')}
      </Button>
      <Button type="submit" form="menuItemForm" loading={isPending}>
        {isEditMode ? t('common.save', 'Save') : t('common.add', 'Add')}
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode
        ? t('menus.items.editItem', 'Edit Menu Item')
        : t('menus.items.addItem', 'Add Menu Item')
      }
      maxWidth="2xl"
      footer={footerContent}
    >
      <form id="menuItemForm" onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
        {/* Image Selection - Multi-select */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('menus.items.images', 'Images')}
            {selectedMediaIds.size > 0 && (
              <span className="ml-2 text-xs font-normal text-gray-500">
                ({selectedMediaIds.size} selected)
              </span>
            )}
          </label>

          {/* Selected Images Preview */}
          <div className="flex flex-wrap items-start gap-3 mb-3">
            {isEditMode && isLoadingItemMedia ? (
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Loading assigned images...</span>
              </div>
            ) : getSelectedMediaList().length > 0 ? (
              getSelectedMediaList().map((media) => (
                <div
                  key={media.id}
                  className={`relative w-20 h-20 rounded-lg overflow-hidden border-2 ${
                    primaryMediaId === media.id
                      ? 'border-yellow-500 ring-2 ring-yellow-200'
                      : 'border-gray-200 dark:border-gray-600'
                  }`}
                >
                  <img src={media.url} alt={media.title || ''} className="w-full h-full object-cover" />
                  {/* Primary badge */}
                  {primaryMediaId === media.id && (
                    <div className="absolute top-0.5 left-0.5 bg-yellow-500 text-white text-[9px] px-1 rounded font-medium">
                      Primary
                    </div>
                  )}
                  {/* Remove button */}
                  <button
                    type="button"
                    onClick={() => handleToggleMedia(media)}
                    className="absolute top-0.5 right-0.5 bg-red-500 text-white rounded-full p-0.5 hover:bg-red-600"
                  >
                    <X className="w-3 h-3" />
                  </button>
                  {/* Set as primary button */}
                  {primaryMediaId !== media.id && (
                    <button
                      type="button"
                      onClick={(e) => handleSetPrimary(media.id, e)}
                      className="absolute bottom-0.5 right-0.5 bg-gray-800/70 text-yellow-400 rounded-full p-0.5 hover:bg-gray-800"
                      title="Set as primary"
                    >
                      <Star className="w-3 h-3" />
                    </button>
                  )}
                </div>
              ))
            ) : (
              <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                <ImageIcon className="w-8 h-8 text-gray-400" />
              </div>
            )}

            {/* Action buttons */}
            <div className="flex flex-col justify-center space-y-1.5">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowMediaPicker(!showMediaPicker)}
              >
                {showMediaPicker
                  ? t('menus.items.hideMedia', 'Hide Media')
                  : t('menus.items.selectImages', 'Select Images')
                }
              </Button>
              {selectedMediaIds.size > 0 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleRemoveAllImages}
                  className="text-red-600 hover:text-red-700 text-xs"
                >
                  {t('menus.items.removeAll', 'Remove All')}
                </Button>
              )}
            </div>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {t('menus.items.multiImageHint', 'Click images to select. Click star to set primary.')}
          </p>
        </div>

        {/* Media Picker - Multi-select */}
        {showMediaPicker && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-gray-50 dark:bg-gray-800/50">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                {t('menus.items.selectFromMedia', 'Select from Menu Media')}
                <span className="ml-2 text-xs font-normal text-gray-500">
                  (click to toggle selection)
                </span>
              </h4>
              <button
                type="button"
                onClick={() => setShowMediaPicker(false)}
                className="text-gray-400 hover:text-gray-500 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {isLoadingMedia ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              </div>
            ) : mediaData && mediaData.items.length > 0 ? (
              <div className="grid grid-cols-5 sm:grid-cols-7 gap-2 max-h-48 overflow-y-auto">
                {mediaData.items.map((media) => {
                  const isSelected = selectedMediaIds.has(media.id);
                  const isPrimary = primaryMediaId === media.id;

                  return (
                    <button
                      key={media.id}
                      type="button"
                      onClick={() => handleToggleMedia(media)}
                      className={`
                        relative aspect-square rounded-md overflow-hidden border-2 transition-all
                        ${isSelected
                          ? isPrimary
                            ? 'border-yellow-500 ring-2 ring-yellow-200'
                            : 'border-blue-500 ring-2 ring-blue-200'
                          : 'border-transparent hover:border-gray-300 dark:hover:border-gray-600'
                        }
                      `}
                    >
                      <img
                        src={media.url}
                        alt={media.alt_text || media.original_filename}
                        className="w-full h-full object-cover"
                      />
                      {isSelected && (
                        <div className={`absolute inset-0 ${isPrimary ? 'bg-yellow-500' : 'bg-blue-500'} bg-opacity-30 flex items-center justify-center`}>
                          {isPrimary ? (
                            <Star className="w-5 h-5 text-white fill-white" />
                          ) : (
                            <Check className="w-5 h-5 text-white" />
                          )}
                        </div>
                      )}
                      {/* Click to set as primary when already selected */}
                      {isSelected && !isPrimary && (
                        <button
                          type="button"
                          onClick={(e) => handleSetPrimary(media.id, e)}
                          className="absolute bottom-0.5 right-0.5 bg-gray-800/70 text-yellow-400 rounded-full p-0.5 hover:bg-gray-800 z-10"
                          title="Set as primary"
                        >
                          <Star className="w-3 h-3" />
                        </button>
                      )}
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                {t('menus.items.noMediaAvailable', 'No images available. Upload images in the Menu Media tab.')}
              </p>
            )}
          </div>
        )}

        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t('menus.items.name', 'Name')} <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            {...register('name')}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
            placeholder={t('menus.items.namePlaceholder', 'e.g. Nasi Goreng Special')}
          />
          {errors.name && <p className="mt-1 text-sm text-red-500">{errors.name.message}</p>}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t('menus.items.description', 'Description')}
          </label>
          <textarea
            {...register('description')}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
            placeholder={t('menus.items.descriptionPlaceholder', 'Brief description of the item')}
          />
        </div>

        {/* Price & Currency */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('menus.items.price', 'Price')}
            </label>
            <input
              type="number"
              step="1"
              {...register('price')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('menus.items.currency', 'Currency')}
            </label>
            <select
              {...register('currency')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="IDR">IDR</option>
              <option value="USD">USD</option>
              <option value="SGD">SGD</option>
              <option value="MYR">MYR</option>
            </select>
          </div>
        </div>

        {/* Category & Subcategory */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('menus.items.category', 'Category')}
            </label>
            {isLoadingCategories ? (
              <div className="flex items-center justify-center py-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              </div>
            ) : showCustomCategory ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  {...register('category')}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
                  placeholder={t('menus.items.categoryPlaceholder', 'e.g. Main Course')}
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => {
                    setShowCustomCategory(false);
                    setValue('category', '');
                  }}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <select
                value={currentCategory || ''}
                onChange={(e) => handleCategoryChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">-- Select Category --</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.name}>
                    {cat.name}
                  </option>
                ))}
                {hasCategories && <option disabled>──────────</option>}
                <option value="__custom__">+ Add Custom Category</option>
              </select>
            )}
            {!hasCategories && !showCustomCategory && (
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {t('menus.items.noCategoriesHint', 'No categories defined. Add categories in Menu Edit.')}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('menus.items.subcategory', 'Subcategory')}
            </label>
            {(() => {
              // Get subcategories for selected category
              const selectedCat = categories.find(cat => cat.name === currentCategory);
              const subcategories = selectedCat?.subcategories || [];
              const hasSubcategories = subcategories.length > 0;

              if (!currentCategory) {
                return (
                  <input
                    type="text"
                    {...register('subcategory')}
                    disabled
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400"
                    placeholder={t('menus.items.selectCategoryFirst', 'Select category first')}
                  />
                );
              }

              if (hasSubcategories) {
                return (
                  <select
                    {...register('subcategory')}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">-- Select Subcategory --</option>
                    {subcategories.map((sub) => (
                      <option key={sub} value={sub}>
                        {sub}
                      </option>
                    ))}
                  </select>
                );
              }

              return (
                <input
                  type="text"
                  {...register('subcategory')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
                  placeholder={t('menus.items.subcategoryPlaceholder', 'e.g. Hot, Cold')}
                />
              );
            })()}
            {currentCategory && (
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {t('menus.items.subcategoryHint', 'Subcategories can be managed in Menu Edit → Categories')}
              </p>
            )}
          </div>
        </div>

        {/* Variant */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t('menus.items.variant', 'Variant')}
          </label>
          <Controller
            name="variant"
            control={control}
            render={({ field }) => (
              <VariantAutocomplete
                value={field.value || ''}
                suggestions={variantSuggestions || []}
                onChange={field.onChange}
                placeholder={t('menus.items.variantPlaceholder', 'e.g. Hot, Cold, Large, Small...')}
              />
            )}
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {t('menus.items.variantHint', 'Press Enter or comma to add variant')}
          </p>
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {t('menus.items.tags', 'Tags')}
          </label>
          <input
            type="text"
            {...register('tags')}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
            placeholder={t('menus.items.tagsPlaceholder', 'e.g. spicy, bestseller, halal (comma separated)')}
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {t('menus.items.tagsHint', 'Separate multiple tags with commas')}
          </p>
        </div>

        {/* Status Toggles - Horizontal */}
        <div className="flex flex-wrap gap-6">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              {...register('is_active')}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_active" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              {t('menus.items.isActive', 'Active')}
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_featured"
              {...register('is_featured')}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_featured" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              {t('menus.items.isFeatured', 'Featured')}
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_available"
              {...register('is_available')}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_available" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              {t('menus.items.isAvailable', 'Available')}
            </label>
          </div>
        </div>

      </form>
    </Modal>
  );
};
