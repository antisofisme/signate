/**
 * Menu List Component
 * Displays all menus in a table with actions
 */

import { useState, useMemo } from 'react';
import { Edit, Trash2, List, Copy, Download, ExternalLink, UtensilsCrossed, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import QRCode from 'qrcode';
import { useDeleteMenuWithPIN } from '../hooks/useMenus';
import { EmptyState, TABLE_STYLES, SortableTableHeader, TableSkeleton } from '@/shared/components';
import type { SortConfig } from '@/shared/components';
import { PinVerificationModal } from './PinVerificationModal';
import type { Menu } from '../types/menu';
import { toast } from '@/shared/utils/toast';

interface MenuListProps {
  menus: Menu[];
  isLoading: boolean;
  total: number;
  currentPage: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onEdit: (menu: Menu) => void;
  onManageItems: (menu: Menu) => void;
  onDelete?: (menu: Menu) => void;
  searchQuery?: string;
  // Sorting props
  sortConfig?: SortConfig | null;
  onSortChange?: (config: SortConfig | null) => void;
}

export const MenuList = ({
  menus,
  isLoading,
  total,
  currentPage,
  pageSize,
  onPageChange,
  onEdit,
  onManageItems,
  onDelete,
  searchQuery = '',
  sortConfig,
  onSortChange,
}: MenuListProps) => {
  const { t } = useTranslation();
  const [menuToDelete, setMenuToDelete] = useState<Menu | null>(null);
  const [showPinModal, setShowPinModal] = useState(false);
  const [downloadingQRMenuId, setDownloadingQRMenuId] = useState<number | null>(null);

  const deleteWithPINMutation = useDeleteMenuWithPIN();

  // Client-side search filter only (sorting is now server-side)
  const filteredMenus = useMemo(() => {
    if (!menus) return [];
    if (!searchQuery) return menus;
    return menus.filter((menu) =>
      menu.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [menus, searchQuery]);

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
    return <TableSkeleton columns={6} rows={5} />;
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
        <div className="overflow-x-auto">
          <table className={`${TABLE_STYLES.table} table-fixed`}>
            <thead className={TABLE_STYLES.thead}>
            <tr>
              <th className={`${TABLE_STYLES.th} w-[25%]`}>
                {sortConfig && onSortChange ? (
                  <SortableTableHeader
                    columnKey="name"
                    sortConfig={sortConfig}
                    onSortChange={onSortChange}
                  >
                    {t('menus.menuName', 'Menu Name')}
                  </SortableTableHeader>
                ) : (
                  t('menus.menuName', 'Menu Name')
                )}
              </th>
              <th className={`${TABLE_STYLES.th} w-20`}>
                {sortConfig && onSortChange ? (
                  <SortableTableHeader
                    columnKey="is_active"
                    sortConfig={sortConfig}
                    onSortChange={onSortChange}
                  >
                    {t('menus.status', 'Status')}
                  </SortableTableHeader>
                ) : (
                  t('menus.status', 'Status')
                )}
              </th>
              <th className={`${TABLE_STYLES.th} w-24`}>
                {sortConfig && onSortChange ? (
                  <SortableTableHeader
                    columnKey="menu_type"
                    sortConfig={sortConfig}
                    onSortChange={onSortChange}
                  >
                    {t('menus.type', 'Type')}
                  </SortableTableHeader>
                ) : (
                  t('menus.type', 'Type')
                )}
              </th>
              <th className={`${TABLE_STYLES.th} w-20`}>
                {sortConfig && onSortChange ? (
                  <SortableTableHeader
                    columnKey="items_count"
                    sortConfig={sortConfig}
                    onSortChange={onSortChange}
                  >
                    {t('menus.itemsColumn', 'Items')}
                  </SortableTableHeader>
                ) : (
                  t('menus.itemsColumn', 'Items')
                )}
              </th>
              <th className={`${TABLE_STYLES.th} w-28`}>
                {t('menus.publicAccess', 'Public Access')}
              </th>
              <th className={`${TABLE_STYLES.th} w-32`}>
                {t('menus.actions', 'Actions')}
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
      </div>

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            {t('common.pagination.showing', 'Showing')} {currentPage * pageSize + 1} {t('common.pagination.to', 'to')}{' '}
            {Math.min((currentPage + 1) * pageSize, total)} {t('common.pagination.of', 'of')} {total} {t('common.pagination.results', 'results')}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => onPageChange(Math.max(0, currentPage - 1))}
              disabled={currentPage === 0}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              {t('common.previous', 'Previous')}
            </button>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={(currentPage + 1) * pageSize >= total}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              {t('common.next', 'Next')}
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
