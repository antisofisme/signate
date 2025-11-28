/**
 * Pending Device Card Component
 *
 * Display pending devices awaiting activation with quick approve action
 * Includes quota checks before activation
 */

import { CheckCircle, Monitor, Tv, AlertTriangle } from 'lucide-react';
import { useActivateDevice } from '../hooks/useDevices';
import { useCheckDeviceQuota } from '@/features/organizations/hooks/useOrganizationQuota';
import { useAuthStore } from '@/lib/stores/authStore';
import type { Device } from '../types/device';
import { toast } from 'sonner';

interface PendingDeviceCardProps {
  device: Device;
  onActivated?: () => void;
}

export function PendingDeviceCard({ device, onActivated }: PendingDeviceCardProps) {
  const { user } = useAuthStore();
  const activateDevice = useActivateDevice();

  // Check device quota before allowing activation
  const { data: quotaCheck, isLoading: quotaLoading } = useCheckDeviceQuota(user?.organization_id);

  const handleActivate = async () => {
    if (!device.unique_code) return;

    // Check quota before activating
    if (quotaCheck && !quotaCheck.allowed) {
      toast.error('Device Quota Exceeded', {
        description: quotaCheck.reason || 'Cannot activate more devices. Please upgrade your plan or remove inactive devices.',
      });
      return;
    }

    try {
      await activateDevice.mutateAsync({
        unique_code: device.unique_code,
      });
      onActivated?.();
    } catch (error) {
      // Error already handled by mutation
    }
  };

  const DeviceIcon = device.device_type === 'tv' ? Tv : Monitor;

  // Check if quota is exceeded
  const isQuotaExceeded = quotaCheck && !quotaCheck.allowed;

  return (
    <div
      className={`border rounded-lg p-4 transition-all ${
        isQuotaExceeded
          ? 'bg-orange-50 border-orange-200 dark:bg-orange-900/10 dark:border-orange-800'
          : 'bg-blue-50 border-blue-200 dark:bg-blue-900/10 dark:border-blue-800 hover:shadow-md'
      }`}
    >
      <div className="flex items-start justify-between">
        {/* Device Info */}
        <div className="flex items-start gap-3 flex-1">
          <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <DeviceIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>

          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {device.device_name}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {device.device_type === 'tv' ? 'TV Device' : 'Monitor Device'}
              {device.platform && ` • ${device.platform}`}
            </p>

            {/* Activation Code */}
            <div className="mt-3 flex items-center gap-2">
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Activation Code:
              </span>
              <code className="px-3 py-1 rounded font-mono text-lg font-bold tracking-wider bg-white border-2 border-blue-300 text-blue-700 dark:bg-gray-700 dark:border-blue-600 dark:text-blue-300">
                {device.unique_code}
              </code>
            </div>

            {/* IP Address */}
            {device.ip_address && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                IP: {device.ip_address}
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2 ml-4">
          {!isQuotaExceeded && (
            <button
              onClick={handleActivate}
              disabled={activateDevice.isPending || quotaLoading}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              {activateDevice.isPending || quotaLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  {quotaLoading ? 'Checking...' : 'Activating...'}
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Activate
                </>
              )}
            </button>
          )}

          {isQuotaExceeded && (
            <div className="flex items-center gap-2 px-4 py-2 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded-lg text-sm font-medium">
              <AlertTriangle className="w-4 h-4" />
              Quota Exceeded
            </div>
          )}
        </div>
      </div>

      {/* Info Message */}
      {!isQuotaExceeded && (
        <div className="mt-4 bg-white dark:bg-gray-700 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
          <p className="text-xs text-gray-600 dark:text-gray-400">
            <strong>Next steps:</strong> Click "Activate" to approve this device.
            The device will receive activation confirmation and start operating.
          </p>
        </div>
      )}

      {/* Quota Exceeded Warning */}
      {isQuotaExceeded && (
        <div className="mt-4 bg-orange-50 dark:bg-orange-900/10 border border-orange-200 dark:border-orange-700 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-semibold text-orange-800 dark:text-orange-300">
                Device Quota Limit Reached
              </p>
              <p className="text-xs text-orange-700 dark:text-orange-400 mt-1">
                {quotaCheck?.reason || 'Your organization has reached the maximum number of devices.'}
                {quotaCheck && (
                  <span className="block mt-1">
                    Current: {quotaCheck.current} / {quotaCheck.max} devices
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
