/**
 * Analytics Page (Wrapper)
 * Wrapper for AnalyticsPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import { AnalyticsPage } from './AnalyticsPage';

export default function AnalyticsPageWrapper() {
  return (
    <>
      <PageHeader
        title="Analytics & Reports"
        description="Track content performance and device engagement"
      />
      <AnalyticsPage />
    </>
  );
}
