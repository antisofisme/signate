# Multi-Language Translation System Documentation

## Overview

The Translation Management System provides a comprehensive solution for managing content translations across 15 languages with an intuitive UI, bulk import/export capabilities, and smart fallback mechanisms.

## Features

### 1. Language Support

**Supported Languages (15):**
- 🇬🇧 English (en)
- 🇮🇩 Indonesian (id)
- 🇨🇳 Chinese (zh)
- 🇯🇵 Japanese (ja)
- 🇰🇷 Korean (ko)
- 🇹🇭 Thai (th)
- 🇻🇳 Vietnamese (vi)
- 🇪🇸 Spanish (es)
- 🇫🇷 French (fr)
- 🇩🇪 German (de)
- 🇵🇹 Portuguese (pt)
- 🇷🇺 Russian (ru)
- 🇸🇦 Arabic (ar) - RTL support
- 🇮🇳 Hindi (hi)
- 🇲🇾 Malay (ms)

### 2. Translation Manager Component

**Location:** `/web-admin/src/components/content/TranslationManager.tsx`

**Features:**
- Tab-based interface (one tab per language)
- Real-time validation
- Unsaved changes indicator
- Primary language designation
- RTL language support
- Fallback chain visualization

**Integration:**
```typescript
import TranslationManager from '../TranslationManager';

<TranslationManager contentId={content.id} />
```

### 3. Language Selector Component

**Location:** `/web-admin/src/components/translations/LanguageSelector.tsx`

**Features:**
- Dropdown with language flags
- Search/filter capability
- Exclude already-used languages
- RTL indicator badges
- Native language names

**Usage:**
```typescript
<LanguageSelector
  value={selectedLanguage}
  onChange={setSelectedLanguage}
  excludeLanguages={['en', 'id']}
  placeholder="Select a language"
/>
```

### 4. Bulk Import System

**Location:** `/web-admin/src/components/translations/BulkImportModal.tsx`

**Features:**
- CSV file upload
- Preview before import
- Validation with error reporting
- Template download
- Row-by-row error display

**CSV Format:**
```csv
language,title,description,is_primary
en,Welcome to Our Hotel,Enjoy your stay with us,true
id,Selamat Datang di Hotel Kami,Nikmati menginap bersama kami,false
zh,欢迎光临我们的酒店,与我们一起享受您的住宿,false
```

### 5. API Service

**Location:** `/web-admin/src/services/api/translations.ts`

**Endpoints:**

#### List Translations
```typescript
translationsApi.list(contentId: string)
// GET /api/content/{contentId}/translations
```

#### Create Translation
```typescript
translationsApi.create(contentId: string, data: TranslationCreate)
// POST /api/content/{contentId}/translations
```

#### Update Translation
```typescript
translationsApi.update(contentId: string, language: string, data: TranslationUpdate)
// PATCH /api/content/{contentId}/translations/{language}
```

#### Delete Translation
```typescript
translationsApi.remove(contentId: string, language: string)
// DELETE /api/content/{contentId}/translations/{language}
```

#### Bulk Import
```typescript
translationsApi.bulkImport(contentId: string, file: File)
// POST /api/translations/bulk-import
```

#### Export CSV
```typescript
translationsApi.exportCSV(contentId: string)
// GET /api/translations/export?content_ids={contentId}&format=csv
```

#### Download Template
```typescript
translationsApi.downloadTemplate()
// Client-side generation
```

## Backend API

### Router Configuration

**File:** `/backend/app/api/translations.py`

**Prefix:** `/api/content`

**Tags:** `["translations"]`

### Endpoints

#### 1. Add Translation
```
POST /api/content/{content_id}/translations
```

**Request Body:**
```json
{
  "language": "id",
  "title": "Selamat Datang",
  "description": "Deskripsi dalam Bahasa Indonesia",
  "is_primary": false,
  "status": "approved"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Translation added for language 'id'",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "content_id": 123,
    "language": "id",
    "title": "Selamat Datang",
    "description": "Deskripsi dalam Bahasa Indonesia",
    "is_primary": false,
    "status": "approved",
    "direction": "ltr",
    "created_at": "2025-01-28T10:00:00Z",
    "updated_at": "2025-01-28T10:00:00Z"
  }
}
```

#### 2. List Translations
```
GET /api/content/{content_id}/translations
```

