/**
 * Schedules Management Page (Wrapper)
 * Wrapper for feature-based SchedulesPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import SchedulesPageContent from '@/features/schedules/pages/SchedulesPage';
import { useTranslation } from 'react-i18next';

export default function SchedulesPage() {
  const { t } = useTranslation();

  return (
    <>
      <PageHeader
        title={t('navigation.schedules')}
        description={t('schedules.subtitle', 'Schedule when playlists play on your devices')}
      />
      <SchedulesPageContent />
    </>
  );
}
