/**
 * Analytics Page (Wrapper)
 * Wrapper for AnalyticsPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import { AnalyticsPage } from './AnalyticsPage';
import { useTranslation } from 'react-i18next';

export default function AnalyticsPageWrapper() {
  const { t } = useTranslation();

  return (
    <>
      <PageHeader
        title={t('analytics.title')}
        description={t('analytics.description')}
      />
      <AnalyticsPage />
    </>
  );
}
