/**
 * Overview Tab - Device Management Modal
 *
 * Quick glance dashboard with:
 * - Device information cards
 * - Quick action buttons
 * - Key metrics summary
 */

import {
  Wifi,
  MapPin,
  Calendar,
  Monitor as MonitorIcon,
  Volume2,
  RotateCcw,
  Activity,
  FileText,
  Zap,
  RotateCw,
  Camera,
  Eye,
} from 'lucide-react';
import type { Device } from '../../../types/device';
import { useSendCommand } from '../../../hooks/useDevices';
import { toast } from 'sonner';

interface OverviewTabProps {
  device: Device;
  isOnline: boolean;
  onRefresh?: () => void;
}

export function OverviewTab({ device, isOnline, onRefresh }: OverviewTabProps) {
  const sendCommand = useSendCommand();

  // Handle quick command
  const handleQuickCommand = async (
    commandType: 'reboot' | 'screenshot' | 'refresh',
    label: string
  ) => {
    try {
      await sendCommand.mutateAsync({
        id: device.id,
        commandData: { command_type: commandType },
      });
      toast.success(`${label} command sent successfully`);
      onRefresh?.();
    } catch (error) {
      // Error handled by mutation
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Quick Actions Bar */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
          Quick Actions
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            onClick={() => handleQuickCommand('refresh', 'Refresh Content')}
            disabled={sendCommand.isPending || !isOnline}
            className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex flex-col items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RotateCw className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Refresh
            </span>
          </button>

          <button
            onClick={() => handleQuickCommand('reboot', 'Reboot')}
            disabled={sendCommand.isPending || !isOnline}
            className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex flex-col items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Zap className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Reboot
            </span>
          </button>

          <button
            onClick={() => handleQuickCommand('screenshot', 'Screenshot')}
            disabled={sendCommand.isPending || !isOnline}
            className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex flex-col items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Camera className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Screenshot
            </span>
          </button>

          <button
            onClick={() => toast.info('Preview feature coming soon')}
            disabled={!isOnline}
            className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex flex-col items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Eye className="w-5 h-5 text-green-600 dark:text-green-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Preview
            </span>
          </button>
        </div>
      </div>

      {/* Information Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Device Info Card */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Device Information
          </h4>
          <div className="space-y-2 text-sm">
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
          </div>
        </div>

        {/* Network Card */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <Wifi className="w-4 h-4" />
            Network
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">IP Address:</span>
              <span className="font-medium text-gray-900 dark:text-white font-mono text-xs">
                {device.ip_address || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Status:</span>
              <span
                className={`font-medium ${
                  isOnline
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {isOnline ? 'Connected' : 'Disconnected'}
              </span>
            </div>
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

        {/* Display Card */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <MonitorIcon className="w-4 h-4" />
            Display
          </h4>
          <div className="space-y-2 text-sm">
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
          </div>
        </div>

        {/* Location Card */}
        {device.room_number && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              Location
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Room:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {device.room_number}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Health Summary Card */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Health Status
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Overall:</span>
              <span
                className={`font-medium ${
                  isOnline
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {isOnline ? 'Healthy' : 'Offline'}
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              View Health tab for detailed metrics
            </p>
          </div>
        </div>

        {/* Timestamps Card */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Timeline
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Created:</span>
              <span className="text-gray-900 dark:text-white text-xs">
                {new Date(device.created_at).toLocaleDateString()}
              </span>
            </div>
            {device.updated_at && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Updated:</span>
                <span className="text-gray-900 dark:text-white text-xs">
                  {new Date(device.updated_at).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status Notice */}
      {!isOnline && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <p className="text-sm text-yellow-700 dark:text-yellow-300">
            <strong>Device Offline:</strong> This device hasn't been seen in the last 5 minutes.
            Commands will be queued and executed when the device comes back online.
          </p>
        </div>
      )}
    </div>
  );
}
