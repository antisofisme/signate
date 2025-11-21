# Advanced Schedule Features - Implementation Guide

## Overview

This document describes the comprehensive Advanced Schedule Features implementation for the CMS, including conflict detection, real-time validation, calendar preview, and active schedule monitoring.

## Features Implemented

### 1. Schedule Conflict Detector
**File**: `components/ScheduleConflictDetector.tsx`

**Features**:
- Real-time conflict detection with 500ms debouncing
- Visual severity indicators (Critical/Warning/Info)
- Expandable conflict list with schedule details
- Priority comparison to determine conflict severity
- Auto-refresh on form field changes
- Click-through to conflicting schedules

**Usage**:
```tsx
import { ScheduleConflictDetector } from '@/features/schedules/components'

<ScheduleConflictDetector
  playlistId={formData.playlist_id}
  startDate={formData.start_date}
  endDate={formData.end_date}
  startTime={formData.start_time}
  endTime={formData.end_time}
  recurrenceType={formData.recurrence_type}
  recurrencePattern={pattern}
  excludeScheduleId={scheduleId}
  onConflictClick={(id) => navigateToSchedule(id)}
/>
```

**Color Coding**:
- Red: Critical conflicts (same priority)
- Yellow: Warnings (different priority)
- Green: No conflicts

---

### 2. Schedule Preview Calendar
**File**: `components/SchedulePreviewCalendar.tsx`

**Features**:
- Month/week calendar view showing next 30 days
- Visual occurrence indicators with priority colors
- Exception dates display with strikethrough
- Hover tooltips with full details
- Date selection to view occurrence details
- Automatic month navigation
- Priority-based color coding

**Usage**:
```tsx
import { SchedulePreviewCalendar } from '@/features/schedules/components'
import { useSchedulePreview } from '@/features/schedules/hooks'

const previewOccurrences = useSchedulePreview(occurrencesData, priority)

<SchedulePreviewCalendar
  occurrences={previewOccurrences}
  playlistName="Morning Playlist"
  priority={50}
  exceptionDates={['2025-12-25', '2025-12-31']}
/>
```

**Priority Colors**:
- Red (75-100): Critical priority
- Orange (50-74): High priority
- Blue (25-49): Normal priority
- Gray (0-24): Low priority

---

### 3. Active Schedule Indicator
**File**: `components/ActiveScheduleIndicator.tsx`

**Features**:
- Real-time "What's playing now" display
- Auto-refresh every 1 minute
- Countdown to next schedule change
- Three display modes: Banner, Widget, Inline
- Live status badge
- Current time and priority display

**Display Modes**:

**Banner Mode** (Top of page):
```tsx
<ActiveScheduleIndicator
  mode="banner"
  onScheduleClick={(id) => viewSchedule(id)}
/>
```

**Widget Mode** (Dashboard/Sidebar):
```tsx
<ActiveScheduleIndicator
  mode="widget"
  autoRefresh={true}
  refreshInterval={60000}
/>
```

**Inline Mode** (List view):
```tsx
<ActiveScheduleIndicator
  mode="inline"
  onScheduleClick={(id) => viewSchedule(id)}
/>
```

---

### 4. Schedule Priority Manager
**File**: `components/SchedulePriorityManager.tsx`

**Features**:
- Visual priority slider (0-100)
- Quick adjustment buttons (+10, -10, Reset)
- Related schedules analysis
- Conflict warnings for similar priorities
- Priority level indicators (Low/Normal/High/Critical)
- Real-time conflict detection

**Usage**:
```tsx
import { SchedulePriorityManager } from '@/features/schedules/components'

<SchedulePriorityManager
  currentPriority={50}
  onPriorityChange={(priority) => setValue('priority', priority)}
  relatedSchedules={schedulesAtSameTime}
/>
```

**Priority Ranges**:
- 0-24: Low
- 25-49: Normal
- 50-74: High
- 75-100: Critical

---

### 5. Recurrence Pattern Builder
**File**: `components/RecurrencePatternBuilder.tsx`

**Features**:
- Visual pattern builder for all recurrence types
- Natural language preview
- Quick presets (Weekdays, Weekends, Every Day, etc.)
- Day-of-week checkboxes for weekly patterns
- Day-of-month selector for monthly patterns
- Cron expression support for custom patterns
- Automatic validation

**Pattern Types**:

**Daily**:
- Interval selector (every N days)

**Weekly**:
- Day-of-week multi-select (M T W T F S S)

**Monthly**:
- Specific day (1-31)
- Last day of month option

**Custom**:
- Cron expression input
- Link to crontab.guru for help

**Quick Presets**:
- Weekdays (Mon-Fri)
- Weekends (Sat-Sun)
- Every Day
- Every Other Day
- First of Month
- Last of Month

**Usage**:
```tsx
import { RecurrencePatternBuilder } from '@/features/schedules/components'

<RecurrencePatternBuilder
  recurrenceType="weekly"
  pattern={pattern}
  onPatternChange={(newPattern) => setPattern(newPattern)}
  disabled={isLoading}
/>
```

