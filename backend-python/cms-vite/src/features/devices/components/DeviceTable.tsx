/**
 * Device Table
 * Table component for displaying devices
 */

import { useTranslation } from 'react-i18next';
import { Monitor, Tv, Trash2, Edit } from 'lucide-react';
import { DeviceStatusBadge } from './DeviceStatusBadge';
import type { Device } from '../types/device';

interface DeviceTableProps {
  devices: Device[];
  onEdit?: (device: Device) => void;
  onDelete?: (device: Device) => void;
}

export function DeviceTable({ devices, onEdit, onDelete }: DeviceTableProps) {
  const { t } = useTranslation();

  if (devices.length === 0) {
    return (
      <div className="text-center py-12">
        <Monitor className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          {t('devices.noDevices')}
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {t('devices.type')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {t('devices.name')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {t('devices.room')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {t('devices.status')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {t('devices.lastSeen')}
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {t('common.actions')}
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {devices.map((device) => (
            <tr key={device.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
              {/* Type */}
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  {device.device_type === 'tv' ? (
                    <Tv className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                  ) : (
                    <Monitor className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                  )}
                  <span className="ml-2 text-sm text-gray-900 dark:text-white capitalize">
                    {device.device_type}
                  </span>
                </div>
              </td>

              {/* Name */}
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {device.device_name}
                </div>
                {device.platform && (
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {device.platform}
                  </div>
                )}
              </td>

              {/* Room */}
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900 dark:text-white">
                  {device.room_number || '-'}
                </div>
              </td>

              {/* Status */}
              <td className="px-6 py-4 whitespace-nowrap">
                <DeviceStatusBadge status={device.status} isOnline={device.is_online} />
              </td>

              {/* Last Seen */}
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                {device.last_seen
                  ? new Date(device.last_seen).toLocaleString()
                  : t('devices.never')}
              </td>

              {/* Actions */}
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div className="flex items-center justify-end gap-2">
                  {onEdit && (
                    <button
                      onClick={() => onEdit(device)}
                      className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                      title={t('common.edit')}
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => onDelete(device)}
                      className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                      title={t('common.delete')}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
