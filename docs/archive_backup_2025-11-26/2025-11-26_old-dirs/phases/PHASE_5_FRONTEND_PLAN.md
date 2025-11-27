# Phase 5: Frontend Implementation Plan

**Date**: 2025-01-11
**Status**: Planning Phase
**Target**: React + Vite CMS UI for Phase 5 Features
**Estimated Time**: 24-32 hours (3-4 working days)

---

## 🎯 OVERVIEW

All Phase 5 backend systems are complete with 46 REST API endpoints ready for consumption. Now we need to build the CMS UI for managing:

1. **Widget System** - Create and manage overlay widgets
2. **Template System** - Edit templates with variable substitution
3. **Translation System** - Manage multi-language content
4. **Schedule System** - Build complex scheduling rules

---

## 📋 FRONTEND ARCHITECTURE

### Technology Stack

**Framework**: React 18 + Vite
**State Management**:
- Zustand (global state)
- TanStack Query (server state)

**Forms**: React Hook Form + Zod validation
**UI Components**: Tailwind CSS + shadcn/ui
**HTTP Client**: Axios
**Routing**: React Router v6

### Project Structure

```
cms-vite/src/
├── features/
│   ├── widgets/
│   │   ├── api/widgetApi.ts
│   │   ├── components/
│   │   │   ├── WidgetForm.tsx
│   │   │   ├── WidgetList.tsx
│   │   │   ├── WidgetPreview.tsx
│   │   │   ├── WidgetTypeSelector.tsx
│   │   │   ├── LayoutEditor.tsx
│   │   │   └── PlaylistAssignment.tsx
│   │   ├── hooks/
│   │   │   ├── useWidgets.ts
│   │   │   └── useWidgetMutations.ts
│   │   ├── types/widget.types.ts
│   │   └── pages/WidgetsPage.tsx
│   ├── templates/
│   │   ├── api/templateApi.ts
│   │   ├── components/
│   │   │   ├── TemplateEditor.tsx
│   │   │   ├── TemplateList.tsx
│   │   │   ├── VariableBuilder.tsx
│   │   │   ├── TemplatePreview.tsx
│   │   │   └── RenderTest.tsx
│   │   ├── hooks/
│   │   │   ├── useTemplates.ts
│   │   │   └── useTemplateMutations.ts
│   │   ├── types/template.types.ts
│   │   └── pages/TemplatesPage.tsx
│   ├── translations/
│   │   ├── api/translationApi.ts
│   │   ├── components/
│   │   │   ├── TranslationForm.tsx
│   │   │   ├── TranslationList.tsx
│   │   │   ├── LanguageSelector.tsx
│   │   │   ├── BulkImport.tsx
│   │   │   └── StatsWidget.tsx
│   │   ├── hooks/
│   │   │   ├── useTranslations.ts
│   │   │   └── useTranslationMutations.ts
│   │   ├── types/translation.types.ts
│   │   └── pages/TranslationsPage.tsx
│   └── schedules/
│       ├── api/scheduleApi.ts
│       ├── components/
│       │   ├── ScheduleForm.tsx
│       │   ├── ScheduleList.tsx
│       │   ├── RecurrenceBuilder.tsx
│       │   ├── CalendarView.tsx
│       │   ├── ConflictDetector.tsx
│       │   └── NextOccurrences.tsx
│       ├── hooks/
│       │   ├── useSchedules.ts
│       │   └── useScheduleMutations.ts
│       ├── types/schedule.types.ts
│       └── pages/SchedulesPage.tsx
├── shared/
│   ├── components/
│   │   ├── DataTable.tsx
│   │   ├── Modal.tsx
│   │   ├── ConfirmDialog.tsx
│   │   └── LoadingSpinner.tsx
│   └── utils/
│       ├── api.ts
│       └── formatters.ts
└── App.tsx
```

---

## 🚀 IMPLEMENTATION ROADMAP

### Phase 6.1: Widget Manager UI (6-8 hours)

**Priority**: HIGH (Most visible feature)

#### Components to Build

1. **WidgetsPage.tsx** (Main page)
   - List view with filters
   - Create/Edit/Delete actions
   - Search and pagination

