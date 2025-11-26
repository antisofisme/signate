/**
 * Device Edit Modal Component
 *
 * Edit device settings and configuration
 * Uses centralized Modal component
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Save, Loader2 } from 'lucide-react';
import { Modal } from '@/shared/components';
import { useUpdateDevice } from '../../hooks/useDevices';
import type { Device } from '../../types/device';

interface DeviceEditModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
  onSuccess?: () => void;
}

export function DeviceEditModal({
  isOpen,
  device,
  onClose,
  onSuccess,
}: DeviceEditModalProps) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    device_name: '',
    rotation: 0,
    volume_enabled: true,
    room_number: '',
  });
  const [error, setError] = useState<string | null>(null);

  const updateMutation = useUpdateDevice();

  // Initialize form when device changes
  useEffect(() => {
    if (device) {
      setFormData({
        device_name: device.device_name,
        rotation: device.rotation || 0,
        volume_enabled: device.is_volume_enabled !== false,
        room_number: device.room_number || '',
      });
    }
  }, [device]);

  if (!device) return null;

  // Reset form
  const resetForm = () => {
    if (device) {
      setFormData({
        device_name: device.device_name,
        rotation: device.rotation || 0,
        volume_enabled: device.is_volume_enabled !== false,
        room_number: device.room_number || '',
      });
    }
    setError(null);
  };

  // Handle close
  const handleClose = () => {
    if (!updateMutation.isPending) {
      resetForm();
      onClose();
    }
  };

  // Handle submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.device_name.trim()) {
      setError(t('devices.modals.errors.nameRequired'));
      return;
    }

    try {
      await updateMutation.mutateAsync({
        id: device.id,
        data: {
          device_name: formData.device_name.trim(),
          rotation: formData.rotation,
          is_volume_enabled: formData.volume_enabled,
          room_number: formData.room_number.trim() || undefined,
        },
      });

      onSuccess?.();
      handleClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || t('devices.modals.errors.updateFailed'));
    }
  };

  // Footer
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={handleClose}
          disabled={updateMutation.isPending}
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 transition-colors"
        >
          {t('devices.buttons.cancel')}
        </button>
        <button
          type="submit"
          form="device-edit-form"
          disabled={updateMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
        >
          {updateMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {t('devices.modals.saving')}
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              {t('devices.modals.saveChanges')}
            </>
          )}
        </button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('devices.modals.editDevice')}
      maxWidth="md"
      footer={footer}
    >
      {/* Form */}
      <form id="device-edit-form" onSubmit={handleSubmit} className="p-6 space-y-4">
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Device Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('devices.modals.deviceNameLabel')} <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.device_name}
            onChange={(e) => {
              setFormData((prev) => ({ ...prev, device_name: e.target.value }));
              setError(null);
            }}
            placeholder={t('devices.placeholders.deviceName')}
            maxLength={200}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={updateMutation.isPending}
            required
          />
        </div>

        {/* Rotation */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('devices.modals.screenRotation')}
          </label>
          <select
            value={formData.rotation}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, rotation: parseInt(e.target.value) }))
            }
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={updateMutation.isPending}
          >
            <option value={0}>{t('devices.modals.rotation0')}</option>
            <option value={90}>{t('devices.modals.rotation90')}</option>
            <option value={180}>{t('devices.modals.rotation180')}</option>
            <option value={270}>{t('devices.modals.rotation270')}</option>
          </select>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {t('devices.modals.rotationHelp')}
          </p>
        </div>

        {/* Volume Enabled */}
        <div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.volume_enabled}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, volume_enabled: e.target.checked }))
              }
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              disabled={updateMutation.isPending}
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {t('devices.modals.enableAudio')}
            </span>
          </label>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 ml-6">
            {t('devices.modals.audioHelp')}
          </p>
        </div>

        {/* Room Number (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('devices.modals.roomNumberOptional')}
          </label>
          <input
            type="text"
            value={formData.room_number}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, room_number: e.target.value }))
            }
            placeholder={t('devices.placeholders.roomNumber')}
            maxLength={50}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={updateMutation.isPending}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {t('devices.modals.roomHelp')}
          </p>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <strong>{t('devices.modals.changesNote')}</strong> {t('devices.modals.changesEffect')}
          </p>
        </div>
      </form>
    </Modal>
  );
}
