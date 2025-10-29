# Translation System Architecture

## Component Hierarchy

```
EditContentModal
│
└── TranslationManager
    ├── Header Section
    │   ├── Title + Language Count Badge
    │   └── Action Buttons
    │       ├── Export CSV Button
    │       ├── Bulk Import Button
    │       └── Add Language Button
    │
    ├── Language Tabs
    │   ├── Tab 1: English 🇬🇧 ★ (primary)
    │   ├── Tab 2: Indonesian 🇮🇩 •• (dirty)
    │   └── Tab N: Arabic 🇸🇦 [RTL]
    │
    ├── Translation Form (Active Tab)
    │   ├── Language Info Panel
    │   │   ├── Flag + Language Name
    │   │   ├── Native Name
    │   │   ├── RTL Badge (if applicable)
    │   │   └── Remove Language Button
    │   │
    │   ├── Primary Language Checkbox
    │   │   └── "Set as Primary Language ★"
    │   │
    │   ├── Form Fields
    │   │   ├── Title Input (RTL aware)
    │   │   └── Description Textarea (RTL aware)
    │   │
    │   └── Fallback Info Box (non-primary)
    │       └── "Falls back to: English"
    │
    ├── Save/Cancel Buttons (if dirty)
    │
    ├── Add Language Modal
    │   └── LanguageSelector Component
    │       ├── Search Input
    │       ├── Language List (filtered)
    │       │   ├── Language Option 1
    │       │   ├── Language Option 2
    │       │   └── ...
    │       └── Footer (count display)
    │
    └── BulkImportModal Component
        ├── Instructions Panel
        ├── Download Template Button
        ├── File Upload Zone
        ├── Preview Table
        │   ├── Header Row
        │   ├── Data Rows (validated)
        │   │   ├── Valid Row ✓
        │   │   └── Invalid Row ✗
        │   └── Summary Row
        └── Import/Cancel Buttons
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │             EditContentModal                              │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │         TranslationManager                          │  │  │
│  │  │                                                      │  │  │
│  │  │  State:                                              │  │  │
│  │  │  - translations: TranslationFormData[]              │  │  │
│  │  │  - activeTab: string                                │  │  │
│  │  │  - isLoading: boolean                               │  │  │
│  │  │  - isSaving: boolean                                │  │  │
│  │  │                                                      │  │  │
│  │  │  Actions:                                            │  │  │
│  │  │  - loadTranslations()                               │  │  │
│  │  │  - handleAddLanguage()                              │  │  │
│  │  │  - handleRemoveLanguage()                           │  │  │
│  │  │  - handleFieldChange()                              │  │  │
│  │  │  - handleSave()                                     │  │  │
│  │  │  - handleExport()                                   │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ↑
                    API Service Layer
┌─────────────────────────────────────────────────────────────────┐
│                  translationsApi Service                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Methods:                                                 │  │
│  │  - list(contentId)          → GET    /content/{id}/...   │  │
│  │  - create(contentId, data)  → POST   /content/{id}/...   │  │
│  │  - update(contentId, lang)  → PATCH  /content/{id}/...   │  │
│  │  - remove(contentId, lang)  → DELETE /content/{id}/...   │  │
│  │  - bulkImport(contentId)    → POST   /translations/...   │  │
│  │  - exportCSV(contentId)     → GET    /translations/...   │  │
│  │                                                           │  │
│  │  Uses: api (axios instance from ./index)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ↑
                       HTTP Requests
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /backend/app/api/translations.py                        │  │
│  │                                                           │  │
│  │  Router: /api/content                                    │  │
│  │                                                           │  │
│  │  Endpoints:                                              │  │
│  │  - POST   /content/{id}/translations                    │  │
│  │  - GET    /content/{id}/translations                    │  │
│  │  - GET    /content/{id}/translations/{lang}             │  │
│  │  - PATCH  /content/{id}/translations/{lang}             │  │
│  │  - DELETE /content/{id}/translations/{lang}             │  │
│  │  - POST   /translations/bulk-import                     │  │
│  │  - GET    /translations/export                          │  │
│  │  - GET    /content/languages                            │  │
│  │                                                           │  │
│  │  Uses: TranslationService                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ↑
                         Database Layer
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Tables:                                                  │  │
│  │  - content_translations                                  │  │
│  │    - id (UUID)                                           │  │
│  │    - content_id (FK)                                     │  │
│  │    - language (varchar)                                  │  │
│  │    - title (text)                                        │  │
│  │    - description (text)                                  │  │
│  │    - is_primary (boolean)                                │  │
│  │    - status (enum)                                       │  │
│  │    - created_at (timestamp)                              │  │
│  │    - updated_at (timestamp)                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## State Management Flow

### Load Translations Flow

```
User opens EditContentModal
         ↓
TranslationManager mounts
         ↓
useEffect triggers loadTranslations()
         ↓
translationsApi.list(contentId)
         ↓
GET /api/content/{id}/translations
         ↓
Backend queries database
         ↓
Returns Translation[]
         ↓
setTranslations(data)
         ↓
UI updates with language tabs
```

### Add Translation Flow

```
User clicks "Add Language"
         ↓
