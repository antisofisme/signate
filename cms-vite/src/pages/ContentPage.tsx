/**
 * Content Management Page
 *
 * LAYER 1: PRESENTATION
 * Displays content library with upload, filters, and management
 */

import { PageHeader } from '@/shared/components';
import { ContentTable } from '@/features/contents/components/ContentTable';

export default function ContentPage() {
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
