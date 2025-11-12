/**
 * Audit Logs Page (Wrapper)
 * Wrapper for feature-based AuditPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import AuditPageContent from '@/features/audit/pages/AuditPage';

export default function AuditLogsPage() {
  return (
    <>
      <PageHeader
        title="Audit Logs"
        description="View system activity and user actions"
      />
      <AuditPageContent />
    </>
  );
}
