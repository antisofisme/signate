/**
 * Device Table Component
 *
 * LAYER 1: PRESENTATION
 * Device management table with filters and actions
 *
 * PERFORMANCE: Modal components are lazy loaded to reduce initial bundle size
 * by ~100 KB (modals are loaded on demand when user clicks action buttons)
 */

import { useState, useCallback, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Monitor,
  Tv,
  Trash2,
  Loader2,
  Edit,
  Filter,
  X,
  Circle,
  Plus,
  Eye,
  Terminal,
  Tag,
  FileText,
  List,
  Wifi,
  Play,
  Activity,
  RefreshCw,
} from 'lucide-react';
import {
  useDeviceList,
  useDeleteDevice,
  useUpdateDevice,
} from '../hooks/useDevices';
import type { Device, DeviceStatus, DeviceType } from '../types/device';
import { toast } from 'sonner';
import { PendingDeviceCard } from './PendingDeviceCard';
import {
  TableSkeleton,
  EmptyState,
  ErrorDisplay,
  ConfirmDialog,
} from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';

// Lazy load modal components for better initial page load
const TVRegisterModal = lazy(() =>
  import('./modals/TVRegisterModal').then((m) => ({ default: m.TVRegisterModal }))
);
const MonitorRegisterModal = lazy(() =>
  import('./modals/MonitorRegisterModal').then((m) => ({ default: m.MonitorRegisterModal }))
);
const ActivationCodeModal = lazy(() =>
  import('./modals/ActivationCodeModal').then((m) => ({ default: m.ActivationCodeModal }))
);
const DeviceManagementModal = lazy(() =>
  import('./modals/DeviceManagementModal').then((m) => ({ default: m.DeviceManagementModal }))
);
const DeviceSettingsModal = lazy(() =>
  import('./modals/DeviceSettingsModal').then((m) => ({ default: m.DeviceSettingsModal }))
);
const UnifiedContentAssignmentModal = lazy(() =>
  import('./modals/UnifiedContentAssignmentModal').then((m) => ({ default: m.UnifiedContentAssignmentModal }))
);
const DeviceLogsModal = lazy(() =>
  import('./modals/DeviceLogsModal').then((m) => ({ default: m.DeviceLogsModal }))
);

// Types needed for lazy loaded components
import type { DeviceTabId } from './modals/DeviceManagementModal';
import type { ContentAssignmentTabId } from './modals/UnifiedContentAssignmentModal';

// Loading fallback for modals
function ModalLoadingFallback() {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 flex flex-col items-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="mt-2 text-gray-600 dark:text-gray-300">Loading...</span>
      </div>
    </div>
  );
}

