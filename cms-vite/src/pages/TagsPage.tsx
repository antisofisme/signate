/**
 * Tags Management Page (Wrapper)
 * Wrapper for feature-based TagsPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import TagsPageContent from '@/features/tags/pages/TagsPage';

export default function TagsPage() {
  return (
    <>
      <PageHeader
        title="Tags Management"
        description="Organize your devices and content with tags"
      />
      <TagsPageContent />
    </>
  );
}
