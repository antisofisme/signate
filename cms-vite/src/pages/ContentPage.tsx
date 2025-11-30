/**
 * Content Management Page
 *
 * LAYER 1: PRESENTATION
 * Displays content library with upload, filters, and management
 * Includes tabs for Active Content and Recycle Bin (soft-deleted)
 * Supports both Table and Gallery view modes with localStorage persistence
 */

import { useState, useEffect } from 'react';
import { FileImage, Trash2, Table2, LayoutGrid } from 'lucide-react';
import { PageHeader, AccessDenied, PageSkeleton, Tabs, TabPanel, Button } from '@/shared/components';
import { ContentTable } from '@/features/contents/components/ContentTable';
import { DeletedContentTable } from '@/features/contents/components/DeletedContentTable';
import { ContentGalleryView } from '@/features/contents/components/ContentGalleryView';
import { DeletedContentGalleryView } from '@/features/contents/components/DeletedContentGalleryView';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useTranscodingProgress } from '@/features/contents/hooks/useTranscodingProgress';
import { useTranslation } from 'react-i18next';

// View mode types
type ViewMode = 'table' | 'gallery';
const VIEW_MODE_KEY = 'content.viewMode';

const CONTENT_TABS = [
  { id: 'active', label: 'Active Content', icon: FileImage },
  { id: 'deleted', label: 'Recycle Bin', icon: Trash2 },
];

export default function ContentPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('active');

  // View mode state with localStorage persistence
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem(VIEW_MODE_KEY);
    return saved === 'gallery' || saved === 'table' ? saved : 'table';
  });

  // Persist view mode to localStorage
  useEffect(() => {
    localStorage.setItem(VIEW_MODE_KEY, viewMode);
  }, [viewMode]);

  // Listen for transcoding progress via WebSocket
  useTranscodingProgress();

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
      {/* Sticky Page Header with View Toggle */}
      <div className="flex items-center justify-between mb-6">
        <PageHeader
          title={t('contents.title')}
          description={t('contents.subtitle', 'Manage your media files (images, videos, audio)')}
        />

        {/* View Mode Toggle */}
        <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
          <Button
            variant={viewMode === 'table' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('table')}
            leftIcon={<Table2 className="w-4 h-4" />}
            title={t('contents.viewMode.table', 'Table View')}
          >
            {t('contents.viewMode.table', 'Table')}
          </Button>
          <Button
            variant={viewMode === 'gallery' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('gallery')}
            leftIcon={<LayoutGrid className="w-4 h-4" />}
            title={t('contents.viewMode.gallery', 'Gallery View')}
          >
            {t('contents.viewMode.gallery', 'Gallery')}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={CONTENT_TABS}
        activeTab={activeTab}
        onChange={setActiveTab}
        className="mb-6"
      />

      {/* Tab Panels - Conditional View Rendering */}
      <TabPanel activeTab={activeTab} tabId="active">
        <div className="space-y-6">
          {viewMode === 'table' ? <ContentTable /> : <ContentGalleryView />}
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