2. **WidgetForm.tsx** (Create/Edit form)
   - Widget name and description
   - Widget type selector (dropdown)
   - Dynamic config form based on type
   - Layout editor (position/size)
   - Form validation with Zod

3. **WidgetTypeSelector.tsx**
   - Radio/Card selector for widget types
   - Icons and descriptions for each type
   - Preview of widget type

4. **LayoutEditor.tsx**
   - Visual position picker
   - X, Y, Width, Height inputs
   - Preview canvas (1920x1080 grid)
   - Drag-and-drop positioning

5. **WidgetPreview.tsx**
   - Live preview of widget
   - Different backgrounds (content preview)
   - Responsive sizing

6. **PlaylistAssignment.tsx**
   - Assign widget to playlists
   - Z-index configuration
   - Enable/disable per playlist
   - List of assigned playlists

#### API Integration (widgetApi.ts)

```typescript
// Widget CRUD
export const getWidgets = (params?) => api.get('/widgets', { params })
export const getWidget = (id) => api.get(`/widgets/${id}`)
export const createWidget = (data) => api.post('/widgets', data)
export const updateWidget = (id, data) => api.put(`/widgets/${id}`, data)
export const deleteWidget = (id) => api.delete(`/widgets/${id}`)

// Playlist assignment
export const assignWidgetToPlaylist = (playlistId, data) =>
  api.post(`/widgets/playlists/${playlistId}/widgets`, data)
export const getPlaylistWidgets = (playlistId) =>
  api.get(`/widgets/playlists/${playlistId}/widgets`)
export const updatePlaylistWidget = (id, data) =>
  api.put(`/widgets/playlist-widgets/${id}`, data)
export const removeWidgetFromPlaylist = (playlistId, widgetId) =>
  api.delete(`/widgets/playlists/${playlistId}/widgets/${widgetId}`)
```

#### Custom Hooks

```typescript
// useWidgets.ts
export const useWidgets = (filters?) => {
  return useQuery(['widgets', filters], () => getWidgets(filters))
}

export const useWidget = (id) => {
  return useQuery(['widget', id], () => getWidget(id))
}

// useWidgetMutations.ts
export const useCreateWidget = () => {
  const queryClient = useQueryClient()
  return useMutation(createWidget, {
    onSuccess: () => {
      queryClient.invalidateQueries(['widgets'])
      toast.success('Widget created')
    }
  })
}

export const useUpdateWidget = () => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ id, data }) => updateWidget(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['widgets'])
        toast.success('Widget updated')
      }
    }
  )
}

export const useDeleteWidget = () => {
  const queryClient = useQueryClient()
  return useMutation(deleteWidget, {
    onSuccess: () => {
      queryClient.invalidateQueries(['widgets'])
      toast.success('Widget deleted')
    }
  })
}
```

#### Type Definitions

```typescript
// widget.types.ts
export type WidgetType = 'clock' | 'weather' | 'news' | 'hotel_info' | 'custom'

export interface Widget {
  id: number
  organization_id: number
  name: string
  description?: string
  widget_type: WidgetType
  config: Record<string, any>
  layout: {
    x: number
    y: number
    width: number
    height: number
  }
  created_at: string
  updated_at: string
}

export interface CreateWidgetRequest {
  name: string
  description?: string
  widget_type: WidgetType
  config: Record<string, any>
  layout: {
    x: number
    y: number
    width: number
    height: number
  }
}

export interface PlaylistWidget {
  id: number
  playlist_id: number
  widget_id: number
  z_index: number
  is_enabled: boolean
  widget?: Widget
}
```

#### Validation Schema (Zod)

```typescript
// widget.schema.ts
import { z } from 'zod'

export const layoutSchema = z.object({
  x: z.number().min(0).max(1920),
  y: z.number().min(0).max(1080),
  width: z.number().min(50).max(1920),
  height: z.number().min(50).max(1080),
})

export const widgetSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  description: z.string().optional(),
  widget_type: z.enum(['clock', 'weather', 'news', 'hotel_info', 'custom']),
  config: z.record(z.any()),
  layout: layoutSchema,
})
```

---

### Phase 6.2: Template Editor UI (6-8 hours)

**Priority**: HIGH (Dynamic content feature)

#### Components to Build

1. **TemplatesPage.tsx** (Main page)
   - List view with template types filter
   - Create/Edit/Delete actions
   - Search and pagination
   - Template type badges

