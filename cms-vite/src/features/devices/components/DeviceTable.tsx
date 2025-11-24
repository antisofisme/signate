/**
 * Device Table Component
 *
 * LAYER 1: PRESENTATION
 * Device management table with filters and actions
 */

import { useState } from 'react';
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
} from 'lucide-react';
import {
  useDeviceList,
  useDeleteDevice,
  useUpdateDevice,
} from '../hooks/useDevices';
import type { Device, DeviceStatus, DeviceType } from '../types/device';
import { toast } from 'sonner';
import { TVRegisterModal } from './modals/TVRegisterModal';
import { MonitorRegisterModal } from './modals/MonitorRegisterModal';
import { ActivationCodeModal } from './modals/ActivationCodeModal';
import { DeviceManagementModal, type DeviceTabId } from './modals/DeviceManagementModal';
import { DeviceSettingsModal } from './modals/DeviceSettingsModal';
import { UnifiedContentAssignmentModal, type ContentAssignmentTabId } from './modals/UnifiedContentAssignmentModal';
import { DeviceLogsModal } from './modals/DeviceLogsModal';
import { PendingDeviceCard } from './PendingDeviceCard';

// Delete Confirmation Modal
interface DeleteConfirmModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function DeleteConfirmModal({
  isOpen,
  device,
  onClose,
  onConfirm,
  isLoading,
}: DeleteConfirmModalProps) {
  if (!isOpen || !device) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Delete Device
        </h3>
        <p className="text-gray-700 dark:text-gray-300 mb-2">
          Are you sure you want to delete this device?
        </p>
        <p className="text-gray-900 dark:text-white font-semibold mb-6">
          {device.device_name}
        </p>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export function DeviceTable() {
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

  // Fetch devices
  const { data, isLoading, error } = useDeviceList(apiFilters);
  const devices = data?.items || [];
  const total = data?.total || 0;

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
          Pending
        </span>
      );
    }

    if (device.status === 'inactive') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
          <Circle className="w-2 h-2 fill-current" />
          Inactive
        </span>
      );
    }

    return isOnline ? (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
        <Circle className="w-2 h-2 fill-current" />
        Online
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
        <Circle className="w-2 h-2 fill-current" />
        Offline
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
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setScope('my_org')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
              scope === 'my_org'
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            My Devices
          </button>
          <button
            onClick={() => setScope('unassigned')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
              scope === 'unassigned'
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            Unassigned Pool
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {scope === 'my_org' ? 'My Devices' : 'Unassigned Devices'}
            </h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {total} {total === 1 ? 'device' : 'devices'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Register TV Button */}
            <button
              onClick={() => setTvRegisterModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <Tv className="w-4 h-4" />
              Register TV
            </button>

            {/* Register Monitor Button */}
            <button
              onClick={() => setMonitorRegisterModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <Monitor className="w-4 h-4" />
              Register Monitor
            </button>

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
              Filters
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
                  Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="all">All Statuses</option>
                  <option value="pending">Pending</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              {/* Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Device Type
                </label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="all">All Types</option>
                  <option value="tv">TV</option>
                  <option value="monitor">Monitor</option>
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
            Pending Devices Awaiting Activation
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
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : error ? (
          <div className="text-center py-12 text-red-600">
            Error loading devices
          </div>
        ) : devices.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            No devices found
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Device
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Last Seen
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
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
                      <div className="flex items-center justify-end gap-2">
                        {/* View Logs - Opens Device Logs Modal */}
                        <button
                          onClick={() =>
                            setLogsModal({ isOpen: true, device })
                          }
                          className="text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-300"
                          title="View device logs"
                        >
                          <Terminal className="w-4 h-4" />
                        </button>

                        {/* View Device - Opens unified modal (Overview tab) */}
                        <button
                          onClick={() =>
                            setDeviceManagementModal({ isOpen: true, device, defaultTab: 'overview' })
                          }
                          className="text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-300"
                          title="View device"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        {/* Content Management - Opens separate UnifiedContentAssignmentModal */}
                        <button
                          onClick={() =>
                            setContentAssignmentModal({ isOpen: true, device, defaultTab: 'direct' })
                          }
                          className="text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
                          title="Manage content, tags & playlists"
                        >
                          <FileText className="w-4 h-4" />
                        </button>

                        {/* Edit/Settings - Opens standalone Settings Modal */}
                        <button
                          onClick={() =>
                            setSettingsModal({ isOpen: true, device })
                          }
                          className="text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-300"
                          title="Edit device settings"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() =>
                            setDeleteModal({ isOpen: true, device })
                          }
                          className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                          title="Delete device"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={deleteModal.isOpen}
        device={deleteModal.device}
        onClose={() => setDeleteModal({ isOpen: false, device: null })}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />

      {/* TV Registration Modal */}
      <TVRegisterModal
        isOpen={tvRegisterModal}
        onClose={() => setTvRegisterModal(false)}
        onSuccess={(device) => {
          setActivationCodeModal({ isOpen: true, device });
        }}
      />

      {/* Monitor Registration Modal */}
      <MonitorRegisterModal
        isOpen={monitorRegisterModal}
        onClose={() => setMonitorRegisterModal(false)}
        onSuccess={() => {
          // Refresh device list after successful registration
        }}
      />

      {/* Activation Code Modal */}
      <ActivationCodeModal
        isOpen={activationCodeModal.isOpen}
        device={activationCodeModal.device}
        onClose={() => setActivationCodeModal({ isOpen: false, device: null })}
      />

      {/* ✨ NEW: Unified Device Management Modal - Replaces 10+ old modals */}
      <DeviceManagementModal
        isOpen={deviceManagementModal.isOpen}
        device={deviceManagementModal.device}
        defaultTab={deviceManagementModal.defaultTab}
        onClose={() => setDeviceManagementModal({ isOpen: false, device: null, defaultTab: 'overview' })}
        onRefresh={() => {
          // React Query will auto-refetch
        }}
      />

      {/* ✨ Unified Content Assignment Modal - Separate modal with 3 tabs */}
      <UnifiedContentAssignmentModal
        isOpen={contentAssignmentModal.isOpen}
        device={contentAssignmentModal.device}
        defaultTab={contentAssignmentModal.defaultTab}
        onClose={() => setContentAssignmentModal({ isOpen: false, device: null, defaultTab: 'direct' })}
      />

      {/* ✨ Device Settings Modal - Standalone settings/edit modal */}
      <DeviceSettingsModal
        isOpen={settingsModal.isOpen}
        device={settingsModal.device}
        onClose={() => setSettingsModal({ isOpen: false, device: null })}
        onSuccess={() => {
          // React Query will auto-refetch
        }}
      />

      {/* ✨ Device Logs Modal - View console, connection, and speed test logs */}
      <DeviceLogsModal
        isOpen={logsModal.isOpen}
        device={logsModal.device}
        onClose={() => setLogsModal({ isOpen: false, device: null })}
      />
    </>
  );
}
