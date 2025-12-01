/**
 * Menu Form Component
 * Form for creating and editing menus
 * In edit mode, also shows category management section
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Edit2, Trash2, X, Loader2 } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { useCreateMenu, useUpdateMenu } from '../hooks/useMenus';
import {
  useMenuCategories,
  useCreateMenuCategory,
  useUpdateMenuCategory,
  useDeleteMenuCategory,
} from '../hooks/useMenuCategories';
import type { Menu, MenuType, MenuCategory } from '../types/menu';

const menuFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name is too long'),
  menu_type: z.enum(['restaurant', 'laundry', 'spa', 'room_service', 'other']),
  description: z.string().optional(),
  is_active: z.boolean().default(true),
  show_prices: z.boolean().default(true),
  display_mode: z.enum(['grid', 'list', 'carousel', 'minimalist']).default('grid'),
  // Color scheme (60-30-10 principle)
  primary_color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid color format').optional().or(z.literal('')),
  secondary_color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid color format').optional().or(z.literal('')),
  theme_color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid color format').optional().or(z.literal('')),
  whatsapp_number: z.string().max(20).optional().or(z.literal('')),
  phone_number: z.string().max(20).optional().or(z.literal('')),
  contact_label: z.string().max(100).optional().or(z.literal('')),
  outlet_extension: z.string().max(50).optional().or(z.literal('')),
  footer_description: z.string().optional().or(z.literal('')),
});

type MenuFormData = z.infer<typeof menuFormSchema>;

interface MenuFormProps {
  menu?: Menu;
  onClose: () => void;
  onSuccess?: () => void;
}

export const MenuForm = ({ menu, onClose, onSuccess }: MenuFormProps) => {
  const isEditMode = !!menu;
  const createMutation = useCreateMenu();
  const updateMutation = useUpdateMenu();

  // Category management state (only for edit mode)
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState<MenuCategory | null>(null);
  const [newCategoryName, setNewCategoryName] = useState('');

  // Subcategory management state
  const [addingSubcategoryForId, setAddingSubcategoryForId] = useState<number | null>(null);
  const [newSubcategoryName, setNewSubcategoryName] = useState('');

  // Fetch categories for this menu (only in edit mode)
  const { data: categoriesData, isLoading: isLoadingCategories } = useMenuCategories(
    menu?.id || 0,
    isEditMode
  );

  // Category mutations
  const createCategoryMutation = useCreateMenuCategory(menu?.id || 0);
  const updateCategoryMutation = useUpdateMenuCategory(menu?.id || 0);
  const deleteCategoryMutation = useDeleteMenuCategory(menu?.id || 0);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<MenuFormData>({
    resolver: zodResolver(menuFormSchema),
    defaultValues: menu
      ? {
          name: menu.name,
          menu_type: menu.menu_type,
          description: menu.description || '',
          is_active: menu.is_active,
          show_prices: menu.show_prices,
          display_mode: menu.display_mode,
          // Color scheme (60-30-10)
          primary_color: menu.primary_color || '#ffffff',
          secondary_color: menu.secondary_color || '#f3f4f6',
          theme_color: menu.theme_color || '#3b82f6',
          whatsapp_number: menu.whatsapp_number || '',
          phone_number: menu.phone_number || '',
          contact_label: menu.contact_label || '',
          outlet_extension: menu.outlet_extension || '',
          footer_description: menu.footer_description || '',
        }
      : {
          is_active: true,
          show_prices: true,
          display_mode: 'grid',
          // Default colors (60-30-10)
          primary_color: '#ffffff',
          secondary_color: '#f3f4f6',
          theme_color: '#3b82f6',
        },
  });

  const currentMenuType = watch('menu_type');

  const onSubmit = async (data: MenuFormData) => {
    try {
      // Clean empty strings and prepare payload
      const baseData = {
        name: data.name,
        menu_type: data.menu_type,
        description: data.description || undefined,
        is_active: data.is_active,
        show_prices: data.show_prices,
        display_mode: data.display_mode,
        // Color scheme (60-30-10)
        primary_color: data.primary_color || '#ffffff',
        secondary_color: data.secondary_color || '#f3f4f6',
        theme_color: data.theme_color || '#3b82f6',
        whatsapp_number: data.whatsapp_number || undefined,
        phone_number: data.phone_number || undefined,
        contact_label: data.contact_label || undefined,
        outlet_extension: data.outlet_extension || undefined,
        footer_description: data.footer_description || undefined,
      };

      if (isEditMode) {
        await updateMutation.mutateAsync({ id: menu.id, data: baseData });
      } else {
        await createMutation.mutateAsync(baseData);
      }

      onSuccess?.();
      onClose();
    } catch (error) {
      // Error handled by mutation hooks
    }
  };

  // Category handlers
  const handleAddCategory = async () => {
    if (!newCategoryName.trim() || !menu) return;

    await createCategoryMutation.mutateAsync({
      name: newCategoryName.trim(),
      menu_type: menu.menu_type,
      menu_id: menu.id,
    });

    setNewCategoryName('');
    setShowCategoryForm(false);
  };

  const handleUpdateCategory = async () => {
    if (!newCategoryName.trim() || !editingCategory) return;

    await updateCategoryMutation.mutateAsync({
      categoryId: editingCategory.id,
      data: { name: newCategoryName.trim() },
    });

    setNewCategoryName('');
    setEditingCategory(null);
    setShowCategoryForm(false);
  };

  const handleDeleteCategory = async (categoryId: number) => {
    if (confirm('Are you sure you want to delete this category?')) {
      await deleteCategoryMutation.mutateAsync(categoryId);
    }
  };

  const startEditCategory = (category: MenuCategory) => {
    setEditingCategory(category);
    setNewCategoryName(category.name);
    setShowCategoryForm(true);
  };

  const cancelCategoryForm = () => {
    setShowCategoryForm(false);
    setEditingCategory(null);
    setNewCategoryName('');
  };

  // Subcategory handlers
  const handleAddSubcategory = async (category: MenuCategory) => {
    if (!newSubcategoryName.trim()) return;

    const updatedSubcategories = [...(category.subcategories || []), newSubcategoryName.trim()];
    await updateCategoryMutation.mutateAsync({
      categoryId: category.id,
      data: { subcategories: updatedSubcategories },
    });

    setNewSubcategoryName('');
    setAddingSubcategoryForId(null);
  };

  const handleRemoveSubcategory = async (category: MenuCategory, subcategoryToRemove: string) => {
    const updatedSubcategories = (category.subcategories || []).filter(
      (sub) => sub !== subcategoryToRemove
    );
    await updateCategoryMutation.mutateAsync({
      categoryId: category.id,
      data: { subcategories: updatedSubcategories },
    });
  };

  const isCategoryMutating =
    createCategoryMutation.isPending ||
    updateCategoryMutation.isPending ||
    deleteCategoryMutation.isPending;

  // Footer with action buttons
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end space-x-3">
        <Button
          type="button"
          variant="outline"
          onClick={onClose}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          form="menu-form"
          loading={isSubmitting}
        >
          {isEditMode ? 'Update Menu' : 'Create Menu'}
        </Button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={isEditMode ? 'Edit Menu' : 'Create New Menu'}
      maxWidth="2xl"
      footer={footer}
    >
      {/* Scrollable form content */}
      <form id="menu-form" onSubmit={handleSubmit(onSubmit)} className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Basic Info */}
        <div className="space-y-4">
          <h3 className="font-medium text-gray-900 dark:text-white">Basic Information</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Menu Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              {...register('name')}
              className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
              placeholder="e.g., Restaurant Menu"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Menu Type <span className="text-red-500">*</span>
            </label>
            <select
              {...register('menu_type')}
              className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
            >
              <option value="restaurant">Restaurant</option>
              <option value="laundry">Laundry</option>
              <option value="spa">Spa</option>
              <option value="room_service">Room Service</option>
              <option value="other">Other</option>
            </select>
            {errors.menu_type && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.menu_type.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
            <textarea
              {...register('description')}
              rows={3}
              className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
              placeholder="Optional menu description"
            />
          </div>
        </div>

        {/* Category Management (Edit Mode Only) */}
        {isEditMode && menu && (
          <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-6">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-gray-900 dark:text-white">Categories</h3>
              {!showCategoryForm && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCategoryForm(true)}
                  leftIcon={<Plus className="w-4 h-4" />}
                >
                  Add Category
                </Button>
              )}
            </div>

            {/* Category Form */}
            {showCategoryForm && (
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={newCategoryName}
                    onChange={(e) => setNewCategoryName(e.target.value)}
                    placeholder="Category name"
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-blue-500 focus:border-blue-500"
                    autoFocus
                  />
                  <Button
                    type="button"
                    size="sm"
                    onClick={editingCategory ? handleUpdateCategory : handleAddCategory}
                    disabled={!newCategoryName.trim() || isCategoryMutating}
                    loading={createCategoryMutation.isPending || updateCategoryMutation.isPending}
                  >
                    {editingCategory ? 'Update' : 'Add'}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={cancelCategoryForm}
                    disabled={isCategoryMutating}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}

            {/* Category List */}
            {isLoadingCategories ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              </div>
            ) : categoriesData && categoriesData.items.length > 0 ? (
              <div className="space-y-3">
                {categoriesData.items.map((category) => (
                  <div
                    key={category.id}
                    className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                  >
                    {/* Category header */}
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">{category.name}</span>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => startEditCategory(category)}
                          className="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 transition-colors"
                          title="Edit"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteCategory(category.id)}
                          className="p-1.5 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
                          title="Delete"
                          disabled={deleteCategoryMutation.isPending}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Subcategories section */}
                    <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                      <span className="text-xs text-gray-500 dark:text-gray-400">Subcategories:</span>
                      <div className="mt-1 flex flex-wrap gap-2 items-center">
                        {/* Subcategory chips */}
                        {(category.subcategories || []).map((sub) => (
                          <span
                            key={sub}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded-md"
                          >
                            {sub}
                            <button
                              type="button"
                              onClick={() => handleRemoveSubcategory(category, sub)}
                              className="hover:text-red-600 dark:hover:text-red-400"
                              title="Remove"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))}

                        {/* Add subcategory input or button */}
                        {addingSubcategoryForId === category.id ? (
                          <div className="flex items-center gap-1">
                            <input
                              type="text"
                              value={newSubcategoryName}
                              onChange={(e) => setNewSubcategoryName(e.target.value)}
                              placeholder="Subcategory name"
                              className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-xs bg-white dark:bg-gray-700 text-gray-900 dark:text-white w-32"
                              autoFocus
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  e.preventDefault();
                                  handleAddSubcategory(category);
                                } else if (e.key === 'Escape') {
                                  setAddingSubcategoryForId(null);
                                  setNewSubcategoryName('');
                                }
                              }}
                            />
                            <button
                              type="button"
                              onClick={() => handleAddSubcategory(category)}
                              disabled={!newSubcategoryName.trim() || updateCategoryMutation.isPending}
                              className="p-1 text-blue-600 hover:text-blue-700 disabled:opacity-50"
                            >
                              <Plus className="w-4 h-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setAddingSubcategoryForId(null);
                                setNewSubcategoryName('');
                              }}
                              className="p-1 text-gray-500 hover:text-gray-700"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => setAddingSubcategoryForId(category.id)}
                            className="inline-flex items-center gap-1 px-2 py-1 border border-dashed border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 text-xs rounded-md hover:border-blue-500 hover:text-blue-500 transition-colors"
                          >
                            <Plus className="w-3 h-3" />
                            Add
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                No categories yet. Add categories to organize your menu items.
              </p>
            )}
          </div>
        )}

        {/* Display Settings */}
        <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-6">
          <h3 className="font-medium text-gray-900 dark:text-white">Display Settings</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Display Mode</label>
            <select
              {...register('display_mode')}
              className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
            >
              <option value="grid">Grid</option>
              <option value="list">List</option>
              <option value="carousel">Carousel</option>
              <option value="minimalist">Minimalist</option>
            </select>
          </div>

          {/* Color Scheme - 60-30-10 Principle */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Color Scheme (60-30-10)
              </label>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Primary | Secondary | Accent
              </span>
            </div>

            <div className="grid grid-cols-3 gap-4">
              {/* Primary Color - 60% */}
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Background (60%)
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="color"
                    {...register('primary_color')}
                    className="h-10 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 cursor-pointer"
                  />
                </div>
                <input
                  type="text"
                  {...register('primary_color')}
                  className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-2 py-1 text-xs"
                  placeholder="#ffffff"
                />
              </div>

              {/* Secondary Color - 30% */}
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Header (30%)
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="color"
                    {...register('secondary_color')}
                    className="h-10 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 cursor-pointer"
                  />
                </div>
                <input
                  type="text"
                  {...register('secondary_color')}
                  className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-2 py-1 text-xs"
                  placeholder="#f3f4f6"
                />
              </div>

              {/* Theme/Accent Color - 10% */}
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Accent (10%)
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="color"
                    {...register('theme_color')}
                    className="h-10 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 cursor-pointer"
                  />
                </div>
                <input
                  type="text"
                  {...register('theme_color')}
                  className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-2 py-1 text-xs"
                  placeholder="#3b82f6"
                />
              </div>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              60% Background, 30% Header/Categories, 10% Buttons/Highlights
            </p>
            {(errors.primary_color || errors.secondary_color || errors.theme_color) && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">Invalid color format (use #RRGGBB)</p>
            )}
          </div>

          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input type="checkbox" {...register('is_active')} className="rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Active</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" {...register('show_prices')} className="rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Show Prices</span>
            </label>
          </div>
        </div>

        {/* Contact Buttons */}
        <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-6">
          <h3 className="font-medium text-gray-900 dark:text-white">Contact Information</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              WhatsApp Number
            </label>
            <input
              type="text"
              {...register('whatsapp_number')}
              className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
              placeholder="+62 812 3456 7890"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Phone Number</label>
            <input
              type="text"
              {...register('phone_number')}
              className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
              placeholder="+62 21 1234 5678"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Contact Label
            </label>
            <input
              type="text"
              {...register('contact_label')}
              className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
              placeholder="e.g., Order Now, Call Us, Contact Restaurant"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Outlet Extension
            </label>
            <input
              type="text"
              {...register('outlet_extension')}
              className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
              placeholder="e.g., 123, 4567"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Phone extension number displayed as a badge (non-clickable info)
            </p>
          </div>
        </div>

        {/* Footer Settings */}
        <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-6">
          <h3 className="font-medium text-gray-900 dark:text-white">Footer Settings</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Footer Description
            </label>
            <textarea
              {...register('footer_description')}
              rows={2}
              className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
              placeholder="Custom footer text displayed in the menu viewer"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              This text will be displayed in the footer of the public menu viewer
            </p>
          </div>
        </div>
      </form>
    </Modal>
  );
};
