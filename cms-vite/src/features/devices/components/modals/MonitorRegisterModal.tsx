/**
 * Monitor Register Modal Component
 *
 * Modal for registering Monitor devices (browser-based)
 * Uses centralized Modal component
 */

import { useState } from 'react';
import { Monitor, Loader2 } from 'lucide-react';
import { Modal } from '@/shared/components';
import { useMonitorRegister } from '../../hooks/useDevices';

interface MonitorRegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function MonitorRegisterModal({
  isOpen,
  onClose,
  onSuccess,
}: MonitorRegisterModalProps) {
  const [formData, setFormData] = useState({
    activation_code: '',
    device_name: '',
    platform: 'browser',
  });
  const [error, setError] = useState<string | null>(null);

  const registerMutation = useMonitorRegister();

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
    return 'Failed to activate device';
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      activation_code: '',
      device_name: '',
      platform: 'browser',
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
      await registerMutation.mutateAsync({
        unique_code: formData.activation_code,
        device_name: formData.device_name.trim(),
      });

      resetForm();
      onSuccess?.();
      onClose();
    } catch (err: any) {
      setError(formatErrorMessage(err));
    }
  };

  // Custom header with icon
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
          <Monitor className="w-5 h-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Register Monitor Device
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Browser-based display
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
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-lg tracking-widest text-center focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            disabled={registerMutation.isPending}
            required
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            6-digit code displayed on monitor screen
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
            placeholder="e.g., Reception Monitor, Meeting Room Display"
            maxLength={200}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            disabled={registerMutation.isPending}
          >
            <option value="browser">Web Browser</option>
            <option value="chrome">Chrome</option>
            <option value="firefox">Firefox</option>
            <option value="edge">Edge</option>
            <option value="safari">Safari</option>
          </select>
        </div>

        {/* Info Box */}
        <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-3">
          <p className="text-sm text-purple-700 dark:text-purple-300">
            <strong>How it works:</strong> Enter the 6-digit activation code shown on the monitor screen. The device will be automatically assigned to your organization.
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
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            {registerMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Activating...
              </>
            ) : (
              <>
                <Monitor className="w-4 h-4" />
                Activate Monitor
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
