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
  Pencil,
  Filter,
  Circle,
  Plus,
  Eye,
  Terminal,
  FileSymlink,
  RefreshCw,
  ListMusic,
  RotateCcw,
} from 'lucide-react';
import {
  useDeviceList,
  useDeleteDevice,
  useUpdateDevice,
  useRestoreDevice,
  useReleaseDevice,
} from '../hooks/useDevices';
import type { Device, DeviceStatus, DeviceType, LocationType } from '../types/device';
import { toast } from '@/shared/utils/toast';
import { PendingDeviceCard } from './PendingDeviceCard';
import {
  TableSkeleton,
  EmptyState,
  ErrorDisplay,
  ConfirmDialog,
  Button,
  TABLE_STYLES,
  ACTION_BUTTON,
  SortableTableHeader,
  Pagination,
  OnlineStatusCell,
} from '@/shared/components';
import { useTableSort, usePagination } from '@/shared/hooks';
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

  // Pagination
  const pagination = usePagination({ pageSize: 20 });

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


  // Build filters for API (includes sorting and pagination)
  const apiFilters = {
    scope,
    ...(statusFilter !== 'all' && { status: statusFilter }),
    ...(typeFilter !== 'all' && { device_type: typeFilter }),
    ...sortParams, // Adds sort_by and sort_dir from URL state
    skip: pagination.skip,
    limit: pagination.limit,
  };

  // Fetch devices with refetch function for manual refresh
  const { data, isLoading, error, refetch, isFetching } = useDeviceList(apiFilters);
  const devices = data?.items || [];
  const total = data?.total || 0;
  const totalPages = pagination.getTotalPages(total);

  // Manual refresh handler
  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  // Mutations
  const deleteMutation = useDeleteDevice();
  const releaseMutation = useReleaseDevice();
  const restoreMutation = useRestoreDevice();

  // Restore modal state
  const [restoreModal, setRestoreModal] = useState<{
    isOpen: boolean;
    device: Device | null;
  }>({ isOpen: false, device: null });

  // Delete handler - releases when in Device List, permanently deletes in Unassigned Pool
  const handleDelete = async () => {
    if (!deleteModal.device) return;

    try {
      if (scope === 'my_org') {
        // Device List: Release to Unassigned Pool
        await releaseMutation.mutateAsync(deleteModal.device.id);
      } else {
        // Unassigned Pool: Permanent delete
        await deleteMutation.mutateAsync(deleteModal.device.id);
      }
      setDeleteModal({ isOpen: false, device: null });
      // Cache invalidation is handled by the mutation's onSuccess
      // Using refetchType: 'active' to prevent race conditions
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Restore handler
  const handleRestore = async () => {
    if (!restoreModal.device) return;

    try {
      await restoreMutation.mutateAsync(restoreModal.device.id);
      // Close modal - device already removed from list via optimistic update
      setRestoreModal({ isOpen: false, device: null });
      // Don't auto-switch tab - let user see the device disappear first
      // User can manually switch to Device List to see the restored device
    } catch (error) {
      // Error handled by mutation
      setRestoreModal({ isOpen: false, device: null });
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

  // Location type badge
  const getLocationBadge = (locationType: LocationType) => {
    const locationConfig: Record<LocationType, { label: string; color: string }> = {
      guest_room: { label: t('devices.locations.guestRoom', 'Guest Room'), color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' },
      lobby: { label: t('devices.locations.lobby', 'Lobby'), color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' },
      restaurant: { label: t('devices.locations.restaurant', 'Restaurant'), color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' },
      conference_room: { label: t('devices.locations.conference', 'Conference'), color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
      other: { label: t('devices.locations.other', 'Other'), color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300' },
    };

    const config = locationConfig[locationType] || locationConfig.other;
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  return (
    <>
      {/* Scope Tabs - Standardized like ViewTabs (no box) */}
      <div className="mb-4 border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-4" role="tablist" aria-label={t('devices.tabs.scopeSelection', 'Device scope selection')}>
          <button
            onClick={() => { setScope('my_org'); pagination.resetPage(); }}
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
            onClick={() => { setScope('released'); pagination.resetPage(); }}
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
                  onChange={(e) => { setStatusFilter(e.target.value as any); pagination.resetPage(); }}
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
                  onChange={(e) => { setTypeFilter(e.target.value as any); pagination.resetPage(); }}
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
          <TableSkeleton columns={9} rows={5} />
        </div>
      )}

      {/* Table - Only when has data */}
      {!isLoading && !error && devices.length > 0 && (
        <div className={TABLE_STYLES.container}>
          <div className="overflow-x-auto">
            <table className={`${TABLE_STYLES.table} table-fixed`}>
              <thead className={TABLE_STYLES.thead}>
                <tr>
                  <th className="w-72 px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <SortableTableHeader
                      columnKey="device_name"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.table.device')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-16 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <SortableTableHeader
                      columnKey="room_number"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.table.roomNumber', 'Room #')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-24 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <SortableTableHeader
                      columnKey="location_type"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.table.location', 'Location')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-28 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('devices.table.playlist', 'Playlist')}
                  </th>
                  <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <SortableTableHeader
                      columnKey="status"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.statusLabel')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <SortableTableHeader
                      columnKey="device_type"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.type')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-28 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <SortableTableHeader
                      columnKey="ip_address"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.table.ipAddress')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-24 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <SortableTableHeader
                      columnKey="last_seen_at"
                      sortConfig={sortConfig}
                      onSortChange={onSortChange}
                    >
                      {t('devices.lastSeen')}
                    </SortableTableHeader>
                  </th>
                  <th className="w-36 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
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
                    <td className="px-3 py-4 overflow-hidden">
                      <div className="min-w-0 overflow-hidden">
                        <div className="font-medium text-gray-900 dark:text-white truncate" title={device.device_name}>
                          {device.device_name}
                        </div>
                        {device.model_name && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 truncate" title={device.model_name}>
                            {device.model_name}
                          </div>
                        )}
                      </div>
                    </td>
                    {/* Room Number */}
                    <td className={`${TABLE_STYLES.tdNoWrap} font-mono text-sm`}>
                      {device.room_number || '-'}
                    </td>
                    {/* Location Type */}
                    <td className={TABLE_STYLES.tdNoWrap}>
                      {getLocationBadge(device.location_type)}
                    </td>
                    {/* Playlist Name */}
                    <td className={TABLE_STYLES.tdNoWrap}>
                      {device.playlist_name ? (
                        <div className="flex items-center gap-1.5 text-sm">
                          <ListMusic className="w-3.5 h-3.5 text-blue-500" />
                          <span className="text-gray-900 dark:text-white truncate max-w-[120px]" title={device.playlist_name}>
                            {device.playlist_name}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400 dark:text-gray-500 text-sm">-</span>
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
                    {/* Last Seen - Using OnlineStatusCell with relative time */}
                    <td className={TABLE_STYLES.tdNoWrap}>
                      <OnlineStatusCell
                        lastSeen={device.last_seen_at}
                        isOnline={device.is_online}
                      />
                    </td>
                    <td className={TABLE_STYLES.td}>
                      <div className="flex items-center gap-2" role="group" aria-label={t('devices.table.actionsFor', { name: device.device_name })}>
                        {/* View Logs - Opens Device Logs Modal */}
                        <button
                          onClick={() => setLogsModal({ isOpen: true, device })}
                          className={ACTION_BUTTON.LOGS}
                          title={t('devices.actions.viewLogs')}
                          aria-label={t('devices.actions.viewLogsFor', { name: device.device_name })}
                        >
                          <Terminal className="w-4 h-4" aria-hidden="true" />
                        </button>

                        {/* View Device - Opens unified modal (Overview tab) */}
                        <button
                          onClick={() => setDeviceManagementModal({ isOpen: true, device, defaultTab: 'overview' })}
                          className={ACTION_BUTTON.VIEW}
                          title={t('devices.actions.viewDevice')}
                          aria-label={t('devices.actions.viewDeviceFor', { name: device.device_name })}
                        >
                          <Eye className="w-4 h-4" aria-hidden="true" />
                        </button>

                        {/* Content Management - Opens separate UnifiedContentAssignmentModal */}
                        {canUpdate && (
                          <button
                            onClick={() => setContentAssignmentModal({ isOpen: true, device, defaultTab: 'direct' })}
                            className={ACTION_BUTTON.ASSIGN}
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
                            className={ACTION_BUTTON.EDIT}
                            title={t('devices.actions.editSettings')}
                            aria-label={t('devices.actions.editSettingsFor', { name: device.device_name })}
                          >
                            <Pencil className="w-4 h-4" aria-hidden="true" />
                          </button>
                        )}

                        {/* Restore Device - Only in released scope */}
                        {scope === 'released' && canUpdate && (
                          <button
                            onClick={() => setRestoreModal({ isOpen: true, device })}
                            className={ACTION_BUTTON.RESTORE}
                            title={t('devices.actions.restoreDevice', 'Restore Device')}
                            aria-label={t('devices.actions.restoreDeviceFor', { name: device.device_name })}
                          >
                            <RotateCcw className="w-4 h-4" aria-hidden="true" />
                          </button>
                        )}

                        {/* Delete Device */}
                        {canDelete && (
                          <button
                            onClick={() => setDeleteModal({ isOpen: true, device })}
                            className={ACTION_BUTTON.DELETE}
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

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
              <Pagination
                currentPage={pagination.currentPage}
                totalPages={totalPages}
                onPageChange={pagination.goToPage}
                totalItems={total}
                pageSize={pagination.pageSize}
              />
            </div>
          )}
        </div>
      )}

      {/* Delete Confirmation Dialog - Different messaging for Release vs Permanent Delete */}
      <ConfirmDialog
        open={deleteModal.isOpen}
        onOpenChange={(open) => !open && setDeleteModal({ isOpen: false, device: null })}
        title={
          // Unsigned Pool (released devices) = Permanent Delete
          // Device List (my_org) = Release to Unsigned Pool
          scope === 'released'
            ? t('devices.modals.permanentlyDelete', 'Permanently Delete Device')
            : t('devices.modals.releaseDevice', 'Release Device')
        }
        description={
          deleteModal.device
            ? scope === 'released'
              ? t('devices.confirmPermanentDelete', 'This will PERMANENTLY delete "{{name}}". The device record will be removed, all assignments will be deleted, and the device must re-register from scratch.', { name: deleteModal.device.device_name })
              : t('devices.confirmRelease', 'This will move "{{name}}" to Unsigned Pool. The device will stop displaying content but can be re-activated later. Assigned playlists will be preserved.', { name: deleteModal.device.device_name })
            : ''
        }
        confirmLabel={
          scope === 'released'
            ? t('devices.buttons.permanentlyDelete', 'Permanently Delete')
            : t('devices.buttons.release', 'Release Device')
        }
        cancelLabel={t('devices.buttons.cancel')}
        onConfirm={handleDelete}
        isLoading={scope === 'my_org' ? releaseMutation.isPending : deleteMutation.isPending}
        variant={scope === 'released' ? 'danger' : 'warning'}
      />

      {/* Restore Confirmation Dialog */}
      <ConfirmDialog
        open={restoreModal.isOpen}
        onOpenChange={(open) => !open && setRestoreModal({ isOpen: false, device: null })}
        title={t('devices.modals.restoreDevice', 'Restore Device')}
        description={
          restoreModal.device
            ? t('devices.confirmRestore', 'This will restore "{{name}}" to active device list. The device will start displaying content again.', { name: restoreModal.device.device_name })
            : ''
        }
        confirmLabel={t('devices.buttons.restore', 'Restore')}
        cancelLabel={t('devices.buttons.cancel')}
        onConfirm={handleRestore}
        isLoading={restoreMutation.isPending}
        variant="info"
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
