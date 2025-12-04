// ✅ REFACTORED: Migrated to shared Modal component
/**
 * Schedule View Modal Component
 * Display schedule details in a modal
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Eye } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { getScheduleStatus, DEFAULT_SCHEDULE_COLOR, type Schedule } from '../types/schedule.types';
import { SchedulePreviewCalendar } from './SchedulePreviewCalendar';
import { useNextOccurrences, useSchedulePreview } from '../hooks/useAdvancedSchedules';

interface ScheduleViewModalProps {
  isOpen: boolean;
  schedule: Schedule;
  onClose: () => void;
  onEdit?: () => void; // Optional - only provided if user has edit permission
}

export function ScheduleViewModal({ isOpen, schedule, onClose, onEdit }: ScheduleViewModalProps) {
  const { t } = useTranslation();
  const [showPreview, setShowPreview] = useState(false);

  // Get schedule color
  const scheduleColor = schedule.color || DEFAULT_SCHEDULE_COLOR;

  // Derive status from is_active and dates
  const status = getScheduleStatus(schedule)

  // Fetch next occurrences (raw data)
  const { data: occurrencesData, isLoading: isLoadingPreview } = useNextOccurrences(
    Number(schedule.id),
    { enabled: showPreview && isOpen }
  );

  // Transform to preview format
  const previewOccurrences = useSchedulePreview(
    occurrencesData,
    scheduleColor
  );

  // Footer with action buttons
  const footer = (
    <div className="flex justify-between gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700" role="group" aria-label={t('schedules.viewModal.actions', 'Schedule actions')}>
      {/* Left: Preview Button */}
      <Button
        variant="outline"
        onClick={() => setShowPreview(!showPreview)}
        leftIcon={<Eye className="w-4 h-4" />}
        className="border-purple-300 dark:border-purple-600 text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20"
        aria-expanded={showPreview}
        aria-controls="schedule-preview-section"
        aria-label={showPreview ? t('schedules.actions.hidePreview') : t('schedules.actions.showPreview')}
      >
        {showPreview ? t('schedules.actions.hidePreview') : t('schedules.actions.showPreview')}
      </Button>

      {/* Right: Edit & Close */}
      <div className="flex gap-3" role="group" aria-label={t('schedules.viewModal.primaryActions', 'Primary actions')}>
        {onEdit && (
          <Button
            onClick={onEdit}
            aria-label={t('schedules.actions.editSchedule')}
          >
            {t('schedules.actions.editSchedule')}
          </Button>
        )}
        <Button
          variant="secondary"
          onClick={onClose}
          aria-label={t('schedules.viewModal.close')}
        >
          {t('schedules.viewModal.close')}
        </Button>
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
                    status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : status === 'paused'
                      ? 'bg-yellow-100 text-yellow-800'
                      : status === 'expired'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                  }`}>
                    {t(`schedules.status.${status}`)}
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
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
              {schedule.timezone && (
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    {t('schedules.viewModal.fields.timezone')}
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-white">{schedule.timezone}</dd>
                </div>
              )}
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
                color={scheduleColor}
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
