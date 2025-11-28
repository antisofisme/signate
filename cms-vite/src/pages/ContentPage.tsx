/**
 * Content Management Page
 *
 * LAYER 1: PRESENTATION
 * Displays content library with upload, filters, and management
 */

import { PageHeader, AccessDenied } from '@/shared/components';
import { ContentTable } from '@/features/contents/components/ContentTable';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useTranslation } from 'react-i18next';

export default function ContentPage() {
  const { t } = useTranslation();
  // Permission check - user needs view access to contents
  const { hasPermission, isLoading } = useCanPerformAction('contents', 'read');

  // Wait for permission check to complete
  if (isLoading) {
    return null; // Could add a loading skeleton here
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

      {/* Content Table */}
      <div className="space-y-6">
        <ContentTable />
      </div>
    </>
  );
}
