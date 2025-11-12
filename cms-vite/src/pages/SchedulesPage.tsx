/**
 * Schedules Management Page (Wrapper)
 * Wrapper for feature-based SchedulesPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import SchedulesPageContent from '@/features/schedules/pages/SchedulesPage';

export default function SchedulesPage() {
  return (
    <>
      <PageHeader
        title="Schedule Manager"
        description="Create and manage automated content playback schedules"
      />
      <SchedulesPageContent />
    </>
  );
}
