/**
 * Menu List Component
 * Displays all menus in a table with actions
 */

import { useState, useMemo } from 'react';
import { Edit, Trash2, List, Copy, Download, ExternalLink, UtensilsCrossed, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import QRCode from 'qrcode';
import { useMenus, useDeleteMenuWithPIN } from '../hooks/useMenus';
import { EmptyState, TABLE_STYLES } from '@/shared/components';
import { PinVerificationModal } from './PinVerificationModal';
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
  const [menuToDelete, setMenuToDelete] = useState<Menu | null>(null);
  const [showPinModal, setShowPinModal] = useState(false);
  const [downloadingQRMenuId, setDownloadingQRMenuId] = useState<number | null>(null);
  const pageSize = 20;

  // Fetch menus
  const { data, isLoading, error } = useMenus({
    skip: currentPage * pageSize,
    limit: pageSize,
    menu_type: menuTypeFilter || undefined,
    is_active: isActiveFilter === '' ? undefined : isActiveFilter,
  });

  const deleteWithPINMutation = useDeleteMenuWithPIN();

  // Client-side search filter and alphabetical sorting
  const filteredMenus = useMemo(() => {
    if (!data?.items) return [];
    return [...data.items]
      .filter((menu) => menu.name.toLowerCase().includes(searchQuery.toLowerCase()))
      .sort((a, b) => a.name.localeCompare(b.name, 'id', { sensitivity: 'base' }));
  }, [data?.items, searchQuery]);

  const handleDelete = (menu: Menu) => {
    setMenuToDelete(menu);
    setShowPinModal(true);
  };

  const handlePinVerified = () => {
    if (menuToDelete) {
      // PIN was verified in modal, now just need to confirm deletion
      // The modal will close and we show success
      deleteWithPINMutation.mutate(menuToDelete.id);
      setMenuToDelete(null);
    }
  };

  const handleCopyPublicUrl = (menu: Menu) => {
    if (menu.public_url) {
      navigator.clipboard.writeText(menu.public_url);
      toast.success('Public URL copied to clipboard');
    }
  };

  const handleDownloadQR = async (menu: Menu) => {
    if (!menu.public_url) {
      toast.error('Menu tidak memiliki URL publik');
      return;
    }

    try {
      setDownloadingQRMenuId(menu.id);

      // Generate QR code as data URL
      const dataUrl = await QRCode.toDataURL(menu.public_url, {
        width: 512,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF',
        },
      });

      // Create download link
      const link = document.createElement('a');
      link.href = dataUrl;
      link.download = `menu_${menu.name.replace(/[^a-zA-Z0-9]/g, '_')}_qr.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      toast.success('QR Code berhasil diunduh!');
    } catch (error) {
      console.error('Failed to generate QR code:', error);
      toast.error('Gagal mengunduh QR Code');
    } finally {
      setDownloadingQRMenuId(null);
    }
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
      <div className={TABLE_STYLES.container}>
        <table className={TABLE_STYLES.table}>
          <thead className={TABLE_STYLES.thead}>
            <tr>
              <th className={TABLE_STYLES.th}>
                Menu Name
              </th>
              <th className={TABLE_STYLES.th}>
                Status
              </th>
              <th className={TABLE_STYLES.th}>
                Type
              </th>
              <th className={TABLE_STYLES.th}>
                Items
              </th>
              <th className={TABLE_STYLES.th}>
                Public Access
              </th>
              <th className={TABLE_STYLES.th}>
                Actions
              </th>
            </tr>
          </thead>
          <tbody className={TABLE_STYLES.tbody}>
            {filteredMenus.map((menu) => (
              <tr key={menu.id} className={TABLE_STYLES.tr}>
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
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 capitalize">
                    {menu.menu_type.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {menu.items_count} items
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
                    {menu.public_url && (
                      <button
                        onClick={() => handleDownloadQR(menu)}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors disabled:opacity-50"
                        title="Download QR Code"
                        disabled={downloadingQRMenuId === menu.id}
                      >
                        {downloadingQRMenuId === menu.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Download className="w-4 h-4" />
                        )}
                      </button>
                    )}
                  </div>
                </td>
                <td className={TABLE_STYLES.td}>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onManageItems(menu)}
                      className={TABLE_STYLES.actionBtnGreen}
                      title="Manage Items"
                    >
                      <List className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onEdit(menu)}
                      className={TABLE_STYLES.actionBtnBlue}
                      title="Edit Menu"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(menu)}
                      className={TABLE_STYLES.actionBtnRed}
                      title="Delete Menu"
                      disabled={deleteWithPINMutation.isPending}
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

      {/* PIN Verification Modal */}
      <PinVerificationModal
        open={showPinModal}
        onOpenChange={setShowPinModal}
        onVerified={handlePinVerified}
        title="Delete Menu"
        description="Enter your organization PIN to confirm menu deletion."
        menuName={menuToDelete?.name}
      />
    </div>
  );
};