LanguageSelector modal opens
         ↓
User selects language
         ↓
New translation added to state
         ↓
activeTab switches to new language
         ↓
User enters title + description
         ↓
User clicks "Save Translations"
         ↓
translationsApi.create(contentId, data)
         ↓
POST /api/content/{id}/translations
         ↓
Backend creates translation
         ↓
Success response
         ↓
loadTranslations() refreshes data
         ↓
Toast notification: "Translation added"
```

### Update Translation Flow

```
User switches to existing language tab
         ↓
User modifies title or description
         ↓
handleFieldChange() updates state
         ↓
isDirty flag set to true
         ↓
Orange dot appears on tab
         ↓
User clicks "Save Translations"
         ↓
translationsApi.update(contentId, lang, data)
         ↓
PATCH /api/content/{id}/translations/{lang}
         ↓
Backend updates translation
         ↓
Success response
         ↓
loadTranslations() refreshes data
         ↓
Toast notification: "Translations saved"
```

### Bulk Import Flow

```
User clicks "Bulk Import"
         ↓
BulkImportModal opens
         ↓
User downloads template (optional)
         ↓
User uploads CSV file
         ↓
File parsed client-side
         ↓
Preview table shows validation
         ↓
User clicks "Import"
         ↓
translationsApi.bulkImport(contentId, file)
         ↓
POST /api/translations/bulk-import
         ↓
Backend processes CSV
         ↓
Returns BulkImportResponse
         ↓
Modal shows results
         ↓
onImportComplete() refreshes translations
         ↓
Toast notification: "Imported X translations"
```

---

## File Structure

```
web-admin/
├── src/
│   ├── components/
│   │   ├── content/
│   │   │   ├── TranslationManager.tsx       ← Main component
│   │   │   └── modals/
│   │   │       └── EditContentModal.tsx     ← Integration point
│   │   │
│   │   ├── translations/
│   │   │   ├── LanguageSelector.tsx         ← Language picker
│   │   │   └── BulkImportModal.tsx          ← CSV import
│   │   │
│   │   └── shared/
│   │       ├── Modal.tsx                    ← Used by modals
│   │       └── Button.tsx                   ← Used by all
│   │
│   ├── services/
│   │   └── api/
│   │       ├── index.ts                     ← Axios config
│   │       └── translations.ts              ← Translation API
│   │
│   ├── types/
│   │   ├── translation.ts                   ← Translation types
│   │   └── api.ts                           ← API types
│   │
│   └── utils/
│       ├── toast.ts                         ← Notifications
│       └── formatters.ts                    ← Text formatting
│
├── TRANSLATION_SYSTEM_DOCUMENTATION.md      ← Full docs
├── TRANSLATION_QUICK_REFERENCE.md           ← Quick guide
├── TRANSLATION_IMPLEMENTATION_CHECKLIST.md  ← Checklist
└── TRANSLATION_ARCHITECTURE.md              ← This file
```

---

## Type System

```typescript
// Core Types
interface Language {
  code: string          // ISO 639-1 (e.g., "en", "id")
  name: string          // English name (e.g., "Indonesian")
  nativeName: string    // Native name (e.g., "Bahasa Indonesia")
  flag: string          // Emoji flag (e.g., "🇮🇩")
  isRTL: boolean        // Right-to-left indicator
}

interface Translation {
  id: string
  content_id: string
  language: string
  title: string
  description: string
  is_primary: boolean
  created_at: string
  updated_at: string
}

// Form State (Client-side)
interface TranslationFormData extends Translation {
  isNew?: boolean       // Not yet saved to server
  isDirty?: boolean     // Has unsaved changes
}

// API Payloads
interface TranslationCreate {
  language: string
  title: string
  description: string
  is_primary?: boolean
}

interface TranslationUpdate {
  title?: string
  description?: string
  is_primary?: boolean
}

// API Responses
interface BulkImportResponse {
  imported: number
  updated: number
  errors: Array<{
    row: number
    message: string
  }>
}
```

---

## Event Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interactions                        │
└─────────────────────────────────────────────────────────────┘
           │
           ├──► Click "Add Language"
           │         ↓
           │    Open LanguageSelector
           │         ↓
           │    Select Language
           │         ↓
           │    Add to translations[]
           │         ↓
           │    Switch activeTab
           │
           ├──► Switch Language Tab
           │         ↓
           │    setActiveTab(language)
           │         ↓
           │    Re-render form with new data
           │
           ├──► Edit Title/Description
           │         ↓
           │    handleFieldChange()
           │         ↓
           │    Update translations[].{field}
           │         ↓
           │    Set isDirty = true
           │
           ├──► Set as Primary
           │         ↓
           │    handleSetPrimary()
           │         ↓
           │    Update all is_primary flags
           │         ↓
           │    Set isDirty = true
           │
           ├──► Click "Save Translations"
           │         ↓
           │    Filter dirty translations
           │         ↓
           │    Validate all fields
           │         ↓
           │    For each dirty translation:
           │         ├─► If new: create()
           │         └─► If existing: update()
           │         ↓
           │    loadTranslations() (refresh)
           │         ↓
           │    Show success toast
           │
           ├──► Click "Remove Language"
           │         ↓
           │    Confirm deletion
           │         ↓
           │    If new: Remove from state
           │    If existing: remove() API call
           │         ↓
           │    Update translations[]
           │         ↓
           │    Switch activeTab if needed
           │
           ├──► Click "Bulk Import"
           │         ↓
           │    Open BulkImportModal
           │         ↓
           │    User uploads CSV
           │         ↓
           │    Parse and validate
           │         ↓
           │    Show preview table
           │         ↓
           │    User clicks "Import"
           │         ↓
           │    bulkImport() API call
           │         ↓
           │    Show results
           │         ↓
           │    Refresh translations
           │
           └──► Click "Export CSV"
                     ↓
                exportCSV() API call
                     ↓
                Download file
```

