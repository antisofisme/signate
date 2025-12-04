/**
 * Menu Items Manager Component
 * Unified View/Edit mode for menu items management
 *
 * Features:
 * - View Mode: Read-only display with Edit per-item button
 * - Edit Mode: Inline editing for all items (bulk edit)
 * - 2-row layout per item matching the bulk edit design
 * - Add/Delete items in both modes
 * - Search, pagination, import/export
 */

import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Upload,
  Download,
  Plus,
  Loader2,
  Edit3,
  Eye,
  Search,
  X,
  RefreshCw,
  Image as ImageIcon,
  Check,
} from 'lucide-react';
import { toast } from '@/shared/utils/toast';
import { Modal, Button } from '@/shared/components';
import { cn } from '@/lib/utils';
import { useMenuItems, useDeleteMenuItem } from '../hooks/useMenuItems';
import { useMenuCategories } from '../hooks/useMenuCategories';
import { useDistinctVariants } from '../hooks/useDistinctVariants';
import { useMenuItemsEditor } from '../hooks/useMenuItemsEditor';
import { menuApi } from '../api/menuApi';
import { ExcelImportModal } from './ExcelImportModal';
import { MenuItemFormModal } from './MenuItemFormModal';
import { MenuItemTableRow } from './MenuItemTableRow';
import { toEditableItem } from '../types/menu';
import type { Menu, MenuItem, EditableItem, MenuMedia } from '../types/menu';

interface MenuItemsManagerProps {
  menu: Menu;
  onClose: () => void;
}

