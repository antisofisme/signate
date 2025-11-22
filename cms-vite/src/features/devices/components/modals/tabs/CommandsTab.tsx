/**
 * Commands Tab - Device Management Modal
 *
 * Consolidated command control panel:
 * - All remote commands in one place
 * - Command history
 * - Queue status for offline devices
 */

import type { Device } from '../../../types/device';
import { DeviceCommandControl } from '../../DeviceCommandControl';

interface CommandsTabProps {
  device: Device;
  isOnline: boolean;
}

export function CommandsTab({ device, isOnline }: CommandsTabProps) {
  return (
    <div className="p-6">
      <DeviceCommandControl deviceId={device.id} deviceName={device.device_name} />

      {!isOnline && (
        <div className="mt-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <p className="text-sm text-yellow-700 dark:text-yellow-300">
            <strong>Device Offline:</strong> Commands will be queued and executed when device comes back online.
          </p>
        </div>
      )}
    </div>
  );
}
