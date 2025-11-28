/**
 * Device Management Page
 *
 * LAYER 1: PRESENTATION
 * Displays device list with filters and management
 */

import { PageHeader, AccessDenied, PageSkeleton } from '@/shared/components';
import { DeviceTable } from '@/features/devices/components/DeviceTable';
import { OrganizationHealthSummary } from '@/features/devices/components/OrganizationHealthSummary';
import { useDeviceWebSocket } from '@/features/devices/hooks/useDeviceWebSocket';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useTranslation } from 'react-i18next';

export default function DevicesPage() {
  const { t } = useTranslation();
  // Check permissions
  const { hasPermission, isLoading: isCheckingPermission } = useCanPerformAction(
    'devices',
    'read'
  );

  // Enable real-time device updates only if user has permission
  useDeviceWebSocket();

  // Get organization ID from localStorage (set during login)
  const orgId = localStorage.getItem('selected-org-id');
  const organizationId = orgId ? parseInt(orgId, 10) : 0;

  // Show loading state while checking permissions
  if (isCheckingPermission) {
    return <PageSkeleton />;
  }

  // Show access denied if no permission
  if (!hasPermission) {
    return <AccessDenied />;
  }

  return (
    <>
      {/* Sticky Page Header */}
      <PageHeader
        title={t('devices.title')}
        description={t('devices.subtitle')}
      />

      {/* Content */}
      <div className="space-y-6">
        {/* Organization Health Summary Widget */}
        {organizationId > 0 && (
          <OrganizationHealthSummary organizationId={organizationId} />
        )}

        {/* Device Table */}
        <DeviceTable />
      </div>
    </>
  );
}