2. **TemplateEditor.tsx** (Code editor)
   - Monaco Editor or CodeMirror integration
   - Syntax highlighting for Jinja2
   - Variable autocomplete
   - Line numbers and formatting
   - Template type selector

3. **VariableBuilder.tsx**
   - Add/Remove variables
   - Variable type selection (string, number, date)
   - Default values
   - Variable list display
   - Extract from template button

4. **TemplatePreview.tsx**
   - Live preview with sample data
   - Data input form
   - Rendered output display
   - Error display if invalid

5. **RenderTest.tsx**
   - Test template with custom data
   - Save preview data
   - Multiple test scenarios
   - Validation messages

#### API Integration (templateApi.ts)

```typescript
// Template CRUD
export const getTemplates = (params?) => api.get('/templates', { params })
export const getTemplate = (id) => api.get(`/templates/${id}`)
export const createTemplate = (data) => api.post('/templates', data)
export const updateTemplate = (id, data) => api.put(`/templates/${id}`, data)
export const deleteTemplate = (id) => api.delete(`/templates/${id}`)

// Template operations
export const renderTemplate = (id, data) =>
  api.post(`/templates/${id}/render`, data)
export const validateTemplate = (content) =>
  api.post('/templates/validate', { content })
export const extractVariables = (content) =>
  api.post('/templates/extract-variables', { content })
```

#### Type Definitions

```typescript
// template.types.ts
export type TemplateType = 'text' | 'image' | 'video' | 'html' | 'greeting'

export interface Template {
  id: number
  organization_id: number
  name: string
  description?: string
  content: string
  template_type: TemplateType
  variables: Record<string, string>
  preview_data?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface RenderTemplateRequest {
  data: Record<string, any>
}

export interface RenderTemplateResponse {
  rendered_content: string
  variables_used: string[]
  render_time_ms: number
}
```

---

### Phase 6.3: Translation Manager UI (4-6 hours)

**Priority**: MEDIUM (Essential for multi-language)

#### Components to Build

1. **TranslationsPage.tsx** (Main page)
   - List with entity type and language filters
   - Create/Edit/Delete actions
   - Bulk import button
   - Statistics summary

2. **TranslationForm.tsx** (Create/Edit form)
   - Entity type selector
   - Entity ID input
   - Language selector (10 languages)
   - Field name input
   - Translation text area
   - Character count

3. **LanguageSelector.tsx**
   - Dropdown with flags
   - Language codes and names
   - Search/filter languages
   - Currently used languages highlighted

4. **BulkImport.tsx**
   - File upload (CSV/JSON)
   - Preview import data
   - Validation results
   - Import/cancel actions
   - Progress indicator

5. **StatsWidget.tsx**
   - Total translations count
   - Languages used
   - Completion rate per language
   - Entity type breakdown
   - Chart visualization

#### API Integration (translationApi.ts)

```typescript
// Translation CRUD
export const getTranslations = (params?) => api.get('/translations', { params })
export const getTranslation = (id) => api.get(`/translations/${id}`)
export const createTranslation = (data) => api.post('/translations', data)
export const deleteTranslation = (id) => api.delete(`/translations/${id}`)

// Entity translations
export const getEntityTranslations = (entityType, entityId, languageCode) =>
  api.get(`/translations/${entityType}/${entityId}`, {
    params: { language_code: languageCode }
  })
export const deleteEntityTranslations = (entityType, entityId, languageCode?) =>
  api.delete(`/translations/${entityType}/${entityId}`, {
    params: { language_code: languageCode }
  })

// Bulk operations
export const bulkImportTranslations = (data) =>
  api.post('/translations/bulk', data)

// Languages
export const getSupportedLanguages = () =>
  api.get('/translations/languages/supported')
export const getOrganizationLanguages = () =>
  api.get('/translations/languages/organization')
export const getTranslationStats = () =>
  api.get('/translations/stats')
```

---

### Phase 6.4: Schedule Builder UI (8-10 hours)

**Priority**: HIGH (Complex feature, most time-consuming)

#### Components to Build

1. **SchedulesPage.tsx** (Main page)
   - List with filters (playlist, recurrence type, active status)
   - Create/Edit/Delete actions
   - Priority badges
   - Active/Inactive toggle
   - Search and pagination

