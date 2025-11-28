/**
 * Widgets Management Page (Wrapper)
 * Wrapper for feature-based WidgetsPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import WidgetsPageContent from '@/features/widgets/pages/WidgetsPage';

export default function WidgetsPage() {
  return (
    <>
      <PageHeader
        title="Widget Manager"
        description="Configure and manage display widgets for your screens"
      />
      <WidgetsPageContent />
    </>
  );
}
