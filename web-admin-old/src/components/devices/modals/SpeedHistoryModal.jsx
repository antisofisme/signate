import { useQuery } from '@tanstack/react-query'
import { devicesAPI } from '../../../services/api'
import { Modal, Button } from '../../shared'
import { Activity, Download, Upload, Clock, Server, Wifi } from 'lucide-react'

/**
 * SpeedHistoryModal Component
 * Displays speed test history for a device
 *
 * Features:
 * - Shows list of speed tests ordered by date (newest first)
 * - Displays download/upload speeds, quality, latency, jitter
 * - Auto-refreshes every 60 seconds
 * - Responsive table design
 *
 * @param {Object} device - Device object
 * @param {Function} onClose - Callback when modal should close
 */
export default function SpeedHistoryModal({ device, onClose }) {
  // Fetch speed test history (last 20 tests)
  const { data: historyData, isLoading } = useQuery({
    queryKey: ['devices', device.id, 'speedtest', 'history'],
    queryFn: () => devicesAPI.getSpeedTests(device.id, 20).then(res => res.data),
    refetchInterval: 10000, // Auto-refresh every 10 seconds
  })

  const getQualityBadge = (quality) => {
    const classes = quality === 'good'
      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
      : quality === 'fair'
      ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
      : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'

    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${classes}`}>
        {quality}
      </span>
    )
  }

  // Footer with close button
  const footer = (
    <div className="flex justify-end">
      <Button onClick={onClose} variant="primary">
        Close
      </Button>
    </div>
  )

  return (
    <Modal
      isOpen={true}
      title={
        <div className="flex items-center gap-2">
          <Activity className="w-6 h-6 text-blue-600" />
          <span>Speed Test History - {device.device_name}</span>
        </div>
      }
      onClose={onClose}
      size="4xl"
      footer={footer}
    >
      {/* Content */}
      <div className="p-6">
        {isLoading ? (
          <div className="text-center text-gray-500 dark:text-gray-400 py-12">
            <Activity className="w-12 h-12 mx-auto mb-3 animate-pulse opacity-30" />
            <p>Loading speed test history...</p>
          </div>
        ) : !historyData || historyData.total === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 py-12">
            <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No speed test history available</p>
            <p className="text-sm mt-1">Viewer will perform speed test every 30 minutes</p>
          </div>
        ) : (
          <div>
            <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
              Showing {historyData.items.length} of {historyData.total} total tests
            </div>

            {/* Speed Test History Table */}
            <div className="overflow-x-auto -mx-6 px-6">
              <div className="inline-block min-w-full align-middle">
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
                <thead className="bg-gray-50 dark:bg-gray-800 border-b dark:border-gray-700">
                  <tr>
                    <th className="px-2 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                      <Clock className="w-4 h-4 inline mr-1" />
                      Tested At
                    </th>
                    <th className="px-2 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                      <Download className="w-4 h-4 inline mr-1" />
                      Download
                    </th>
                    <th className="px-2 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                      <Upload className="w-4 h-4 inline mr-1" />
                      Upload
                    </th>
                    <th className="px-2 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                      Quality
                    </th>
                    <th className="px-2 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                      <Wifi className="w-4 h-4 inline mr-1" />
                      Metrics
                    </th>
                    <th className="px-2 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                      <Server className="w-4 h-4 inline mr-1" />
                      DNS
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {historyData.items.map((test) => (
                    <tr key={test.id} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                      <td className="px-2 py-2 whitespace-nowrap text-gray-900 dark:text-gray-100">
                        <div className="text-sm">{new Date(test.tested_at).toLocaleDateString()}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(test.tested_at).toLocaleTimeString()}
                        </div>
                      </td>
                      <td className="px-2 py-2 whitespace-nowrap">
                        <div className="text-sm font-semibold text-green-600 dark:text-green-400">
                          {test.download_speed.toFixed(2)} Mbps
                        </div>
                      </td>
                      <td className="px-2 py-2 whitespace-nowrap">
                        <div className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                          {test.upload_speed.toFixed(2)} Mbps
                        </div>
                      </td>
                      <td className="px-2 py-2 whitespace-nowrap">
                        {getQualityBadge(test.quality)}
                      </td>
                      <td className="px-2 py-2 text-xs text-gray-600 dark:text-gray-400">
                        {test.latency && <div>Latency: {test.latency}ms</div>}
                        {test.jitter && <div>Jitter: {test.jitter}ms</div>}
                        {test.packet_loss !== null && <div>Loss: {test.packet_loss}%</div>}
                        {!test.latency && !test.jitter && !test.packet_loss && (
                          <div className="text-gray-400 dark:text-gray-500">-</div>
                        )}
                      </td>
                      <td className="px-2 py-2 text-xs text-gray-600 dark:text-gray-400 font-mono">
                        {test.dns_server || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
                </div>
              </div>
            </div>

            {/* Quality Legend */}
            <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Quality Thresholds:</div>
              <div className="grid grid-cols-3 gap-4 text-xs text-gray-600 dark:text-gray-400">
                <div>
                  <span className="inline-block w-3 h-3 bg-green-500 rounded mr-1"></span>
                  <span className="font-medium">Good:</span> Download ≥25 Mbps AND Upload ≥10 Mbps
                </div>
                <div>
                  <span className="inline-block w-3 h-3 bg-yellow-500 rounded mr-1"></span>
                  <span className="font-medium">Fair:</span> Download ≥10 Mbps AND Upload ≥5 Mbps
                </div>
                <div>
                  <span className="inline-block w-3 h-3 bg-red-500 rounded mr-1"></span>
                  <span className="font-medium">Poor:</span> Below fair thresholds
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}
