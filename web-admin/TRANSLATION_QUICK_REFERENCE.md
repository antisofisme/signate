# Translation System - Quick Reference

## Component Usage

### 1. TranslationManager (Main Component)

```typescript
import TranslationManager from './components/content/TranslationManager';

// In EditContentModal or any content form
<TranslationManager contentId={content.id} />
```

**Props:**
- `contentId` (required): Content ID to manage translations for
- `className` (optional): Additional CSS classes

---

### 2. LanguageSelector (Dropdown Component)

```typescript
import LanguageSelector from './components/translations/LanguageSelector';

const [language, setLanguage] = useState('');

<LanguageSelector
  value={language}
  onChange={setLanguage}
  excludeLanguages={['en', 'id']}  // Already added languages
  placeholder="Select language"
  disabled={false}
/>
```

**Props:**
- `value`: Selected language code
- `onChange`: Callback when language changes
- `excludeLanguages`: Array of language codes to exclude
- `placeholder`: Placeholder text
- `disabled`: Disable selector
- `className`: Additional CSS classes

---

### 3. BulkImportModal (Import UI)

```typescript
import BulkImportModal from './components/translations/BulkImportModal';

const [showImport, setShowImport] = useState(false);

<BulkImportModal
  isOpen={showImport}
  onClose={() => setShowImport(false)}
  contentId={content.id}
  onImportComplete={() => {
    // Refresh translations
    loadTranslations();
  }}
/>
```

**Props:**
- `isOpen`: Modal open state
- `onClose`: Close callback
- `contentId`: Content ID
- `onImportComplete`: Success callback

---

## API Usage

### Import API Service

```typescript
import translationsApi from './services/api/translations';
```

### List Translations

```typescript
const translations = await translationsApi.list(contentId);
// Returns: Translation[]
```

### Create Translation

```typescript
const newTranslation = await translationsApi.create(contentId, {
  language: 'id',
  title: 'Selamat Datang',
  description: 'Deskripsi dalam bahasa Indonesia',
  is_primary: false
});
// Returns: Translation
```

### Update Translation

```typescript
const updated = await translationsApi.update(contentId, 'id', {
  title: 'Updated Title',
  description: 'Updated Description'
});
// Returns: Translation
```

### Delete Translation

```typescript
await translationsApi.remove(contentId, 'id');
// Returns: void
```

### Bulk Import

```typescript
const file = event.target.files[0]; // CSV file

const result = await translationsApi.bulkImport(contentId, file);
// Returns: BulkImportResponse
// {
//   imported: 5,
//   updated: 2,
//   errors: [{row: 4, message: "..."}]
// }
```

### Export CSV

```typescript
const blob = await translationsApi.exportCSV(contentId);

// Download file
const url = URL.createObjectURL(blob);
const link = document.createElement('a');
link.href = url;
link.download = `translations_${contentId}.csv`;
link.click();
```

### Download Template

```typescript
translationsApi.downloadTemplate();
// Downloads: translation_template.csv
```

---

## Language Utilities

### Import Types

```typescript
import {
  SUPPORTED_LANGUAGES,
  getLanguageByCode,
  getLanguageName,
  getLanguageFlag,
  isRTLLanguage
} from './types/translation';
```

### Get Language Info

```typescript
const language = getLanguageByCode('id');
// Returns: {
//   code: 'id',
//   name: 'Indonesian',
//   nativeName: 'Bahasa Indonesia',
//   flag: '🇮🇩',
//   isRTL: false
// }
```

### Get Language Name

```typescript
const name = getLanguageName('id');
// Returns: "Indonesian"
```

### Get Language Flag

```typescript
const flag = getLanguageFlag('id');
// Returns: "🇮🇩"
```

### Check RTL Language

```typescript
const isRTL = isRTLLanguage('ar');
// Returns: true (for Arabic)

const isRTL = isRTLLanguage('en');
// Returns: false (for English)
```

### Get All Supported Languages

```typescript
import { SUPPORTED_LANGUAGES } from './types/translation';

const languages = SUPPORTED_LANGUAGES;
// Returns: Language[] (15 languages)
```

---

## CSV Format

### Template Structure

