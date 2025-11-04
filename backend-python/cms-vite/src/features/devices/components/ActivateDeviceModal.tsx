/**
 * Activate Device Modal
 * Modal for activating devices with 6-digit code
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useActivateDevice } from '../hooks/useDevices';
import type { ActivateDeviceRequest } from '../types/device';

interface ActivateDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ActivateDeviceModal({ isOpen, onClose }: ActivateDeviceModalProps) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<ActivateDeviceRequest>({
    unique_code: '',
    device_name: '',
    room_number: '',
  });

  const { mutate: activate, isPending, isError, error } = useActivateDevice();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    activate(formData, {
      onSuccess: () => {
        onClose();
        setFormData({ unique_code: '', device_name: '', room_number: '' });
      },
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black bg-opacity-30 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            {t('devices.activateDevice')}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Activation Code */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('devices.activationCode')} *
              </label>
              <input
                type="text"
                value={formData.unique_code}
                onChange={(e) => setFormData({ ...formData, unique_code: e.target.value.toUpperCase() })}
                maxLength={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-md dark:border-gray-600 dark:bg-gray-700 dark:text-white uppercase tracking-widest text-center text-lg font-mono"
                placeholder="ABC123"
                required
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {t('devices.codeFromScreen')}
              </p>
            </div>

            {/* Device Name (Optional) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('devices.deviceName')}
              </label>
              <input
                type="text"
                value={formData.device_name}
                onChange={(e) => setFormData({ ...formData, device_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md dark:border-gray-600 dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Room Number (Optional) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('devices.roomNumber')}
              </label>
              <input
                type="text"
                value={formData.room_number}
                onChange={(e) => setFormData({ ...formData, room_number: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md dark:border-gray-600 dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Error */}
            {isError && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
                <p className="text-sm text-red-800 dark:text-red-300">
                  {error instanceof Error ? error.message : t('devices.activationFailed')}
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                disabled={isPending}
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                disabled={isPending}
              >
                {isPending ? t('common.loading') : t('devices.activate')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
