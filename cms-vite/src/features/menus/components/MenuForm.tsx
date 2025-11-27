/**
 * Menu Form Component
 * Form for creating and editing menus
 *
 * ✅ REFACTORED: Now uses shared Modal component for consistency
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '@/shared/components';
import { useCreateMenu, useUpdateMenu } from '../hooks/useMenus';
import type { Menu, MenuType, DisplayMode } from '../types/menu';

const menuFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name is too long'),
  menu_type: z.enum(['restaurant', 'laundry', 'spa', 'room_service', 'other']),
  description: z.string().optional(),
  is_active: z.boolean().default(true),
  show_prices: z.boolean().default(true),
  display_mode: z.enum(['grid', 'list', 'carousel']).default('grid'),
  theme_color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid color format').optional().or(z.literal('')),
  whatsapp_number: z.string().max(20).optional().or(z.literal('')),
  phone_number: z.string().max(20).optional().or(z.literal('')),
  contact_label: z.string().max(100).optional().or(z.literal('')),
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

  const {
    register,
    handleSubmit,
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
          theme_color: menu.theme_color || '',
          whatsapp_number: menu.whatsapp_number || '',
          phone_number: menu.phone_number || '',
          contact_label: menu.contact_label || '',
        }
      : {
          is_active: true,
          show_prices: true,
          display_mode: 'grid',
        },
  });

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
        theme_color: data.theme_color || undefined,
        whatsapp_number: data.whatsapp_number || undefined,
        phone_number: data.phone_number || undefined,
        contact_label: data.contact_label || undefined,
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

  // Footer with action buttons
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          disabled={isSubmitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          form="menu-form"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          disabled={isSubmitting}
        >
          {isSubmitting
            ? isEditMode
              ? 'Updating...'
              : 'Creating...'
            : isEditMode
            ? 'Update Menu'
            : 'Create Menu'}
        </button>
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

        {/* Display Settings */}
        <div className="space-y-4">
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
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Theme Color (Hex)
            </label>
            <div className="mt-1 flex items-center space-x-2">
              <input
                type="color"
                {...register('theme_color')}
                className="h-10 w-20 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              />
              <input
                type="text"
                {...register('theme_color')}
                className="flex-1 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
                placeholder="#FF5733"
              />
            </div>
            {errors.theme_color && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.theme_color.message}</p>
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
        <div className="space-y-4">
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
        </div>
      </form>
    </Modal>
  );
};