2. **ScheduleForm.tsx** (Complex form)
   - Name and description
   - Playlist selector
   - Date range picker (start/end dates)
   - Time range picker (start/end times)
   - Recurrence type selector
   - Dynamic recurrence pattern builder
   - Exception dates picker
   - Priority slider (0-100)
   - Active toggle

3. **RecurrenceBuilder.tsx** (Most complex)
   - Recurrence type tabs (once, daily, weekly, monthly, yearly)
   - **Daily**: Interval input (every N days)
   - **Weekly**: Day checkboxes (Mon-Sun)
   - **Monthly**: Day selector (1-31, multiple selection)
   - **Yearly**: Month + day picker
   - Visual preview of pattern
   - Next occurrences preview

4. **CalendarView.tsx**
   - Month view calendar
   - Scheduled dates highlighted
   - Exception dates marked
   - Click date to see schedules
   - Color coding by priority
   - Conflict indicators

5. **ConflictDetector.tsx**
   - Real-time conflict checking
   - List of conflicting schedules
   - Priority comparison
   - Warning/error messages
   - Resolution suggestions

6. **NextOccurrences.tsx**
   - List of next 10 occurrences
   - Date and time display
   - Exception indicators
   - Calculate from custom date
   - Timeline view

#### API Integration (scheduleApi.ts)

```typescript
// Schedule CRUD
export const getSchedules = (params?) => api.get('/schedules', { params })
export const getSchedule = (id) => api.get(`/schedules/${id}`)
export const createSchedule = (data) => api.post('/schedules', data)
export const updateSchedule = (id, data) => api.put(`/schedules/${id}`, data)
export const deleteSchedule = (id) => api.delete(`/schedules/${id}`)
export const deactivateSchedule = (id) =>
  api.post(`/schedules/${id}/deactivate`)

// Active schedule
export const getActiveScheduleNow = () =>
  api.get('/schedules/active/now')
export const checkActiveSchedule = (data) =>
  api.post('/schedules/active/check', data)

// Recurrence
export const calculateNextOccurrence = (id, fromDate?) =>
  api.post(`/schedules/${id}/calculate-next`, { from_date: fromDate })

// Conflicts
export const checkConflicts = (data) =>
  api.post('/schedules/check-conflicts', data)
```

#### Type Definitions

```typescript
// schedule.types.ts
export type RecurrenceType = 'once' | 'daily' | 'weekly' | 'monthly' | 'yearly'

export interface RecurrencePattern {
  interval?: number
  days?: number[]
  month?: number
  day_of_month?: number
}

export interface Schedule {
  id: number
  organization_id: number
  name: string
  description?: string
  playlist_id: number
  start_date: string
  end_date?: string
  start_time?: string
  end_time?: string
  recurrence_type: RecurrenceType
  recurrence_pattern?: RecurrencePattern
  exceptions?: string[]
  priority: number
  is_active: boolean
  created_by?: number
  created_at: string
  updated_at: string
}

export interface CreateScheduleRequest {
  name: string
  description?: string
  playlist_id: number
  start_date: string
  end_date?: string
  start_time?: string
  end_time?: string
  recurrence_type: RecurrenceType
  recurrence_pattern?: RecurrencePattern
  exceptions?: string[]
  priority: number
  is_active: boolean
}
```

---

## 🎨 UI/UX GUIDELINES

### Design Principles

1. **Consistency**: Use shadcn/ui components throughout
2. **Feedback**: Toast notifications for all actions
3. **Validation**: Real-time form validation with error messages
4. **Loading States**: Skeleton loaders during data fetching
5. **Empty States**: Helpful messages when no data
6. **Responsiveness**: Mobile-friendly layouts

### Color Coding

- **Widgets**: Blue theme
- **Templates**: Green theme
- **Translations**: Purple theme
- **Schedules**: Orange theme

### Common Patterns

**List Pages**:
- Search bar at top
- Filters in sidebar or header
- Data table with sorting
- Pagination at bottom
- Create button (FAB or top-right)

**Forms**:
- Step-by-step for complex forms
- Save/Cancel buttons
- Dirty state detection
- Confirm before discard

**Modals**:
- Create/Edit in modal or side panel
- Delete confirmation dialog
- Preview in modal

