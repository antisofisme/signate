/**
 * Content Management Page
 *
 * LAYER 1: PRESENTATION
 * Displays content library with upload, filters, and management
 * Includes tabs for Active Content and Recycle Bin (soft-deleted)
 */

import { useState } from 'react';
import { FileImage, Trash2 } from 'lucide-react';
import { PageHeader, AccessDenied, PageSkeleton, Tabs, TabPanel } from '@/shared/components';
import { ContentTable } from '@/features/contents/components/ContentTable';
import { DeletedContentTable } from '@/features/contents/components/DeletedContentTable';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useTranscodingProgress } from '@/features/contents/hooks/useTranscodingProgress';
import { useTranslation } from 'react-i18next';

const CONTENT_TABS = [
  { id: 'active', label: 'Active Content', icon: FileImage },
  { id: 'deleted', label: 'Recycle Bin', icon: Trash2 },
];

export default function ContentPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('active');

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
      {/* Sticky Page Header */}
      <PageHeader
        title={t('contents.title')}
        description={t('contents.subtitle', 'Manage your media files (images, videos, audio)')}
      />

      {/* Tabs */}
      <Tabs
        tabs={CONTENT_TABS}
        activeTab={activeTab}
        onChange={setActiveTab}
        className="mb-6"
      />

      {/* Tab Panels */}
      <TabPanel activeTab={activeTab} tabId="active">
        <div className="space-y-6">
          <ContentTable />
        </div>
      </TabPanel>

      <TabPanel activeTab={activeTab} tabId="deleted">
        <div className="space-y-6">
          <DeletedContentTable />
        </div>
      </TabPanel>
    </>
  );
}
