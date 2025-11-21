/**
 * TV Register Modal Component
 *
 * Modal for registering TV devices (WebOS/native apps)
 * Uses centralized Modal component
 */

import { useState } from 'react';
import { Tv, Loader2 } from 'lucide-react';
import { Modal } from '@/shared/components';
import { useTVRegister } from '../../hooks/useDevices';
import type { Device } from '../../types/device';

interface TVRegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (device: Device) => void;
}

export function TVRegisterModal({ isOpen, onClose, onSuccess }: TVRegisterModalProps) {
  const [formData, setFormData] = useState({
    activation_code: '',
    device_name: '',
    platform: 'webOS',
    model_name: '',
    firmware_version: '',
  });
  const [error, setError] = useState<string | null>(null);

  const registerMutation = useTVRegister();

  // Helper to format error messages
  const formatErrorMessage = (err: any): string => {
    if (typeof err?.response?.data?.detail === 'string') {
      return err.response.data.detail;
    }
    if (Array.isArray(err?.response?.data?.detail)) {
      return err.response.data.detail
        .map((e: any) => `${e.loc?.join('.') || 'Field'}: ${e.msg}`)
        .join(', ');
    }
    return 'Failed to activate TV device';
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      activation_code: '',
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

    if (!formData.activation_code || formData.activation_code.length !== 6) {
      setError('Activation code must be 6 digits');
      return;
    }

    if (!formData.device_name.trim()) {
      setError('Device name is required');
      return;
    }

    try {
      const device = await registerMutation.mutateAsync({
        unique_code: formData.activation_code,
        device_name: formData.device_name.trim(),
      });

      resetForm();
      onSuccess?.(device);
      onClose();
    } catch (err: any) {
      setError(formatErrorMessage(err));
    }
  };

  // Custom header with icon
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
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
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      maxWidth="md"
      customHeader={customHeader}
    >
      {/* Form */}
      <form onSubmit={handleSubmit} className="p-6 space-y-4">
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Activation Code */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Activation Code <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.activation_code}
            onChange={(e) => {
              const value = e.target.value.replace(/\D/g, '').slice(0, 6);
              setFormData((prev) => ({ ...prev, activation_code: value }));
              setError(null);
            }}
            placeholder="Enter 6-digit code"
            maxLength={6}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-lg tracking-widest text-center focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={registerMutation.isPending}
            required
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            6-digit code displayed on TV screen
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

        {/* Info Box */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <strong>How it works:</strong> Enter the 6-digit activation code shown on the TV screen. The device will be automatically assigned to your organization.
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
                Activating...
              </>
            ) : (
              <>
                <Tv className="w-4 h-4" />
                Activate TV
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
