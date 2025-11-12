/**
 * Schedules Page
 * Main page for schedule management
 */

import { useState } from 'react'
import {
  useSchedules,
  useOccurrences,
  useCreateSchedule,
  useUpdateSchedule,
  useDeleteSchedule,
  useActivateSchedule,
  useDeactivateSchedule,
  usePauseSchedule,
} from '../hooks/useSchedules'
import ScheduleList from '../components/ScheduleList'
import ScheduleForm from '../components/ScheduleForm'
import CalendarView from '../components/CalendarView'
import type {
  Schedule,
  CreateScheduleRequest,
  UpdateScheduleRequest,
  CalendarEvent,
} from '../types/schedule.types'

type ViewMode = 'list' | 'calendar'
type ModalMode = 'create' | 'edit' | 'view' | null

export const SchedulesPage = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [modalMode, setModalMode] = useState<ModalMode>(null)
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [selectedDate, setSelectedDate] = useState<Date>(new Date())

  // Calculate date range for calendar
  const startOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1)
  const endOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0)

  // Queries
  const { data, isLoading } = useSchedules()
  const occurrencesQuery = useOccurrences(
    {
      start_date: startOfMonth.toISOString().split('T')[0],
      end_date: endOfMonth.toISOString().split('T')[0],
    },
    viewMode === 'calendar'
  )

  // Mutations
  const createMutation = useCreateSchedule()
  const updateMutation = useUpdateSchedule()
  const deleteMutation = useDeleteSchedule()
  const activateMutation = useActivateSchedule()
  const deactivateMutation = useDeactivateSchedule()
  const pauseMutation = usePauseSchedule()

  // Handlers
  const handleCreate = () => {
    setModalMode('create')
    setSelectedSchedule(null)
  }

  const handleView = (schedule: Schedule) => {
    setModalMode('view')
    setSelectedSchedule(schedule)
  }

  const handleEdit = (schedule: Schedule) => {
    setModalMode('edit')
    setSelectedSchedule(schedule)
  }

  const handleDelete = (schedule: Schedule) => {
    setSelectedSchedule(schedule)
    setShowDeleteConfirm(true)
  }

  const handleActivate = async (schedule: Schedule) => {
    try {
      await activateMutation.mutateAsync(schedule.id)
    } catch (error) {
      console.error('Activate error:', error)
    }
  }

  const handleDeactivate = async (schedule: Schedule) => {
    try {
      await deactivateMutation.mutateAsync(schedule.id)
    } catch (error) {
      console.error('Deactivate error:', error)
    }
  }

  const handlePause = async (schedule: Schedule) => {
    try {
      await pauseMutation.mutateAsync(schedule.id)
    } catch (error) {
      console.error('Pause error:', error)
    }
  }

  const handleSubmit = async (
    formData: CreateScheduleRequest | UpdateScheduleRequest
  ) => {
    try {
      if (modalMode === 'create') {
        await createMutation.mutateAsync(formData as CreateScheduleRequest)
      } else if (modalMode === 'edit' && selectedSchedule) {
        await updateMutation.mutateAsync({
          id: selectedSchedule.id,
          data: formData as UpdateScheduleRequest,
        })
      }
      setModalMode(null)
      setSelectedSchedule(null)
    } catch (error) {
      console.error('Submit error:', error)
    }
  }

  const confirmDelete = async () => {
    if (!selectedSchedule) return

    try {
      await deleteMutation.mutateAsync(selectedSchedule.id)
      setShowDeleteConfirm(false)
      setSelectedSchedule(null)
    } catch (error) {
      console.error('Delete error:', error)
    }
  }

  // Convert occurrences to calendar events
  const calendarEvents: CalendarEvent[] = occurrencesQuery.data?.occurrences.map((occurrence) => ({
    id: occurrence.schedule_id,
    title: `${occurrence.schedule_name} - ${occurrence.playlist_name}`,
    start: new Date(`${occurrence.occurrence_date}T${occurrence.start_time}`),
    end: new Date(`${occurrence.occurrence_date}T${occurrence.end_time}`),
    schedule: data?.schedules.find(s => s.id === occurrence.schedule_id) || {} as Schedule,
  })) || []

  const schedules = data?.schedules || []

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Schedule Manager</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Create and manage automated content playback schedules
            </p>
          </div>
          <div className="flex gap-3">
            {/* View Mode Toggle */}
            <div className="inline-flex rounded-lg border border-gray-200 dark:border-gray-700">
              <button
                onClick={() => setViewMode('list')}
                className={`px-4 py-2 text-sm font-medium rounded-l-lg ${
                  viewMode === 'list'
                    ? 'bg-purple-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                📋 List
              </button>
              <button
                onClick={() => setViewMode('calendar')}
                className={`px-4 py-2 text-sm font-medium rounded-r-lg ${
                  viewMode === 'calendar'
                    ? 'bg-purple-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                📅 Calendar
              </button>
            </div>

            {/* Create Button */}
            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
            >
              <span>➕</span>
              <span>Create Schedule</span>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
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
        />
      ) : (
        <CalendarView
          events={calendarEvents}
          selectedDate={selectedDate}
          onDateSelect={setSelectedDate}
          onEventClick={(event) => {
            const schedule = schedules.find(s => s.id === event.schedule.id)
            if (schedule) handleView(schedule)
          }}
          isLoading={occurrencesQuery.isLoading}
        />
      )}

      {/* Create/Edit Modal */}
      {(modalMode === 'create' || modalMode === 'edit') && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-5xl w-full my-8">
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 rounded-t-lg">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {modalMode === 'create' ? 'Create Schedule' : 'Edit Schedule'}
              </h2>
            </div>
            <div className="p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
              <ScheduleForm
                schedule={selectedSchedule || undefined}
                onSubmit={handleSubmit}
                onCancel={() => {
                  setModalMode(null)
                  setSelectedSchedule(null)
                }}
                isLoading={createMutation.isPending || updateMutation.isPending}
              />
            </div>
          </div>
        </div>
      )}

      {/* View Modal */}
      {modalMode === 'view' && selectedSchedule && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 rounded-t-lg flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Schedule Details</h2>
              <button
                onClick={() => {
                  setModalMode(null)
                  setSelectedSchedule(null)
                }}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Basic Information</h3>
                <dl className="grid grid-cols-1 gap-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Name</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-white">{selectedSchedule.name}</dd>
                  </div>
                  {selectedSchedule.description && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Description</dt>
                      <dd className="mt-1 text-sm text-gray-900 dark:text-white">{selectedSchedule.description}</dd>
                    </div>
                  )}
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</dt>
                    <dd className="mt-1">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        selectedSchedule.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : selectedSchedule.status === 'paused'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                      }`}>
                        {selectedSchedule.status}
                      </span>
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Timing */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Timing</h3>
                <dl className="grid grid-cols-2 gap-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Start Date</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                      {new Date(selectedSchedule.start_date).toLocaleDateString()}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">End Date</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                      {selectedSchedule.end_date
                        ? new Date(selectedSchedule.end_date).toLocaleDateString()
                        : 'No end date'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Daily Time</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                      {selectedSchedule.start_time} - {selectedSchedule.end_time}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Timezone</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-white">{selectedSchedule.timezone}</dd>
                  </div>
                </dl>
              </div>

              {/* Recurrence */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Recurrence</h3>
                <p className="text-sm text-gray-900 dark:text-white">
                  Type: <strong className="capitalize">{selectedSchedule.recurrence_type}</strong>
                </p>
                {selectedSchedule.recurrence_pattern && (
                  <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-700 rounded text-xs overflow-x-auto text-gray-900 dark:text-white">
                    {JSON.stringify(selectedSchedule.recurrence_pattern, null, 2)}
                  </pre>
                )}
              </div>

              {/* Assigned Resources */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Assigned Resources</h3>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Playlist</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                      {selectedSchedule.playlist_name || `Playlist #${selectedSchedule.playlist_id}`}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Devices</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                      {selectedSchedule.device_ids.length} device(s) assigned
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => {
                    setModalMode('edit')
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Edit Schedule
                </button>
                <button
                  onClick={() => {
                    setModalMode(null)
                    setSelectedSchedule(null)
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && selectedSchedule && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Delete Schedule</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to delete this schedule? This action cannot be undone.
            </p>
            <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded p-3 mb-6">
              <p className="text-sm font-medium text-gray-900 dark:text-white">{selectedSchedule.name}</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                {selectedSchedule.recurrence_type} • {selectedSchedule.device_ids.length} device(s)
              </p>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false)
                  setSelectedSchedule(null)
                }}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
              >
                {deleteMutation.isPending && (
                  <svg
                    className="animate-spin h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                )}
                Delete Schedule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SchedulesPage