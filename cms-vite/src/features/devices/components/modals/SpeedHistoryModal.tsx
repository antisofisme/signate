/**
 * Speed History Modal Component
 *
 * Display network speed test history for a device with quality indicators
 * Uses centralized Modal component
 */

import { Wifi, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Modal } from '@/shared/components';
import { deviceApi } from '../../api/deviceApi';
import type { Device } from '../../types/device';

interface SpeedHistoryModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

interface SpeedTest {
  id: number;
  download_speed: number;
  upload_speed: number;
  latency: number;
  jitter?: number;
  packet_loss?: number;
  quality: 'good' | 'fair' | 'poor';
  tested_at: string;
}

export function SpeedHistoryModal({
  isOpen,
  device,
  onClose,
}: SpeedHistoryModalProps) {
  // Fetch speed test history
  const { data: speedTests, isLoading } = useQuery({
    queryKey: ['device-speed-tests', device?.id],
    queryFn: async () => {
      if (!device?.id) return [];
      const response = await deviceApi.getSpeedTests?.(device.id);
      return response?.items || [];
    },
    enabled: isOpen && !!device?.id,
    refetchInterval: 60000, // Refresh every 60 seconds
  });

  if (!device) return null;

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'good':
        return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
      case 'fair':
        return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30';
      case 'poor':
        return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
      default:
        return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-700';
    }
  };

  const formatSpeed = (speed: number) => {
    return speed.toFixed(2);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('id-ID', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  // Calculate averages
  const averages = speedTests?.length
    ? {
        download: speedTests.reduce((sum: number, test: SpeedTest) => sum + test.download_speed, 0) / speedTests.length,
        upload: speedTests.reduce((sum: number, test: SpeedTest) => sum + test.upload_speed, 0) / speedTests.length,
        latency: speedTests.reduce((sum: number, test: SpeedTest) => sum + test.latency, 0) / speedTests.length,
      }
    : null;

  // Custom header with icon
  const customHeader = (
    <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Wifi className="w-5 h-5" />
            Network Speed Test History
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {device.device_name}
          </p>
        </div>
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
      <div className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : !speedTests || speedTests.length === 0 ? (
          <div className="text-center py-12">
            <Wifi className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">
              No speed test history available
            </p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
              Speed tests will appear here once the device runs them
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary Cards */}
            {averages && (
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300 mb-2">
                    <TrendingDown className="w-4 h-4" />
                    <span className="text-sm font-medium">Avg Download</span>
                  </div>
                  <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                    {formatSpeed(averages.download)} <span className="text-sm">Mbps</span>
                  </p>
                </div>

                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-green-700 dark:text-green-300 mb-2">
                    <TrendingUp className="w-4 h-4" />
                    <span className="text-sm font-medium">Avg Upload</span>
                  </div>
                  <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                    {formatSpeed(averages.upload)} <span className="text-sm">Mbps</span>
                  </p>
                </div>

                <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300 mb-2">
                    <Activity className="w-4 h-4" />
                    <span className="text-sm font-medium">Avg Latency</span>
                  </div>
                  <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                    {Math.round(averages.latency)} <span className="text-sm">ms</span>
                  </p>
                </div>
              </div>
            )}

            {/* Speed Test Table */}
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Date & Time
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Download
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Upload
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Latency
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Jitter
                    </th>
                    <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Quality
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {speedTests.map((test: SpeedTest) => (
                    <tr
                      key={test.id}
                      className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                    >
                      <td className="py-3 px-4 text-sm text-gray-900 dark:text-gray-100">
                        {formatDate(test.tested_at)}
                      </td>
                      <td className="py-3 px-4 text-sm text-right font-medium text-blue-600 dark:text-blue-400">
                        {formatSpeed(test.download_speed)} Mbps
                      </td>
                      <td className="py-3 px-4 text-sm text-right font-medium text-green-600 dark:text-green-400">
                        {formatSpeed(test.upload_speed)} Mbps
                      </td>
                      <td className="py-3 px-4 text-sm text-right text-gray-700 dark:text-gray-300">
                        {test.latency} ms
                      </td>
                      <td className="py-3 px-4 text-sm text-right text-gray-700 dark:text-gray-300">
                        {test.jitter ? `${test.jitter} ms` : '-'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getQualityColor(test.quality)}`}>
                          {test.quality.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Info */}
            <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                Quality Criteria:
              </h4>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>
                  <span className="font-medium text-green-600 dark:text-green-400">Good:</span> Download ≥ 25 Mbps, Upload ≥ 10 Mbps
                </li>
                <li>
                  <span className="font-medium text-yellow-600 dark:text-yellow-400">Fair:</span> Download ≥ 10 Mbps, Upload ≥ 5 Mbps
                </li>
                <li>
                  <span className="font-medium text-red-600 dark:text-red-400">Poor:</span> Below fair criteria
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex justify-between items-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Showing last {speedTests?.length || 0} speed tests
          </p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}
