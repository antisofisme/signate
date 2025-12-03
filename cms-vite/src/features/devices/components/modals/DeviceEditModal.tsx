/**
 * Device Edit Modal Component
 *
 * Edit device settings and configuration
 * Uses centralized Modal component + React Hook Form
 */

import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Save } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { FormInput, FormSelect, FormCheckbox } from '@/shared/components/form';
import { useUpdateDevice } from '../../hooks/useDevices';
import type { Device } from '../../types/device';

// Form validation schema
const deviceEditSchema = z.object({
  device_name: z.string().min(1, 'Nama device harus diisi').max(200),
  rotation: z.string(), // stored as string, converted to number on submit
  volume_enabled: z.boolean(),
  room_number: z.string().max(50).optional(),
});

type DeviceEditFormData = z.infer<typeof deviceEditSchema>;

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
  const updateMutation = useUpdateDevice();

  const methods = useForm<DeviceEditFormData>({
    resolver: zodResolver(deviceEditSchema),
    defaultValues: {
      device_name: '',
      rotation: '0',
      volume_enabled: true,
      room_number: '',
    },
  });

  const {
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = methods;

  // Initialize form when device changes
  useEffect(() => {
    if (device && isOpen) {
      reset({
        device_name: device.device_name,
        rotation: String(device.rotation || 0),
        volume_enabled: device.is_volume_enabled !== false,
        room_number: device.room_number || '',
      });
    }
  }, [device, isOpen, reset]);

  if (!device) return null;

  // Handle close
  const handleClose = () => {
    if (!updateMutation.isPending) {
      reset();
      onClose();
    }
  };

  // Handle submit
  const onSubmit = async (data: DeviceEditFormData) => {
    try {
      await updateMutation.mutateAsync({
        id: device.id,
        data: {
          device_name: data.device_name.trim(),
          rotation: parseInt(data.rotation, 10),
          is_volume_enabled: data.volume_enabled,
          room_number: data.room_number?.trim() || undefined,
        },
      });

      onSuccess?.();
      handleClose();
    } catch (err: any) {
      setError('root', {
        message: err?.response?.data?.detail || t('devices.modals.errors.updateFailed'),
      });
    }
  };

  // Rotation options
  const rotationOptions = [
    { value: '0', label: t('devices.modals.rotation0') },
    { value: '90', label: t('devices.modals.rotation90') },
    { value: '180', label: t('devices.modals.rotation180') },
    { value: '270', label: t('devices.modals.rotation270') },
  ];

  // Footer
  const footer = (
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        type="button"
        variant="secondary"
        onClick={handleClose}
        disabled={updateMutation.isPending}
      >
        {t('devices.buttons.cancel')}
      </Button>
      <Button
        type="submit"
        form="device-edit-form"
        disabled={updateMutation.isPending}
        loading={updateMutation.isPending}
        leftIcon={<Save className="w-4 h-4" />}
      >
        {updateMutation.isPending ? t('devices.modals.saving') : t('devices.modals.saveChanges')}
      </Button>
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
      <FormProvider {...methods}>
        <form id="device-edit-form" onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          {/* Root Error Message */}
          {errors.root && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <p className="text-sm text-red-600 dark:text-red-400">{errors.root.message}</p>
            </div>
          )}

          {/* Device Name */}
          <FormInput
            name="device_name"
            label={t('devices.modals.deviceNameLabel')}
            placeholder={t('devices.placeholders.deviceName')}
            required
            disabled={updateMutation.isPending}
            maxLength={200}
          />

          {/* Rotation */}
          <FormSelect
            name="rotation"
            label={t('devices.modals.screenRotation')}
            options={rotationOptions}
            description={t('devices.modals.rotationHelp')}
            disabled={updateMutation.isPending}
          />

          {/* Volume Enabled */}
          <FormCheckbox
            name="volume_enabled"
            label={t('devices.modals.enableAudio')}
            description={t('devices.modals.audioHelp')}
            disabled={updateMutation.isPending}
          />

          {/* Room Number (Optional) */}
          <FormInput
            name="room_number"
            label={t('devices.modals.roomNumberOptional')}
            placeholder={t('devices.placeholders.roomNumber')}
            description={t('devices.modals.roomHelp')}
            disabled={updateMutation.isPending}
            maxLength={50}
          />

          {/* Info Box */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              <strong>{t('devices.modals.changesNote')}</strong> {t('devices.modals.changesEffect')}
            </p>
          </div>
        </form>
      </FormProvider>
    </Modal>
  );
}
