/**
 * Device Management Page
 *
 * LAYER 1: PRESENTATION
 * Displays device list with filters and management
 */

import { PageHeader } from '@/shared/components';
import { DeviceTable } from '@/features/devices/components/DeviceTable';

export default function DevicesPage() {
  return (
    <>
      {/* Sticky Page Header */}
      <PageHeader
        title="Device Management"
        description="Monitor and manage TV and monitor devices for digital signage"
      />

      {/* Device Table */}
      <div className="space-y-6">
        <DeviceTable />
      </div>
    </>
  );
}
