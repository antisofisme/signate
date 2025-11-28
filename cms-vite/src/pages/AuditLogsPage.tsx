/**
 * Audit Logs Page (Wrapper)
 * Wrapper for feature-based AuditPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import AuditPageContent from '@/features/audit/pages/AuditPage';
import { useTranslation } from 'react-i18next';

export default function AuditLogsPage() {
  const { t } = useTranslation();

  return (
    <>
      <PageHeader
        title={t('audit.title')}
        description={t('audit.description')}
      />
      <AuditPageContent />
    </>
  );
}
