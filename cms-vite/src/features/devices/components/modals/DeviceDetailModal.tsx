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
  Globe,
  Building,
  Clock,
  Network,
  Cpu,
  HardDrive,
  Play,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { useDevice, useSendCommand, useDeviceCapabilities, useDeviceHealth } from '../../hooks/useDevices';
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

  // Fetch capabilities and health data
  const { data: capabilities } = useDeviceCapabilities(
    initialDevice?.id || 0,
    isOpen && !!initialDevice
  );

  const { data: healthData } = useDeviceHealth(
    initialDevice?.id || 0,
    isOpen && !!initialDevice
  );

  const device = freshDevice || initialDevice;
  const sendCommand = useSendCommand();
  const health = healthData?.health;

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

        {/* Location & Network (GeoIP) */}
        {(device.geo_city || device.geo_country || device.geo_isp) && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
              <Globe className="w-4 h-4" />
              Location & Network
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 text-sm">
              {/* Left Column - Location */}
              <div className="space-y-3">
                {device.geo_city && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      City:
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {device.geo_city}
                    </span>
                  </div>
                )}
                {device.geo_region && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Region:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {device.geo_region}
                    </span>
                  </div>
                )}
                {device.geo_country && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <Globe className="w-3 h-3" />
                      Country:
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {device.geo_country}
                      {device.geo_country_code && ` (${device.geo_country_code})`}
                    </span>
                  </div>
                )}
              </div>

              {/* Right Column - Network */}
              <div className="space-y-3">
                {device.geo_isp && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <Building className="w-3 h-3" />
                      ISP:
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white text-right text-xs">
                      {device.geo_isp}
                    </span>
                  </div>
                )}
                {device.geo_timezone && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Timezone:
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white text-xs">
                      {device.geo_timezone}
                    </span>
                  </div>
                )}
                {device.connection_type && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <Network className="w-3 h-3" />
                      Connection:
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {device.connection_type}
                      {device.connection_speed && ` (${device.connection_speed.toFixed(1)} Mbps)`}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Map coordinates (if available) */}
            {device.geo_latitude && device.geo_longitude && (
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  Coordinates: {device.geo_latitude.toFixed(4)}, {device.geo_longitude.toFixed(4)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Device Capabilities (Phase 6) */}
        {capabilities && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
              <Cpu className="w-4 h-4" />
              Device Capabilities
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 text-sm">
              {/* Left Column - Codecs */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 dark:text-gray-400">Video Codecs:</span>
                  <div className="flex gap-1">
                    <span className={`px-1.5 py-0.5 rounded text-xs ${capabilities.codec_h264 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-500 dark:bg-gray-800'}`}>
                      H.264 {capabilities.codec_h264 ? '✓' : '✗'}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-xs ${capabilities.codec_h265 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-500 dark:bg-gray-800'}`}>
                      H.265 {capabilities.codec_h265 ? '✓' : '✗'}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-xs ${capabilities.codec_vp9 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-500 dark:bg-gray-800'}`}>
                      VP9 {capabilities.codec_vp9 ? '✓' : '✗'}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-xs ${capabilities.codec_av1 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-500 dark:bg-gray-800'}`}>
                      AV1 {capabilities.codec_av1 ? '✓' : '✗'}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 dark:text-gray-400">Audio Codecs:</span>
                  <div className="flex gap-1">
                    <span className={`px-1.5 py-0.5 rounded text-xs ${capabilities.codec_aac ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-500 dark:bg-gray-800'}`}>
                      AAC {capabilities.codec_aac ? '✓' : '✗'}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-xs ${capabilities.codec_opus ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-500 dark:bg-gray-800'}`}>
                      Opus {capabilities.codec_opus ? '✓' : '✗'}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">WebGL:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {capabilities.webgl_version || 'N/A'}
                  </span>
                </div>
              </div>

              {/* Right Column - Hardware */}
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">CPU Cores:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {capabilities.hardware_concurrency} cores
                  </span>
                </div>
                {capabilities.device_memory_gb && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Device RAM:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {capabilities.device_memory_gb} GB
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Display:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {capabilities.screen_width}x{capabilities.screen_height} @ {capabilities.display_refresh_rate}Hz
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Player:</span>
                  <span className="font-medium text-gray-900 dark:text-white text-xs">
                    v{capabilities.player_version}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Device Health Metrics (Phase 6) */}
        {health && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Health Metrics
              <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${
                health.overall_status === 'healthy'
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : health.overall_status === 'warning'
                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}>
                {health.overall_status}
              </span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              {/* System Metrics */}
              <div className="space-y-2">
                <div className="font-medium text-gray-700 dark:text-gray-300 text-xs uppercase tracking-wide">System</div>
                {health.memory_usage !== null && health.memory_usage !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Memory:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {health.memory_usage.toFixed(1)}%
                    </span>
                  </div>
                )}
                {health.disk_usage !== null && health.disk_usage !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Disk:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {health.disk_usage.toFixed(1)}%
                    </span>
                  </div>
                )}
                {health.fps_current && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">FPS:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {health.fps_current}
                    </span>
                  </div>
                )}
                {health.cpu_pressure && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">CPU Pressure:</span>
                    <span className={`font-medium ${
                      health.cpu_pressure === 'nominal' ? 'text-green-600 dark:text-green-400' :
                      health.cpu_pressure === 'fair' ? 'text-yellow-600 dark:text-yellow-400' :
                      'text-red-600 dark:text-red-400'
                    }`}>
                      {health.cpu_pressure}
                    </span>
                  </div>
                )}
              </div>

              {/* Network Metrics */}
              <div className="space-y-2">
                <div className="font-medium text-gray-700 dark:text-gray-300 text-xs uppercase tracking-wide">Network</div>
                {health.network_latency_ms && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Latency:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {health.network_latency_ms} ms
                    </span>
                  </div>
                )}
                {health.network_download_mbps && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Download:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {health.network_download_mbps.toFixed(1)} Mbps
                    </span>
                  </div>
                )}
                {health.connection_quality && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Quality:</span>
                    <span className={`font-medium ${
                      health.connection_quality === 'excellent' ? 'text-green-600 dark:text-green-400' :
                      health.connection_quality === 'good' ? 'text-green-500 dark:text-green-300' :
                      health.connection_quality === 'fair' ? 'text-yellow-600 dark:text-yellow-400' :
                      'text-red-600 dark:text-red-400'
                    }`}>
                      {health.connection_quality}
                    </span>
                  </div>
                )}
              </div>

              {/* Playback Metrics */}
              <div className="space-y-2">
                <div className="font-medium text-gray-700 dark:text-gray-300 text-xs uppercase tracking-wide">Playback</div>
                {health.content_play_count !== null && health.content_play_count !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Plays:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {health.content_play_count}
                    </span>
                  </div>
                )}
                {health.playback_stalls_count !== null && health.playback_stalls_count !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Stalls:</span>
                    <span className={`font-medium ${health.playback_stalls_count > 5 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'}`}>
                      {health.playback_stalls_count}
                    </span>
                  </div>
                )}
                {health.error_rate_percent !== null && health.error_rate_percent !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Error Rate:</span>
                    <span className={`font-medium ${health.error_rate_percent > 5 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                      {health.error_rate_percent.toFixed(1)}%
                    </span>
                  </div>
                )}
                {health.content_errors_count > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Errors:</span>
                    <span className="font-medium text-red-600 dark:text-red-400">
                      {health.content_errors_count}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Last recorded time */}
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
              Last updated: {new Date(health.recorded_at).toLocaleString()}
            </div>
          </div>
        )}

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
