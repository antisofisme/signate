/**
 * Organizations Page Wrapper
 *
 * LAYER 1: PRESENTATION
 * Wrapper for organizations page with PageHeader
 */

import { PageHeader } from '@/shared/components';
import OrganizationsPageContent from '@/features/organizations/pages/OrganizationsPage';

export default function OrganizationsPage() {
  return (
    <div>
      <PageHeader
        title="Organizations"
        description="Manage your organizations and their settings"
      />
      <OrganizationsPageContent />
    </div>
  );
}
