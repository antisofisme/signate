/**
 * Schedule Overview Widget Component
 *
 * LAYER 1: PRESENTATION
 * Schedule overview with active today list and status summary
 */

import { Calendar, Clock, Play, AlertTriangle, CheckCircle, ListVideo } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ScheduleOverview } from '../api/dashboard.api';

interface ScheduleOverviewWidgetProps {
  data: ScheduleOverview | undefined;
  isLoading: boolean;
}

export default function ScheduleOverviewWidget({ data, isLoading }: ScheduleOverviewWidgetProps) {
  const { t } = useTranslation();

  const formatTime = (time: string | null) => {
    if (!time) return t('dashboard.scheduleOverview.allDay', 'All Day');
    // Time is in HH:MM:SS format, convert to HH:MM
    return time.substring(0, 5);
  };

  const scheduleStats = [
    {
      label: t('dashboard.scheduleOverview.totalSchedules', 'Total Schedules'),
      value: data?.total_schedules || 0,
      icon: Calendar,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    },
    {
      label: t('dashboard.scheduleOverview.active', 'Active'),
      value: data?.active_schedules || 0,
      icon: CheckCircle,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
    {
      label: t('dashboard.scheduleOverview.runningNow', 'Running Now'),
      value: data?.running_now || 0,
      icon: Play,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    },
    {
      label: t('dashboard.scheduleOverview.endingSoon', 'Ending Soon'),
      value: data?.ending_soon || 0,
      icon: AlertTriangle,
      color: data?.ending_soon && data.ending_soon > 0
        ? 'text-orange-600 dark:text-orange-400'
        : 'text-gray-600 dark:text-gray-400',
      bgColor: data?.ending_soon && data.ending_soon > 0
        ? 'bg-orange-100 dark:bg-orange-900/30'
        : 'bg-gray-100 dark:bg-gray-700',
    },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
        {t('dashboard.scheduleOverview.title', 'Schedule Overview')}
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Schedule Stats */}
        <div className="grid grid-cols-2 gap-4">
          {scheduleStats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div
                key={stat.label}
                className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                    <Icon className={`w-5 h-5 ${stat.color}`} />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {isLoading ? '-' : stat.value}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {stat.label}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Active Today */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
            {t('dashboard.scheduleOverview.activeToday', 'Active Today')}
          </h3>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
              ))}
            </div>
          ) : data?.active_today && data.active_today.length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {data.active_today.map((schedule) => (
                <div
                  key={schedule.schedule_id}
                  className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {schedule.name}
                      </p>
                      {schedule.playlist_name && (
                        <div className="flex items-center gap-1 mt-1">
                          <ListVideo className="w-3 h-3 text-gray-400" />
                          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                            {schedule.playlist_name}
                          </p>
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end ml-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        schedule.priority >= 10
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                          : schedule.priority >= 5
                          ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}>
                        P{schedule.priority}
                      </span>
                      <div className="flex items-center gap-1 mt-1">
                        <Clock className="w-3 h-3 text-gray-400" />
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {formatTime(schedule.start_time)}
                          {schedule.end_time && ` - ${formatTime(schedule.end_time)}`}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Calendar className="w-12 h-12 text-gray-400 dark:text-gray-500 mb-3" />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('dashboard.scheduleOverview.noSchedules', 'No active schedules today')}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
