/**
 * TV Register Modal Component
 *
 * Modal for registering TV devices (WebOS/native apps)
 */

import { useState } from 'react';
import { X, Tv, Loader2 } from 'lucide-react';
import { useTVRegister } from '../../hooks/useDevices';
import type { Device } from '../../types/device';

interface TVRegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (device: Device) => void;
}

export function TVRegisterModal({ isOpen, onClose, onSuccess }: TVRegisterModalProps) {
  const [formData, setFormData] = useState({
    organization_pin: '',
    device_name: '',
    platform: 'webOS',
    model_name: '',
    firmware_version: '',
  });
  const [error, setError] = useState<string | null>(null);

  const registerMutation = useTVRegister();

  if (!isOpen) return null;

  // Reset form
  const resetForm = () => {
    setFormData({
      organization_pin: '',
      device_name: '',
      platform: 'webOS',
      model_name: '',
      firmware_version: '',
    });
    setError(null);
  };

  // Handle close
  const handleClose = () => {
    if (!registerMutation.isPending) {
      resetForm();
      onClose();
    }
  };

  // Handle submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.organization_pin || formData.organization_pin.length !== 8) {
      setError('Organization PIN must be 8 digits');
      return;
    }

    if (!formData.device_name.trim()) {
      setError('Device name is required');
      return;
    }

    try {
      const device = await registerMutation.mutateAsync({
        organization_pin: formData.organization_pin,
        device_name: formData.device_name.trim(),
        platform: formData.platform,
        model_name: formData.model_name.trim() || undefined,
        firmware_version: formData.firmware_version.trim() || undefined,
      });

      resetForm();
      onSuccess?.(device);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to register TV device');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
              <Tv className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Register TV Device
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                WebOS or native app devices
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={registerMutation.isPending}
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

          {/* Organization PIN */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Organization PIN <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.organization_pin}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, '').slice(0, 8);
                setFormData((prev) => ({ ...prev, organization_pin: value }));
                setError(null);
              }}
              placeholder="Enter 8-digit PIN"
              maxLength={8}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={registerMutation.isPending}
              required
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              8-digit organization PIN from admin
            </p>
          </div>

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
              placeholder="e.g., Lobby TV 1, Room 101 TV"
              maxLength={200}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={registerMutation.isPending}
              required
            />
          </div>

          {/* Platform */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Platform
            </label>
            <select
              value={formData.platform}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, platform: e.target.value }))
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={registerMutation.isPending}
            >
              <option value="webOS">LG webOS</option>
              <option value="tizen">Samsung Tizen</option>
              <option value="android">Android TV</option>
              <option value="native">Native App</option>
            </select>
          </div>

          {/* Model Name (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Model Name (Optional)
            </label>
            <input
              type="text"
              value={formData.model_name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, model_name: e.target.value }))
              }
              placeholder="e.g., LG 55UN7300, Samsung QN55Q80A"
              maxLength={100}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={registerMutation.isPending}
            />
          </div>

          {/* Firmware Version (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Firmware Version (Optional)
            </label>
            <input
              type="text"
              value={formData.firmware_version}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, firmware_version: e.target.value }))
              }
              placeholder="e.g., 5.0.0, 6.2.1"
              maxLength={50}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={registerMutation.isPending}
            />
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              <strong>Next Step:</strong> After registration, you'll receive a 6-digit
              activation code. Enter this code on your TV to complete the setup.
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={registerMutation.isPending}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={registerMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
            >
              {registerMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Registering...
                </>
              ) : (
                <>
                  <Tv className="w-4 h-4" />
                  Register TV
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
