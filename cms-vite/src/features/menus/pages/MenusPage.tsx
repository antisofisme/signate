/**
 * Menus Page
 *
 * LAYER 1: PRESENTATION
 * Main page for digital menu management - orchestration only
 */

import { useState } from 'react';
import { Plus, Search } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PageHeader, PageSkeleton, AccessDenied, Button } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { MenuList } from '../components/MenuList';
import { MenuForm } from '../components/MenuForm';
import { MenuItemsManager } from '../components/MenuItemsManager';
import type { Menu, MenuType } from '../types/menu';

export default function MenusPage() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canView, isLoading: isCheckingPermission } = useCanPerformAction('menus', 'read');
  const { hasPermission: canCreate } = useCanPerformAction('menus', 'create');

  // State
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingMenu, setEditingMenu] = useState<Menu | null>(null);
  const [managingItemsMenu, setManagingItemsMenu] = useState<Menu | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [menuTypeFilter, setMenuTypeFilter] = useState<MenuType | ''>('');
  const [isActiveFilter, setIsActiveFilter] = useState<boolean | ''>('');

  // Handlers
  const handleEdit = (menu: Menu) => {
    setEditingMenu(menu);
  };

  const handleManageItems = (menu: Menu) => {
    setManagingItemsMenu(menu);
  };

  const handleCloseForm = () => {
    setShowCreateForm(false);
    setEditingMenu(null);
  };

  // Permission loading
  if (isCheckingPermission) {
    return <PageSkeleton />;
  }

  // Access denied
  if (!canView) {
    return <AccessDenied />;
  }

  return (
    <>
      <PageHeader
        title={t('menus.title')}
        description={t('menus.subtitle')}
        actions={
          canCreate && (
            <Button onClick={() => setShowCreateForm(true)}>
              <Plus className="w-5 h-5 mr-2" />
              {t('menus.createMenu')}
            </Button>
          )
        }
      />

      <div className="space-y-6">
        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 w-5 h-5" />
                <input
                  type="text"
                  placeholder={t('menus.searchPlaceholder')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Menu Type Filter */}
            <div>
              <select
                value={menuTypeFilter}
                onChange={(e) => setMenuTypeFilter(e.target.value as MenuType | '')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">{t('menus.allTypes')}</option>
                <option value="restaurant">{t('menus.types.restaurant')}</option>
                <option value="laundry">{t('menus.types.laundry')}</option>
                <option value="spa">{t('menus.types.spa')}</option>
                <option value="room_service">{t('menus.types.roomService')}</option>
                <option value="other">{t('menus.types.other')}</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <select
                value={isActiveFilter === '' ? '' : isActiveFilter ? 'true' : 'false'}
                onChange={(e) =>
                  setIsActiveFilter(e.target.value === '' ? '' : e.target.value === 'true')
                }
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">{t('menus.allStatus')}</option>
                <option value="true">{t('menus.active')}</option>
                <option value="false">{t('menus.inactive')}</option>
              </select>
            </div>
          </div>
        </div>

        {/* Menu List */}
        <MenuList
          onEdit={handleEdit}
          onManageItems={handleManageItems}
          searchQuery={searchQuery}
          menuTypeFilter={menuTypeFilter}
          isActiveFilter={isActiveFilter}
        />

        {/* Modals */}
        {(showCreateForm || editingMenu) && (
          <MenuForm
            menu={editingMenu || undefined}
            onClose={handleCloseForm}
            onSuccess={handleCloseForm}
          />
        )}

        {managingItemsMenu && (
          <MenuItemsManager
            menu={managingItemsMenu}
            onClose={() => setManagingItemsMenu(null)}
          />
        )}
      </div>
    </>
  );
}
