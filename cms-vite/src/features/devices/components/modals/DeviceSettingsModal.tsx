/**
 * Device Settings Modal - Standalone
 *
 * Separated modal for device edit/settings:
 * - Opened via Edit button (not inside management modal)
 * - Focused on configuration only
 * - Simpler UX for quick edits
 */

import { Modal } from '@/shared/components';
import { Settings } from 'lucide-react';
import type { Device } from '../../types/device';
import { SettingsTab } from './tabs/SettingsTab';

interface DeviceSettingsModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
  onSuccess?: () => void;
}

export function DeviceSettingsModal({
  isOpen,
  device,
  onClose,
  onSuccess,
}: DeviceSettingsModalProps) {
  if (!device) return null;

  const handleSuccess = () => {
    onSuccess?.();
    // Don't close automatically - let user decide
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
            <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Device Settings
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              {device.device_name}
            </p>
          </div>
        </div>
      }
      maxWidth="2xl"
    >
      <SettingsTab device={device} onSuccess={handleSuccess} />
    </Modal>
  );
}
