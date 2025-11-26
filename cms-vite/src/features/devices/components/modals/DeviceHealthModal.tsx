/**
 * Device Health Modal Component
 *
 * LAYER 1: PRESENTATION
 * Modal showing device health dashboard and command controls
 * Uses centralized Modal component
 */

import { useTranslation } from 'react-i18next';
import { Modal } from '@/shared/components';
import { DeviceHealthDashboard } from '../DeviceHealthDashboard';
import { DeviceCommandControl } from '../DeviceCommandControl';
import type { Device } from '../../types/device';

interface DeviceHealthModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

export function DeviceHealthModal({ isOpen, device, onClose }: DeviceHealthModalProps) {
  const { t } = useTranslation();

  if (!device) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t('devices.modals.deviceHealth')}
      subtitle={`${device.device_name} (ID: ${device.id})`}
      maxWidth="6xl"
      footer={
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            {t('common.close')}
          </button>
        </div>
      }
    >
      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Command Control Section */}
        <DeviceCommandControl deviceId={device.id} deviceName={device.device_name} />

        {/* Health Dashboard Section */}
        <DeviceHealthDashboard deviceId={device.id} autoRefresh={true} />
      </div>
    </Modal>
  );
}