```csv
language,title,description,is_primary
en,Welcome to Our Hotel,Enjoy your stay with us,true
id,Selamat Datang di Hotel Kami,Nikmati menginap bersama kami,false
zh,欢迎光临我们的酒店,与我们一起享受您的住宿,false
ja,私たちのホテルへようこそ,私たちとの滞在をお楽しみください,false
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `language` | string | Yes | ISO 639-1 language code (en, id, zh, etc.) |
| `title` | string | Yes | Translated title |
| `description` | string | Yes | Translated description |
| `is_primary` | boolean | No | Set as primary language (true/false) |

---

## Supported Languages

| Code | Name | Native Name | Flag | RTL |
|------|------|-------------|------|-----|
| `en` | English | English | 🇬🇧 | No |
| `id` | Indonesian | Bahasa Indonesia | 🇮🇩 | No |
| `zh` | Chinese | 中文 | 🇨🇳 | No |
| `ja` | Japanese | 日本語 | 🇯🇵 | No |
| `ko` | Korean | 한국어 | 🇰🇷 | No |
| `th` | Thai | ภาษาไทย | 🇹🇭 | No |
| `vi` | Vietnamese | Tiếng Việt | 🇻🇳 | No |
| `es` | Spanish | Español | 🇪🇸 | No |
| `fr` | French | Français | 🇫🇷 | No |
| `de` | German | Deutsch | 🇩🇪 | No |
| `pt` | Portuguese | Português | 🇵🇹 | No |
| `ru` | Russian | Русский | 🇷🇺 | No |
| `ar` | Arabic | العربية | 🇸🇦 | Yes |
| `hi` | Hindi | हिन्दी | 🇮🇳 | No |
| `ms` | Malay | Bahasa Melayu | 🇲🇾 | No |

---

## Type Definitions

### Translation

```typescript
interface Translation {
  id: string;
  content_id: string;
  language: string;
  title: string;
  description: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}
```

### TranslationCreate

```typescript
interface TranslationCreate {
  language: string;
  title: string;
  description: string;
  is_primary?: boolean;
}
```

### TranslationUpdate

```typescript
interface TranslationUpdate {
  title?: string;
  description?: string;
  is_primary?: boolean;
}
```

### BulkImportResponse

```typescript
interface BulkImportResponse {
  imported: number;
  updated: number;
  errors: Array<{
    row: number;
    message: string;
  }>;
}
```

### Language

```typescript
interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
  isRTL: boolean;
}
```

---

## Common Patterns

### Load and Display Translations

```typescript
const [translations, setTranslations] = useState<Translation[]>([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  const loadTranslations = async () => {
    try {
      const data = await translationsApi.list(contentId);
      setTranslations(data);
    } catch (error) {
      console.error('Failed to load translations:', error);
    } finally {
      setLoading(false);
    }
  };

  loadTranslations();
}, [contentId]);
```

### Add New Translation

```typescript
const handleAddTranslation = async (language: string) => {
  try {
    const newTranslation = await translationsApi.create(contentId, {
      language,
      title: `Title in ${language}`,
      description: `Description in ${language}`,
      is_primary: false
    });

    setTranslations([...translations, newTranslation]);
    showToast('Translation added successfully', 'success');
  } catch (error) {
    showToast('Failed to add translation', 'error');
  }
};
```

### Update Translation

```typescript
const handleUpdateTranslation = async (language: string, updates: TranslationUpdate) => {
  try {
    const updated = await translationsApi.update(contentId, language, updates);

    setTranslations(
      translations.map(t => t.language === language ? updated : t)
    );

    showToast('Translation updated', 'success');
  } catch (error) {
    showToast('Failed to update translation', 'error');
  }
};
```

### Delete Translation

```typescript
const handleDeleteTranslation = async (language: string) => {
  if (!confirm(`Delete ${getLanguageName(language)} translation?`)) {
    return;
  }

  try {
    await translationsApi.remove(contentId, language);

    setTranslations(
      translations.filter(t => t.language !== language)
    );

    showToast('Translation deleted', 'success');
  } catch (error) {
    showToast('Failed to delete translation', 'error');
  }
};
```

### Bulk Import with Error Handling

```typescript
const handleBulkImport = async (file: File) => {
  try {
    const result = await translationsApi.bulkImport(contentId, file);

    if (result.errors.length === 0) {
      showToast(`Imported ${result.imported} translations`, 'success');
    } else {
      showToast(
        `Imported ${result.imported}, ${result.errors.length} errors`,
        'warning'
      );

      // Display errors
      result.errors.forEach(error => {
        console.error(`Row ${error.row}: ${error.message}`);
      });
    }

    // Reload translations
    loadTranslations();
  } catch (error) {
    showToast('Import failed', 'error');
  }
};
```

---

## Backend API Endpoints

### Base URL
```
/api/content
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/content/{id}/translations` | Create translation |
| GET | `/content/{id}/translations` | List translations |
| GET | `/content/{id}/translations/{lang}` | Get translation with fallback |
| PATCH | `/content/{id}/translations/{lang}` | Update translation |
| DELETE | `/content/{id}/translations/{lang}` | Delete translation |
| POST | `/translations/bulk-import` | Bulk import CSV |
| GET | `/translations/export` | Export to CSV/JSON |
| GET | `/content/languages` | List supported languages |

---

## Best Practices

### 1. Always Validate User Input

```typescript
if (!title.trim()) {
  showToast('Title is required', 'error');
  return;
}