export const MenuItemsManager = ({ menu, onClose }: MenuItemsManagerProps) => {
  const { t } = useTranslation();

  // UI State
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [isEditMode, setIsEditMode] = useState(false);
  const pageSize = 50;

  // Data fetching
  const { data, isLoading, refetch } = useMenuItems(menu.id, {
    skip: currentPage * pageSize,
    limit: pageSize,
  });
  const { data: categories } = useMenuCategories(menu.id, true);
  const { data: variantSuggestions } = useDistinctVariants(menu.id, true);
  const deleteMutation = useDeleteMenuItem(menu.id);

  // Edit mode state management via custom hook
  const editor = useMenuItemsEditor({
    menuId: menu.id,
    items: data?.items || [],
    enabled: isEditMode,
  });

  // Sort and filter items alphabetically by name
  const sortedItems = useMemo(() => {
    if (!data?.items) return [];
    let items = [...data.items].sort((a, b) =>
      a.name.localeCompare(b.name, 'id', { sensitivity: 'base' })
    );

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      items = items.filter((item) =>
        item.name.toLowerCase().includes(query) ||
        (item.description || '').toLowerCase().includes(query) ||
        (item.category || '').toLowerCase().includes(query) ||
        (item.subcategory || '').toLowerCase().includes(query) ||
        (item.variant || '').toLowerCase().includes(query) ||
        (item.tags || '').toLowerCase().includes(query)
      );
    }

    return items;
  }, [data?.items, searchQuery]);

  // Filter editable items by search query
  const filteredEditableItems = useMemo(() => {
    if (!isEditMode) return [];
    if (!searchQuery.trim()) return editor.editableItems;

    const query = searchQuery.toLowerCase();
    return editor.editableItems.filter((item) =>
      item.name.toLowerCase().includes(query) ||
      item.description.toLowerCase().includes(query) ||
      item.category.toLowerCase().includes(query) ||
      item.subcategory.toLowerCase().includes(query) ||
      item.variant.toLowerCase().includes(query) ||
      item.tags.toLowerCase().includes(query)
    );
  }, [isEditMode, editor.editableItems, searchQuery]);

  // Display items based on mode
  const displayItems = isEditMode
    ? filteredEditableItems
    : sortedItems.map(toEditableItem);

  // Handle mode toggle
  const handleModeToggle = () => {
    if (isEditMode) {
      // Switching from Edit to View mode
      if (editor.modifiedCount > 0) {
        if (!window.confirm(t('menus.bulkEdit.confirmDiscard', 'You have unsaved changes. Discard them?'))) {
          return;
        }
      }
      setIsEditMode(false);
      editor.resetChanges();
    } else {
      // Switching from View to Edit mode
      setIsEditMode(true);
    }
  };

  // Handle delete (works in both modes)
  const handleDelete = async (itemId: number) => {
    const item = isEditMode
      ? editor.editableItems.find((i) => i.id === itemId)
      : sortedItems.find((i) => i.id === itemId);

    if (!item) return;

    if (window.confirm(t('menus.items.confirmDelete', `Are you sure you want to delete "${item.name}"?`))) {
      try {
        await deleteMutation.mutateAsync(itemId);
        if (isEditMode) {
          editor.resetChanges();
        }
      } catch {
        // Error handled by mutation
      }
    }
  };

  // Handle edit item (View mode - opens popup)
  const handleEditItem = (item: EditableItem) => {
    // Convert EditableItem back to MenuItem for the form modal
    const menuItem: MenuItem = {
      id: item.id,
      menu_id: item.menu_id,
      organization_id: item.organization_id,
      name: item.name,
      description: item.description || undefined,
      price: item.price ?? undefined,
      currency: item.currency,
      image_url: item.image_url || undefined,
      video_url: item.video_url,
      content_id: item.content_id,
      category: item.category || undefined,
      subcategory: item.subcategory || undefined,
      variant: item.variant || undefined,
      tags: item.tags || undefined,
      display_order: item.display_order,
      is_active: item.is_active,
      is_featured: item.is_featured,
      is_available: item.is_available,
      created_at: '',
    };
    setEditingItem(menuItem);
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const blob = await menuApi.exportMenu(menu.id);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${menu.name.replace(/[^a-z0-9]/gi, '_')}_menu.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success(t('menus.items.exportSuccess', 'Menu exported successfully'));
    } catch (error) {
      toast.error(t('menus.items.exportError', 'Failed to export menu'));
    } finally {
      setIsExporting(false);
    }
  };

  const formatPrice = (price?: number | null, currency: string = 'IDR') => {
    if (price === null || price === undefined) return '-';
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
    }).format(price);
  };

  // Handle save all (Edit mode)
  const handleSaveAll = async () => {
    await editor.handleSaveAll();
    // Refetch data after save
    await refetch();
  };

  // Custom header with actions and search
  const customHeader = (
    <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      {/* Top row: Title and close button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {menu.name}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t('menus.items.itemsTotal', { count: data?.total || 0, defaultValue: '{{count}} items' })}
            {searchQuery && displayItems.length !== (isEditMode ? editor.editableItems.length : data?.items?.length || 0) && (
              <span className="ml-2 text-blue-600 dark:text-blue-400">
                ({displayItems.length} {t('common.filtered', 'filtered')})
              </span>
            )}
            {isEditMode && editor.isLoadingItemMedia && (
              <span className="ml-2 inline-flex items-center gap-1 text-blue-600">
                <Loader2 className="w-3 h-3 animate-spin" />
                Loading images...
              </span>
            )}
          </p>
        </div>
        {/* Close Button */}
        <button
          onClick={onClose}
          className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-500 dark:text-gray-400 transition-colors"
          aria-label="Close modal"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Toolbar row: Search + Buttons */}
      {data && data.items.length > 0 && (
        <div className="mt-4 flex items-center justify-between gap-4">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 w-4 h-4" />
            <input
              type="text"
              placeholder={t('menus.items.searchItems', 'Search items...')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-8 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-blue-500 focus:border-blue-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            {/* View/Edit Mode Toggle */}
            <Button
              variant={isEditMode ? 'primary' : 'outline'}
              size="sm"
              onClick={handleModeToggle}
              leftIcon={isEditMode ? <Eye className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
            >
              {isEditMode ? t('menus.items.viewMode', 'View Mode') : t('menus.items.editMode', 'Edit Mode')}
            </Button>

            {/* Add Item Button - only in View mode */}
            {!isEditMode && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowAddModal(true)}
                leftIcon={<Plus className="w-4 h-4" />}
              >
                {t('menus.items.addItem', 'Add Item')}
              </Button>
            )}

            {/* Import Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowImportModal(true)}
              leftIcon={<Upload className="w-4 h-4" />}
            >
              {t('menus.items.import', 'Import')}
            </Button>

            {/* Export Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              loading={isExporting}
              leftIcon={<Download className="w-4 h-4" />}
              disabled={!data?.items.length}
            >
              {t('menus.items.export', 'Export')}
            </Button>
          </div>
        </div>
      )}
    </div>
  );

  // Footer - always visible to maintain consistent height
  const modalFooter = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between bg-gray-50 dark:bg-gray-900">
      {isEditMode ? (
        <>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {editor.modifiedCount > 0 ? (
                <span className="text-amber-600 dark:text-amber-400 font-medium">
                  {editor.modifiedCount} {t('menus.bulkEdit.itemsModified', 'items modified')}
                </span>
              ) : (
                t('menus.bulkEdit.noChanges', 'No changes')
              )}
            </span>
            {editor.failedCount > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={editor.handleRetryFailed}
                disabled={editor.isSaving}
                leftIcon={<RefreshCw className="w-3 h-3" />}
              >
                Retry {editor.failedCount} failed
              </Button>
            )}
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={handleModeToggle}
              disabled={editor.isSaving}
            >
              {t('common.cancel', 'Cancel')}
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveAll}
              disabled={editor.modifiedCount === 0 || editor.isSaving}
              loading={editor.isSaving}
            >
              {editor.isSaving
                ? t('menus.bulkEdit.saving', 'Saving...')
                : t('menus.bulkEdit.saveAll', 'Save All Changes')}
            </Button>
          </div>
        </>
      ) : (
        <>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {t('menus.items.viewModeHint', 'Click Edit Mode to make changes')}
          </span>
          <Button variant="outline" onClick={onClose}>
            {t('common.close', 'Close')}
          </Button>
        </>
      )}
    </div>
  );

  return (
    <>
      <Modal
        isOpen={true}
        onClose={onClose}
        maxWidth="6xl"
        showHeader={false}
        customHeader={customHeader}
        footer={modalFooter}
        closeOnBackdropClick={!isEditMode || editor.modifiedCount === 0}
      >
        {/* Content area - Modal handles scrolling */}
        <div className="p-6 min-h-[calc(100vh-320px)]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : searchQuery && displayItems.length === 0 && (data?.items.length || 0) > 0 ? (
            // No search results but has items
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                {t('menus.items.noSearchResults', 'No items match your search')}
              </p>
              <Button variant="outline" onClick={() => setSearchQuery('')}>
                {t('common.clearSearch', 'Clear search')}
              </Button>
            </div>
          ) : displayItems.length > 0 ? (
            <div className="space-y-4">
              {/* Items Table with 2-row layout */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-16">
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
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-32">
                        {t('menus.bulkEdit.subcategory', 'Subcategory')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {displayItems.map((item) => (
                      <MenuItemTableRow
                        key={item.id}
                        item={item}
                        mode={isEditMode ? 'edit' : 'view'}
                        categories={categories?.items || []}
                        variantSuggestions={variantSuggestions || []}
                        formatPrice={formatPrice}
                        onEditItem={handleEditItem}
                        onDeleteItem={handleDelete}
                        onUpdateField={editor.updateField}
                        onImageClick={editor.setSelectedItemIdForMedia}
                        onRemoveNew={editor.removeNewItem}
                        disabled={editor.isSaving}
                        canDelete={true}
                      />
                    ))}
                  </tbody>
                </table>

                {/* Add New Item Button - Edit mode only, inside table container */}
                {isEditMode && (
                  <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                    <Button
                      variant="outline"
                      onClick={editor.addNewItem}
                      disabled={editor.isSaving}
                      leftIcon={<Plus className="w-4 h-4" />}
                      className="w-full border-dashed"
                    >
                      {t('menus.bulkEdit.addNewItem', 'Add New Item')}
                    </Button>
                  </div>
                )}
              </div>

              {/* Pagination - View mode only */}
              {!isEditMode && data && data.total > pageSize && (
                <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    {t('common.showing', 'Showing')} {currentPage * pageSize + 1} - {Math.min((currentPage + 1) * pageSize, data.total)} {t('common.of', 'of')} {data.total}
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                      disabled={currentPage === 0}
                    >
                      {t('common.previous', 'Previous')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => p + 1)}
                      disabled={!data.has_next}
                    >
                      {t('common.next', 'Next')}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <ImageIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                {t('menus.items.noItems', 'No menu items yet')}
              </p>
              <div className="flex items-center justify-center space-x-3">
                <Button
                  variant="primary"
                  onClick={() => setShowAddModal(true)}
                  leftIcon={<Plus className="w-4 h-4" />}
                >
                  {t('menus.items.addItem', 'Add Item')}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowImportModal(true)}
                  leftIcon={<Upload className="w-4 h-4" />}
                >
                  {t('menus.items.importExcel', 'Import Excel')}
                </Button>
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* Import Modal */}
      <ExcelImportModal
        isOpen={showImportModal}
        menuId={menu.id}
        menuName={menu.name}
        onClose={() => setShowImportModal(false)}
        onSuccess={() => {
          setShowImportModal(false);
          refetch();
        }}
      />

      {/* Add Item Modal - View mode */}
      <MenuItemFormModal
        isOpen={showAddModal}
        menuId={menu.id}
        item={null}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          setShowAddModal(false);
          refetch();
        }}
      />

      {/* Edit Item Modal - View mode */}
      {editingItem && (
        <MenuItemFormModal
          isOpen={true}
          menuId={menu.id}
          item={editingItem}
          onClose={() => setEditingItem(null)}
          onSuccess={() => {
            setEditingItem(null);
            refetch();
          }}
        />
      )}

      {/* Media Picker Modal - Edit mode */}
      <Modal
        isOpen={editor.selectedItemIdForMedia !== null}
        onClose={editor.closeMediaPicker}
        maxWidth="lg"
        title={t('menus.bulkEdit.selectImages', 'Select Images')}
      >
        <div className="p-4">
          {/* Current Item Info with selection count */}
          {editor.selectedItemForMedia && (
            <div className="flex items-center gap-4 mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex gap-1">
                {/* Show up to 3 thumbnails */}
                {editor.selectedItemForMedia.media_ids.slice(0, 3).map((mediaId, idx) => {
                  const media = editor.mediaData?.items.find((m) => m.id === mediaId);
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
                {editor.selectedItemForMedia.media_ids.length === 0 && (
                  <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center">
                    <ImageIcon className="w-4 h-4 text-gray-400" />
                  </div>
                )}
                {editor.selectedItemForMedia.media_ids.length > 3 && (
                  <div className="w-10 h-10 bg-gray-300 dark:bg-gray-600 rounded flex items-center justify-center text-xs font-medium" style={{ marginLeft: '-8px' }}>
                    +{editor.selectedItemForMedia.media_ids.length - 3}
                  </div>
                )}
              </div>
              <div className="flex-1">
                <div className="font-medium text-gray-900 dark:text-white">
                  {editor.selectedItemForMedia.name || t('menus.bulkEdit.newItem', 'New Item')}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {editor.selectedItemForMedia.media_ids.length > 0
                    ? t('menus.bulkEdit.selectedCount', { count: editor.selectedItemForMedia.media_ids.length, defaultValue: '{{count}} image(s) selected' })
                    : t('menus.bulkEdit.selectMultipleImages', 'Click images to select (multi-select)')}
                </div>
              </div>
              {editor.selectedItemForMedia.media_ids.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={editor.handleRemoveAllImages}
                  className="text-red-600 hover:text-red-700"
                >
                  {t('menus.bulkEdit.clearAll', 'Clear All')}
                </Button>
              )}
            </div>
          )}

          {/* Media Grid - Multi-Select with Checkboxes */}
          {editor.isLoadingMedia ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            </div>
          ) : editor.mediaData && editor.mediaData.items.length > 0 ? (
            <div className="grid grid-cols-5 sm:grid-cols-6 md:grid-cols-8 gap-2 max-h-80 overflow-y-auto">
              {editor.mediaData.items.map((media) => {
                const isSelected = editor.selectedItemForMedia?.media_ids.includes(media.id) ?? false;
                const selectionIndex = editor.selectedItemForMedia?.media_ids.indexOf(media.id) ?? -1;
                return (
                  <button
                    key={media.id}
                    type="button"
                    onClick={() => editor.handleToggleMedia(media)}
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
              {editor.selectedItemForMedia?.media_ids.length
                ? t('menus.bulkEdit.firstImagePrimary', 'First selected image will be the primary thumbnail')
                : ''}
            </div>
            <Button variant="primary" onClick={editor.closeMediaPicker}>
              {t('common.done', 'Done')}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};
