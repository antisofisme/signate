/**
 * Device Edit Modal Component
 *
 * Edit device settings and configuration
 */

import { useState, useEffect } from 'react';
import { X, Save, Loader2 } from 'lucide-react';
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

  if (!isOpen || !device) return null;

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
      setError('Device name is required');
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
      setError(err?.response?.data?.detail || 'Failed to update device');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Edit Device
          </h3>
          <button
            onClick={handleClose}
            disabled={updateMutation.isPending}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Device Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Device Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.device_name}
              onChange={(e) => {
                setFormData((prev) => ({ ...prev, device_name: e.target.value }));
                setError(null);
              }}
              placeholder="e.g., Lobby TV 1, Room 101 Display"
              maxLength={200}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={updateMutation.isPending}
              required
            />
          </div>

          {/* Rotation */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Screen Rotation
            </label>
            <select
              value={formData.rotation}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, rotation: parseInt(e.target.value) }))
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={updateMutation.isPending}
            >
              <option value={0}>0° (Normal)</option>
              <option value={90}>90° (Clockwise)</option>
              <option value={180}>180° (Upside Down)</option>
              <option value={270}>270° (Counter-Clockwise)</option>
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Adjust screen orientation for portrait/landscape displays
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
                Enable Audio/Volume
              </span>
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 ml-6">
              Allow audio playback for video content
            </p>
          </div>

          {/* Room Number (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Room Number (Optional)
            </label>
            <input
              type="text"
              value={formData.room_number}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, room_number: e.target.value }))
              }
              placeholder="e.g., 101, A-205, Lobby"
              maxLength={50}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={updateMutation.isPending}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              For hotel/office deployments
            </p>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              <strong>Note:</strong> Changes will take effect immediately on the device.
              The device may need to refresh to apply rotation changes.
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={updateMutation.isPending}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