if (!description.trim()) {
  showToast('Description is required', 'error');
  return;
}
```

### 2. Handle RTL Languages Properly

```typescript
<input
  type="text"
  dir={isRTLLanguage(language) ? 'rtl' : 'ltr'}
  value={title}
  onChange={handleChange}
/>
```

### 3. Show Loading States

```typescript
{isLoading ? (
  <div className="flex items-center justify-center py-12">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    <span className="ml-3">Loading translations...</span>
  </div>
) : (
  <TranslationList translations={translations} />
)}
```

### 4. Provide User Feedback

```typescript
try {
  await translationsApi.create(contentId, data);
  showToast('Translation added successfully', 'success');
} catch (error) {
  showToast('Failed to add translation', 'error');
}
```

### 5. Debounce Search Input

```typescript
const [searchTerm, setSearchTerm] = useState('');
const debouncedSearch = useDebounce(searchTerm, 300);

useEffect(() => {
  filterLanguages(debouncedSearch);
}, [debouncedSearch]);
```

---

## Troubleshooting

### Issue: Translations not loading
**Fix:** Check API endpoint and network tab for errors

### Issue: CSV import fails
**Fix:** Verify CSV format matches template exactly

### Issue: RTL text not displaying correctly
**Fix:** Ensure `dir="rtl"` attribute is set on input/textarea

### Issue: Primary language indicator not showing
**Fix:** Verify `is_primary` field in translation data

### Issue: Language selector shows used languages
**Fix:** Pass `excludeLanguages` prop with used language codes

---

## Quick Commands

### Generate CSV Template
```typescript
translationsApi.downloadTemplate();
```

### Export All Translations
```typescript
const blob = await translationsApi.exportCSV(contentId);
```

### Get Available Languages
```typescript
const available = SUPPORTED_LANGUAGES.filter(
  lang => !usedLanguages.includes(lang.code)
);
```

### Check Translation Coverage
```typescript
const coverage = (translations.length / SUPPORTED_LANGUAGES.length) * 100;
console.log(`Translation coverage: ${coverage.toFixed(0)}%`);
```

---

## File Locations

```
web-admin/
├── src/
│   ├── components/
│   │   ├── content/
│   │   │   └── TranslationManager.tsx          # Main manager component
│   │   └── translations/
│   │       ├── LanguageSelector.tsx            # Language picker
│   │       └── BulkImportModal.tsx             # CSV import UI
│   ├── services/
│   │   └── api/
│   │       └── translations.ts                 # API service
│   └── types/
│       └── translation.ts                      # Type definitions
└── TRANSLATION_SYSTEM_DOCUMENTATION.md         # Full documentation
```

---

## Version

**Current Version:** 1.0.0
**Last Updated:** 2025-01-28
**Compatibility:** React 19+, TypeScript 5+
