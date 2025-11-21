/**
 * Device Logs Modal Component
 *
 * Comprehensive console logs and connection logs viewer
 * Wraps DeviceLogsViewer in a modal dialog
 */

import { X } from 'lucide-react';
import { DeviceLogsViewer } from '../DeviceLogsViewer';
import type { Device } from '../../types/device';

interface DeviceLogsModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

export function DeviceLogsModal({ isOpen, device, onClose }: DeviceLogsModalProps) {
  if (!isOpen || !device) return null;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
      onKeyDown={handleKeyDown}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-6xl max-h-[95vh] overflow-hidden flex flex-col mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Device Logs
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {device.device_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content - DeviceLogsViewer */}
        <div className="flex-1 overflow-y-auto p-6">
          <DeviceLogsViewer deviceId={device.id} deviceName={device.device_name} />
        </div>
      </div>
    </div>
  );
}
