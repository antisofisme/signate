/**
 * Device Logs Modal Component
 *
 * Comprehensive console logs and connection logs viewer
 * Uses centralized Modal component
 */

import { Modal } from '@/shared/components';
import { DeviceLogsViewer } from '../DeviceLogsViewer';
import type { Device } from '../../types/device';

interface DeviceLogsModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

export function DeviceLogsModal({ isOpen, device, onClose }: DeviceLogsModalProps) {
  if (!device) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Device Logs"
      subtitle={device.device_name}
      maxWidth="6xl"
    >
      <div className="p-6">
        <DeviceLogsViewer deviceId={device.id} deviceName={device.device_name} />
      </div>
    </Modal>
  );
}
