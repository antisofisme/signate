/**
 * Device Detail Modal Component
 *
 * Comprehensive device information dashboard
 * Uses centralized Modal component
 */

import {
  Tv,
  Monitor,
  Terminal,
  Zap,
  Activity,
  RotateCw,
  Volume2,
  MapPin,
  Wifi,
  Calendar,
  Settings,
  FileText,
} from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { useDevice, useSendCommand } from '../../hooks/useDevices';
import type { Device } from '../../types/device';
import { toast } from '@/shared/utils/toast';

interface DeviceDetailModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
  onEdit?: (device: Device) => void;
  onShowLogs?: (device: Device) => void;
}

export function DeviceDetailModal({
  isOpen,
  device: initialDevice,
  onClose,
  onEdit,
  onShowLogs,
}: DeviceDetailModalProps) {
  // Fetch fresh data if we have device ID
  const { data: freshDevice } = useDevice(
    initialDevice?.id || 0,
    isOpen && !!initialDevice
  );

  const device = freshDevice || initialDevice;
  const sendCommand = useSendCommand();

  if (!device) return null;

  // Calculate online status
  const isOnline = device.last_seen_at
    ? new Date().getTime() - new Date(device.last_seen_at).getTime() < 5 * 60 * 1000
    : false;

  // Handle quick commands
  const handleQuickCommand = async (
    commandType: 'reboot' | 'screenshot' | 'volume' | 'brightness' | 'refresh'
  ) => {
    try {
      await sendCommand.mutateAsync({
        id: device.id,
        commandData: { command_type: commandType },
      });
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Device type icon
  const DeviceIcon = device.device_type === 'tv' ? Tv : Monitor;

  // Custom header with device icon and status
  const customHeader = (
    <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between z-10">
      <div className="flex items-center gap-3">
        <div
          className={`w-12 h-12 rounded-lg flex items-center justify-center ${
            device.device_type === 'tv'
              ? 'bg-blue-100 dark:bg-blue-900'
              : 'bg-purple-100 dark:bg-purple-900'
          }`}
        >
          <DeviceIcon
            className={`w-6 h-6 ${
              device.device_type === 'tv'
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-purple-600 dark:text-purple-400'
            }`}
          />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {device.device_name}
          </h2>
          <div className="flex items-center gap-2 mt-1">
            {/* Status Badge */}
            {device.status === 'pending' ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                Pending Activation
              </span>
            ) : isOnline ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                Online
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                <span className="w-2 h-2 bg-red-500 rounded-full" />
                Offline
              </span>
            )}
            <span className="text-sm text-gray-500 dark:text-gray-400 capitalize">
              {device.device_type}
            </span>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {onEdit && (
          <Button
            variant="secondary"
            onClick={() => onEdit(device)}
            leftIcon={<Settings className="w-4 h-4" />}
          >
            Edit
          </Button>
        )}
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="4xl"
      customHeader={customHeader}
    >
      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Quick Actions */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Quick Actions
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {onShowLogs && (
              <button
                onClick={() => onShowLogs(device)}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex flex-col items-center gap-2"
              >
                <Terminal className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  View Logs
                </span>
              </button>
            )}
            <button
              onClick={() => handleQuickCommand('refresh')}
              disabled={sendCommand.isPending || !isOnline}
              className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex flex-col items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RotateCw className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Refresh
              </span>
            </button>
            <button
              onClick={() => handleQuickCommand('reboot')}
              disabled={sendCommand.isPending || !isOnline}
              className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex flex-col items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Zap className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Reboot
              </span>
            </button>
            <button
              onClick={() => toast.info('Speed test feature coming soon')}
              disabled={!isOnline}
              className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex flex-col items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Activity className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Speed Test
              </span>
            </button>
          </div>
        </div>

        {/* Device Information */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Device Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 text-sm">
            {/* Left Column */}
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Type:</span>
                <span className="font-medium text-gray-900 dark:text-white capitalize">
                  {device.device_type}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Platform:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {device.platform || 'N/A'}
                </span>
              </div>
              {device.model_name && (
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Model:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {device.model_name}
                  </span>
                </div>
              )}
              {device.firmware_version && (
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Firmware:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {device.firmware_version}
                  </span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Wifi className="w-3 h-3" />
                  IP Address:
                </span>
                <span className="font-medium text-gray-900 dark:text-white font-mono text-xs">
                  {device.ip_address || 'N/A'}
                </span>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Resolution:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {device.screen_width && device.screen_height
                    ? `${device.screen_width}x${device.screen_height}`
                    : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Rotation:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {device.rotation || 0}°
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Volume2 className="w-3 h-3" />
                  Volume:
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {device.is_volume_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              {device.room_number && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    Room:
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {device.room_number}
                  </span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  Last Seen:
                </span>
                <span className="font-medium text-gray-900 dark:text-white text-xs">
                  {device.last_seen_at
                    ? new Date(device.last_seen_at).toLocaleString()
                    : 'Never'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Timestamps */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Timeline
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Created:</span>
              <span className="text-gray-900 dark:text-white">
                {new Date(device.created_at).toLocaleString()}
              </span>
            </div>
            {device.updated_at && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Updated:</span>
                <span className="text-gray-900 dark:text-white">
                  {new Date(device.updated_at).toLocaleString()}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
