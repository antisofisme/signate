/**
 * Devices Page
 * Main page for device management
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, RefreshCw, Filter } from 'lucide-react';
import { useAuthStore } from '@/lib/stores/authStore';
import { useDevices } from '@/features/devices/hooks/useDevices';
import { DeviceTable, ActivateDeviceModal } from '@/features/devices/components';
import type { DeviceFilters } from '@/features/devices/types/device';

export default function DevicesPage() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [isActivateModalOpen, setIsActivateModalOpen] = useState(false);
  const [filters, setFilters] = useState<DeviceFilters>({});

  // Fetch devices
  const { data, isLoading, isError, error, refetch } = useDevices(
    user?.organization_id || 0,
    filters
  );

  const handleEdit = (device: any) => {
    // TODO: Implement edit device
    console.log('Edit device:', device);
  };

  const handleDelete = (device: any) => {
    // TODO: Implement delete device
    if (confirm(t('devices.confirmDelete'))) {
      console.log('Delete device:', device);
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t('navigation.devices')}
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            {t('devices.subtitle')}
          </p>
        </div>
        <button
          onClick={() => setIsActivateModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          {t('devices.activateDevice')}
        </button>
      </div>

      {/* Stats */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {t('devices.totalDevices')}
            </div>
            <div className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
              {data.total}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {t('devices.onlineDevices')}
            </div>
            <div className="mt-2 text-3xl font-bold text-green-600 dark:text-green-400">
              {data.online}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {t('devices.offlineDevices')}
            </div>
            <div className="mt-2 text-3xl font-bold text-gray-600 dark:text-gray-400">
              {data.total - data.online}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {t('common.filters')}:
            </span>
          </div>

          <select
            value={filters.status || ''}
            onChange={(e) => setFilters({ ...filters, status: e.target.value as any || undefined })}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            <option value="">{t('devices.allStatuses')}</option>
            <option value="active">{t('devices.status.active')}</option>
            <option value="pending">{t('devices.status.pending')}</option>
            <option value="inactive">{t('devices.status.inactive')}</option>
          </select>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={filters.online_only || false}
              onChange={(e) => setFilters({ ...filters, online_only: e.target.checked || undefined })}
              className="rounded border-gray-300 dark:border-gray-600"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {t('devices.onlineOnly')}
            </span>
          </label>

          <button
            onClick={() => refetch()}
            className="ml-auto inline-flex items-center gap-2 px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700 dark:text-white"
          >
            <RefreshCw className="h-4 w-4" />
            {t('common.refresh')}
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        {isLoading ? (
          <div className="p-12 text-center">
            <div className="animate-spin inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              {t('common.loading')}
            </p>
          </div>
        ) : isError ? (
          <div className="p-12 text-center">
            <p className="text-red-600 dark:text-red-400">
              {error instanceof Error ? error.message : t('devices.loadError')}
            </p>
          </div>
        ) : data ? (
          <DeviceTable
            devices={data.devices}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ) : null}
      </div>

      {/* Activate Modal */}
      <ActivateDeviceModal
        isOpen={isActivateModalOpen}
        onClose={() => setIsActivateModalOpen(false)}
      />
    </div>
  );
}
