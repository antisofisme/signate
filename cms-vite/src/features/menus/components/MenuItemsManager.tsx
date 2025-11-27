/**
 * Menu Items Manager Component
 * Manage items for a menu
 *
 * ✅ REFACTORED: Now uses shared Modal component for consistency
 */

import { useState } from 'react';
import { Upload, Trash2, Star } from 'lucide-react';
import { Modal } from '@/shared/components';
import { useMenuItems, useDeleteMenuItem } from '../hooks/useMenuItems';
import { ExcelImportModal } from './ExcelImportModal';
import type { Menu, MenuItem } from '../types/menu';

interface MenuItemsManagerProps {
  menu: Menu;
  onClose: () => void;
}

export const MenuItemsManager = ({ menu, onClose }: MenuItemsManagerProps) => {
  const [showImportModal, setShowImportModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 50;

  const { data, isLoading } = useMenuItems(menu.id, {
    skip: currentPage * pageSize,
    limit: pageSize,
  });
  const deleteMutation = useDeleteMenuItem(menu.id);

  const handleDelete = async (item: MenuItem) => {
    if (window.confirm(`Are you sure you want to delete "${item.name}"?`)) {
      deleteMutation.mutate(item.id);
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
          {menu.name} - Items
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {data?.total || 0} items total
        </p>
      </div>
      <div className="flex items-center space-x-3">
        <button
          onClick={() => setShowImportModal(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
        >
          <Upload className="w-4 h-4" />
          <span>Import Excel</span>
        </button>
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
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : data && data.items.length > 0 ? (
            <div className="space-y-4">
              {/* Items Table */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Item Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Category
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Price
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {data.items.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-start space-x-3">
                            {item.is_featured && (
                              <Star className="w-4 h-4 text-yellow-500 mt-1" />
                            )}
                            <div className="flex-1">
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {item.name}
                              </div>
                              {item.description && (
                                <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-md">
                                  {item.description}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {item.category && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                              {item.category}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {menu.show_prices
                            ? formatPrice(item.price, item.currency)
                            : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col space-y-1">
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                item.is_active
                                  ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                                  : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                              }`}
                            >
                              {item.is_active ? 'Active' : 'Inactive'}
                            </span>
                            {!item.is_available && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">
                                Unavailable
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              onClick={() => handleDelete(item)}
                              className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors"
                              title="Delete Item"
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
                    Showing {currentPage * pageSize + 1} to{' '}
                    {Math.min((currentPage + 1) * pageSize, data.total)} of {data.total}{' '}
                    results
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                      disabled={currentPage === 0}
                      className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage((p) => p + 1)}
                      disabled={!data.has_next}
                      className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <p className="text-gray-500 dark:text-gray-400 mb-4">No items yet</p>
              <button
                onClick={() => setShowImportModal(true)}
                className="inline-flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                <Upload className="w-4 h-4" />
                <span>Import from Excel</span>
              </button>
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
        onSuccess={() => setShowImportModal(false)}
      />
    </>
  );
};
