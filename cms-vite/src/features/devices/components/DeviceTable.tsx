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
  Circle,
  Plus,
  Eye,
  Terminal,
  FileSymlink,
  RefreshCw,
} from 'lucide-react';
import {
  useDeviceList,
  useDeleteDevice,
  useUpdateDevice,
} from '../hooks/useDevices';
import type { Device, DeviceStatus, DeviceType } from '../types/device';
import { toast } from '@/shared/utils/toast';
import { PendingDeviceCard } from './PendingDeviceCard';
import {
  TableSkeleton,
  EmptyState,
  ErrorDisplay,
  ConfirmDialog,
  Button,
  TABLE_STYLES,
  SortableTableHeader,
} from '@/shared/components';
import { useTableSort } from '@/shared/hooks';
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

  // Scope filter (my_org for Device List, released for Unsigned Pool)
  const [scope, setScope] = useState<'my_org' | 'released'>('my_org');

  // Filters
  const [statusFilter, setStatusFilter] = useState<DeviceStatus | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<DeviceType | 'all'>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Sorting - Uses URL state for persistence
  const { sortConfig, onSortChange, sortParams } = useTableSort({
    defaultSort: { key: 'device_name', direction: 'asc' }, // Default sort by name
  });

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


  // Build filters for API (includes sorting)
  const apiFilters = {
    scope,
    ...(statusFilter !== 'all' && { status: statusFilter }),
    ...(typeFilter !== 'all' && { device_type: typeFilter }),
    ...sortParams, // Adds sort_by and sort_dir from URL state
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
      {/* Scope Tabs - Standardized like ViewTabs (no box) */}
      <div className="mb-4 border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-4" role="tablist" aria-label={t('devices.tabs.scopeSelection', 'Device scope selection')}>
          <button
            onClick={() => setScope('my_org')}
            role="tab"
            aria-selected={scope === 'my_org'}
            aria-controls="device-table-panel"
            id="tab-my-devices"
            className={`flex items-center gap-2 py-2 px-1 border-b-2 text-sm font-medium transition-colors whitespace-nowrap ${
              scope === 'my_org'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
            }`}
          >
            {t('devices.tabs.myDevices')}
          </button>
          <button
            onClick={() => setScope('released')}
            role="tab"
            aria-selected={scope === 'released'}
            aria-controls="device-table-panel"
            id="tab-released"
            className={`flex items-center gap-2 py-2 px-1 border-b-2 text-sm font-medium transition-colors whitespace-nowrap ${
              scope === 'released'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
            }`}
          >
            {t('devices.tabs.unassignedPool')}
          </button>
        </nav>
      </div>

      {/* Toolbar - Standardized layout without box */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
        {/* Left: Filter Button */}
        <div className="flex items-center gap-2">
          <Button
            variant={showFilters ? 'primary' : 'outline'}
            onClick={() => setShowFilters(!showFilters)}
            leftIcon={<Filter className="w-4 h-4" />}
            className={showFilters ? '!bg-blue-50 dark:!bg-blue-900 !text-blue-700 dark:!text-blue-200' : ''}
          >
            {t('devices.filters.filters')}
          </Button>
        </div>

        {/* Right: Action Buttons - Full width on mobile */}
        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          {/* Refresh Button */}
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isFetching}
            title={t('common.refresh', 'Refresh')}
            aria-label={t('common.refresh', 'Refresh device list')}
            leftIcon={<RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />}
          />

          {/* Register Device Button */}
          {canCreate && (
            <Button
              variant="primary"
              onClick={() => setMonitorRegisterModal(true)}
              leftIcon={<><Plus className="w-4 h-4" /><Monitor className="w-4 h-4" /></>}
            >
              {t('devices.buttons.registerDevice', 'Register Device')}
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
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

      {/* Stats: langsung di atas tabel */}
      <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        <span className="font-medium">{total}</span> {total === 1 ? t('devices.messages.deviceCount') : t('devices.messages.devicesCount')}
        {' • '}
        <span className="font-medium text-green-600 dark:text-green-400">
          {devices.filter(d => {
            if (!d.last_seen_at) return false;
            return new Date().getTime() - new Date(d.last_seen_at).getTime() < 5 * 60 * 1000;
          }).length}
        </span> {t('devices.online')}
        {' • '}
        <span className="font-medium text-red-600 dark:text-red-400">
          {devices.filter(d => {
            if (!d.last_seen_at) return true;
            return new Date().getTime() - new Date(d.last_seen_at).getTime() >= 5 * 60 * 1000;
          }).length}
        </span> {t('devices.offline')}
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

      {/* Empty State - No box wrapper */}
      {!isLoading && !error && devices.length === 0 && (
        <EmptyState
          icon={Monitor}
          title={t('devices.messages.noDevicesFound')}
          description={
            scope === 'my_org'
              ? t('devices.messages.noDevicesInOrg', 'No devices registered in your organization yet.')
              : t('devices.messages.noUnassignedDevices', 'No unassigned devices available.')
          }
        />
      )}

      {/* Error State */}
      {error && (
        <ErrorDisplay
          error={error}
          onRetry={handleRefresh}
          className="py-12"
        />
      )}

      {/* Loading State */}
      {isLoading && (
        <div className={TABLE_STYLES.container}>
          <TableSkeleton columns={6} rows={5} />
        </div>
      )}

      {/* Table - Only when has data */}
      {!isLoading && !error && devices.length > 0 && (
        <div className={TABLE_STYLES.container}>
          <div className="overflow-x-auto">
            <table className={TABLE_STYLES.table}>
              <thead className={TABLE_STYLES.thead}>
                <tr>
                  <th className={TABLE_STYLES.th}>
                    <SortableTableHeader
                      columnKey="device_name"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.table.device')}
                    </SortableTableHeader>
                  </th>
                  <th className={TABLE_STYLES.th}>
                    <SortableTableHeader
                      columnKey="status"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.statusLabel')}
                    </SortableTableHeader>
                  </th>
                  <th className={TABLE_STYLES.th}>
                    <SortableTableHeader
                      columnKey="device_type"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.type')}
                    </SortableTableHeader>
                  </th>
                  <th className={TABLE_STYLES.th}>
                    <SortableTableHeader
                      columnKey="ip_address"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.table.ipAddress')}
                    </SortableTableHeader>
                  </th>
                  <th className={TABLE_STYLES.th}>
                    <SortableTableHeader
                      columnKey="last_seen_at"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.lastSeen')}
                    </SortableTableHeader>
                  </th>
                  <th className={TABLE_STYLES.th}>
                    {t('devices.table.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className={TABLE_STYLES.tbody}>
                {devices.map((device) => (
                  <tr
                    key={device.id}
                    className={TABLE_STYLES.tr}
                  >
                    <td className={TABLE_STYLES.tdNoWrap}>
                      <div className="font-medium">
                        {device.device_name}
                      </div>
                      {device.model_name && (
                        <div className={TABLE_STYLES.muted}>
                          {device.model_name}
                        </div>
                      )}
                    </td>
                    <td className={TABLE_STYLES.tdNoWrap}>
                      {getStatusBadge(device)}
                    </td>
                    <td className={TABLE_STYLES.tdNoWrap}>
                      <div className="flex items-center gap-2">
                        {getTypeIcon(device.device_type)}
                        <span className="capitalize">{device.device_type}</span>
                      </div>
                    </td>
                    <td className={`${TABLE_STYLES.tdNoWrap} ${TABLE_STYLES.muted}`}>
                      {device.ip_address || '-'}
                    </td>
                    <td className={`${TABLE_STYLES.tdNoWrap} ${TABLE_STYLES.muted}`}>
                      {device.last_seen_at
                        ? new Date(device.last_seen_at).toLocaleString()
                        : '-'}
                    </td>
                    <td className={TABLE_STYLES.td}>
                      <div className="flex items-center gap-2" role="group" aria-label={t('devices.table.actionsFor', { name: device.device_name })}>
                        {/* View Logs - Opens Device Logs Modal */}
                        <button
                          onClick={() => setLogsModal({ isOpen: true, device })}
                          className={TABLE_STYLES.actionBtnPurple}
                          title={t('devices.actions.viewLogs')}
                          aria-label={t('devices.actions.viewLogsFor', { name: device.device_name })}
                        >
                          <Terminal className="w-4 h-4" aria-hidden="true" />
                        </button>

                        {/* View Device - Opens unified modal (Overview tab) */}
                        <button
                          onClick={() => setDeviceManagementModal({ isOpen: true, device, defaultTab: 'overview' })}
                          className={TABLE_STYLES.actionBtnGray}
                          title={t('devices.actions.viewDevice')}
                          aria-label={t('devices.actions.viewDeviceFor', { name: device.device_name })}
                        >
                          <Eye className="w-4 h-4" aria-hidden="true" />
                        </button>

                        {/* Content Management - Opens separate UnifiedContentAssignmentModal */}
                        {canUpdate && (
                          <button
                            onClick={() => setContentAssignmentModal({ isOpen: true, device, defaultTab: 'direct' })}
                            className={TABLE_STYLES.actionBtnIndigo}
                            title={t('devices.actions.manageContent')}
                            aria-label={t('devices.actions.manageContentFor', { name: device.device_name })}
                          >
                            <FileSymlink className="w-4 h-4" aria-hidden="true" />
                          </button>
                        )}

                        {/* Edit/Settings - Opens standalone Settings Modal */}
                        {canUpdate && (
                          <button
                            onClick={() => setSettingsModal({ isOpen: true, device })}
                            className={TABLE_STYLES.actionBtnBlue}
                            title={t('devices.actions.editSettings')}
                            aria-label={t('devices.actions.editSettingsFor', { name: device.device_name })}
                          >
                            <Edit className="w-4 h-4" aria-hidden="true" />
                          </button>
                        )}

                        {/* Delete Device */}
                        {canDelete && (
                          <button
                            onClick={() => setDeleteModal({ isOpen: true, device })}
                            className={TABLE_STYLES.actionBtnRed}
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
        </div>
      )}

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
