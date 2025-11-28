/**
 * Organizations Page Wrapper
 *
 * LAYER 1: PRESENTATION
 * Wrapper for organizations page with PageHeader
 */

import { PageHeader } from '@/shared/components';
import OrganizationsPageContent from '@/features/organizations/pages/OrganizationsPage';
import { useTranslation } from 'react-i18next';

export default function OrganizationsPage() {
  const { t } = useTranslation();

  return (
    <div>
      <PageHeader
        title={t('organizations.title')}
        description={t('organizations.description')}
      />
      <OrganizationsPageContent />
    </div>
  );
}
