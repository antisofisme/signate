/**
 * Device Status Badge
 * Visual indicator for device status and online state
 */

import { useTranslation } from 'react-i18next';
import type { DeviceStatus } from '../types/device';

interface DeviceStatusBadgeProps {
  status: DeviceStatus;
  isOnline: boolean;
}

export function DeviceStatusBadge({ status, isOnline }: DeviceStatusBadgeProps) {
  const { t } = useTranslation();

  // Status badge
  const statusColors: Record<DeviceStatus, string> = {
    active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  };

  // Online indicator (only for active devices)
  const onlineColor = isOnline
    ? 'bg-green-500'
    : 'bg-gray-400';

  return (
    <div className="flex items-center gap-2">
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[status]}`}>
        {t(`devices.status.${status}`)}
      </span>
      
      {status === 'active' && (
        <div className="flex items-center gap-1">
          <span className={`h-2 w-2 rounded-full ${onlineColor}`} />
          <span className="text-xs text-gray-600 dark:text-gray-400">
            {isOnline ? t('devices.online') : t('devices.offline')}
          </span>
        </div>
      )}
    </div>
  );
}
