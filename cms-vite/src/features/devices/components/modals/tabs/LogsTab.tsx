/**
 * Logs Tab - Device Management Modal
 *
 * Technical logs for debugging:
 * - Console logs
 * - Connection logs
 * - Error logs
 */

import type { Device } from '../../../types/device';
import { DeviceLogsViewer } from '../../DeviceLogsViewer';

interface LogsTabProps {
  device: Device;
}

export function LogsTab({ device }: LogsTabProps) {
  return (
    <div className="p-6">
      <DeviceLogsViewer deviceId={device.id} deviceName={device.device_name} />
    </div>
  );
}
