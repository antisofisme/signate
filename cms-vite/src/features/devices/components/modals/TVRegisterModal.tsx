/**
 * TV Register Modal Component
 *
 * Modal for registering TV devices (WebOS/native apps)
 * Uses centralized Modal component + React Hook Form
 */

import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Tv, Loader2 } from 'lucide-react';
import { Modal } from '@/shared/components';
import { FormInput, ActivationCodeInput } from '@/shared/components/form';
import { useTVRegister } from '../../hooks/useDevices';
import type { Device } from '../../types/device';

// Form validation schema
const tvRegisterSchema = z.object({
  activation_code: z
    .string()
    .length(6, 'Kode aktivasi harus 6 digit')
    .regex(/^\d+$/, 'Kode aktivasi hanya boleh angka'),
  device_name: z.string().min(1, 'Nama device harus diisi').max(200),
});

type TVRegisterFormData = z.infer<typeof tvRegisterSchema>;

interface TVRegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (device: Device) => void;
}

export function TVRegisterModal({ isOpen, onClose, onSuccess }: TVRegisterModalProps) {
  const { t } = useTranslation();
  const registerMutation = useTVRegister();

  const methods = useForm<TVRegisterFormData>({
    resolver: zodResolver(tvRegisterSchema),
    defaultValues: {
      activation_code: '',
      device_name: '',
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
      });
    }
  }, [isOpen, reset]);

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
    return t('devices.modals.errors.failedToActivate');
  };

  // Handle close
  const handleClose = () => {
    if (!registerMutation.isPending) {
      reset();
      onClose();
    }
  };

  // Handle submit
  const onSubmit = async (data: TVRegisterFormData) => {
    try {
      const device = await registerMutation.mutateAsync({
        unique_code: data.activation_code,
        device_name: data.device_name.trim(),
      });

      reset();
      onSuccess?.(device);
      onClose();
    } catch (err: any) {
      setError('root', {
        message: formatErrorMessage(err),
      });
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
            {t('devices.modals.registerTV')}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t('devices.modals.webosOrNative')}
          </p>
        </div>
      </div>
    </div>
  );

  const footerContent = (
    <div className="flex justify-end gap-3 pt-4 px-6 pb-6">
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
        form="tv-register-form"
        disabled={registerMutation.isPending}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
      >
        {registerMutation.isPending ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            {t('devices.modals.registering')}
          </>
        ) : (
          <>
            <Tv className="w-4 h-4" />
            {t('devices.modals.register')}
          </>
        )}
      </button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      maxWidth="md"
      customHeader={customHeader}
      footer={footerContent}
    >
      <FormProvider {...methods}>
        <form id="tv-register-form" onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
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
            description={t('devices.modals.codeHelp')}
            required
            disabled={registerMutation.isPending}
          />

          {/* Device Name */}
          <FormInput
            name="device_name"
            label={t('devices.modals.deviceNameLabel')}
            placeholder={t('devices.placeholders.deviceName')}
            required
            disabled={registerMutation.isPending}
            maxLength={200}
          />

          {/* Info Box */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              <strong>{t('devices.modals.howItWorks')}</strong> {t('devices.modals.howItWorksDesc')}
            </p>
          </div>
        </form>
      </FormProvider>
    </Modal>
  );
}
