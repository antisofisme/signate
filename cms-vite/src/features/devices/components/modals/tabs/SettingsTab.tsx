/**
 * Settings Tab - Device Management Modal
 *
 * Device configuration and settings:
 * - Basic settings (name, rotation, volume, room)
 * - Advanced settings
 * - Danger zone (deactivate, delete)
 */

import { useEffect } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Save, Loader2, AlertTriangle } from 'lucide-react';
import type { Device } from '../../../types/device';
import { useUpdateDevice } from '../../../hooks/useDevices';
import { FormInput, FormSelect, FormSwitch, InlineError } from '@/shared/components';

// Zod validation schema
const deviceSettingsSchema = z.object({
  device_name: z
    .string()
    .min(1, 'Device name is required')
    .max(200, 'Device name must be less than 200 characters')
    .trim(),
  rotation: z.string().refine((val) => ['0', '90', '180', '270'].includes(val), {
    message: 'Rotation must be 0, 90, 180, or 270 degrees',
  }),
  volume_enabled: z.boolean(),
  room_number: z.string().max(50, 'Room number must be less than 50 characters').optional(),
});

type DeviceSettingsForm = z.infer<typeof deviceSettingsSchema>;

interface SettingsTabProps {
  device: Device;
  onSuccess?: () => void;
}

export function SettingsTab({ device, onSuccess }: SettingsTabProps) {
  const updateMutation = useUpdateDevice();

  // Initialize React Hook Form with Zod resolver
  const methods = useForm<DeviceSettingsForm>({
    resolver: zodResolver(deviceSettingsSchema),
    defaultValues: {
      device_name: device.device_name,
      rotation: String(device.rotation || 0),
      volume_enabled: device.is_volume_enabled !== false,
      room_number: device.room_number || '',
    },
  });

  const { handleSubmit, reset } = methods;

  // Reset form when device changes
  useEffect(() => {
    reset({
      device_name: device.device_name,
      rotation: String(device.rotation || 0),
      volume_enabled: device.is_volume_enabled !== false,
      room_number: device.room_number || '',
    });
  }, [device, reset]);

  // Handle submit
  const onSubmit = async (data: DeviceSettingsForm) => {
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
    } catch (err) {
      // Error is handled by mutation with toast
    }
  };

  const rotationOptions = [
    { value: '0', label: '0° (Normal)' },
    { value: '90', label: '90° (Clockwise)' },
    { value: '180', label: '180° (Upside Down)' },
    { value: '270', label: '270° (Counter-Clockwise)' },
  ];

  return (
    <div className="p-6">
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Settings */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
              Basic Settings
            </h3>

            <div className="space-y-4">
              {/* Device Name */}
              <FormInput
                name="device_name"
                label="Device Name"
                placeholder="e.g., Lobby TV 1, Room 101 Display"
                required
                disabled={updateMutation.isPending}
              />

              {/* Rotation */}
              <FormSelect
                name="rotation"
                label="Screen Rotation"
                options={rotationOptions}
                description="Adjust screen orientation for portrait/landscape displays"
                disabled={updateMutation.isPending}
              />

              {/* Volume Enabled */}
              <FormSwitch
                name="volume_enabled"
                label="Enable Audio/Volume"
                description="Allow audio playback for video content"
                disabled={updateMutation.isPending}
              />

              {/* Room Number */}
              <FormInput
                name="room_number"
                label="Room Number (Optional)"
                placeholder="e.g., 101, A-205, Lobby"
                description="For hotel/office deployments"
                disabled={updateMutation.isPending}
              />
            </div>
          </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={updateMutation.isPending}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
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

        {/* Info Box */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <strong>Note:</strong> Changes will take effect immediately on the device. The device
            may need to refresh to apply rotation changes.
          </p>
        </div>

        {/* Danger Zone */}
        <div className="border border-red-200 dark:border-red-800 rounded-lg p-4 bg-red-50 dark:bg-red-900/10">
          <h3 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Danger Zone
          </h3>
          <p className="text-sm text-red-600 dark:text-red-400 mb-3">
            These actions are irreversible. Please be careful.
          </p>
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => alert('Deactivate device functionality coming soon')}
              className="w-full px-4 py-2 border border-red-300 dark:border-red-700 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 transition-colors text-sm font-medium"
            >
              Deactivate Device
            </button>
            <button
              type="button"
              onClick={() => alert('Delete device functionality coming soon')}
              className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
            >
              Delete Device
            </button>
          </div>
        </div>
        </form>
      </FormProvider>
    </div>
  );
}
