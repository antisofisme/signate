/**
 * Sessions Management Page (Wrapper)
 * Wrapper for feature-based SessionsPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import SessionsPageContent from '@/features/sessions/pages/SessionsPage';
import { useTranslation } from 'react-i18next';

export default function SessionsPage() {
  const { t } = useTranslation();

  return (
    <>
      <PageHeader
        title={t('sessions.title')}
        description={t('sessions.description')}
      />
      <SessionsPageContent />
    </>
  );
}
