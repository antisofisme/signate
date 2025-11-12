/**
 * Device Health Overview Component
 *
 * LAYER 1: PRESENTATION
 * Device health summary with donut chart and top issues
 */

import { CheckCircle, AlertTriangle, XCircle, WifiOff } from 'lucide-react';
import { DeviceHealthSummary } from '../api/dashboard.api';

interface DeviceHealthOverviewProps {
  data: DeviceHealthSummary | undefined;
  isLoading: boolean;
}

export default function DeviceHealthOverview({ data, isLoading }: DeviceHealthOverviewProps) {
  const total = data ? data.healthy + data.warning + data.error + data.offline : 0;

  const getPercentage = (value: number) => {
    if (!total) return 0;
    return Math.round((value / total) * 100);
  };

  const healthStats = [
    {
      label: 'Healthy',
      value: data?.healthy || 0,
      percentage: getPercentage(data?.healthy || 0),
      icon: CheckCircle,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
    {
      label: 'Warning',
      value: data?.warning || 0,
      percentage: getPercentage(data?.warning || 0),
      icon: AlertTriangle,
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    },
    {
      label: 'Error',
      value: data?.error || 0,
      percentage: getPercentage(data?.error || 0),
      icon: XCircle,
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
    },
    {
      label: 'Offline',
      value: data?.offline || 0,
      percentage: getPercentage(data?.offline || 0),
      icon: WifiOff,
      color: 'text-gray-600 dark:text-gray-400',
      bgColor: 'bg-gray-100 dark:bg-gray-700',
    },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
        Device Health Overview
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Health Stats */}
        <div className="space-y-4">
          {healthStats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="flex items-center gap-4">
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {stat.label}
                    </span>
                    <span className="text-sm font-semibold text-gray-900 dark:text-white">
                      {isLoading ? '-' : `${stat.value} (${stat.percentage}%)`}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${
                        stat.label === 'Healthy'
                          ? 'bg-green-500 dark:bg-green-600'
                          : stat.label === 'Warning'
                          ? 'bg-yellow-500 dark:bg-yellow-600'
                          : stat.label === 'Error'
                          ? 'bg-red-500 dark:bg-red-600'
                          : 'bg-gray-500 dark:bg-gray-600'
                      }`}
                      style={{ width: `${stat.percentage}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Top Issues */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
            Top Issues
          </h3>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
              ))}
            </div>
          ) : data?.issues && data.issues.length > 0 ? (
            <div className="space-y-3">
              {data.issues.slice(0, 5).map((issue, index) => (
                <div
                  key={index}
                  className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {issue.type}
                    </span>
                    <span className="text-xs font-semibold text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 px-2 py-1 rounded">
                      {issue.count} {issue.count === 1 ? 'device' : 'devices'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {issue.devices.slice(0, 3).join(', ')}
                    {issue.devices.length > 3 && ` +${issue.devices.length - 3} more`}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 dark:text-green-400 mb-3" />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No issues detected
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
