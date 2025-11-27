/**
 * Content Management Page
 *
 * LAYER 1: PRESENTATION
 * Displays content library with upload, filters, and management
 */

import { PageHeader, AccessDenied } from '@/shared/components';
import { ContentTable } from '@/features/contents/components/ContentTable';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';

export default function ContentPage() {
  // Permission check - user needs view access to contents
  const { hasPermission, isLoading } = useCanPerformAction('contents', 'view');

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
        title="Content Library"
        description="Manage your media content (images, videos, audio) for digital signage"
      />

      {/* Content Table */}
      <div className="space-y-6">
        <ContentTable />
      </div>
    </>
  );
}