export function DeviceTable() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canCreate } = useCanPerformAction('devices', 'create');
  const { hasPermission: canUpdate } = useCanPerformAction('devices', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('devices', 'delete');

  // Scope filter (my_org or unassigned)
  const [scope, setScope] = useState<'my_org' | 'unassigned'>('my_org');

  // Filters
  const [statusFilter, setStatusFilter] = useState<DeviceStatus | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<DeviceType | 'all'>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Modals
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    device: Device | null;
  }>({ isOpen: false, device: null });
  const [tvRegisterModal, setTvRegisterModal] = useState(false);
  const [monitorRegisterModal, setMonitorRegisterModal] = useState(false);
  const [activationCodeModal, setActivationCodeModal] = useState<{
    isOpen: boolean;
    device: Device | null;
  }>({ isOpen: false, device: null });

  // ✨ NEW: Unified Device Management Modal
  const [deviceManagementModal, setDeviceManagementModal] = useState<{
    isOpen: boolean;
    device: Device | null;
    defaultTab: DeviceTabId;
  }>({ isOpen: false, device: null, defaultTab: 'overview' });

  // Content Assignment Modal (separate from DeviceManagementModal)
  const [contentAssignmentModal, setContentAssignmentModal] = useState<{
    isOpen: boolean;
    device: Device | null;
    defaultTab: ContentAssignmentTabId;
  }>({ isOpen: false, device: null, defaultTab: 'direct' });

  // Device Settings Modal (separate from DeviceManagementModal)
  const [settingsModal, setSettingsModal] = useState<{
    isOpen: boolean;
    device: Device | null;
  }>({ isOpen: false, device: null });

  // Device Logs Modal
  const [logsModal, setLogsModal] = useState<{
    isOpen: boolean;
    device: Device | null;
  }>({ isOpen: false, device: null });

  // Build filters for API
  const apiFilters = {
    scope,
    ...(statusFilter !== 'all' && { status: statusFilter }),
    ...(typeFilter !== 'all' && { device_type: typeFilter }),
  };

  // Fetch devices with refetch function for manual refresh
  const { data, isLoading, error, refetch, isFetching } = useDeviceList(apiFilters);
  const devices = data?.items || [];
  const total = data?.total || 0;

  // Manual refresh handler
  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  // Mutations
  const deleteMutation = useDeleteDevice();

  // Delete handler
  const handleDelete = async () => {
    if (!deleteModal.device) return;

    try {
      await deleteMutation.mutateAsync(deleteModal.device.id);
      setDeleteModal({ isOpen: false, device: null });
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Status badge
  const getStatusBadge = (device: Device) => {
    const isOnline = device.last_seen_at
      ? new Date().getTime() - new Date(device.last_seen_at).getTime() < 5 * 60 * 1000
      : false;

    if (device.status === 'pending') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
          <Circle className="w-2 h-2 fill-current" />
          {t('devices.status.pending')}
        </span>
      );
    }

    if (device.status === 'inactive') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
          <Circle className="w-2 h-2 fill-current" />
          {t('devices.status.inactive')}
        </span>
      );
    }

    return isOnline ? (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
        <Circle className="w-2 h-2 fill-current" />
        {t('devices.online')}
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
        <Circle className="w-2 h-2 fill-current" />
        {t('devices.offline')}
      </span>
    );
  };

  // Device type icon
  const getTypeIcon = (type: DeviceType) => {
    return type === 'tv' ? (
      <Tv className="w-4 h-4" />
    ) : (
      <Monitor className="w-4 h-4" />
    );
  };

  return (
    <>
      {/* Scope Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 mb-4">
        <div className="flex border-b border-gray-200 dark:border-gray-700" role="tablist" aria-label={t('devices.tabs.scopeSelection', 'Device scope selection')}>
          <button
            onClick={() => setScope('my_org')}
            role="tab"
            aria-selected={scope === 'my_org'}
            aria-controls="device-table-panel"
            id="tab-my-devices"
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 ${
              scope === 'my_org'
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            {t('devices.tabs.myDevices')}
          </button>
          <button
            onClick={() => setScope('unassigned')}
            role="tab"
            aria-selected={scope === 'unassigned'}
            aria-controls="device-table-panel"
            id="tab-unassigned"
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 ${
              scope === 'unassigned'
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            {t('devices.tabs.unassignedPool')}
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {scope === 'my_org' ? t('devices.tabs.myDevices') : t('devices.tabs.unassignedDevices')}
            </h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {total} {total === 1 ? t('devices.messages.deviceCount') : t('devices.messages.devicesCount')}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Refresh Button */}
            <button
              onClick={handleRefresh}
              disabled={isFetching}
              className="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              title={t('common.refresh', 'Refresh')}
              aria-label={t('common.refresh', 'Refresh device list')}
            >
              <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            </button>

            {/* Register TV Button */}
            {canCreate && (
              <button
                onClick={() => setTvRegisterModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <Tv className="w-4 h-4" />
                {t('devices.buttons.registerTV')}
              </button>
            )}

            {/* Register Monitor Button */}
            {canCreate && (
              <button
                onClick={() => setMonitorRegisterModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <Monitor className="w-4 h-4" />
                {t('devices.buttons.registerMonitor')}
              </button>
            )}

            {/* Filter Button */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                showFilters
                  ? 'bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-700 text-blue-700 dark:text-blue-200'
                  : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <Filter className="w-4 h-4" />
              {t('devices.filters.filters')}
            </button>
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('devices.statusLabel')}
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="all">{t('devices.allStatuses')}</option>
                  <option value="pending">{t('devices.status.pending')}</option>
                  <option value="active">{t('devices.status.active')}</option>
                  <option value="inactive">{t('devices.status.inactive')}</option>
                </select>
              </div>

              {/* Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('devices.filters.deviceType')}
                </label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="all">{t('devices.filters.allTypes')}</option>
                  <option value="tv">{t('devices.filters.tv')}</option>
                  <option value="monitor">{t('devices.filters.monitor')}</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Pending Devices Section */}
      {devices.filter((d) => d.status === 'pending').length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('devices.messages.pendingDevicesAwaiting')}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {devices
              .filter((d) => d.status === 'pending')
              .map((device) => (
                <PendingDeviceCard
                  key={device.id}
                  device={device}
                  onActivated={() => {
                    // Refresh will happen automatically via React Query
                  }}
                />
              ))}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
          <TableSkeleton columns={6} rows={5} />
        ) : error ? (
          <ErrorDisplay
            error={error}
            onRetry={handleRefresh}
            className="py-12"
          />
        ) : devices.length === 0 ? (
          <EmptyState
            icon={Monitor}
            title={t('devices.messages.noDevicesFound')}
            description={
              scope === 'my_org'
                ? t('devices.messages.noDevicesInOrg', 'No devices registered in your organization yet.')
                : t('devices.messages.noUnassignedDevices', 'No unassigned devices available.')
            }
            action={
              canCreate && scope === 'my_org' && (
                <button
                  onClick={() => setTvRegisterModal(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  {t('devices.buttons.registerTV')}
                </button>
              )
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('devices.table.device')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('devices.type')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('devices.statusLabel')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('devices.table.ipAddress')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('devices.lastSeen')}
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('devices.table.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {devices.map((device) => (
                  <tr
                    key={device.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {device.device_name}
                      </div>
                      {device.model_name && (
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {device.model_name}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                        {getTypeIcon(device.device_type)}
                        <span className="capitalize">{device.device_type}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(device)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                      {device.ip_address || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                      {device.last_seen_at
                        ? new Date(device.last_seen_at).toLocaleString()
                        : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-1" role="group" aria-label={t('devices.table.actionsFor', { name: device.device_name })}>
                        {/* View Logs - Opens Device Logs Modal */}
                        <button
                          onClick={() =>
                            setLogsModal({ isOpen: true, device })
                          }
                          className="p-2 rounded-lg text-purple-600 hover:text-purple-800 hover:bg-purple-50 dark:text-purple-400 dark:hover:text-purple-300 dark:hover:bg-purple-900/20 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                          title={t('devices.actions.viewLogs')}
                          aria-label={t('devices.actions.viewLogsFor', { name: device.device_name })}
                        >
                          <Terminal className="w-4 h-4" aria-hidden="true" />
                        </button>

                        {/* View Device - Opens unified modal (Overview tab) */}
                        <button
                          onClick={() =>
                            setDeviceManagementModal({ isOpen: true, device, defaultTab: 'overview' })
                          }
                          className="p-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                          title={t('devices.actions.viewDevice')}
                          aria-label={t('devices.actions.viewDeviceFor', { name: device.device_name })}
                        >
                          <Eye className="w-4 h-4" aria-hidden="true" />
                        </button>

                        {/* Content Management - Opens separate UnifiedContentAssignmentModal */}
                        {canUpdate && (
                          <button
                            onClick={() =>
                              setContentAssignmentModal({ isOpen: true, device, defaultTab: 'direct' })
                            }
                            className="p-2 rounded-lg text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:text-indigo-300 dark:hover:bg-indigo-900/20 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                            title={t('devices.actions.manageContent')}
                            aria-label={t('devices.actions.manageContentFor', { name: device.device_name })}
                          >
                            <FileText className="w-4 h-4" aria-hidden="true" />
                          </button>
                        )}

                        {/* Edit/Settings - Opens standalone Settings Modal */}
                        {canUpdate && (
                          <button
                            onClick={() =>
                              setSettingsModal({ isOpen: true, device })
                            }
                            className="p-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                            title={t('devices.actions.editSettings')}
                            aria-label={t('devices.actions.editSettingsFor', { name: device.device_name })}
                          >
                            <Edit className="w-4 h-4" aria-hidden="true" />
                          </button>
                        )}

                        {/* Delete Device */}
                        {canDelete && (
                          <button
                            onClick={() =>
                              setDeleteModal({ isOpen: true, device })
                            }
                            className="p-2 rounded-lg text-red-600 hover:text-red-800 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-900/20 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                            title={t('devices.actions.deleteDevice')}
                            aria-label={t('devices.actions.deleteDeviceFor', { name: device.device_name })}
                          >
                            <Trash2 className="w-4 h-4" aria-hidden="true" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteModal.isOpen}
        onOpenChange={(open) => !open && setDeleteModal({ isOpen: false, device: null })}
        title={t('devices.modals.deleteDevice', 'Delete Device')}
        description={
          deleteModal.device
            ? t('devices.confirmDelete') + ` "${deleteModal.device.device_name}"?`
            : ''
        }
        confirmLabel={t('devices.buttons.delete')}
        cancelLabel={t('devices.buttons.cancel')}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
        variant="danger"
      />

      {/* Lazy loaded modals - Only loaded when needed */}
      <Suspense fallback={<ModalLoadingFallback />}>
        {/* TV Registration Modal */}
        {tvRegisterModal && (
          <TVRegisterModal
            isOpen={tvRegisterModal}
            onClose={() => setTvRegisterModal(false)}
            onSuccess={(device) => {
              setActivationCodeModal({ isOpen: true, device });
            }}
          />
        )}

        {/* Monitor Registration Modal */}
        {monitorRegisterModal && (
          <MonitorRegisterModal
            isOpen={monitorRegisterModal}
            onClose={() => setMonitorRegisterModal(false)}
            onSuccess={() => {
              // Refresh device list after successful registration
            }}
          />
        )}

        {/* Activation Code Modal */}
        {activationCodeModal.isOpen && (
          <ActivationCodeModal
            isOpen={activationCodeModal.isOpen}
            device={activationCodeModal.device}
            onClose={() => setActivationCodeModal({ isOpen: false, device: null })}
          />
        )}

        {/* Unified Device Management Modal */}
        {deviceManagementModal.isOpen && (
          <DeviceManagementModal
            isOpen={deviceManagementModal.isOpen}
            device={deviceManagementModal.device}
            defaultTab={deviceManagementModal.defaultTab}
            onClose={() => setDeviceManagementModal({ isOpen: false, device: null, defaultTab: 'overview' })}
            onRefresh={() => {
              // React Query will auto-refetch
            }}
          />
        )}

        {/* Unified Content Assignment Modal */}
        {contentAssignmentModal.isOpen && (
          <UnifiedContentAssignmentModal
            isOpen={contentAssignmentModal.isOpen}
            device={contentAssignmentModal.device}
            defaultTab={contentAssignmentModal.defaultTab}
            onClose={() => setContentAssignmentModal({ isOpen: false, device: null, defaultTab: 'direct' })}
          />
        )}

        {/* Device Settings Modal */}
        {settingsModal.isOpen && (
          <DeviceSettingsModal
            isOpen={settingsModal.isOpen}
            device={settingsModal.device}
            onClose={() => setSettingsModal({ isOpen: false, device: null })}
            onSuccess={() => {
              // React Query will auto-refetch
            }}
          />
        )}

        {/* Device Logs Modal */}
        {logsModal.isOpen && (
          <DeviceLogsModal
            isOpen={logsModal.isOpen}
            device={logsModal.device}
            onClose={() => setLogsModal({ isOpen: false, device: null })}
          />
        )}
      </Suspense>
    </>
  );
}
