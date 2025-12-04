/**
 * Full Calendar View Component
 * Advanced calendar with FullCalendar library for drag-and-drop scheduling
 */

import { useRef, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import listPlugin from '@fullcalendar/list'
import { EventInput, EventClickArg, DateSelectArg, EventDropArg } from '@fullcalendar/core'
import type { EventResizeDoneArg } from '@fullcalendar/interaction'
import type { Schedule, ScheduleOccurrence } from '../types/schedule.types'
import { DEFAULT_SCHEDULE_COLOR } from '../types/schedule.types'

// Helper to darken a hex color for borders
const darkenColor = (hex: string, percent: number = 20): string => {
  // Remove # if present
  const cleanHex = hex.replace('#', '')
  const num = parseInt(cleanHex, 16)
  const amt = Math.round(2.55 * percent)
  const R = Math.max(0, (num >> 16) - amt)
  const G = Math.max(0, ((num >> 8) & 0x00FF) - amt)
  const B = Math.max(0, (num & 0x0000FF) - amt)
  return `#${(0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)}`
}

interface FullCalendarViewProps {
  schedules: Schedule[]
  occurrences: ScheduleOccurrence[]
  onEventClick?: (schedule: Schedule) => void
  onDateSelect?: (start: Date, end: Date) => void
  onEventDrop?: (scheduleId: number, newStart: Date, newEnd: Date) => void
  onEventResize?: (scheduleId: number, newStart: Date, newEnd: Date) => void
  view?: 'month' | 'week' | 'day' | 'list'
  editable?: boolean
  isLoading?: boolean
}

export function FullCalendarView({
  schedules,
  occurrences,
  onEventClick,
  onDateSelect,
  onEventDrop,
  onEventResize,
  view = 'month',
  editable = false,
  isLoading = false,
}: FullCalendarViewProps) {
  const { t } = useTranslation()
  const calendarRef = useRef<FullCalendar>(null)

  // Convert schedule occurrences to FullCalendar events
  const events: EventInput[] = useMemo(() => {
    return occurrences.map((occurrence) => {
      const schedule = schedules.find((s) => s.id === occurrence.schedule_id)
      const scheduleColor = schedule?.color || occurrence.color || DEFAULT_SCHEDULE_COLOR

      // Combine date with time for full DateTime
      const startDateTime = new Date(`${occurrence.occurrence_date}T${occurrence.start_time}`)
      const endDateTime = new Date(`${occurrence.occurrence_date}T${occurrence.end_time}`)

      return {
        id: `${occurrence.schedule_id}-${occurrence.occurrence_date}`,
        title: occurrence.schedule_name,
        start: startDateTime,
        end: endDateTime,
        backgroundColor: scheduleColor,
        borderColor: darkenColor(scheduleColor),
        textColor: '#FFFFFF',
        editable: editable,
        extendedProps: {
          scheduleId: occurrence.schedule_id,
          schedule,
          occurrence,
          color: scheduleColor,
          playlistName: occurrence.playlist_name,
          deviceCount: occurrence.devices.length,
        },
      }
    })
  }, [occurrences, schedules, editable])

  const handleEventClick = (info: EventClickArg) => {
    const schedule = info.event.extendedProps.schedule as Schedule
    if (schedule && onEventClick) {
      onEventClick(schedule)
    }
  }

  const handleDateSelect = (selectInfo: DateSelectArg) => {
    if (onDateSelect) {
      onDateSelect(selectInfo.start, selectInfo.end)
    }
    // Clear selection
    selectInfo.view.calendar.unselect()
  }

  const handleEventDrop = (info: EventDropArg) => {
    const scheduleId = info.event.extendedProps.scheduleId as number
    if (scheduleId && onEventDrop && info.event.start && info.event.end) {
      onEventDrop(scheduleId, info.event.start, info.event.end)
    } else {
      // Revert if no handler
      info.revert()
    }
  }

  const handleEventResize = (info: EventResizeDoneArg) => {
    const scheduleId = info.event.extendedProps.scheduleId as number
    if (scheduleId && onEventResize && info.event.start && info.event.end) {
      onEventResize(scheduleId, info.event.start, info.event.end)
    } else {
      // Revert if no handler
      info.revert()
    }
  }

  const initialView =
    view === 'month' ? 'dayGridMonth' :
    view === 'week' ? 'timeGridWeek' :
    view === 'day' ? 'timeGridDay' :
    'listWeek'

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          <span className="ml-3 text-gray-600 dark:text-gray-400">{t('schedules.fullCalendar.loadingCalendar')}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <style>{`
        /* FullCalendar Dark Mode Styles */
        .dark .fc {
          --fc-border-color: rgb(55, 65, 81);
          --fc-button-bg-color: rgb(37, 99, 235);
          --fc-button-border-color: rgb(37, 99, 235);
          --fc-button-hover-bg-color: rgb(29, 78, 216);
          --fc-button-hover-border-color: rgb(29, 78, 216);
          --fc-button-active-bg-color: rgb(30, 64, 175);
          --fc-button-active-border-color: rgb(30, 64, 175);
          --fc-today-bg-color: rgba(37, 99, 235, 0.1);
          --fc-neutral-bg-color: rgb(31, 41, 55);
          --fc-page-bg-color: rgb(31, 41, 55);
        }

        .dark .fc .fc-toolbar-title,
        .dark .fc .fc-col-header-cell-cushion,
        .dark .fc .fc-daygrid-day-number,
        .dark .fc .fc-timegrid-slot-label,
        .dark .fc .fc-list-day-text,
        .dark .fc .fc-list-day-side-text,
        .dark .fc .fc-list-event-title {
          color: rgb(243, 244, 246);
        }

        .dark .fc .fc-daygrid-day-bg,
        .dark .fc .fc-scrollgrid-section-body td,
        .dark .fc .fc-timegrid-body {
          background-color: rgb(31, 41, 55);
        }

        .dark .fc .fc-scrollgrid-sync-table {
          background-color: rgb(31, 41, 55);
        }

        /* Event styles */
        .fc-event {
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 0.875rem;
        }

        .fc-event:hover {
          transform: scale(1.02);
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .fc-event-title {
          font-weight: 500;
          padding: 2px 4px;
        }

        .fc-event-time {
          font-weight: 600;
          opacity: 0.9;
        }

        /* Dragging indicator */
        .fc-event-dragging {
          opacity: 0.75;
          cursor: move !important;
        }

        .fc-event-resizing {
          opacity: 0.75;
        }

        /* List view styles */
        .fc-list-event:hover td {
          background-color: rgba(37, 99, 235, 0.1);
        }

        .dark .fc-list-event:hover td {
          background-color: rgba(37, 99, 235, 0.2);
        }

        /* Time grid styles */
        .fc-timegrid-event {
          border-radius: 4px;
          padding: 2px 4px;
        }

        /* Day grid styles */
        .fc-daygrid-event {
          border-radius: 4px;
          padding: 2px 4px;
          margin: 1px 2px;
        }
      `}</style>

      <FullCalendar
        ref={calendarRef}
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin]}
        initialView={initialView}
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
        }}
        events={events}
        editable={editable}
        droppable={editable}
        selectable={true}
        selectMirror={true}
        dayMaxEvents={4}
        weekends={true}
        height="auto"
        nowIndicator={true}
        eventClick={handleEventClick}
        select={handleDateSelect}
        eventDrop={handleEventDrop}
        eventResize={handleEventResize}
        eventContent={(eventInfo) => {
          const { playlistName, deviceCount } = eventInfo.event.extendedProps
          const isTimeGrid = eventInfo.view.type.includes('timeGrid')
          const isDayGrid = eventInfo.view.type.includes('dayGrid')

          return (
            <div className="fc-event-main-frame w-full">
              <div className="fc-event-time text-xs font-semibold">
                {eventInfo.timeText}
              </div>
              <div className="fc-event-title-container">
                <div className="fc-event-title fc-sticky text-sm font-medium">
                  <span className="truncate">{eventInfo.event.title}</span>
                </div>
                {isTimeGrid && (
                  <div className="text-xs opacity-90 mt-1">
                    <div className="truncate">{playlistName}</div>
                    <div className="text-xs opacity-75 mt-0.5">
                      {deviceCount} device{deviceCount !== 1 ? 's' : ''}
                    </div>
                  </div>
                )}
                {isDayGrid && eventInfo.view.type !== 'dayGridMonth' && (
                  <div className="text-xs opacity-75 mt-0.5">
                    {deviceCount} device{deviceCount !== 1 ? 's' : ''}
                  </div>
                )}
              </div>
            </div>
          )
        }}
        // Localization
        locale="en"
        buttonText={{
          today: t('schedules.fullCalendar.buttons.today'),
          month: t('schedules.fullCalendar.buttons.month'),
          week: t('schedules.fullCalendar.buttons.week'),
          day: t('schedules.fullCalendar.buttons.day'),
          list: t('schedules.fullCalendar.buttons.list'),
        }}
        slotLabelFormat={{
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        }}
        eventTimeFormat={{
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        }}
        slotDuration="00:30:00"
        slotMinTime="00:00:00"
        slotMaxTime="24:00:00"
        allDaySlot={false}
      />

      {/* Calendar Legend */}
      <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <span className="font-semibold text-gray-700 dark:text-gray-300">
            {t('schedules.calendarLegend.scheduleColors')}:
          </span>
          <span className="text-gray-600 dark:text-gray-400">
            {t('schedules.calendarLegend.customColorsPerSchedule')}
          </span>
        </div>
        {editable && (
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            {t('schedules.fullCalendar.tip')}: {t('schedules.fullCalendar.tipMessage')}
          </div>
        )}
      </div>
    </div>
  )
}

export default FullCalendarView
