/**
 * Live Device Monitor Component
 *
 * LAYER 1: PRESENTATION
 * Real-time device monitoring table
 */

import { useState } from 'react';
import { Monitor, MapPin, Activity, Cpu, HardDrive, Eye } from 'lucide-react';
import { LiveDevice } from '../api/dashboard.api';
import { formatDistanceToNow } from 'date-fns';

interface LiveDeviceMonitorProps {
  devices: LiveDevice[] | undefined;
  isLoading: boolean;
}

export default function LiveDeviceMonitor({ devices, isLoading }: LiveDeviceMonitorProps) {
  const [filter, setFilter] = useState<'all' | 'online' | 'offline' | 'warning' | 'error'>('all');

  const filteredDevices = devices?.filter((device) => {
    if (filter === 'all') return true;
    return device.status === filter;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
      case 'warning':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400';
      case 'error':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
      case 'offline':
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-400';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-400';
    }
  };

  const getUsageColor = (usage: number | null) => {
    if (!usage) return 'bg-gray-300 dark:bg-gray-600';
    if (usage < 50) return 'bg-green-500 dark:bg-green-600';
    if (usage < 80) return 'bg-yellow-500 dark:bg-yellow-600';
    return 'bg-red-500 dark:bg-red-600';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Live Device Monitor
        </h2>

        {/* Filter Buttons */}
        <div className="flex gap-2">
          {['all', 'online', 'warning', 'error', 'offline'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status as any)}
              className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors ${
                filter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                Device
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                Status
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                Location
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                Current Content
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                System
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 dark:text-white">
                Last Seen
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, index) => (
                <tr key={index} className="border-b border-gray-200 dark:border-gray-700">
                  <td colSpan={6} className="py-4">
                    <div className="h-16 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
                  </td>
                </tr>
              ))
            ) : filteredDevices && filteredDevices.length > 0 ? (
              filteredDevices.map((device) => (
                <tr
                  key={device.id}
                  className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Monitor className="w-4 h-4 text-gray-400" />
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {device.name}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                        device.status
                      )}`}
                    >
                      {device.status}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                      <MapPin className="w-3 h-3" />
                      {device.location}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                      <Eye className="w-3 h-3" />
                      {device.current_content || '-'}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="space-y-1">
                      {/* CPU Usage */}
                      <div className="flex items-center gap-2">
                        <Cpu className="w-3 h-3 text-gray-400" />
                        <div className="flex-1">
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                            <div
                              className={`h-1.5 rounded-full transition-all ${getUsageColor(
                                device.cpu_usage
                              )}`}
                              style={{ width: `${device.cpu_usage || 0}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400 w-8">
                          {device.cpu_usage ? `${device.cpu_usage}%` : '-'}
                        </span>
                      </div>
                      {/* Storage Usage */}
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-3 h-3 text-gray-400" />
                        <div className="flex-1">
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                            <div
                              className={`h-1.5 rounded-full transition-all ${getUsageColor(
                                device.storage_usage
                              )}`}
                              style={{ width: `${device.storage_usage || 0}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400 w-8">
                          {device.storage_usage ? `${device.storage_usage}%` : '-'}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {formatDistanceToNow(new Date(device.last_seen_at), { addSuffix: true })}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-500 dark:text-gray-400">
                  No devices found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="h-32 bg-gray-200 dark:bg-gray-700 animate-pulse rounded-lg" />
          ))
        ) : filteredDevices && filteredDevices.length > 0 ? (
          filteredDevices.map((device) => (
            <div
              key={device.id}
              className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Monitor className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {device.name}
                  </span>
                </div>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                    device.status
                  )}`}
                >
                  {device.status}
                </span>
              </div>
              <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
                <div className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {device.location}
                </div>
                {device.current_content && (
                  <div className="flex items-center gap-1">
                    <Eye className="w-3 h-3" />
                    {device.current_content}
                  </div>
                )}
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {formatDistanceToNow(new Date(device.last_seen_at), { addSuffix: true })}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">No devices found</div>
        )}
      </div>
    </div>
  );
}