---

### 6. Enhanced Schedule Form
**File**: `components/ScheduleFormEnhanced.tsx`

**Features**:
- All basic schedule fields with validation
- Real-time conflict detection integration
- Live validation feedback (checkmarks/errors)
- Calendar preview toggle
- Priority manager integration
- Exception dates management
- Recurrence pattern builder
- Validation summary at top
- Smart form state management

**Validation Indicators**:
- Green checkmark: Field valid
- Red X: Field invalid with error message
- Yellow warning: Conflicts or warnings

**Usage**:
```tsx
import { ScheduleFormEnhanced } from '@/features/schedules/components'

<ScheduleFormEnhanced
  schedule={editingSchedule}
  onSubmit={(data) => handleSubmit(data)}
  onCancel={() => closeModal()}
  isLoading={isSaving}
/>
```

---

## API Integration

### Advanced Schedule API Functions
**File**: `api/scheduleAdvancedApi.ts`

**Functions**:

```typescript
// Check schedule conflicts
checkScheduleConflict(data: CheckConflictRequest): Promise<CheckConflictResponse>

// Validate schedule configuration
validateSchedule(data: ValidateScheduleRequest): Promise<ValidateScheduleResponse>

// Calculate next occurrences
calculateNextOccurrence(scheduleId: number, fromDate?: string): Promise<CalculateNextOccurrenceResponse>

// Get active schedule at specific time
getActiveSchedule(checkDate?: string, checkTime?: string): Promise<ActiveScheduleResponse>
```

---

## React Query Hooks

### Advanced Schedule Hooks
**File**: `hooks/useAdvancedSchedules.ts`

**Hooks**:

```typescript
// Conflict detection with debouncing
useScheduleConflicts(data, options)

// Schedule validation
useScheduleValidation(data, options)

// Next occurrences calculation
useNextOccurrences(scheduleId, options)

// Active schedule with auto-refresh
useActiveSchedule(checkDate, checkTime, options)

// UI state helpers
useConflictState(conflictData, isLoading)
useValidationState(validationData, isLoading)
useSchedulePreview(occurrences, priority)
useTimeUntilNextChange(nextOccurrence)

// Combined state for forms
useCombinedScheduleState(conflictRequest, validationRequest, scheduleId)
```

---

## Type Definitions

### Advanced Types
**File**: `types/advanced.ts`

**Key Types**:
- `CheckConflictRequest` - Conflict detection request
- `CheckConflictResponse` - Conflict detection response
- `ValidateScheduleRequest` - Validation request
- `ValidateScheduleResponse` - Validation response
- `CalculateNextOccurrenceResponse` - Occurrence calculation
- `ActiveScheduleResponse` - Active schedule data
- `PreviewOccurrence` - Calendar preview occurrence
- `RecurrencePreset` - Quick recurrence presets

---

## Backend API Endpoints

The following backend endpoints must be implemented:

```
POST /api/v1/schedules/check-conflict
Body: {
  playlist_id: number
  start_date: string
  end_date?: string
  start_time?: string
  end_time?: string
  recurrence_type: string
  exclude_schedule_id?: number
}
Response: {
  has_conflicts: boolean
  conflicts: ConflictSchedule[]
  message: string
}

POST /api/v1/schedules/validate
Body: {
  start_date: string
  end_date?: string
  start_time?: string
  end_time?: string
  recurrence_type: string
  recurrence_pattern?: RecurrencePattern
}
Response: {
  is_valid: boolean
  errors: string[]
  warnings: string[]
}

POST /api/v1/schedules/{schedule_id}/next-occurrence
Body: {
  from_date?: string
}
Response: {
  schedule_id: number
  schedule_name: string
  next_occurrence?: NextOccurrence
  occurrences: NextOccurrence[]
}

POST /api/v1/schedules/active
Body: {
  check_date?: string
  check_time?: string
}
Response: {
  schedule?: Schedule
  playlist_id?: number
  schedule_name?: string
  priority?: number
  is_found: boolean
}
```

---

## Usage Examples

### Example 1: Schedule Form with All Features

```tsx
import { ScheduleFormEnhanced } from '@/features/schedules/components'

function ScheduleModal({ scheduleId, onClose }) {
  const { mutate: createSchedule, isLoading } = useCreateSchedule()

  return (
    <Modal onClose={onClose}>
      <ScheduleFormEnhanced
        schedule={scheduleId ? existingSchedule : undefined}
        onSubmit={(data) => {
          createSchedule(data, {
            onSuccess: () => {
              toast.success('Schedule created')
              onClose()
            }
          })
        }}
        onCancel={onClose}
        isLoading={isLoading}
      />
    </Modal>
  )
}
```

### Example 2: Dashboard with Active Schedule

```tsx
import { ActiveScheduleIndicator } from '@/features/schedules/components'

function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Active schedule banner */}
      <ActiveScheduleIndicator
        mode="banner"
        onScheduleClick={(id) => router.push(`/schedules/${id}`)}
      />

      {/* Dashboard content */}
      <DashboardContent />
    </div>
  )
}
```

