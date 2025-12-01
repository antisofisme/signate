/**
 * Assign to Device Modal
 * Modal for assigning content to one or more devices
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, Monitor, CheckSquare, Square, Loader2, Wifi, WifiOff } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { useDeviceList } from '@/features/devices/hooks/useDevices';
import { useAssignContent } from '@/features/devices/hooks/useDeviceAssignments';
import type { Content } from '../types/content';

interface AssignToDeviceModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  content: Content | null;
  onSuccess?: () => void;
}

export function AssignToDeviceModal({
  open,
  onOpenChange,
  content,
  onSuccess,
}: AssignToDeviceModalProps) {
  const { t } = useTranslation();
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isAssigning, setIsAssigning] = useState(false);

  // Fetch devices (filter by status 'active')
  const { data: devicesData, isLoading: isLoadingDevices } = useDeviceList({ status: 'active' });
  const devices = devicesData?.items || [];

  // Assign content mutation
  const assignContentMutation = useAssignContent();

  // Filter devices by search (search by name, room number, or location type)
  const filteredDevices = devices.filter((device) =>
    device.device_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (device.room_number && device.room_number.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (device.location_type && device.location_type.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleToggleDevice = (deviceId: number) => {
    setSelectedDeviceIds((prev) =>
      prev.includes(deviceId)
        ? prev.filter((id) => id !== deviceId)
        : [...prev, deviceId]
    );
  };

  const handleSelectAll = () => {
    if (selectedDeviceIds.length === filteredDevices.length) {
      setSelectedDeviceIds([]);
    } else {
      setSelectedDeviceIds(filteredDevices.map((d) => d.id));
    }
  };

  const handleAssign = async () => {
    if (!content || selectedDeviceIds.length === 0) return;

    setIsAssigning(true);
    let successCount = 0;
    let failCount = 0;

    // Assign content to each selected device
    for (const deviceId of selectedDeviceIds) {
      try {
        await assignContentMutation.mutateAsync({
          deviceId,
          data: {
            content_id: content.id,
            priority: 50,
          },
        });
        successCount++;
      } catch {
        failCount++;
      }
    }

    setIsAssigning(false);

    // Reset state and close
    setSelectedDeviceIds([]);
    setSearchQuery('');
    onOpenChange(false);
    onSuccess?.();
  };

  const handleClose = () => {
    setSelectedDeviceIds([]);
    setSearchQuery('');
    onOpenChange(false);
  };


  return (
    <Modal
      isOpen={open}
      onClose={handleClose}
      title={t('contents.assignToDevice.title', 'Assign to Device')}
      subtitle={content ? t('contents.assignToDevice.description', 'Select devices to assign "{{name}}" to', { name: content.title }) : ''}
      maxWidth="md"
    >
      <div className="space-y-4">
        {/* Search and Select All */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('contents.assignToDevice.searchPlaceholder', 'Search devices...')}
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleSelectAll}
          >
            {selectedDeviceIds.length === filteredDevices.length
              ? t('common.deselectAll', 'Deselect All')
              : t('common.selectAll', 'Select All')}
          </Button>
        </div>

        {/* Device List */}
        <div className="max-h-[350px] overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
          {isLoadingDevices ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
            </div>
          ) : filteredDevices.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-gray-500">
              <Monitor className="w-8 h-8 mb-2" />
              <p className="text-sm">{t('contents.assignToDevice.noDevices', 'No devices found')}</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredDevices.map((device) => {
                const isSelected = selectedDeviceIds.includes(device.id);
                const online = device.is_online;

                return (
                  <button
                    key={device.id}
                    onClick={() => handleToggleDevice(device.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                      isSelected ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                    }`}
                  >
                    {/* Checkbox */}
                    <div className="flex-shrink-0">
                      {isSelected ? (
                        <CheckSquare className="w-5 h-5 text-blue-500" />
                      ) : (
                        <Square className="w-5 h-5 text-gray-400" />
                      )}
                    </div>

                    {/* Status indicator */}
                    <div className="flex-shrink-0">
                      {online ? (
                        <Wifi className="w-4 h-4 text-green-500" />
                      ) : (
                        <WifiOff className="w-4 h-4 text-gray-400" />
                      )}
                    </div>

                    {/* Device info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {device.device_name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {device.room_number || device.location_type || device.unique_code}
                      </p>
                    </div>

                    {/* Status badge */}
                    <div className="flex-shrink-0">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          online
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                        }`}
                      >
                        {online ? t('devices.status.online', 'Online') : t('devices.status.offline', 'Offline')}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Selected count */}
        {selectedDeviceIds.length > 0 && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {t('contents.assignToDevice.selected', '{{count}} device(s) selected', { count: selectedDeviceIds.length })}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="secondary" onClick={handleClose}>
            {t('common.cancel', 'Cancel')}
          </Button>
          <Button
            variant="primary"
            onClick={handleAssign}
            disabled={selectedDeviceIds.length === 0 || isAssigning}
            loading={isAssigning}
          >
            {t('contents.assignToDevice.assign', 'Assign to {{count}} Device(s)', { count: selectedDeviceIds.length || 0 })}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export default AssignToDeviceModal;
