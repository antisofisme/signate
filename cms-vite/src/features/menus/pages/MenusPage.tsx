/**
 * Menus Page
 * Main page for digital menu management
 */

import { useState } from 'react';
import { Plus, Search, Filter } from 'lucide-react';
import { MenuList } from '../components/MenuList';
import { MenuForm } from '../components/MenuForm';
import { MenuItemsManager } from '../components/MenuItemsManager';
import type { Menu, MenuType } from '../types/menu';

export default function MenusPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingMenu, setEditingMenu] = useState<Menu | null>(null);
  const [managingItemsMenu, setManagingItemsMenu] = useState<Menu | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [menuTypeFilter, setMenuTypeFilter] = useState<MenuType | ''>('');
  const [isActiveFilter, setIsActiveFilter] = useState<boolean | ''>('');

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

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Digital Menus</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your digital menus for restaurant, laundry, spa, and more
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="w-5 h-5" />
          <span>Create Menu</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search menus..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Menu Type Filter */}
          <div>
            <select
              value={menuTypeFilter}
              onChange={(e) => setMenuTypeFilter(e.target.value as MenuType | '')}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Types</option>
              <option value="restaurant">Restaurant</option>
              <option value="laundry">Laundry</option>
              <option value="spa">Spa</option>
              <option value="room_service">Room Service</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={isActiveFilter === '' ? '' : isActiveFilter ? 'true' : 'false'}
              onChange={(e) =>
                setIsActiveFilter(e.target.value === '' ? '' : e.target.value === 'true')
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Status</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
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
  );
};
