/**
 * PMS Configuration Page
 *
 * LAYER 1: PRESENTATION
 * Main page for PMS integration - orchestration only
 */

import { Building2, Save, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PageHeader, StatsCard, Button, AccessDenied, PageSkeleton } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { PMSProviderSelect } from '../components/PMSProviderSelect';
import { PMSConnectionForm } from '../components/PMSConnectionForm';
import { PMSSyncStatus } from '../components/PMSSyncStatus';
import { RoomMappingTable } from '../components/RoomMappingTable';
import { usePMSConfigState } from '../hooks/usePMSConfigState';
import { Users, DoorOpen } from 'lucide-react';

export default function PMSConfigPage() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canView, isLoading: isCheckingPermission } = useCanPerformAction('settings', 'read');
  const { hasPermission: canUpdate } = useCanPerformAction('settings', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('settings', 'delete');

  // Show loading state while checking permissions
  if (isCheckingPermission) {
    return <PageSkeleton />;
  }

  // Show access denied if no read permission
  if (!canView) {
    return <AccessDenied />;
  }

  const {
    config,
    stats,
    devices,
    isLoading,
    activeTab,
    provider,
    connectionConfig,
    syncConfig,
    setActiveTab,
    setProvider,
    setConnectionConfig,
    setSyncConfig,
    handleSave,
    handleDelete,
    isSaving,
    isDeleting,
  } = usePMSConfigState();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">{t('pms.loading', 'Loading PMS configuration...')}</div>
      </div>
    );
  }

  return (
    <>
      <PageHeader
        title={t('pms.title', 'PMS Integration')}
        description={t('pms.subtitle', 'Configure Property Management System integration for hotel signage')}
      />

      <div className="space-y-6">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatsCard icon={Users} iconColor="blue" value={stats.current_guests} label={t('pms.stats.currentGuests', 'Current Guests')} />
            <StatsCard icon={DoorOpen} iconColor="green" value={stats.occupied_rooms} label={t('pms.stats.occupiedRooms', 'Occupied Rooms')} />
            <StatsCard icon={DoorOpen} iconColor="gray" value={stats.vacant_rooms} label={t('pms.stats.vacantRooms', 'Vacant Rooms')} />
            <StatsCard
              icon={Building2}
              iconColor="purple"
              value={`${stats.mapped_devices}/${stats.total_rooms}`}
              label={t('pms.stats.mappedDevices', 'Mapped Devices')}
            />
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('config')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'config'
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {t('pms.tabs.config', 'Configuration')}
          </button>
          <button
            onClick={() => setActiveTab('rooms')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'rooms'
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {t('pms.tabs.rooms', 'Room Mapping')}
          </button>
        </div>

        {/* Config Tab */}
        {activeTab === 'config' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">{t('pms.sections.provider', 'PMS Provider')}</h2>
            <PMSProviderSelect value={provider} onChange={setProvider} />
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">{t('pms.sections.connection', 'Connection Settings')}</h2>
            <PMSConnectionForm config={connectionConfig} onChange={setConnectionConfig} provider={provider} />
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">{t('pms.sections.sync', 'Sync Configuration')}</h2>
            <PMSSyncStatus />
          </div>

          <div className="flex justify-end gap-3">
            {config && canDelete && (
              <Button
                variant="outline"
                onClick={handleDelete}
                disabled={isDeleting}
                loading={isDeleting}
                leftIcon={<Trash2 className="w-4 h-4" />}
                className="border-red-600 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                {t('pms.buttons.deleteConfig', 'Delete Configuration')}
              </Button>
            )}
            {canUpdate && (
              <Button
                onClick={handleSave}
                disabled={isSaving}
                loading={isSaving}
                leftIcon={<Save className="w-4 h-4" />}
              >
                {config ? t('pms.buttons.updateConfig', 'Update Configuration') : t('pms.buttons.createConfig', 'Create Configuration')}
              </Button>
            )}
          </div>
        </div>
        )}

        {/* Room Mapping Tab */}
        {activeTab === 'rooms' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">{t('pms.sections.roomMapping', 'Room to Device Mapping')}</h2>
            <RoomMappingTable availableDevices={devices || []} />
          </div>
        )}
      </div>
    </>
  );
}
