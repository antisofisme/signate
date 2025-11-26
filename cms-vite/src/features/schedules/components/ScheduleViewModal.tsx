/**
 * Schedule View Modal Component
 * Display schedule details in a modal
 */

import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';
import type { Schedule } from '../types/schedule.types';

interface ScheduleViewModalProps {
  schedule: Schedule;
  onClose: () => void;
  onEdit: () => void;
}

export function ScheduleViewModal({ schedule, onClose, onEdit }: ScheduleViewModalProps) {
  const { t } = useTranslation();

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 rounded-t-lg flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {t('schedules.viewModal.title')}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              {t('schedules.viewModal.sections.basicInfo')}
            </h3>
            <dl className="grid grid-cols-1 gap-3">
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {t('schedules.viewModal.fields.name')}
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white">{schedule.name}</dd>
              </div>
              {schedule.description && (
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    {t('schedules.viewModal.fields.description')}
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-white">{schedule.description}</dd>
                </div>
              )}
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {t('schedules.viewModal.fields.status')}
                </dt>
                <dd className="mt-1">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    schedule.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : schedule.status === 'paused'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                  }`}>
                    {t(`schedules.status.${schedule.status}`)}
                  </span>
                </dd>
              </div>
            </dl>
          </div>

          {/* Timing */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              {t('schedules.viewModal.sections.timing')}
            </h3>
            <dl className="grid grid-cols-2 gap-3">
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {t('schedules.viewModal.fields.startDate')}
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                  {new Date(schedule.start_date).toLocaleDateString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {t('schedules.viewModal.fields.endDate')}
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                  {schedule.end_date
                    ? new Date(schedule.end_date).toLocaleDateString()
                    : t('schedules.labels.noEndDate')}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {t('schedules.viewModal.fields.dailyTime')}
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                  {schedule.start_time} - {schedule.end_time}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {t('schedules.viewModal.fields.timezone')}
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white">{schedule.timezone}</dd>
              </div>
            </dl>
          </div>

          {/* Recurrence */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              {t('schedules.viewModal.sections.recurrence')}
            </h3>
            <p className="text-sm text-gray-900 dark:text-white">
              {t('schedules.viewModal.fields.recurrenceType')}{' '}
              <strong className="capitalize">{schedule.recurrence_type}</strong>
            </p>
            {schedule.recurrence_pattern && (
              <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-700 rounded text-xs overflow-x-auto text-gray-900 dark:text-white">
                {JSON.stringify(schedule.recurrence_pattern, null, 2)}
              </pre>
            )}
          </div>

          {/* Assigned Resources */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              {t('schedules.viewModal.sections.assignedResources')}
            </h3>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {t('schedules.viewModal.fields.playlist')}
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                  {schedule.playlist_name || `Playlist #${schedule.playlist_id}`}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {t('schedules.viewModal.fields.devices')}
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                  {t(
                    schedule.device_ids.length !== 1
                      ? 'schedules.viewModal.fields.devicesAssigned_plural'
                      : 'schedules.viewModal.fields.devicesAssigned',
                    { count: schedule.device_ids.length }
                  )}
                </dd>
              </div>
            </dl>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={onEdit}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              {t('schedules.actions.editSchedule')}
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              {t('schedules.viewModal.close')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ScheduleViewModal;
