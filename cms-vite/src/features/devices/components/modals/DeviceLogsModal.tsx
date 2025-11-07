/**
 * Device Logs Modal Component
 *
 * View device activity logs and events
 */

import { useState } from 'react';
import { X, Terminal, Filter, Loader2, Calendar, Activity } from 'lucide-react';
import { useDeviceLogs } from '../../hooks/useDevices';
import type { Device } from '../../types/device';

interface DeviceLogsModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

const EVENT_TYPES = [
  { value: '', label: 'All Events' },
  { value: 'activation', label: 'Activation' },
  { value: 'heartbeat', label: 'Heartbeat' },
  { value: 'command', label: 'Command' },
  { value: 'content_change', label: 'Content Change' },
  { value: 'error', label: 'Error' },
];

export function DeviceLogsModal({ isOpen, device, onClose }: DeviceLogsModalProps) {
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading } = useDeviceLogs(
    device?.id || 0,
    {
      event_type: eventTypeFilter || undefined,
      limit: 50,
    },
    isOpen && !!device
  );

  const logs = data?.items || [];

  if (!isOpen || !device) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <Terminal className="w-5 h-5" />
                Device Logs
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {device.device_name}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`px-3 py-2 rounded-lg border transition-colors ${
                  showFilters
                    ? 'bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-700 text-blue-700 dark:text-blue-200'
                    : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                <Filter className="w-4 h-4" />
              </button>
              <button
                onClick={onClose}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Event Type:
                </label>
                <select
                  value={eventTypeFilter}
                  onChange={(e) => setEventTypeFilter(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                >
                  {EVENT_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Logs Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No logs found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          log.event_type === 'error'
                            ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
                            : log.event_type === 'activation'
                            ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
                            : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {log.event_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                      <Calendar className="w-3 h-3" />
                      {new Date(log.created_at).toLocaleString()}
                    </div>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">{log.message}</p>
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <details className="mt-2">
                      <summary className="text-xs text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300">
                        View metadata
                      </summary>
                      <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-900 rounded text-xs overflow-x-auto">
                        {JSON.stringify(log.metadata, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex justify-between items-center text-sm text-gray-500 dark:text-gray-400">
            <span>
              Showing {logs.length} log{logs.length !== 1 ? 's' : ''}
            </span>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
