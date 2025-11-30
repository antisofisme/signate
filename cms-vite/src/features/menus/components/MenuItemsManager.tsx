/**
 * Menu Items Manager Component
 * Manage items for a menu - Add, Edit, Delete, Import, Export
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, Download, Trash2, Star, Pencil, Image as ImageIcon, Plus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Modal, Button } from '@/shared/components';
import { useMenuItems, useDeleteMenuItem } from '../hooks/useMenuItems';
import { menuApi } from '../api/menuApi';
import { ExcelImportModal } from './ExcelImportModal';
import { MenuItemFormModal } from './MenuItemFormModal';
import type { Menu, MenuItem } from '../types/menu';

interface MenuItemsManagerProps {
  menu: Menu;
  onClose: () => void;
}

export const MenuItemsManager = ({ menu, onClose }: MenuItemsManagerProps) => {
  const { t } = useTranslation();
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 50;

  const { data, isLoading, refetch } = useMenuItems(menu.id, {
    skip: currentPage * pageSize,
    limit: pageSize,
  });
  const deleteMutation = useDeleteMenuItem(menu.id);

  const handleDelete = async (item: MenuItem) => {
    if (window.confirm(t('menus.items.confirmDelete', `Are you sure you want to delete "${item.name}"?`))) {
      deleteMutation.mutate(item.id);
    }
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

  const formatPrice = (price?: number, currency: string = 'IDR') => {
    if (!price) return '-';
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
    }).format(price);
  };

  // Custom header with actions
  const customHeader = (
    <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          {menu.name}
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {data?.total || 0} {t('menus.items.itemsTotal', 'items')}
        </p>
      </div>
      <div className="flex items-center space-x-2">
        {/* Add Item Button */}
        <Button
          variant="primary"
          size="sm"
          onClick={() => setShowAddModal(true)}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          {t('menus.items.addItem', 'Add Item')}
        </Button>

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

        {/* Close Button */}
        <button
          onClick={onClose}
          className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-500 dark:text-gray-400 transition-colors ml-2"
          aria-label="Close modal"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
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
      >
        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : data && data.items.length > 0 ? (
            <div className="space-y-4">
              {/* Items Table */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-16">
                        {t('menus.items.image', 'Image')}
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {t('menus.items.name', 'Name')}
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {t('menus.items.category', 'Category')}
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {t('menus.items.price', 'Price')}
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {t('menus.items.status', 'Status')}
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {t('menus.items.actions', 'Actions')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {data.items.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                        {/* Image Column */}
                        <td className="px-4 py-3">
                          <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden flex items-center justify-center">
                            {item.image_url ? (
                              <img
                                src={item.image_url}
                                alt={item.name}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <ImageIcon className="w-5 h-5 text-gray-400" />
                            )}
                          </div>
                        </td>
                        {/* Name Column */}
                        <td className="px-4 py-3">
                          <div className="flex items-start space-x-2">
                            {item.is_featured && (
                              <Star className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0 fill-yellow-500" />
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {item.name}
                              </div>
                              {item.description && (
                                <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">
                                  {item.description}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        {/* Category Column */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          {item.category ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                              {item.category}
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        {/* Price Column */}
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {menu.show_prices
                            ? formatPrice(item.price, item.currency)
                            : '-'}
                        </td>
                        {/* Status Column */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex flex-col space-y-1">
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                item.is_active
                                  ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                                  : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                              }`}
                            >
                              {item.is_active ? t('common.active', 'Active') : t('common.inactive', 'Inactive')}
                            </span>
                            {!item.is_available && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">
                                {t('menus.items.unavailable', 'Unavailable')}
                              </span>
                            )}
                          </div>
                        </td>
                        {/* Actions Column */}
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end space-x-1">
                            <button
                              onClick={() => setEditingItem(item)}
                              className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors p-2 rounded hover:bg-blue-50 dark:hover:bg-blue-900/30"
                              title={t('common.edit', 'Edit')}
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(item)}
                              className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors p-2 rounded hover:bg-red-50 dark:hover:bg-red-900/30"
                              title={t('common.delete', 'Delete')}
                              disabled={deleteMutation.isPending}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {data.total > pageSize && (
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

      {/* Add Item Modal */}
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

      {/* Edit Item Modal */}
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
    </>
  );
};