**Response:**
```json
{
  "success": true,
  "message": "Found 3 translations",
  "data": {
    "content_id": 123,
    "default_language": "en",
    "translations": [
      {
        "id": "...",
        "language": "en",
        "title": "Welcome",
        "is_primary": true
      },
      {
        "id": "...",
        "language": "id",
        "title": "Selamat Datang",
        "is_primary": false
      }
    ],
    "available_languages": ["en", "id", "zh"],
    "missing_languages": ["ja", "ko", "ar"],
    "total_count": 3
  }
}
```

#### 3. Get Translation with Fallback
```
GET /api/content/{content_id}/translations/{language}?use_fallback=true
```

**Fallback Chain:**
1. Requested language
2. Language-specific fallback (e.g., ms → id)
3. Default language (en)
4. Original content language
5. Any available translation

#### 4. Update Translation
```
PATCH /api/content/{content_id}/translations/{language}
```

**Request Body (partial updates):**
```json
{
  "title": "Updated Title",
  "status": "approved"
}
```

#### 5. Delete Translation
```
DELETE /api/content/{content_id}/translations/{language}
```

**Response:** `204 No Content`

#### 6. Bulk Import
```
POST /api/translations/bulk-import?content_id={id}&dry_run=false
```

**Request:** Multipart form data with CSV file

**Response:**
```json
{
  "success": true,
  "message": "Import completed: 5 imported, 2 updated, 1 failed",
  "data": {
    "imported": 5,
    "updated": 2,
    "failed": 1,
    "errors": [
      {
        "row": 4,
        "message": "Invalid language code: xx"
      }
    ],
    "warnings": [],
    "processing_time_ms": 234
  }
}
```

#### 7. Export Translations
```
GET /api/translations/export?content_ids=123&format=csv
```

**Response:** CSV file download

#### 8. Supported Languages
```
GET /api/content/languages
```

**Response:**
```json
{
  "success": true,
  "message": "System supports 15 languages",
  "data": {
    "languages": [
      {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "direction": "ltr",
        "is_supported": true
      }
    ],
    "default_language": "en",
    "total_count": 15
  }
}
```

## User Interface Flow

### Adding Translations

1. **Open Content Edit Modal**
   - Navigate to Contents page
   - Click "Edit" on any content item
   - Scroll to "Translations" section

2. **Add Language**
   - Click "Add Language" button
   - Select language from dropdown (with search)
   - Language selector excludes already-added languages
   - Click "Add Language" to confirm

3. **Enter Translation**
   - Switch to language tab
   - Enter translated title (required)
   - Enter translated description (required)
   - Optionally set as primary language (golden star ★)
   - RTL languages show directional indicator

4. **Save Translations**
   - Click "Save Translations" button
   - All dirty (modified) translations are saved
   - Success toast notification appears

### Bulk Import

1. **Open Bulk Import Modal**
   - Click "Bulk Import" button in TranslationManager
   - Modal opens with instructions

2. **Download Template**
   - Click "Download CSV Template"
   - Template file downloads automatically

3. **Prepare CSV File**
   - Fill in translations in spreadsheet
   - Follow CSV format: `language,title,description,is_primary`
   - Save as CSV file

4. **Upload File**
   - Click "Upload CSV File" or drag & drop
   - System parses and validates CSV
   - Preview shows all rows with validation status

5. **Review Preview**
   - Green checkmarks (✓) = valid rows
   - Red X marks (✗) = invalid rows with error messages
   - Summary shows valid/invalid count

6. **Import**
   - Click "Import" button
   - System processes valid rows
   - Results show imported/updated/failed counts
   - Errors are displayed for failed rows

### Export Translations

1. **Click Export CSV**
   - Button in TranslationManager header
   - File downloads automatically
   - Filename: `translations_{content_id}.csv`

## Type Definitions

### Translation Types

**File:** `/web-admin/src/types/translation.ts`

```typescript
export interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
  isRTL: boolean;
}

export const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧', isRTL: false },
  { code: 'id', name: 'Indonesian', nativeName: 'Bahasa Indonesia', flag: '🇮🇩', isRTL: false },
  // ... more languages
];

export const getLanguageByCode = (code: string): Language | undefined;
export const getLanguageName = (code: string): string;
export const getLanguageFlag = (code: string): string;
export const isRTLLanguage = (code: string): boolean;
```

### API Types

```typescript
export interface Translation {
  id: string;
  content_id: string;
  language: string;
  title: string;
  description: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface TranslationCreate {
  language: string;
  title: string;
  description: string;
  is_primary?: boolean;
}

export interface TranslationUpdate {
  title?: string;
  description?: string;
  is_primary?: boolean;
}

export interface BulkImportResponse {
  imported: number;
  updated: number;
  errors: Array<{
    row: number;
    message: string;
  }>;
}
```

