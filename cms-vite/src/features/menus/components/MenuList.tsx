/**
 * Menu List Component
 * Displays all menus in a table with actions
 */

import { useState } from 'react';
import { Edit, Trash2, List, QrCode, Copy, Download, ExternalLink, UtensilsCrossed } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useMenus, useDeleteMenu } from '../hooks/useMenus';
import { useDownloadQRCode } from '../hooks/useMenuImport';
import { EmptyState } from '@/shared/components';
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
  const { t } = useTranslation();
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
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-800 dark:text-red-300">
        Failed to load menus. Please try again.
      </div>
    );
  }

  if (!filteredMenus.length) {
    return (
      <EmptyState
        icon={UtensilsCrossed}
        title={t('menus.empty.title', 'No menus found')}
        description={t('menus.empty.description', 'Create your first digital menu to get started')}
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Menu Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Items
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Public Access
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {filteredMenus.map((menu) => (
              <tr key={menu.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">{menu.name}</div>
                    {menu.description && (
                      <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">
                        {menu.description}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 capitalize">
                    {menu.menu_type.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {menu.items_count} items
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      menu.is_active
                        ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                    }`}
                  >
                    {menu.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleCopyPublicUrl(menu)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                      title="Copy Public URL"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleOpenPublicUrl(menu)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                      title="Open Public URL"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                    {menu.qr_code_url && (
                      <button
                        onClick={() => handleDownloadQR(menu)}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
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
                      className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
                      title="Edit Menu"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onManageItems(menu)}
                      className="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300 transition-colors"
                      title="Manage Items"
                    >
                      <List className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(menu)}
                      className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors"
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
        <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            Showing {currentPage * pageSize + 1} to{' '}
            {Math.min((currentPage + 1) * pageSize, data.total)} of {data.total} results
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
              disabled={(currentPage + 1) * pageSize >= data.total}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
