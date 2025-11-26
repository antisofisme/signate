/**
 * Menu List Component
 * Displays all menus in a table with actions
 */

import { useState } from 'react';
import { Edit, Trash2, List, QrCode, Copy, Download, ExternalLink } from 'lucide-react';
import { useMenus, useDeleteMenu } from '../hooks/useMenus';
import { useDownloadQRCode } from '../hooks/useMenuImport';
import type { Menu, MenuType } from '../types/menu';
import { toast } from 'sonner';

interface MenuListProps {
  onEdit: (menu: Menu) => void;
  onManageItems: (menu: Menu) => void;
  searchQuery?: string;
  menuTypeFilter?: MenuType | '';
  isActiveFilter?: boolean | '';
}

export const MenuList = ({
  onEdit,
  onManageItems,
  searchQuery = '',
  menuTypeFilter = '',
  isActiveFilter = '',
}: MenuListProps) => {
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 20;

  // Fetch menus
  const { data, isLoading, error } = useMenus({
    skip: currentPage * pageSize,
    limit: pageSize,
    menu_type: menuTypeFilter || undefined,
    is_active: isActiveFilter === '' ? undefined : isActiveFilter,
  });

  const deleteMutation = useDeleteMenu();
  const downloadQRMutation = useDownloadQRCode();

  // Client-side search filter
  const filteredMenus = data?.items.filter((menu) =>
    menu.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const handleDelete = async (menu: Menu) => {
    if (window.confirm(`Are you sure you want to delete menu "${menu.name}"?`)) {
      deleteMutation.mutate(menu.id);
    }
  };

  const handleCopyPublicUrl = (menu: Menu) => {
    if (menu.public_url) {
      navigator.clipboard.writeText(menu.public_url);
      toast.success('Public URL copied to clipboard');
    }
  };

  const handleDownloadQR = (menu: Menu) => {
    downloadQRMutation.mutate({
      menuId: menu.id,
      menuName: menu.name,
    });
  };

  const handleOpenPublicUrl = (menu: Menu) => {
    if (menu.public_url) {
      window.open(menu.public_url, '_blank');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
        Failed to load menus. Please try again.
      </div>
    );
  }

  if (!filteredMenus.length) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No menus found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Menu Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Items
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Public Access
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredMenus.map((menu) => (
              <tr key={menu.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{menu.name}</div>
                    {menu.description && (
                      <div className="text-sm text-gray-500 truncate max-w-xs">
                        {menu.description}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 capitalize">
                    {menu.menu_type.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {menu.items_count} items
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      menu.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {menu.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleCopyPublicUrl(menu)}
                      className="text-gray-400 hover:text-gray-600"
                      title="Copy Public URL"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleOpenPublicUrl(menu)}
                      className="text-gray-400 hover:text-gray-600"
                      title="Open Public URL"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                    {menu.qr_code_url && (
                      <button
                        onClick={() => handleDownloadQR(menu)}
                        className="text-gray-400 hover:text-gray-600"
                        title="Download QR Code"
                        disabled={downloadQRMutation.isPending}
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center justify-end space-x-2">
                    <button
                      onClick={() => onEdit(menu)}
                      className="text-blue-600 hover:text-blue-900"
                      title="Edit Menu"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onManageItems(menu)}
                      className="text-green-600 hover:text-green-900"
                      title="Manage Items"
                    >
                      <List className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(menu)}
                      className="text-red-600 hover:text-red-900"
                      title="Delete Menu"
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
      {data && data.total > pageSize && (
        <div className="flex items-center justify-between px-4 py-3 bg-white rounded-lg shadow">
          <div className="text-sm text-gray-700">
            Showing {currentPage * pageSize + 1} to{' '}
            {Math.min((currentPage + 1) * pageSize, data.total)} of {data.total} results
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
              disabled={(currentPage + 1) * pageSize >= data.total}
              className="px-3 py-1 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
