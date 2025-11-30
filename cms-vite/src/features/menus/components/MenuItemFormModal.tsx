/**
 * Menu Item Form Modal Component
 * Add or Edit menu items with image selection from menu media
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { X, Image as ImageIcon, Check, Loader2 } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { useAddMenuItem, useUpdateMenuItem } from '../hooks/useMenuItems';
import { useMenuMedia } from '../hooks/useMenuMedia';
import type { MenuItem, MenuMedia } from '../types/menu';

// Form validation schema
const menuItemSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  description: z.string().max(1000).optional().nullable(),
  price: z.coerce.number().min(0).optional().nullable(),
  currency: z.string().default('IDR'),
  category: z.string().max(100).optional().nullable(),
  subcategory: z.string().max(100).optional().nullable(),
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
  const [selectedImageUrl, setSelectedImageUrl] = useState<string | null>(item?.image_url || null);

  const addMutation = useAddMenuItem(menuId);
  const updateMutation = useUpdateMenuItem(menuId);
  const { data: mediaData, isLoading: isLoadingMedia } = useMenuMedia();

  const {
    register,
    handleSubmit,
    reset,
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
      tags: item?.tags || '',
      is_active: item?.is_active ?? true,
      is_featured: item?.is_featured ?? false,
      is_available: item?.is_available ?? true,
    },
  });

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
        tags: item?.tags || '',
        is_active: item?.is_active ?? true,
        is_featured: item?.is_featured ?? false,
        is_available: item?.is_available ?? true,
      });
      setSelectedImageUrl(item?.image_url || null);
      setShowMediaPicker(false);
    }
  }, [item, isOpen, reset]);

  const onSubmit = async (data: MenuItemFormData) => {
    const payload = {
      name: data.name,
      description: data.description || undefined,
      price: data.price || undefined,
      currency: data.currency,
      category: data.category || undefined,
      subcategory: data.subcategory || undefined,
      tags: data.tags || undefined,
      image_url: selectedImageUrl || undefined,
      is_active: data.is_active,
      is_featured: data.is_featured,
      is_available: data.is_available,
    };

    if (isEditMode && item) {
      await updateMutation.mutateAsync({
        itemId: item.id,
        data: payload,
      });
    } else {
      await addMutation.mutateAsync(payload);
    }
    onSuccess?.();
    onClose();
  };

  const handleSelectImage = (media: MenuMedia) => {
    setSelectedImageUrl(media.url || null);
    setShowMediaPicker(false);
  };

  const handleRemoveImage = () => {
    setSelectedImageUrl(null);
  };

  const isPending = isSubmitting || addMutation.isPending || updateMutation.isPending;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode
        ? t('menus.items.editItem', 'Edit Menu Item')
        : t('menus.items.addItem', 'Add Menu Item')
      }
      maxWidth="2xl"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
        {/* Image Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('menus.items.image', 'Image')}
          </label>
          <div className="flex items-start space-x-4">
            {/* Current Image Preview */}
            <div className="w-24 h-24 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0">
              {selectedImageUrl ? (
                <img src={selectedImageUrl} alt="Item" className="w-full h-full object-cover" />
              ) : (
                <ImageIcon className="w-10 h-10 text-gray-400" />
              )}
            </div>

            {/* Image Actions */}
            <div className="flex flex-col space-y-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowMediaPicker(!showMediaPicker)}
              >
                {showMediaPicker
                  ? t('menus.items.hideMedia', 'Hide Media')
                  : t('menus.items.selectImage', 'Select Image')
                }
              </Button>
              {selectedImageUrl && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleRemoveImage}
                  className="text-red-600 hover:text-red-700"
                >
                  {t('menus.items.removeImage', 'Remove')}
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Media Picker */}
        {showMediaPicker && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-gray-50 dark:bg-gray-800/50">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                {t('menus.items.selectFromMedia', 'Select from Menu Media')}
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
                {mediaData.items.map((media) => (
                  <button
                    key={media.id}
                    type="button"
                    onClick={() => handleSelectImage(media)}
                    className={`
                      relative aspect-square rounded-md overflow-hidden border-2 transition-all
                      ${selectedImageUrl === media.url
                        ? 'border-blue-500 ring-2 ring-blue-200'
                        : 'border-transparent hover:border-gray-300 dark:hover:border-gray-600'
                      }
                    `}
                  >
                    <img
                      src={media.url}
                      alt={media.alt_text || media.original_filename}
                      className="w-full h-full object-cover"
                    />
                    {selectedImageUrl === media.url && (
                      <div className="absolute inset-0 bg-blue-500 bg-opacity-30 flex items-center justify-center">
                        <Check className="w-5 h-5 text-white" />
                      </div>
                    )}
                  </button>
                ))}
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
        <div className="grid grid-cols-2 gap-4">
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
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('menus.items.category', 'Category')}
            </label>
            <input
              type="text"
              {...register('category')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
              placeholder={t('menus.items.categoryPlaceholder', 'e.g. Main Course')}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('menus.items.subcategory', 'Subcategory')}
            </label>
            <input
              type="text"
              {...register('subcategory')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
              placeholder={t('menus.items.subcategoryPlaceholder', 'e.g. Indonesian')}
            />
          </div>
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

        {/* Form Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button type="button" variant="outline" onClick={onClose}>
            {t('common.cancel', 'Cancel')}
          </Button>
          <Button type="submit" loading={isPending}>
            {isEditMode ? t('common.save', 'Save') : t('common.add', 'Add')}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
