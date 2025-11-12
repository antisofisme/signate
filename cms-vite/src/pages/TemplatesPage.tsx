/**
 * Templates Management Page (Wrapper)
 * Wrapper for feature-based TemplatesPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import TemplatesPageContent from '@/features/templates/pages/TemplatesPage';

export default function TemplatesPage() {
  return (
    <>
      <PageHeader
        title="Template Manager"
        description="Create and manage display templates for your content"
      />
      <TemplatesPageContent />
    </>
  );
}
