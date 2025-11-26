/**
 * Menu Items Manager Component
 * Manage items for a menu
 */

import { useState } from 'react';
import { X, Upload, Plus, Edit, Trash2, Star } from 'lucide-react';
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

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <div>
              <h2 className="text-xl font-semibold">{menu.name} - Items</h2>
              <p className="text-sm text-gray-500 mt-1">
                {data?.total || 0} items total
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowImportModal(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <Upload className="w-4 h-4" />
                <span>Import Excel</span>
              </button>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : data && data.items.length > 0 ? (
              <div className="space-y-4">
                {/* Items Table */}
                <div className="bg-white rounded-lg shadow overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Item Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Price
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {data.items.map((item) => (
                        <tr key={item.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4">
                            <div className="flex items-start space-x-3">
                              {item.is_featured && (
                                <Star className="w-4 h-4 text-yellow-500 mt-1" />
                              )}
                              <div className="flex-1">
                                <div className="text-sm font-medium text-gray-900">
                                  {item.name}
                                </div>
                                {item.description && (
                                  <div className="text-sm text-gray-500 truncate max-w-md">
                                    {item.description}
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {item.category && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {item.category}
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {menu.show_prices
                              ? formatPrice(item.price, item.currency)
                              : '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex flex-col space-y-1">
                              <span
                                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                  item.is_active
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}
                              >
                                {item.is_active ? 'Active' : 'Inactive'}
                              </span>
                              {!item.is_available && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                  Unavailable
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex items-center justify-end space-x-2">
                              <button
                                onClick={() => handleDelete(item)}
                                className="text-red-600 hover:text-red-900"
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
                  <div className="flex items-center justify-between px-4 py-3 bg-white rounded-lg shadow">
                    <div className="text-sm text-gray-700">
                      Showing {currentPage * pageSize + 1} to{' '}
                      {Math.min((currentPage + 1) * pageSize, data.total)} of {data.total}{' '}
                      results
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                        disabled={currentPage === 0}
                        className="px-3 py-1 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setCurrentPage((p) => p + 1)}
                        disabled={!data.has_next}
                        className="px-3 py-1 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 bg-gray-50 rounded-lg">
                <p className="text-gray-500 mb-4">No items yet</p>
                <button
                  onClick={() => setShowImportModal(true)}
                  className="inline-flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  <Upload className="w-4 h-4" />
                  <span>Import from Excel</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

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
