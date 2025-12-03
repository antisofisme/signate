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
import { Trash2, Image, LayoutGrid, Table2, Filter, Upload } from 'lucide-react';
import {
  PageHeader,
  PageSkeleton,
  AccessDenied,
  Tabs,
  TabPanel,
  ViewTabs,
  PageToolbar,
  PageStats,
  Button,
} from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useMenuMediaList } from '../hooks/useMenuMedia';
import { MenuMediaTable } from '../components/MenuMediaTable';
import { MenuMediaDeletedTable } from '../components/MenuMediaDeletedTable';
import { MenuMediaGalleryView } from '../components/MenuMediaGalleryView';
import { MenuMediaDeletedGalleryView } from '../components/MenuMediaDeletedGalleryView';

// View mode types
type ViewMode = 'table' | 'gallery';

// localStorage key for persisting view preference
const VIEW_MODE_STORAGE_KEY = 'menuMedia.viewMode';

// View mode tabs for Table/Gallery switching (standardized layout)
const VIEW_TABS = [
  { id: 'table', label: 'Table', icon: Table2 },
  { id: 'gallery', label: 'Gallery', icon: LayoutGrid },
];

export default function MenuMediaPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('active');
  const [showFilters, setShowFilters] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Permission checks
  const { hasPermission: canCreate } = useCanPerformAction('menus', 'create');

  // Fetch media data for stats
  const { data: mediaData } = useMenuMediaList({});

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
      {/* Page Header */}
      <PageHeader
        title={t('menus.mediaTitle', 'Menu Media')}
        description={t('menus.mediaSubtitle', 'Upload and manage images for your digital menu items')}
      />

      {/* ROW 1: View Mode Tabs (Table/Gallery) */}
      <ViewTabs
        tabs={VIEW_TABS}
        activeTab={viewMode}
        onChange={(id) => setViewMode(id as ViewMode)}
      />

      {/* ROW 2: Content Type Tabs (Active/Deleted) */}
      <Tabs
        tabs={MENU_MEDIA_TABS}
        activeTab={activeTab}
        onChange={setActiveTab}
        className="mb-6"
      />

      {/* ROW 3: Toolbar - Filter kiri, Upload kanan */}
      <PageToolbar>
        <PageToolbar.Left>
          <Button
            variant={showFilters ? 'primary' : 'secondary'}
            onClick={() => setShowFilters(!showFilters)}
            leftIcon={<Filter className="w-4 h-4" />}
          >
            {t('common.filter', 'Filter')}
          </Button>
        </PageToolbar.Left>
        <PageToolbar.Right>
          {canCreate && (
            <Button
              variant="primary"
              onClick={() => setShowUploadModal(true)}
              leftIcon={<Upload className="w-4 h-4" />}
            >
              {t('menus.media.upload', 'Upload')}
            </Button>
          )}
        </PageToolbar.Right>
      </PageToolbar>

      {/* ROW 4: Stats */}
      <PageStats
        total={mediaData?.total || 0}
        totalLabel={t('menus.media.stats.total', 'images')}
      />

      {/* Tab Panels */}
      <TabPanel activeTab={activeTab} tabId="active">
        <div className="space-y-6">
          {viewMode === 'table' ? (
            <MenuMediaTable
              showUploadModal={showUploadModal}
              onCloseUploadModal={() => setShowUploadModal(false)}
              showFilters={showFilters}
            />
          ) : (
            <MenuMediaGalleryView
              showUploadModal={showUploadModal}
              onCloseUploadModal={() => setShowUploadModal(false)}
            />
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
