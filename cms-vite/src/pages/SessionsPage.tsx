/**
 * Sessions Management Page (Wrapper)
 * Wrapper for feature-based SessionsPage with PageHeader
 */

import { Shield } from 'lucide-react';
import { PageHeader } from '@/shared/components';
import SessionsPageContent from '@/features/sessions/pages/SessionsPage';

export default function SessionsPage() {
  return (
    <>
      <PageHeader
        title="Active Sessions"
        description="Manage your active login sessions across devices"
        icon={Shield}
      />
      <SessionsPageContent />
    </>
  );
}
