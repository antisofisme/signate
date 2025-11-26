/**
 * Monitor Register Modal Component
 *
 * Modal for registering Monitor devices (browser-based)
 * Uses centralized Modal component
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Monitor, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
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
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    activation_code: '',
    device_name: '',
    platform: 'browser',
  });
  const [error, setError] = useState<string | null>(null);

  const registerMutation = useMonitorRegister();

  // Helper to format error messages
  const formatErrorMessage = (err: any): string => {
    // Network errors
    if (!err.response) {
      return t('devices.modals.errors.networkError');
    }

    // HTTP status-based messages
    const status = err.response?.status;
    if (status === 404) {
      return t('devices.modals.errors.codeNotFound');
    }
    if (status === 400) {
      // Bad request - check for specific error message
      if (typeof err?.response?.data?.detail === 'string') {
        const detail = err.response.data.detail;

        // Check for common error patterns
        if (detail.toLowerCase().includes('expired')) {
          return t('devices.modals.errors.codeExpired');
        }
        if (detail.toLowerCase().includes('invalid')) {
          return t('devices.modals.errors.invalidCode');
        }
        if (detail.toLowerCase().includes('already')) {
          return t('devices.modals.errors.alreadyActivated');
        }

        return detail;
      }
    }

    // Validation errors (FastAPI format)
    if (Array.isArray(err?.response?.data?.detail)) {
      return err.response.data.detail
        .map((e: any) => `${e.loc?.join('.') || 'Field'}: ${e.msg}`)
        .join(', ');
    }

    // Generic detail message
    if (typeof err?.response?.data?.detail === 'string') {
      return err.response.data.detail;
    }

    // Fallback
    return t('devices.modals.errors.activationFailed', { status: status || 'unknown' });
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

    // Validation
    if (!formData.activation_code || formData.activation_code.length !== 6) {
      setError(t('devices.modals.errors.codeRequired'));
      return;
    }

    if (!formData.device_name.trim()) {
      setError(t('devices.modals.errors.nameRequired'));
      return;
    }

    // Log for debugging
    console.log('[MonitorRegisterModal] Submitting registration:', {
      unique_code: formData.activation_code,
      device_name: formData.device_name.trim(),
    });

    try {
      const result = await registerMutation.mutateAsync({
        unique_code: formData.activation_code,
        device_name: formData.device_name.trim(),
      });

      console.log('[MonitorRegisterModal] Registration successful:', result);

      // Only close modal and reset form if successful
      resetForm();
      if (onSuccess) {
        onSuccess();
      }
      onClose();
    } catch (err: any) {
      // Enhanced error logging
      console.error('[MonitorRegisterModal] Registration failed:', err);
      console.error('[MonitorRegisterModal] Error response:', err?.response);
      console.error('[MonitorRegisterModal] Error data:', err?.response?.data);

      const errorMessage = formatErrorMessage(err);
      console.error('[MonitorRegisterModal] Formatted error:', errorMessage);

      setError(errorMessage);

      // Show toast as additional feedback
      toast.error(errorMessage);

      // DO NOT close modal on error - let user see the error and retry
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
            {t('devices.modals.registerMonitor')}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t('devices.modals.browserBasedDisplay')}
          </p>
        </div>
      </div>
    </div>
  );

  // Footer
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={handleClose}
          disabled={registerMutation.isPending}
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 transition-colors"
        >
          {t('devices.buttons.cancel')}
        </button>
        <button
          type="submit"
          form="monitor-register-form"
          disabled={registerMutation.isPending}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
        >
          {registerMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {t('devices.modals.registering')}
            </>
          ) : (
            <>
              <Monitor className="w-4 h-4" />
              {t('devices.modals.activateMonitor')}
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
      maxWidth="md"
      customHeader={customHeader}
      footer={footer}
    >
      {/* Form */}
      <form id="monitor-register-form" onSubmit={handleSubmit} className="p-6 space-y-4">
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Activation Code */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('devices.modals.activationCodeLabel')} <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.activation_code}
            onChange={(e) => {
              const value = e.target.value.replace(/\D/g, '').slice(0, 6);
              setFormData((prev) => ({ ...prev, activation_code: value }));
              setError(null);
            }}
            placeholder={t('devices.placeholders.enterCode')}
            maxLength={6}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-lg tracking-widest text-center focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            disabled={registerMutation.isPending}
            required
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {t('devices.modals.monitorCodeHelp')}
          </p>
        </div>

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
            placeholder={t('devices.placeholders.monitorName')}
            maxLength={200}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            disabled={registerMutation.isPending}
            required
          />
        </div>

        {/* Platform */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('devices.modals.platform')}
          </label>
          <select
            value={formData.platform}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, platform: e.target.value }))
            }
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            disabled={registerMutation.isPending}
          >
            <option value="browser">{t('devices.modals.platformWebBrowser')}</option>
            <option value="chrome">{t('devices.modals.platformChrome')}</option>
            <option value="firefox">{t('devices.modals.platformFirefox')}</option>
            <option value="edge">{t('devices.modals.platformEdge')}</option>
            <option value="safari">{t('devices.modals.platformSafari')}</option>
          </select>
        </div>

        {/* Info Box */}
        <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-3">
          <p className="text-sm text-purple-700 dark:text-purple-300">
            <strong>{t('devices.modals.howItWorks')}</strong> {t('devices.modals.howItWorksMonitor')}
          </p>
        </div>
      </form>
    </Modal>
  );
}
