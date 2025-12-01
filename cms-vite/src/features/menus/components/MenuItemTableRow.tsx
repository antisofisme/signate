/**
 * Menu Item Table Row Component
 * 2-row layout for each menu item with View/Edit mode support
 *
 * Row 1: Active, Image, Name, Description, Price, Category, Subcategory
 * Row 2: Variant, Tags, Highlight, Available, Actions
 */

import { useTranslation } from 'react-i18next';
import {
  Loader2,
  Trash2,
  Image as ImageIcon,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  PackageCheck,
  PackageX,
  Camera,
  X,
  Pencil,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { VariantAutocomplete } from './VariantAutocomplete';
import { TagsInput } from './TagsInput';
import type { EditableItem, MenuCategory } from '../types/menu';

export type ViewMode = 'view' | 'edit';

interface MenuItemTableRowProps {
  item: EditableItem;
  mode: ViewMode;
  categories: MenuCategory[];
  variantSuggestions: string[];
  formatPrice: (price?: number | null, currency?: string) => string;
  // View mode actions
  onEditItem?: (item: EditableItem) => void;
  onDeleteItem?: (itemId: number) => void;
  // Edit mode actions
  onUpdateField?: (itemId: number, field: keyof EditableItem, value: any) => void;
  onImageClick?: (itemId: number) => void;
  onRemoveNew?: (itemId: number) => void;
  disabled?: boolean;
  canDelete?: boolean;
}

// Toggle Switch Component
const ToggleSwitch = ({
  checked,
  onChange,
  disabled: isDisabled,
}: {
  checked: boolean;
  onChange: (val: boolean) => void;
  disabled?: boolean;
}) => (
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

export const MenuItemTableRow = ({
  item,
  mode,
  categories,
  variantSuggestions,
  formatPrice,
  onEditItem,
  onDeleteItem,
  onUpdateField,
  onImageClick,
  onRemoveNew,
  disabled = false,
  canDelete = true,
}: MenuItemTableRowProps) => {
  const { t } = useTranslation();
  const isEditMode = mode === 'edit';

  // Row styling based on status
  const rowClasses = cn(
    'transition-all duration-200',
    item.hasChanges && item.status === 'idle' && 'bg-yellow-50 dark:bg-yellow-900/20',
    item.status === 'saving' && 'opacity-50',
    item.status === 'success' && 'bg-green-50 dark:bg-green-900/20',
    item.status === 'error' && 'bg-red-50 dark:bg-red-900/20'
  );

  const borderClasses = cn(
    item.hasChanges && 'border-l-4 border-l-yellow-500',
    item.status === 'success' && 'border-l-4 border-l-green-500',
    item.status === 'error' && 'border-l-4 border-l-red-500'
  );

  // Get subcategories for selected category
  const selectedCategory = categories.find((cat) => cat.name === item.category);
  const subcategories = selectedCategory?.subcategories || [];

  return (
    <>
      {/* Row 1: Active, Image, Name, Description, Price, Category, Subcategory */}
      <tr className={cn(rowClasses, borderClasses, 'border-b-2 border-gray-400 dark:border-gray-500')}>
        {/* Active Toggle/Badge - rowSpan=2 */}
        <td rowSpan={2} className="px-2 pt-3 py-1 align-middle text-center">
          <div className="flex flex-col items-center gap-1">
            {isEditMode ? (
              <ToggleSwitch
                checked={item.is_active}
                onChange={(val) => onUpdateField?.(item.id, 'is_active', val)}
                disabled={disabled}
              />
            ) : (
              <span
                className={cn(
                  'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                  item.is_active
                    ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                )}
              >
                {item.is_active ? 'Active' : 'Inactive'}
              </span>
            )}
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

        {/* Image - rowSpan=2 */}
        <td rowSpan={2} className="pr-3 pt-3 py-1 align-middle">
          <button
            type="button"
            onClick={() => isEditMode && !disabled && onImageClick?.(item.id)}
            disabled={disabled || !isEditMode}
            className={cn(
              'w-14 h-14 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden flex items-center justify-center relative group',
              isEditMode && !disabled && 'hover:ring-2 hover:ring-blue-500 cursor-pointer',
              (disabled || !isEditMode) && 'cursor-default'
            )}
            title={isEditMode ? t('menus.bulkEdit.changeImage', 'Click to change image') : ''}
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
            {/* Hover overlay for edit mode */}
            {isEditMode && !disabled && (
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                <Camera className="w-5 h-5 text-white" />
              </div>
            )}
          </button>
        </td>

        {/* Name */}
        <td className="pr-3 pt-3 pb-1 border-b-2 border-gray-300 dark:border-gray-600">
          {isEditMode ? (
            <input
              type="text"
              value={item.name}
              onChange={(e) => onUpdateField?.(item.id, 'name', e.target.value)}
              disabled={disabled}
              className={cn(
                'w-full h-[32px] px-2 py-1 border rounded-md text-sm font-medium',
                'bg-white dark:bg-gray-900 text-gray-900 dark:text-white',
                'border-gray-300 dark:border-gray-600',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                disabled && 'opacity-60 cursor-not-allowed'
              )}
              placeholder={t('menus.bulkEdit.namePlaceholder', 'Item name')}
            />
          ) : (
            <div className="font-medium text-sm text-gray-900 dark:text-white truncate max-w-[160px]">
              {item.name || '-'}
            </div>
          )}
        </td>

        {/* Description */}
        <td className="pr-3 pt-3 pb-1 border-b-2 border-gray-300 dark:border-gray-600">
          {isEditMode ? (
            <input
              type="text"
              value={item.description}
              onChange={(e) => onUpdateField?.(item.id, 'description', e.target.value)}
              disabled={disabled}
              className={cn(
                'w-full h-[32px] px-2 py-1 border rounded-md text-sm',
                'bg-white dark:bg-gray-900 text-gray-900 dark:text-white',
                'border-gray-300 dark:border-gray-600',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                disabled && 'opacity-60 cursor-not-allowed'
              )}
              placeholder={t('menus.bulkEdit.descriptionPlaceholder', 'Description (optional)')}
            />
          ) : (
            <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">
              {item.description || '-'}
            </div>
          )}
        </td>

        {/* Price */}
        <td className="pr-3 pt-3 pb-1 border-b-2 border-gray-300 dark:border-gray-600">
          {isEditMode ? (
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={item.price !== null ? String(Math.floor(item.price)) : ''}
              onChange={(e) => {
                const value = e.target.value.replace(/[^0-9]/g, '');
                onUpdateField?.(item.id, 'price', value ? parseInt(value, 10) : null);
              }}
              onKeyDown={(e) => {
                if (e.key === '.' || e.key === ',' || e.key === '-' || e.key === '+' || e.key === 'e' || e.key === 'E') {
                  e.preventDefault();
                }
              }}
              disabled={disabled}
              className={cn(
                'w-full h-[32px] px-2 py-1 border rounded-md text-sm',
                'bg-white dark:bg-gray-900 text-gray-900 dark:text-white',
                'border-gray-300 dark:border-gray-600',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                disabled && 'opacity-60 cursor-not-allowed'
              )}
              placeholder="0"
            />
          ) : (
            <span className="text-sm text-gray-900 dark:text-white whitespace-nowrap">
              {formatPrice(item.price, item.currency)}
            </span>
          )}
        </td>

        {/* Category */}
        <td className="pr-3 pt-3 pb-1 border-b-2 border-gray-300 dark:border-gray-600">
          {isEditMode ? (
            <select
              value={item.category}
              onChange={(e) => {
                onUpdateField?.(item.id, 'category', e.target.value);
                // Clear subcategory when category changes
                if (e.target.value !== item.category) {
                  onUpdateField?.(item.id, 'subcategory', '');
                }
              }}
              disabled={disabled}
              className={cn(
                'w-full h-[32px] px-2 py-1 border rounded-md text-sm',
                'bg-white dark:bg-gray-900 text-gray-900 dark:text-white',
                'border-gray-300 dark:border-gray-600',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
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
          ) : (
            item.category ? (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                {item.category}
              </span>
            ) : (
              <span className="text-gray-400">-</span>
            )
          )}
        </td>

        {/* Subcategory */}
        <td className="pr-3 pt-3 pb-1 border-b-2 border-gray-300 dark:border-gray-600">
          {isEditMode ? (
            !item.category || subcategories.length === 0 ? (
              <span className="text-xs text-gray-400 dark:text-gray-500">-</span>
            ) : (
              <select
                value={item.subcategory}
                onChange={(e) => onUpdateField?.(item.id, 'subcategory', e.target.value)}
                disabled={disabled}
                className={cn(
                  'w-full h-[32px] px-2 py-1 border rounded-md text-sm',
                  'bg-white dark:bg-gray-900 text-gray-900 dark:text-white',
                  'border-gray-300 dark:border-gray-600',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                  disabled && 'opacity-60 cursor-not-allowed'
                )}
              >
                <option value="">-- Select --</option>
                {subcategories.map((sub) => (
                  <option key={sub} value={sub}>
                    {sub}
                  </option>
                ))}
              </select>
            )
          ) : (
            item.subcategory ? (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-100 dark:bg-cyan-900 text-cyan-800 dark:text-cyan-200">
                {item.subcategory}
              </span>
            ) : (
              <span className="text-gray-400">-</span>
            )
          )}
        </td>
      </tr>

      {/* Row 2: Variant, Tags, Highlight, Available, Actions */}
      <tr className={cn(rowClasses, 'border-b border-gray-200 dark:border-gray-700')}>
        <td colSpan={5} className="pr-3 pt-1 pb-3">
          <div className="flex items-center gap-3">
            {/* Variant */}
            <div className="flex-1">
              {isEditMode ? (
                <VariantAutocomplete
                  value={item.variant}
                  suggestions={variantSuggestions}
                  onChange={(val) => onUpdateField?.(item.id, 'variant', val)}
                  disabled={disabled}
                  placeholder={t('menus.bulkEdit.variantPlaceholder', 'Variants (e.g. Hot, Cold)...')}
                />
              ) : (
                <div className="flex flex-wrap gap-1">
                  {item.variant ? (
                    item.variant.split(',').map((v, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200"
                      >
                        {v.trim()}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-gray-400">-</span>
                  )}
                </div>
              )}
            </div>

            {/* Tags */}
            <div className="flex-1">
              {isEditMode ? (
                <TagsInput
                  value={item.tags}
                  onChange={(val) => onUpdateField?.(item.id, 'tags', val)}
                  disabled={disabled}
                  placeholder={t('menus.bulkEdit.tagsPlaceholder', 'Add tags...')}
                />
              ) : (
                <div className="flex flex-wrap gap-1">
                  {item.tags ? (
                    item.tags.split(',').map((tag, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200"
                      >
                        {tag.trim()}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-gray-400">-</span>
                  )}
                </div>
              )}
            </div>

            {/* Highlight (Featured) */}
            {isEditMode ? (
              <label className="flex items-center gap-1.5 cursor-pointer" title="Highlight">
                <input
                  type="checkbox"
                  checked={item.is_featured}
                  onChange={(e) => onUpdateField?.(item.id, 'is_featured', e.target.checked)}
                  disabled={disabled}
                  className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-blue-500 disabled:opacity-60"
                />
                <Sparkles className={cn('w-4 h-4', item.is_featured ? 'text-amber-500' : 'text-gray-400')} />
                <span className="text-xs text-gray-600 dark:text-gray-400">
                  {t('menus.bulkEdit.highlight', 'Highlight')}
                </span>
              </label>
            ) : (
              <div className="flex items-center gap-1">
                <Sparkles className={cn('w-4 h-4', item.is_featured ? 'text-amber-500 fill-amber-500' : 'text-gray-400')} />
                <span className={cn(
                  'text-xs',
                  item.is_featured ? 'text-amber-600 dark:text-amber-400' : 'text-gray-500 dark:text-gray-400'
                )}>
                  {item.is_featured ? 'Highlight' : 'No-Highlight'}
                </span>
              </div>
            )}

            {/* Available */}
            {isEditMode ? (
              <label className="flex items-center gap-1.5 cursor-pointer" title="Available">
                <input
                  type="checkbox"
                  checked={item.is_available}
                  onChange={(e) => onUpdateField?.(item.id, 'is_available', e.target.checked)}
                  disabled={disabled}
                  className="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-blue-500 disabled:opacity-60"
                />
                {item.is_available ? (
                  <PackageCheck className="w-4 h-4 text-green-600" />
                ) : (
                  <PackageX className="w-4 h-4 text-gray-400" />
                )}
                <span className="text-xs text-gray-600 dark:text-gray-400">
                  {t('menus.bulkEdit.available', 'Avail')}
                </span>
              </label>
            ) : (
              <div className="flex items-center gap-1">
                {item.is_available ? (
                  <PackageCheck className="w-4 h-4 text-green-600" />
                ) : (
                  <PackageX className="w-4 h-4 text-red-500" />
                )}
                <span className={cn(
                  'text-xs',
                  item.is_available ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                )}>
                  {item.is_available ? 'Available' : 'Unavailable'}
                </span>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-1">
              {/* Edit button (View mode only) */}
              {!isEditMode && onEditItem && (
                <button
                  onClick={() => onEditItem(item)}
                  className="p-1.5 rounded text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
                  title={t('common.edit', 'Edit')}
                >
                  <Pencil className="w-4 h-4" />
                </button>
              )}

              {/* Delete/Remove button */}
              {item.isNew ? (
                // Remove button for new unsaved items
                <button
                  onClick={() => onRemoveNew?.(item.id)}
                  disabled={disabled}
                  className={cn(
                    'p-1.5 rounded text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors',
                    disabled && 'opacity-60 cursor-not-allowed'
                  )}
                  title={t('common.remove', 'Remove')}
                >
                  <X className="w-4 h-4" />
                </button>
              ) : (
                canDelete && onDeleteItem && (
                  <button
                    onClick={() => onDeleteItem(item.id)}
                    disabled={disabled}
                    className={cn(
                      'p-1.5 rounded text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors',
                      disabled && 'opacity-60 cursor-not-allowed'
                    )}
                    title={t('common.delete', 'Delete')}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )
              )}
            </div>
          </div>
        </td>
      </tr>
    </>
  );
};
