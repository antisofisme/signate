/**
 * Monitor Register Modal Component
 *
 * Modal for registering Monitor devices (browser-based)
 * Uses centralized Modal component + React Hook Form
 */

import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Monitor } from 'lucide-react';
import { toast } from 'sonner';
import { Modal, Button } from '@/shared/components';
import { FormInput, FormSelect, ActivationCodeInput } from '@/shared/components/form';
import { useMonitorRegister } from '../../hooks/useDevices';

// Form validation schema
const monitorRegisterSchema = z.object({
  activation_code: z
    .string()
    .length(6, 'Kode aktivasi harus 6 digit')
    .regex(/^\d+$/, 'Kode aktivasi hanya boleh angka'),
  device_name: z.string().min(1, 'Nama device harus diisi').max(200),
  platform: z.string(),
});

type MonitorRegisterFormData = z.infer<typeof monitorRegisterSchema>;

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
  const registerMutation = useMonitorRegister();

  const methods = useForm<MonitorRegisterFormData>({
    resolver: zodResolver(monitorRegisterSchema),
    defaultValues: {
      activation_code: '',
      device_name: '',
      platform: 'browser',
    },
  });

  const {
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = methods;

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      reset({
        activation_code: '',
        device_name: '',
        platform: 'browser',
      });
    }
  }, [isOpen, reset]);

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

  // Handle close
  const handleClose = () => {
    if (!registerMutation.isPending) {
      reset();
      onClose();
    }
  };

  // Handle submit
  const onSubmit = async (data: MonitorRegisterFormData) => {
    // Log for debugging
    console.log('[MonitorRegisterModal] Submitting registration:', {
      unique_code: data.activation_code,
      device_name: data.device_name.trim(),
    });

    try {
      const result = await registerMutation.mutateAsync({
        unique_code: data.activation_code,
        device_name: data.device_name.trim(),
      });

      console.log('[MonitorRegisterModal] Registration successful:', result);

      // Only close modal and reset form if successful
      reset();
      onSuccess?.();
      onClose();
    } catch (err: any) {
      // Enhanced error logging
      console.error('[MonitorRegisterModal] Registration failed:', err);
      console.error('[MonitorRegisterModal] Error response:', err?.response);
      console.error('[MonitorRegisterModal] Error data:', err?.response?.data);

      const errorMessage = formatErrorMessage(err);
      console.error('[MonitorRegisterModal] Formatted error:', errorMessage);

      setError('root', { message: errorMessage });

      // Show toast as additional feedback
      toast.error(errorMessage);

      // DO NOT close modal on error - let user see the error and retry
    }
  };

  // Platform options
  const platformOptions = [
    { value: 'browser', label: t('devices.modals.platformWebBrowser') },
    { value: 'chrome', label: t('devices.modals.platformChrome') },
    { value: 'firefox', label: t('devices.modals.platformFirefox') },
    { value: 'edge', label: t('devices.modals.platformEdge') },
    { value: 'safari', label: t('devices.modals.platformSafari') },
  ];

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
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        type="button"
        variant="secondary"
        onClick={handleClose}
        disabled={registerMutation.isPending}
      >
        {t('devices.buttons.cancel')}
      </Button>
      <Button
        type="submit"
        form="monitor-register-form"
        disabled={registerMutation.isPending}
        loading={registerMutation.isPending}
        leftIcon={<Monitor className="w-4 h-4" />}
        className="bg-purple-600 hover:bg-purple-700"
      >
        {registerMutation.isPending ? t('devices.modals.registering') : t('devices.modals.activateMonitor')}
      </Button>
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
      <FormProvider {...methods}>
        <form id="monitor-register-form" onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          {/* Root Error Message */}
          {errors.root && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <p className="text-sm text-red-600 dark:text-red-400">{errors.root.message}</p>
            </div>
          )}

          {/* Activation Code */}
          <ActivationCodeInput
            name="activation_code"
            label={t('devices.modals.activationCodeLabel')}
            placeholder={t('devices.placeholders.enterCode')}
            description={t('devices.modals.monitorCodeHelp')}
            required
            disabled={registerMutation.isPending}
          />

          {/* Device Name */}
          <FormInput
            name="device_name"
            label={t('devices.modals.deviceNameLabel')}
            placeholder={t('devices.placeholders.monitorName')}
            required
            disabled={registerMutation.isPending}
            maxLength={200}
          />

          {/* Platform */}
          <FormSelect
            name="platform"
            label={t('devices.modals.platform')}
            options={platformOptions}
            disabled={registerMutation.isPending}
          />

          {/* Info Box */}
          <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-3">
            <p className="text-sm text-purple-700 dark:text-purple-300">
              <strong>{t('devices.modals.howItWorks')}</strong> {t('devices.modals.howItWorksMonitor')}
            </p>
          </div>
        </form>
      </FormProvider>
    </Modal>
  );
}