---

## Validation Flow

```
Client-Side Validation
         │
         ├─► Required Fields Check
         │    - title.trim() !== ''
         │    - description.trim() !== ''
         │    → Show inline error
         │
         ├─► Language Code Check
         │    - SUPPORTED_LANGUAGES.includes(code)
         │    → Show toast error
         │
         ├─► Duplicate Language Check
         │    - !usedLanguages.includes(code)
         │    → Show toast error
         │
         └─► CSV Format Check
              - Correct column count
              - Valid language codes
              - Required fields present
              → Show row errors in table

Server-Side Validation
         │
         ├─► Language Code Validation
         │    - ISO 639-1 format
         │    - Supported by system
         │
         ├─► Content Existence Check
         │    - Content ID exists in DB
         │
         ├─► Primary Language Constraint
         │    - Cannot delete primary language
         │    - Only one primary per content
         │
         └─► Field Length Limits
              - Title max length
              - Description max length
```

---

## Responsive Behavior

```
Desktop (≥1024px)
├── Full width TranslationManager
├── Language tabs in single row
├── Two-column device/tag grids
└── Modal: 2xl (max-width: 672px)

Tablet (768px - 1023px)
├── Full width TranslationManager
├── Scrollable language tabs
├── Single column device/tag grids
└── Modal: xl (max-width: 576px)

Mobile (<768px)
├── Full width TranslationManager
├── Scrollable language tabs
├── Stacked form layout
└── Modal: Full screen
```

---

## Performance Optimization

```
Component Level
├── React.memo() for LanguageSelector options
├── useMemo() for filtered language lists
├── useCallback() for event handlers
└── Debounced search input (300ms)

API Level
├── Batch save operations
├── Single request for bulk import
├── Cached language constants
└── Optimistic UI updates

Rendering
├── Conditional rendering (show only active tab)
├── Lazy loading of modals
├── Virtualization for large lists (future)
└── Skeleton loaders for loading states
```

---

## Error Handling Strategy

```
Error Types
├── Network Errors
│   ├── API unreachable
│   ├── Timeout
│   └── Connection lost
│
├── Validation Errors
│   ├── Required field missing
│   ├── Invalid format
│   └── Constraint violation
│
├── Business Logic Errors
│   ├── Content not found
│   ├── Language already exists
│   └── Cannot delete primary language
│
└── File Upload Errors
    ├── Invalid file type
    ├── File too large
    └── CSV parse error

Error Display
├── Toast Notifications (general errors)
├── Inline Field Errors (form validation)
├── Modal Error Panels (bulk import)
└── Console Logging (debug info)
```

---

## Security Considerations

```
Input Validation
├── Sanitize user input (title, description)
├── Validate language codes (whitelist)
├── Check file size limits
└── Validate CSV structure

API Security
├── Authentication token required
├── CORS configuration
├── Rate limiting (backend)
└── SQL injection prevention (backend)

File Upload Security
├── File type validation (.csv only)
├── File size limit (10MB)
├── Content scanning (future)
└── Temporary file cleanup (backend)
```

---

## Monitoring & Analytics

```
Metrics to Track
├── Translation coverage per content
├── Most/least used languages
├── Bulk import success rate
├── Average time to translate
└── Primary language distribution

Logging
├── API requests/responses
├── Validation errors
├── Import/export operations
└── User actions (audit trail)

Error Tracking
├── Failed API calls
├── Validation failures
├── Import errors
└── Client-side exceptions
```

---

## Deployment Architecture

```
Development Environment
├── Local: localhost:3000 (Vite dev server)
├── API: 192.168.5.12:8001 (proxied)
└── DB: 192.168.5.12:5433 (PostgreSQL)

Production Environment
├── Frontend: Served from /dist (static)
├── API: 192.168.5.12:8001 (Docker)
└── DB: 192.168.5.12:5433 (Docker)

Build Process
├── npm run build
├── TypeScript compilation
├── Vite bundling
└── Asset optimization
```

---

## Version History

### v1.0.0 (2025-01-28)
- Initial implementation
- 15 language support
- Tab-based UI
- Bulk import/export
- RTL support
- Full documentation

---

This architecture document provides a comprehensive overview of the translation system's structure, data flow, and technical implementation.
