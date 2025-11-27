// ✅ REFACTORED: Migrated to shared Modal component
/**
 * Schedule View Modal Component
 * Display schedule details in a modal
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Eye } from 'lucide-react';
import { Modal } from '@/shared/components';
import type { Schedule } from '../types/schedule.types';
import { SchedulePreviewCalendar } from './SchedulePreviewCalendar';
import { useNextOccurrences, useSchedulePreview } from '../hooks/useAdvancedSchedules';

interface ScheduleViewModalProps {
  isOpen: boolean;
  schedule: Schedule;
  onClose: () => void;
  onEdit: () => void;
}

export function ScheduleViewModal({ isOpen, schedule, onClose, onEdit }: ScheduleViewModalProps) {
  const { t } = useTranslation();
  const [showPreview, setShowPreview] = useState(false);

  // Map priority level to number
  const priorityMap: Record<string, number> = {
    low: 1,
    normal: 2,
    high: 3,
    critical: 4
  };

  // Fetch next occurrences (raw data)
  const { data: occurrencesData, isLoading: isLoadingPreview } = useNextOccurrences(
    Number(schedule.id),
    { enabled: showPreview && isOpen }
  );

  // Transform to preview format
  const previewOccurrences = useSchedulePreview(
    occurrencesData,
    priorityMap[schedule.priority] || 2
  );

  // Footer with action buttons
  const footer = (
    <div className="flex justify-between gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700" role="group" aria-label={t('schedules.viewModal.actions', 'Schedule actions')}>
      {/* Left: Preview Button */}
      <button
        onClick={() => setShowPreview(!showPreview)}
        className="px-4 py-2 flex items-center gap-2 border border-purple-300 dark:border-purple-600 text-purple-700 dark:text-purple-300 rounded-md hover:bg-purple-50 dark:hover:bg-purple-900/20 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
        aria-expanded={showPreview}
        aria-controls="schedule-preview-section"
        aria-label={showPreview ? t('schedules.actions.hidePreview') : t('schedules.actions.showPreview')}
      >
        <Eye className="w-4 h-4" aria-hidden="true" />
        {showPreview ? t('schedules.actions.hidePreview') : t('schedules.actions.showPreview')}
      </button>

      {/* Right: Edit & Close */}
      <div className="flex gap-3" role="group" aria-label={t('schedules.viewModal.primaryActions', 'Primary actions')}>
        <button
          onClick={onEdit}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          aria-label={t('schedules.actions.editSchedule')}
        >
          {t('schedules.actions.editSchedule')}
        </button>
        <button
          onClick={onClose}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          aria-label={t('schedules.viewModal.close')}
        >
          {t('schedules.viewModal.close')}
        </button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t('schedules.viewModal.title')}
      footer={footer}
      maxWidth="2xl"
    >
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
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

        {/* Preview Calendar */}
        {showPreview && (
          <div id="schedule-preview-section" className="pt-6 border-t border-gray-200 dark:border-gray-700" role="region" aria-label={t('schedules.previewCalendar.title', 'Schedule preview calendar')}>
            {isLoadingPreview ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin h-8 w-8 border-4 border-purple-500 border-t-transparent rounded-full"></div>
                <span className="ml-3 text-gray-600 dark:text-gray-400">{t('schedules.previewCalendar.loadingPreview')}</span>
              </div>
            ) : previewOccurrences.length > 0 ? (
              <SchedulePreviewCalendar
                occurrences={previewOccurrences}
                playlistName={schedule.playlist_name}
                priority={priorityMap[schedule.priority] || 2}
                exceptionDates={schedule.exception_dates || []}
              />
            ) : null}
          </div>
        )}
      </div>
    </Modal>
  );
}

export default ScheduleViewModal;