## Styling & UI Features

### Language Badges

- **Primary Language:** Golden star (★) indicator
- **RTL Languages:** Purple badge with "RTL" text
- **Unsaved Changes:** Orange dot indicator
- **Language Count:** Blue badge in section header

### Tab Interface

- Active tab: Blue bottom border
- Inactive tabs: Gray, hover effect
- Language flag emoji (2x size)
- Language name displayed
- Visual indicators for state

### Form Fields

- **Title Input:** Full-width text input with RTL support
- **Description Textarea:** 4 rows, auto-expanding
- **Primary Checkbox:** Toggle with visual feedback
- **Fallback Info:** Yellow info box for non-primary languages

### Bulk Import UI

- **Drag & Drop Zone:** Dashed border, hover states
- **Preview Table:** Sticky header, scrollable body
- **Validation Indicators:** Color-coded rows (green/red)
- **Progress Feedback:** Loading spinners, success states

## Error Handling

### Client-Side Validation

```typescript
// Title required
if (!translation.title.trim()) {
  showToast(`Title is required for ${languageName}`, 'error');
  return;
}

// Description required
if (!translation.description.trim()) {
  showToast(`Description is required for ${languageName}`, 'error');
  return;
}
```

### Server-Side Validation

- Language code validation (ISO 639-1)
- Duplicate language detection
- Content existence check
- Primary language constraints

### Error Display

- Toast notifications for general errors
- Inline error messages in forms
- Row-level errors in bulk import preview
- HTTP error details in console

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**
   - Translations loaded on-demand
   - Modal content only loaded when opened

2. **Debouncing**
   - Search input debounced (300ms)
   - Form validation debounced

3. **Caching**
   - Language list cached client-side
   - Translation data cached until mutation

4. **Batch Operations**
   - Bulk save for multiple translations
   - Single API call for bulk import

## Accessibility

### WCAG 2.1 AA Compliance

- ✅ Keyboard navigation support
- ✅ ARIA labels on interactive elements
- ✅ Focus management in modals
- ✅ Color contrast ratios met
- ✅ Screen reader announcements
- ✅ RTL language support

### Keyboard Shortcuts

- `Tab` - Navigate between fields
- `Escape` - Close modals
- `Enter` - Submit forms (in inputs)
- `Space` - Toggle checkboxes

## Testing Recommendations

### Unit Tests

```typescript
// Test language selector
describe('LanguageSelector', () => {
  it('excludes already-used languages', () => {
    // Test implementation
  });

  it('filters languages by search term', () => {
    // Test implementation
  });
});

// Test translation manager
describe('TranslationManager', () => {
  it('loads existing translations', () => {
    // Test implementation
  });

  it('creates new translation', () => {
    // Test implementation
  });

  it('updates existing translation', () => {
    // Test implementation
  });
});
```

### Integration Tests

```typescript
// Test bulk import flow
describe('BulkImport', () => {
  it('imports valid CSV file', () => {
    // Test implementation
  });

  it('validates CSV format', () => {
    // Test implementation
  });

  it('displays errors for invalid rows', () => {
    // Test implementation
  });
});
```

## Troubleshooting

### Common Issues

#### 1. Translations not loading
**Solution:** Check API endpoint configuration in `apiClient.ts`

#### 2. CSV import failing
**Solution:** Verify CSV format matches template exactly

#### 3. RTL text not displaying correctly
**Solution:** Ensure `dir="rtl"` attribute is applied to inputs

#### 4. Primary language cannot be deleted
**Solution:** This is intentional - set another language as primary first

## Future Enhancements

### Planned Features

1. **Translation Memory**
   - Suggest previously used translations
   - Auto-complete based on similar content

2. **Machine Translation Integration**
   - Google Translate API integration
   - Suggest translations for all languages

3. **Translation Status Workflow**
   - Draft → Review → Approved pipeline
   - Reviewer assignment
   - Version history

4. **Advanced Search**
   - Search across all languages
   - Filter by translation status
   - Find untranslated content

5. **Analytics**
   - Translation coverage metrics
   - Most/least translated languages
   - Translation quality scores

## Support

For issues or questions:
- Check this documentation
- Review API endpoint documentation
- Check browser console for errors
- Verify backend API is running
- Test with CSV template file

## Changelog

### Version 1.0.0 (2025-01-28)
- Initial release
- 15 language support
- TranslationManager component
- LanguageSelector component
- BulkImportModal component
- API service integration
- CSV import/export
- RTL language support
- Primary language designation
- Fallback chain visualization