### Example 3: Schedules Page with Preview

```tsx
import {
  ScheduleConflictDetector,
  SchedulePreviewCalendar,
  ActiveScheduleIndicator
} from '@/features/schedules/components'

function SchedulesPage() {
  const [selectedSchedule, setSelectedSchedule] = useState(null)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: Schedule list */}
      <div className="lg:col-span-2">
        <ScheduleList />
      </div>

      {/* Right: Active schedule + preview */}
      <div className="space-y-6">
        <ActiveScheduleIndicator mode="widget" />

        {selectedSchedule && (
          <SchedulePreviewCalendar
            occurrences={occurrences}
            playlistName={selectedSchedule.playlist_name}
            priority={selectedSchedule.priority}
            exceptionDates={selectedSchedule.exception_dates}
          />
        )}
      </div>
    </div>
  )
}
```

---

## Configuration

### Debouncing
- Conflict detection: 500ms
- Validation: 500ms

### Auto-refresh Intervals
- Active schedule: 60 seconds (1 minute)
- Conflict detection: 30 seconds (stale time)
- Validation: 30 seconds (stale time)

### Cache Keys
```typescript
['schedule-conflicts', conflictRequest]
['schedule-validation', validationRequest]
['schedule-occurrences', scheduleId]
['active-schedule', checkDate, checkTime]
```

---

## Color System

### Priority Colors
- Critical (75-100): Red (#EF4444)
- High (50-74): Orange (#F97316)
- Normal (25-49): Blue (#3B82F6)
- Low (0-24): Gray (#6B7280)

### Status Colors
- Active/Success: Green (#10B981)
- Warning: Yellow (#F59E0B)
- Error/Critical: Red (#EF4444)
- Info: Blue (#3B82F6)

---

## Performance Considerations

1. **Debouncing**: All API calls are debounced (500ms) to prevent excessive requests
2. **Caching**: TanStack Query caches responses with 30-60s stale time
3. **Lazy Loading**: Calendar preview only loads when toggled
4. **Optimistic Updates**: Priority changes update UI immediately
5. **Selective Rendering**: Components only re-render on relevant data changes

---

## Best Practices

1. **Always use debounced hooks** for real-time validation
2. **Show loading states** during API calls
3. **Display validation feedback** immediately
4. **Use color coding** consistently across components
5. **Provide natural language previews** for complex patterns
6. **Include tooltips** for additional context
7. **Auto-refresh** active schedule displays
8. **Cache invalidation** after mutations

---

## Troubleshooting

### Conflicts not detecting
- Check if `playlist_id` is provided
- Verify API endpoint is responding
- Check debounce delay (500ms)
- Ensure `exclude_schedule_id` is set for edits

### Calendar not showing occurrences
- Verify `calculateNextOccurrence` API is working
- Check if `recurrence_pattern` is valid
- Ensure date range is within limits

### Active schedule not updating
- Check `refetchInterval` is set (60000ms)
- Verify backend `/api/v1/schedules/active` endpoint
- Check browser console for errors

---

## Dependencies

- React 18+
- TanStack Query (React Query)
- React Hook Form
- Zod (validation)
- date-fns (date utilities)
- Lucide React (icons)
- Tailwind CSS (styling)

---

## File Structure

```
src/features/schedules/
├── api/
│   ├── scheduleApi.ts              # Basic CRUD
│   ├── scheduleAdvancedApi.ts      # Advanced features
│   └── index.ts                    # Exports
├── components/
│   ├── ScheduleConflictDetector.tsx
│   ├── SchedulePreviewCalendar.tsx
│   ├── ActiveScheduleIndicator.tsx
│   ├── SchedulePriorityManager.tsx
│   ├── RecurrencePatternBuilder.tsx
│   ├── ScheduleFormEnhanced.tsx
│   └── index.ts                    # Exports
├── hooks/
│   ├── useSchedules.ts             # Basic hooks
│   ├── useAdvancedSchedules.ts     # Advanced hooks
│   └── index.ts                    # Exports
├── types/
│   ├── schedule.types.ts           # Basic types
│   ├── advanced.ts                 # Advanced types
│   └── index.ts                    # Exports
└── ADVANCED_FEATURES_README.md     # This file
```

---

## Future Enhancements

1. **Drag-and-drop** schedule reordering by priority
2. **Conflict auto-resolution** suggestions
3. **Schedule templates** for common patterns
4. **Bulk operations** (delete, update priority)
5. **Schedule analytics** (most used patterns, conflict hotspots)
6. **Export/Import** schedules (CSV, JSON)
7. **Schedule simulation** (preview conflicts before saving)
8. **Timeline view** showing all schedules on a single timeline

---

## Support

For issues or questions:
1. Check this README
2. Review component prop types in TypeScript
3. Check browser console for errors
4. Verify backend API is responding correctly
5. Test with minimal example

---

**Version**: 1.0.0
**Last Updated**: 2025-11-21
**Author**: Claude Code
