/**
 * System Alerts Panel Component
 *
 * LAYER 1: PRESENTATION
 * System alerts and notifications
 */

import { AlertTriangle, Info, AlertCircle, XCircle, Check } from 'lucide-react';
import { SystemAlert } from '../api/dashboard.api';
import { formatDistanceToNow } from 'date-fns';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { dashboardApi } from '../api/dashboard.api';

interface SystemAlertsPanelProps {
  data: SystemAlert[] | undefined;
  isLoading: boolean;
}

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'critical':
      return XCircle;
    case 'error':
      return AlertCircle;
    case 'warning':
      return AlertTriangle;
    case 'info':
    default:
      return Info;
  }
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border-red-500 dark:border-red-600';
    case 'error':
      return 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 border-red-400 dark:border-red-500';
    case 'warning':
      return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border-yellow-500 dark:border-yellow-600';
    case 'info':
    default:
      return 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border-blue-500 dark:border-blue-600';
  }
};

export default function SystemAlertsPanel({ data, isLoading }: SystemAlertsPanelProps) {
  const queryClient = useQueryClient();

  const acknowledgeMutation = useMutation({
    mutationFn: dashboardApi.acknowledgeAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'alerts'] });
    },
  });

  const unacknowledgedAlerts = data?.filter((alert) => !alert.acknowledged) || [];
  const acknowledgedAlerts = data?.filter((alert) => alert.acknowledged) || [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          System Alerts
        </h2>
        {unacknowledgedAlerts.length > 0 && (
          <span className="px-2.5 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs font-semibold rounded-full">
            {unacknowledgedAlerts.length} new
          </span>
        )}
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-20 bg-gray-200 dark:bg-gray-700 animate-pulse rounded-lg" />
          ))
        ) : data && data.length > 0 ? (
          <>
            {/* Unacknowledged Alerts */}
            {unacknowledgedAlerts.map((alert) => {
              const Icon = getSeverityIcon(alert.severity);
              return (
                <div
                  key={alert.id}
                  className={`p-4 rounded-lg border-l-4 ${getSeverityColor(alert.severity)}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1">
                      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                          {alert.title}
                        </h3>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          {alert.message}
                        </p>
                        {alert.device_name && (
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            Device: <span className="font-medium">{alert.device_name}</span>
                          </p>
                        )}
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => acknowledgeMutation.mutate(alert.id)}
                      disabled={acknowledgeMutation.isPending}
                      className="px-3 py-1 text-xs font-medium bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 flex items-center gap-1"
                    >
                      <Check className="w-3 h-3" />
                      Acknowledge
                    </button>
                  </div>
                </div>
              );
            })}

            {/* Acknowledged Alerts */}
            {acknowledgedAlerts.length > 0 && (
              <>
                {unacknowledgedAlerts.length > 0 && (
                  <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">
                      Acknowledged Alerts
                    </p>
                  </div>
                )}
                {acknowledgedAlerts.slice(0, 3).map((alert) => {
                  const Icon = getSeverityIcon(alert.severity);
                  return (
                    <div
                      key={alert.id}
                      className="p-3 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 opacity-60"
                    >
                      <div className="flex items-start gap-3">
                        <Icon className="w-4 h-4 flex-shrink-0 mt-0.5 text-gray-400" />
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            {alert.title}
                          </h3>
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                          </p>
                        </div>
                        <Check className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                      </div>
                    </div>
                  );
                })}
              </>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Check className="w-12 h-12 text-green-500 dark:text-green-400 mb-3" />
            <p className="text-sm text-gray-500 dark:text-gray-400">All systems operational</p>
          </div>
        )}
      </div>
    </div>
  );
}
