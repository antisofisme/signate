/**
 * Health Tab - Device Management Modal
 *
 * Real-time health monitoring with:
 * - System metrics (CPU, RAM, Disk)
 * - Network speed history
 * - Connection quality
 */

import type { Device } from '../../../types/device';
import { DeviceHealthDashboard } from '../../DeviceHealthDashboard';

interface HealthTabProps {
  device: Device;
  isOnline: boolean;
}

export function HealthTab({ device, isOnline }: HealthTabProps) {
  return (
    <div className="p-6">
      <DeviceHealthDashboard deviceId={device.id} autoRefresh={isOnline} />

      {!isOnline && (
        <div className="mt-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <p className="text-sm text-yellow-700 dark:text-yellow-300">
            <strong>Device Offline:</strong> Health metrics are not available while device is offline.
          </p>
        </div>
      )}
    </div>
  );
}
