/**
 * Content Management Page
 *
 * LAYER 1: PRESENTATION
 * Displays content library with upload, filters, and management
 * Includes tabs for Active Content and Recycle Bin (soft-deleted)
 * Supports both Table and Gallery view modes with localStorage persistence
 */

import { useState, useEffect } from 'react';
import { FileImage, Trash2, Table2, LayoutGrid, Upload, Filter } from 'lucide-react';
import { PageHeader, AccessDenied, PageSkeleton, Tabs, TabPanel, ViewTabs, PageStats, PageToolbar, Button } from '@/shared/components';
import { ContentTable } from '@/features/contents/components/ContentTable';
import { DeletedContentTable } from '@/features/contents/components/DeletedContentTable';
import { ContentGalleryView } from '@/features/contents/components/ContentGalleryView';
import { DeletedContentGalleryView } from '@/features/contents/components/DeletedContentGalleryView';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useTranscodingProgress } from '@/features/contents/hooks/useTranscodingProgress';
import { useContentStats } from '@/features/contents/hooks/useContent';
import { useTranslation } from 'react-i18next';

// View mode types
type ViewMode = 'table' | 'gallery';
const VIEW_MODE_KEY = 'content.viewMode';

// View mode tabs for Table/Gallery switching (standardized layout)
const VIEW_TABS = [
  { id: 'table', label: 'Table', icon: Table2 },
  { id: 'gallery', label: 'Gallery', icon: LayoutGrid },
];

// Content type tabs for Active/Deleted content
const CONTENT_TABS = [
  { id: 'active', label: 'Active Content', icon: FileImage },
  { id: 'deleted', label: 'Recycle Bin', icon: Trash2 },
];

export default function ContentPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('active');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // View mode state with localStorage persistence
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem(VIEW_MODE_KEY);
    return saved === 'gallery' || saved === 'table' ? saved : 'table';
  });

  // Permission check for upload button
  const { hasPermission: canCreate } = useCanPerformAction('contents', 'create');

  // Persist view mode to localStorage
  useEffect(() => {
    localStorage.setItem(VIEW_MODE_KEY, viewMode);
  }, [viewMode]);

  // Listen for transcoding progress via WebSocket
  useTranscodingProgress();

  // Fetch content stats for PageStats
  const { data: statsData } = useContentStats();
  const totalFiles = statsData?.data?.total_files || 0;
  const imageCount = statsData?.data?.by_type?.image?.count || 0;
  const videoCount = statsData?.data?.by_type?.video?.count || 0;
  const audioCount = statsData?.data?.by_type?.audio?.count || 0;

  // Permission check - user needs view access to contents
  const { hasPermission, isLoading } = useCanPerformAction('contents', 'read');

  // Show loading state while checking permissions
  if (isLoading) {
    return <PageSkeleton />;
  }

  // Show access denied if no permission
  if (!hasPermission) {
    return <AccessDenied />;
  }

  return (
    <>
      {/* Page Header */}
      <PageHeader
        title={t('contents.title')}
        description={t('contents.subtitle', 'Manage your media files (images, videos, audio)')}
      />

      {/* View Mode Tabs (Table/Gallery) */}
      <ViewTabs
        tabs={VIEW_TABS}
        activeTab={viewMode}
        onChange={(id) => setViewMode(id as ViewMode)}
      />

      {/* Content Type Tabs (Active/Deleted) */}
      <Tabs
        tabs={CONTENT_TABS}
        activeTab={activeTab}
        onChange={setActiveTab}
        className="mb-4"
      />

      {/* Toolbar: Filter kiri, Upload kanan */}
      <PageToolbar>
        <PageToolbar.Left>
          <Button
            variant={showFilters ? 'primary' : 'secondary'}
            onClick={() => setShowFilters(!showFilters)}
            leftIcon={<Filter className="w-4 h-4" />}
          >
            {t('contents.actions.filters')}
          </Button>
        </PageToolbar.Left>
        <PageToolbar.Right>
          {canCreate && (
            <Button
              variant="primary"
              onClick={() => setShowUploadModal(true)}
              leftIcon={<Upload className="w-4 h-4" />}
            >
              {t('contents.actions.upload')}
            </Button>
          )}
        </PageToolbar.Right>
      </PageToolbar>

      {/* Stats: langsung di atas tabel */}
      <PageStats
        total={totalFiles}
        totalLabel="files"
        stats={[
          { label: 'images', value: imageCount, color: 'text-blue-600 dark:text-blue-400' },
          { label: 'videos', value: videoCount, color: 'text-purple-600 dark:text-purple-400' },
          { label: 'audio', value: audioCount, color: 'text-green-600 dark:text-green-400' },
        ]}
      />

      {/* Tab Panels - Conditional View Rendering */}
      <TabPanel activeTab={activeTab} tabId="active">
        <div className="space-y-6">
          {viewMode === 'table' ? (
            <ContentTable
              showUploadModal={showUploadModal}
              onCloseUploadModal={() => setShowUploadModal(false)}
              showFilters={showFilters}
            />
          ) : (
            <ContentGalleryView
              showUploadModal={showUploadModal}
              onCloseUploadModal={() => setShowUploadModal(false)}
              showFilters={showFilters}
            />
          )}
        </div>
      </TabPanel>

      <TabPanel activeTab={activeTab} tabId="deleted">
        <div className="space-y-6">
          {viewMode === 'table' ? <DeletedContentTable /> : <DeletedContentGalleryView />}
        </div>
      </TabPanel>
    </>
  );
}
