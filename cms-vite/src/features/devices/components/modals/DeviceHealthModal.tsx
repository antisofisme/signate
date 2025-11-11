/**
 * Device Health Modal Component
 *
 * LAYER 1: PRESENTATION
 * Modal showing device health dashboard and command controls
 */

import { X } from 'lucide-react';
import { DeviceHealthDashboard } from '../DeviceHealthDashboard';
import { DeviceCommandControl } from '../DeviceCommandControl';
import type { Device } from '../../types/device';

interface DeviceHealthModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

export function DeviceHealthModal({ isOpen, device, onClose }: DeviceHealthModalProps) {
  if (!isOpen || !device) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-lg w-full max-w-7xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Device Health & Commands
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {device.device_name} (ID: {device.id})
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Command Control Section */}
          <DeviceCommandControl deviceId={device.id} deviceName={device.device_name} />

          {/* Health Dashboard Section */}
          <DeviceHealthDashboard deviceId={device.id} autoRefresh={true} />
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