---

## 📦 SHARED COMPONENTS

These should be built first as they're used across all features:

### 1. DataTable Component
- Sortable columns
- Row selection
- Actions menu
- Pagination
- Loading skeleton

### 2. Modal Component
- Reusable modal wrapper
- Size variants (sm, md, lg, xl)
- Close on overlay click
- Keyboard shortcuts (Esc to close)

### 3. ConfirmDialog Component
- Delete confirmation
- Discard changes confirmation
- Custom messages
- Destructive variant

### 4. LoadingSpinner Component
- Full page loader
- Inline loader
- Overlay loader
- Size variants

### 5. FormField Components
- Text input
- Textarea
- Select dropdown
- Date picker
- Time picker
- Checkbox
- Radio group
- Switch toggle

---

## 🔧 UTILITIES

### API Client Setup

```typescript
// shared/utils/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://192.168.5.12:8001/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor (add auth token)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor (handle errors)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### Date Formatters

```typescript
// shared/utils/formatters.ts
import { format, parseISO } from 'date-fns'

export const formatDate = (date: string) => {
  return format(parseISO(date), 'yyyy-MM-dd')
}

export const formatTime = (time: string) => {
  return format(parseISO(`2000-01-01T${time}`), 'HH:mm')
}

export const formatDateTime = (datetime: string) => {
  return format(parseISO(datetime), 'yyyy-MM-dd HH:mm:ss')
}
```

---

## 📊 IMPLEMENTATION SCHEDULE

### Week 1: Widgets + Templates (12-16 hours)

**Day 1-2**: Widget Manager (6-8 hours)
- Setup shared components
- Widget CRUD UI
- Layout editor
- Playlist assignment

**Day 3-4**: Template Editor (6-8 hours)
- Code editor integration
- Variable builder
- Preview and render testing

### Week 2: Translations + Schedules (12-16 hours)

**Day 5**: Translation Manager (4-6 hours)
- Translation CRUD UI
- Language selector
- Bulk import
- Statistics dashboard

**Day 6-7**: Schedule Builder (8-10 hours)
- Schedule form
- Recurrence builder (complex!)
- Calendar view
- Conflict detection

---

## ✅ ACCEPTANCE CRITERIA

### Widget Manager
- [ ] Create widget with all types
- [ ] Edit widget configuration
- [ ] Delete widget with confirmation
- [ ] Assign widget to playlist
- [ ] Preview widget layout
- [ ] See all widgets in list

### Template Editor
- [ ] Create template with syntax highlighting
- [ ] Extract variables from template
- [ ] Render template with preview data
- [ ] Validate template syntax
- [ ] See all templates in list
- [ ] Filter by template type

### Translation Manager
- [ ] Add translation for entity
- [ ] Delete translation
- [ ] Bulk import translations
- [ ] View translation statistics
- [ ] Filter by language and entity type
- [ ] See all languages used

### Schedule Builder
- [ ] Create schedule with recurrence
- [ ] Set priority and active status
- [ ] Add exception dates
- [ ] Preview next occurrences
- [ ] Detect conflicts
- [ ] See all schedules in calendar view
- [ ] Filter by playlist and status

---

## 🚨 POTENTIAL CHALLENGES

### Technical Challenges

1. **Monaco Editor Integration**: Large bundle size, may need lazy loading
2. **Calendar Component**: Complex scheduling logic, consider using library (react-big-calendar)
3. **Recurrence Builder**: UI complexity, need clear UX for all patterns
4. **Conflict Detection**: Real-time checking, debounce API calls
5. **Bulk Import**: File parsing, validation, progress tracking

### Solutions

- Use code splitting for heavy components
- Consider react-big-calendar for calendar view
- Build recurrence builder step-by-step (one type at a time)
- Use debounce (500ms) for conflict checking
- Use Web Workers for large file processing

---

## 🎯 SUCCESS METRICS

- [ ] All CRUD operations working
- [ ] Forms validated properly
- [ ] Error handling with user-friendly messages
- [ ] Loading states on all async operations
- [ ] Mobile responsive (768px breakpoint)
- [ ] No console errors
- [ ] TypeScript types complete
- [ ] Accessible (ARIA labels)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-11
**Status**: Ready for Implementation
