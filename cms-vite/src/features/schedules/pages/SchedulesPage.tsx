/**
 * Schedules Page
 *
 * LAYER 1: PRESENTATION
 * Main page for schedule management - orchestration only
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ClipboardList, Calendar, Plus } from 'lucide-react';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { AccessDenied, ConfirmDialog, ErrorDisplay, PageSkeleton } from '@/shared/components';
import {
  useSchedules,
  useOccurrences,
  useCreateSchedule,
  useUpdateSchedule,
  useDeleteSchedule,
  useActivateSchedule,
  useDeactivateSchedule,
  usePauseSchedule,
} from '../hooks/useSchedules';
import ScheduleList from '../components/ScheduleList';
import CalendarView from '../components/CalendarView';
import { ScheduleFormModal } from '../components/ScheduleFormModal';
import { ScheduleViewModal } from '../components/ScheduleViewModal';
import type {
  Schedule,
  CreateScheduleRequest,
  UpdateScheduleRequest,
  CalendarEvent,
} from '../types/schedule.types';

type ViewMode = 'list' | 'calendar';
type ModalMode = 'create' | 'edit' | 'view' | null;

export const SchedulesPage = () => {
  const { t } = useTranslation();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  // Check permissions
  const { hasPermission: canView, isLoading: loadingViewPerm } = useCanPerformAction('schedules', 'read');
  const { hasPermission: canCreate } = useCanPerformAction('schedules', 'create');
  const { hasPermission: canEdit } = useCanPerformAction('schedules', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('schedules', 'delete');

  // Show loading state while checking permissions
  if (loadingViewPerm) {
    return <PageSkeleton />;
  }

  // Return access denied if no view permission
  if (!canView) {
    return <AccessDenied />;
  }

  // Calculate date range for calendar
  const startOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
  const endOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0);

  // Queries
  const { data, isLoading, error, refetch } = useSchedules();
  const occurrencesQuery = useOccurrences(
    {
      start_date: startOfMonth.toISOString().split('T')[0],
      end_date: endOfMonth.toISOString().split('T')[0],
    },
    viewMode === 'calendar'
  );

  // Mutations
  const createMutation = useCreateSchedule();
  const updateMutation = useUpdateSchedule();
  const deleteMutation = useDeleteSchedule();
  const activateMutation = useActivateSchedule();
  const deactivateMutation = useDeactivateSchedule();
  const pauseMutation = usePauseSchedule();

  // Handlers
  const handleCreate = () => {
    setModalMode('create');
    setSelectedSchedule(null);
  };

  const handleView = (schedule: Schedule) => {
    setModalMode('view');
    setSelectedSchedule(schedule);
  };

  const handleEdit = (schedule: Schedule) => {
    setModalMode('edit');
    setSelectedSchedule(schedule);
  };

  const handleDelete = (schedule: Schedule) => {
    setSelectedSchedule(schedule);
    setShowDeleteConfirm(true);
  };

  const handleActivate = async (schedule: Schedule) => {
    await activateMutation.mutateAsync(schedule.id);
  };

  const handleDeactivate = async (schedule: Schedule) => {
    await deactivateMutation.mutateAsync(schedule.id);
  };

  const handlePause = async (schedule: Schedule) => {
    await pauseMutation.mutateAsync(schedule.id);
  };

  const handleSubmit = async (formData: CreateScheduleRequest | UpdateScheduleRequest) => {
    if (modalMode === 'create') {
      await createMutation.mutateAsync(formData as CreateScheduleRequest);
    } else if (modalMode === 'edit' && selectedSchedule) {
      await updateMutation.mutateAsync({
        id: selectedSchedule.id,
        data: formData as UpdateScheduleRequest,
      });
    }
    setModalMode(null);
    setSelectedSchedule(null);
  };

  const confirmDelete = async () => {
    if (!selectedSchedule) return;
    await deleteMutation.mutateAsync(selectedSchedule.id);
    setShowDeleteConfirm(false);
    setSelectedSchedule(null);
  };

  // Convert occurrences to calendar events
  const calendarEvents: CalendarEvent[] =
    occurrencesQuery.data?.occurrences.map((occurrence) => ({
      id: occurrence.schedule_id,
      title: `${occurrence.schedule_name} - ${occurrence.playlist_name}`,
      start: new Date(`${occurrence.occurrence_date}T${occurrence.start_time}`),
      end: new Date(`${occurrence.occurrence_date}T${occurrence.end_time}`),
      schedule: data?.schedules.find((s) => s.id === occurrence.schedule_id) || ({} as Schedule),
    })) || [];

  const schedules = data?.schedules || [];

  return (
    <>
      {/* Action Bar */}
      <div className="mb-6 flex justify-between items-center">
        {/* View Mode Toggle */}
        <div className="inline-flex rounded-lg border border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setViewMode('list')}
            className={`px-4 py-2 text-sm font-medium rounded-l-lg flex items-center gap-2 ${
              viewMode === 'list'
                ? 'bg-purple-600 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            <ClipboardList className="w-4 h-4" />
            {t('schedules.page.listView')}
          </button>
          <button
            onClick={() => setViewMode('calendar')}
            className={`px-4 py-2 text-sm font-medium rounded-r-lg flex items-center gap-2 ${
              viewMode === 'calendar'
                ? 'bg-purple-600 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            <Calendar className="w-4 h-4" />
            {t('schedules.page.calendarView')}
          </button>
        </div>

        {/* Create Button */}
        {canCreate && (
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            <span>{t('schedules.createSchedule')}</span>
          </button>
        )}
      </div>

      {/* Error State */}
      {error && (
        <ErrorDisplay
          error={error}
          onRetry={refetch}
          title={t('schedules.messages.loadError', 'Failed to load schedules')}
        />
      )}

      {/* Content */}
      {!error && (
      <div className="space-y-6">
        {viewMode === 'list' ? (
          <ScheduleList
            schedules={schedules}
            isLoading={isLoading}
            onView={handleView}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onActivate={handleActivate}
            onDeactivate={handleDeactivate}
            onPause={handlePause}
            canUpdate={canEdit}
            canDelete={canDelete}
          />
        ) : (
          <CalendarView
            events={calendarEvents}
            selectedDate={selectedDate}
            onDateSelect={setSelectedDate}
            onEventClick={(event) => {
              const schedule = schedules.find((s) => s.id === event.schedule.id);
              if (schedule) handleView(schedule);
            }}
            isLoading={occurrencesQuery.isLoading}
          />
        )}
      </div>
      )}

      {/* Modals */}
      {(modalMode === 'create' || modalMode === 'edit') && (
        <ScheduleFormModal
          mode={modalMode}
          schedule={selectedSchedule || undefined}
          isLoading={createMutation.isPending || updateMutation.isPending}
          onSubmit={handleSubmit}
          onCancel={() => {
            setModalMode(null);
            setSelectedSchedule(null);
          }}
        />
      )}

      {modalMode === 'view' && selectedSchedule && (
        <ScheduleViewModal
          isOpen={modalMode === 'view'}
          schedule={selectedSchedule}
          onClose={() => {
            setModalMode(null);
            setSelectedSchedule(null);
          }}
          onEdit={canEdit ? () => setModalMode('edit') : undefined}
        />
      )}

      {showDeleteConfirm && selectedSchedule && canDelete && (
        <ConfirmDialog
          open={showDeleteConfirm}
          onOpenChange={(open) => {
            setShowDeleteConfirm(open);
            if (!open) setSelectedSchedule(null);
          }}
          title={t('schedules.deleteModal.title')}
          description={t('schedules.deleteModal.confirmMessage') + '\n\n' +
            `${t('schedules.labels.name')}: ${selectedSchedule.name}\n` +
            `${t('schedules.labels.type')}: ${selectedSchedule.recurrence_type}\n` +
            `${t('schedules.labels.devices')}: ${selectedSchedule.device_ids.length} ${t(selectedSchedule.device_ids.length !== 1 ? 'schedules.devices' : 'schedules.device')}`
          }
          confirmLabel={t('schedules.deleteModal.deleteButton')}
          cancelLabel={t('schedules.deleteModal.cancel')}
          onConfirm={confirmDelete}
          isLoading={deleteMutation.isPending}
          variant="danger"
        />
      )}
    </>
  );
};

export default SchedulesPage;
