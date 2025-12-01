/**
 * Menu Media Page
 *
 * LAYER 1: PRESENTATION
 * Dedicated page for managing menu media (images for menu items)
 * Supports two view modes: Table (default) and Gallery (masonry + sidebar)
 * Duplicates are shown as grouped tree in Active Media tab (like Content page)
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Trash2, Image, LayoutGrid, Table2 } from 'lucide-react';
import { PageHeader, PageSkeleton, AccessDenied, Tabs, TabPanel, Button } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { MenuMediaTable } from '../components/MenuMediaTable';
import { MenuMediaDeletedTable } from '../components/MenuMediaDeletedTable';
import { MenuMediaGalleryView } from '../components/MenuMediaGalleryView';
import { MenuMediaDeletedGalleryView } from '../components/MenuMediaDeletedGalleryView';

// View mode types
type ViewMode = 'table' | 'gallery';

// localStorage key for persisting view preference
const VIEW_MODE_STORAGE_KEY = 'menuMedia.viewMode';

export default function MenuMediaPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('active');

  // View mode state with localStorage persistence
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
    return (saved === 'gallery' || saved === 'table') ? saved : 'table';
  });

  // Persist view mode to localStorage
  useEffect(() => {
    localStorage.setItem(VIEW_MODE_STORAGE_KEY, viewMode);
  }, [viewMode]);

  // Create tabs with translated labels (duplicates shown as tree in Active tab)
  const MENU_MEDIA_TABS = [
    { id: 'active', label: t('menus.media.tabs.active', 'Active Media'), icon: Image },
    { id: 'deleted', label: t('menus.media.tabs.deleted', 'Recycle Bin'), icon: Trash2 },
  ];

  // Permission checks
  const { hasPermission: canView, isLoading: isCheckingPermission } = useCanPerformAction('menus', 'read');

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
      <div className="flex items-center justify-between mb-6">
        <PageHeader
          title={t('menus.mediaTitle', 'Menu Media')}
          description={t('menus.mediaSubtitle', 'Upload and manage images for your digital menu items')}
        />

        {/* View Mode Toggle - Available on all tabs */}
        <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
          <Button
            variant={viewMode === 'table' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('table')}
            leftIcon={<Table2 className="w-4 h-4" />}
            title={t('menus.media.viewMode.table', 'Table View')}
          >
            {t('menus.media.viewMode.table', 'Table')}
          </Button>
          <Button
            variant={viewMode === 'gallery' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('gallery')}
            leftIcon={<LayoutGrid className="w-4 h-4" />}
            title={t('menus.media.viewMode.gallery', 'Gallery View')}
          >
            {t('menus.media.viewMode.gallery', 'Gallery')}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={MENU_MEDIA_TABS}
        activeTab={activeTab}
        onChange={setActiveTab}
        className="mb-6"
      />

      {/* Tab Panels */}
      <TabPanel activeTab={activeTab} tabId="active">
        <div className="space-y-6">
          {viewMode === 'table' ? (
            <MenuMediaTable />
          ) : (
            <MenuMediaGalleryView />
          )}
        </div>
      </TabPanel>

      <TabPanel activeTab={activeTab} tabId="deleted">
        <div className="space-y-6">
          {viewMode === 'table' ? (
            <MenuMediaDeletedTable />
          ) : (
            <MenuMediaDeletedGalleryView />
          )}
        </div>
      </TabPanel>
    </>
  );
}
