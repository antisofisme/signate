/**
 * Bulk Assign Devices to Playlist Component
 *
 * Features:
 * - Multi-select device picker with search/filter
 * - Organization scoping
 * - Device status indicators
 * - Conflict warning
 * - Bulk assign action with progress
 */

import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, Loader2, AlertCircle, CheckCircle2, Circle } from 'lucide-react';
import { useDeviceList } from '@/features/devices/hooks/useDevices';
import { useBulkAssignPlaylist } from '@/features/devices/hooks/useDeviceAssignments';
import type { Device } from '@/features/devices/types/device';

interface BulkAssignDevicesProps {
  playlistId: number;
  playlistName: string;
  currentDeviceIds?: number[];
  onSuccess?: () => void;
  onCancel?: () => void;
}

export const BulkAssignDevices: React.FC<BulkAssignDevicesProps> = ({
  playlistId,
  playlistName,
  currentDeviceIds = [],
  onSuccess,
  onCancel,
}) => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<Set<number>>(new Set());
  const [statusFilter, setStatusFilter] = useState<'all' | 'online' | 'offline'>('all');

  // Fetch devices (organization-scoped by default in API)
  const { data: devicesData, isLoading: isLoadingDevices } = useDeviceList({
    limit: 1000, // Get all devices for selection
  });

  const bulkAssign = useBulkAssignPlaylist();

  // Filter devices based on search and status
  const filteredDevices = useMemo(() => {
    if (!devicesData?.items) return [];

    return devicesData.items.filter((device) => {
      // Search filter
      const matchesSearch =
        device.device_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        device.room_number?.toLowerCase().includes(searchQuery.toLowerCase());

      // Status filter
      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'online' && device.is_online) ||
        (statusFilter === 'offline' && !device.is_online);

      return matchesSearch && matchesStatus;
    });
  }, [devicesData?.items, searchQuery, statusFilter]);

  // Check if device already has playlist
  const isAlreadyAssigned = (deviceId: number) => currentDeviceIds.includes(deviceId);

  // Toggle device selection
  const toggleDevice = (deviceId: number) => {
    const newSelection = new Set(selectedDeviceIds);
    if (newSelection.has(deviceId)) {
      newSelection.delete(deviceId);
    } else {
      newSelection.add(deviceId);
    }
    setSelectedDeviceIds(newSelection);
  };

  // Select all filtered devices
  const selectAll = () => {
    const allIds = new Set(filteredDevices.map((d) => d.id));
    setSelectedDeviceIds(allIds);
  };

  // Deselect all
  const deselectAll = () => {
    setSelectedDeviceIds(new Set());
  };

  // Handle bulk assign
  const handleAssign = async () => {
    if (selectedDeviceIds.size === 0) return;

    await bulkAssign.mutateAsync(
      {
        playlistId,
        data: { device_ids: Array.from(selectedDeviceIds) },
      },
      {
        onSuccess: () => {
          setSelectedDeviceIds(new Set());
          onSuccess?.();
        },
      }
    );
  };

  // Count conflicts (devices already assigned)
  const conflictCount = useMemo(() => {
    return Array.from(selectedDeviceIds).filter((id) => isAlreadyAssigned(id)).length;
  }, [selectedDeviceIds, currentDeviceIds]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold">{t('playlists.bulkAssign.title')}</h3>
        <p className="text-sm text-gray-500">
          {t('playlists.bulkAssign.subtitle', { playlistName })}
        </p>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder={t('playlists.bulkAssign.searchPlaceholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              statusFilter === 'all'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {t('playlists.bulkAssign.filters.all')}
          </button>
          <button
            onClick={() => setStatusFilter('online')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              statusFilter === 'online'
                ? 'bg-green-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {t('playlists.bulkAssign.filters.online')}
          </button>
          <button
            onClick={() => setStatusFilter('offline')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              statusFilter === 'offline'
                ? 'bg-gray-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {t('playlists.bulkAssign.filters.offline')}
          </button>
        </div>
      </div>

      {/* Selection Actions */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          {t('playlists.bulkAssign.selection.count', {
            selected: selectedDeviceIds.size,
            total: filteredDevices.length,
          })}
        </div>
        <div className="flex gap-2">
          <button
            onClick={selectAll}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {t('playlists.bulkAssign.selection.selectAll')}
          </button>
          <button
            onClick={deselectAll}
            className="text-sm text-gray-600 hover:text-gray-700 font-medium"
          >
            {t('playlists.bulkAssign.selection.deselectAll')}
          </button>
        </div>
      </div>

      {/* Conflict Warning */}
      {conflictCount > 0 && (
        <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-yellow-800">
              {t(
                conflictCount > 1
                  ? 'playlists.bulkAssign.conflict.title_plural'
                  : 'playlists.bulkAssign.conflict.title',
                { count: conflictCount }
              )}
            </p>
            <p className="text-yellow-700">
              {t('playlists.bulkAssign.conflict.description')}
            </p>
          </div>
        </div>
      )}

      {/* Device List */}
      <div className="border rounded-lg max-h-96 overflow-y-auto">
        {isLoadingDevices ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-500">{t('playlists.bulkAssign.loading')}</span>
          </div>
        ) : filteredDevices.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            {t('playlists.bulkAssign.noDevices')}
          </div>
        ) : (
          <div className="divide-y">
            {filteredDevices.map((device) => {
              const isSelected = selectedDeviceIds.has(device.id);
              const isAssigned = isAlreadyAssigned(device.id);

              return (
                <label
                  key={device.id}
                  className={`flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                    isSelected ? 'bg-blue-50' : ''
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleDevice(device.id)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />

                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{device.device_name}</span>
                      {device.room_number && (
                        <span className="text-sm text-gray-500">
                          {t('playlists.bulkAssign.room', { number: device.room_number })}
                        </span>
                      )}
                      {isAssigned && (
                        <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full">
                          {t('playlists.bulkAssign.alreadyAssigned')}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className={`flex items-center gap-1 text-xs ${
                          device.is_online ? 'text-green-600' : 'text-gray-500'
                        }`}
                      >
                        {device.is_online ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          <Circle className="w-3 h-3" />
                        )}
                        {t(
                          device.is_online
                            ? 'playlists.bulkAssign.status.online'
                            : 'playlists.bulkAssign.status.offline'
                        )}
                      </span>
                      <span className="text-xs text-gray-500">
                        {t(
                          device.device_type === 'tv'
                            ? 'playlists.bulkAssign.deviceTypes.tv'
                            : 'playlists.bulkAssign.deviceTypes.monitor'
                        )}
                      </span>
                    </div>
                  </div>
                </label>
              );
            })}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          disabled={bulkAssign.isPending}
        >
          {t('playlists.buttons.cancel')}
        </button>
        <button
          onClick={handleAssign}
          disabled={selectedDeviceIds.size === 0 || bulkAssign.isPending}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {bulkAssign.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
          {t(
            selectedDeviceIds.size !== 1
              ? 'playlists.bulkAssign.assignButton_plural'
              : 'playlists.bulkAssign.assignButton',
            { count: selectedDeviceIds.size }
          )}
        </button>
      </div>
    </div>
  );
};
