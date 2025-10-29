# Phase 4.2: Multi-Language Content System Design

## Executive Summary

### Business Value
- **Market Expansion**: Support international hotels, airports, and retail chains
- **User Experience**: Guests/customers see content in their preferred language
- **Content Efficiency**: One content asset, multiple language variants (reduce duplication)
- **Operational Flexibility**: Centralized management with localized delivery
- **Competitive Advantage**: Multi-language support is essential for enterprise signage

### Technical Approach
- **Hybrid Model**: Separate language variants table with shared content metadata
- **Smart Fallback**: Language priority chain with graceful degradation
- **Zero-Migration Impact**: Backward compatible with existing single-language content
- **Performance First**: Optimized queries, language-aware caching, CDN-ready

### Implementation Complexity
- **Effort**: 3-4 weeks (1 backend, 1 web-admin, 1 viewer, 0.5-1 migration/testing)
- **Risk**: Medium (database schema changes, backward compatibility)
- **Dependencies**: Content management system, playlist engine, viewer player
- **ROI**: High (unlocks international market, improves UX)

---

## Use Cases

### 1. International Hotel Chain
**Scenario**: Hilton/Marriott with properties in 50+ countries

**Requirements**:
- Same content (breakfast menu, spa hours, hotel info) in 5-10 languages
- Auto-select language based on hotel location (Paris → French, Tokyo → Japanese)
- Guest can manually switch language on in-room TV
- Fallback to English if preferred language unavailable

**Implementation**:
```javascript
// Device configuration
{
  "device_id": "HILTON-TOKYO-ROOM-502",
  "location": "Tokyo, Japan",
  "default_language": "ja",
  "available_languages": ["ja", "en", "zh", "ko"],
  "allow_manual_switch": true
}

// Content with translations
{
  "content_id": 123,
  "content_group": "breakfast-menu",
  "variants": {
    "en": {"title": "Breakfast Menu", "file": "breakfast_en.mp4"},
    "ja": {"title": "朝食メニュー", "file": "breakfast_ja.mp4"},
    "zh": {"title": "早餐菜单", "file": "breakfast_zh.mp4"}
  }
}
```

### 2. Airport Signage
**Scenario**: International airport with passengers from 100+ countries

**Requirements**:
- Flight info, wayfinding, safety notices in 10+ languages
- Rotate languages every 30 seconds (English → Chinese → Japanese → Korean → Arabic → repeat)
- Always show English + local language simultaneously (dual display mode)
- Critical messages (evacuations) in all languages

**Implementation**:
```javascript
// Playlist with language rotation
{
  "playlist_id": 456,
  "display_mode": "rotate_languages",
  "rotation_interval": 30,  // seconds
  "languages": ["en", "zh", "ja", "ko", "ar", "es", "fr"],
  "always_include": ["en"],  // Always show English
  "content": [
    {
      "content_id": 789,
      "type": "flight_info",
      "duration": 180,
      "rotate_translations": true
    }
  ]
}
```

### 3. Retail Store Chain
**Scenario**: Uniqlo/Zara with regional stores

**Requirements**:
- Product promotions in regional languages (California → English/Spanish, Quebec → French/English)
- Seasonal campaigns with localized messaging
- Fallback to English if translation missing
- A/B testing different language variants

**Implementation**:
```javascript
// Location-based language selection
{
  "store_id": "UNIQLO-SF-001",
  "location": "San Francisco, CA",
  "primary_language": "en",
  "secondary_languages": ["es", "zh"],
  "language_selection_strategy": "location_based"
}

// Content with partial translations
{
  "content_id": 999,
  "content_group": "spring-sale",
  "variants": {
    "en": {"title": "Spring Sale 50% Off", "file": "sale_en.mp4"},
    "es": {"title": "Venta de Primavera 50% Descuento", "file": "sale_es.mp4"}
    // Missing "zh" translation → fallback to "en"
  }
}
```

---

## Database Design

### Chosen Approach: **Option C - Dedicated Translations Table (Modified)**

**Rationale**:
1. **Separation of Concerns**: Media files (language-agnostic) vs. text metadata (language-specific)
2. **Storage Efficiency**: Shared media files when possible (e.g., instrumental music video)
3. **Query Performance**: Indexed translations table, avoid JSON scanning
4. **Flexibility**: Easy to add/remove translations without touching content table
5. **Backward Compatibility**: Existing `contents` table structure remains mostly unchanged

### Schema Design

```sql
-- =====================================================
-- CORE CONTENT TABLE (language-agnostic metadata)
-- =====================================================
CREATE TABLE contents (
    id SERIAL PRIMARY KEY,

    -- Content identification
    content_group_id VARCHAR(50) NOT NULL,  -- Groups language variants together
    is_primary BOOLEAN DEFAULT false,        -- One variant is primary (for UI display)

    -- File metadata
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL,          -- 'image', 'video', 'webpage'
    file_size BIGINT,
    duration INTEGER,                         -- seconds
    mime_type VARCHAR(100),

    -- Playback settings (language-agnostic)
    is_enabled BOOLEAN DEFAULT true,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    play_order INTEGER DEFAULT 0,
    skip_asset_check BOOLEAN DEFAULT false,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),

    -- Indexes
    CONSTRAINT unique_content_group UNIQUE(content_group_id, file_path)
);

CREATE INDEX idx_contents_group ON contents(content_group_id);
CREATE INDEX idx_contents_enabled ON contents(is_enabled, start_date, end_date);
CREATE INDEX idx_contents_type ON contents(file_type);

-- =====================================================
-- TRANSLATIONS TABLE (language-specific text/metadata)
-- =====================================================
CREATE TABLE content_translations (
    id SERIAL PRIMARY KEY,

    -- Foreign key to content
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,

    -- Language identifier
    language VARCHAR(10) NOT NULL,           -- 'en', 'id', 'zh-CN', 'zh-TW', 'pt-BR'
    is_default BOOLEAN DEFAULT false,        -- Default translation for this content

    -- Translatable fields
    title VARCHAR(255) NOT NULL,
    description TEXT,

    -- Language-specific media (optional)
    localized_file_path VARCHAR(500),        -- If this variant has different media
    localized_thumbnail VARCHAR(500),        -- Language-specific thumbnail

    -- Overlay/template data (for dynamic content)
    overlay_text JSONB,                      -- {"headline": "...", "price": "..."}

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    translated_by INTEGER REFERENCES users(id),

    -- Constraints
    CONSTRAINT unique_content_language UNIQUE(content_id, language)
);

CREATE INDEX idx_translations_content ON content_translations(content_id);
CREATE INDEX idx_translations_language ON content_translations(language);
CREATE INDEX idx_translations_default ON content_translations(content_id, is_default);

-- =====================================================
-- LANGUAGE CONFIGURATION TABLE
-- =====================================================
CREATE TABLE languages (
    id SERIAL PRIMARY KEY,

    -- Language identification
    code VARCHAR(10) NOT NULL UNIQUE,        -- 'en', 'id', 'zh-CN'
    name VARCHAR(100) NOT NULL,              -- 'English', 'Indonesian', 'Chinese (Simplified)'
    native_name VARCHAR(100),                -- '中文（简体）'

    -- Language properties
    direction VARCHAR(3) DEFAULT 'ltr',      -- 'ltr' or 'rtl'
    is_enabled BOOLEAN DEFAULT true,

    -- Display settings
    sort_order INTEGER DEFAULT 0,
    flag_emoji VARCHAR(10),                  -- '🇺🇸', '🇮🇩', '🇨🇳'

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_languages_enabled ON languages(is_enabled, sort_order);

-- Initial language data
INSERT INTO languages (code, name, native_name, direction, flag_emoji, sort_order) VALUES
('en', 'English', 'English', 'ltr', '🇺🇸', 1),
('id', 'Indonesian', 'Bahasa Indonesia', 'ltr', '🇮🇩', 2),
('zh-CN', 'Chinese (Simplified)', '中文（简体）', 'ltr', '🇨🇳', 3),
('zh-TW', 'Chinese (Traditional)', '中文（繁體）', 'ltr', '🇹🇼', 4),
('ja', 'Japanese', '日本語', 'ltr', '🇯🇵', 5),
('ko', 'Korean', '한국어', 'ltr', '🇰🇷', 6),
('es', 'Spanish', 'Español', 'ltr', '🇪🇸', 7),
('fr', 'French', 'Français', 'ltr', '🇫🇷', 8),
('de', 'German', 'Deutsch', 'ltr', '🇩🇪', 9),
('ar', 'Arabic', 'العربية', 'rtl', '🇸🇦', 10),
('pt-BR', 'Portuguese (Brazil)', 'Português (Brasil)', 'ltr', '🇧🇷', 11),
('ru', 'Russian', 'Русский', 'ltr', '🇷🇺', 12),
('th', 'Thai', 'ไทย', 'ltr', '🇹🇭', 13),
('vi', 'Vietnamese', 'Tiếng Việt', 'ltr', '🇻🇳', 14);

-- =====================================================
-- DEVICE LANGUAGE PREFERENCES
-- =====================================================
ALTER TABLE devices ADD COLUMN IF NOT EXISTS default_language VARCHAR(10) DEFAULT 'en';
ALTER TABLE devices ADD COLUMN IF NOT EXISTS available_languages JSONB DEFAULT '["en"]'::jsonb;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS allow_manual_switch BOOLEAN DEFAULT true;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS language_rotation JSONB DEFAULT NULL;

-- Example language_rotation JSON:
-- {
--   "enabled": true,
--   "interval": 30,
--   "languages": ["en", "zh", "ja"],
--   "include_all": false
-- }

CREATE INDEX idx_devices_language ON devices(default_language);

-- =====================================================
-- SYSTEM-WIDE LANGUAGE SETTINGS
-- =====================================================
INSERT INTO settings (key, value, description) VALUES
('default_system_language', 'en', 'Default language for system-wide content'),
('enabled_languages', '["en", "id", "zh-CN", "ja"]', 'Languages enabled in the system'),
('fallback_chain', '["requested", "en", "any"]', 'Language fallback priority'),
('require_default_translation', 'true', 'Require at least one translation per content');
```

### Migration Strategy

**Phase 1: Schema Addition (Non-Breaking)**
```sql
-- Add new tables without modifying existing content table
CREATE TABLE content_translations (...);
CREATE TABLE languages (...);

-- Add new columns to devices (with defaults)
ALTER TABLE devices ADD COLUMN default_language VARCHAR(10) DEFAULT 'en';
```

**Phase 2: Data Migration (Backward Compatible)**
```sql
-- Migrate existing content to new structure
-- Each existing content becomes a content_group with English translation

-- Step 1: Generate content_group_id for existing content
UPDATE contents
SET content_group_id = CONCAT('legacy_', id::text)
WHERE content_group_id IS NULL;

-- Step 2: Create English translations for all existing content
INSERT INTO content_translations (content_id, language, is_default, title, description)
SELECT
    id,
    'en',
    true,
    name,  -- Map old 'name' field to new 'title'
    COALESCE(description, '')
FROM contents
WHERE NOT EXISTS (
    SELECT 1 FROM content_translations
    WHERE content_translations.content_id = contents.id
);

-- Step 3: Set primary flag for existing content
UPDATE contents SET is_primary = true WHERE is_primary = false;
```

**Phase 3: API Backward Compatibility**
```python
# Old endpoint (still works)
GET /api/content/{id}
# Returns: {..., "name": "...", "description": "..."}
# Behind the scenes: Fetches English translation

# New endpoint
GET /api/content/{id}?language=id
# Returns: {..., "title": "...", "description": "...", "language": "id"}
```

---

## API Specifications

### 1. Content Upload with Translations

**Endpoint**: `POST /api/content/upload`

**Request** (multipart/form-data):
```javascript
// Form data structure
{
  // Primary file
  "file": <File>,

  // Content metadata (JSON string)
  "metadata": {
    "content_group_id": "breakfast-menu-2024",  // Optional: auto-generated if not provided
    "file_type": "video",
    "duration": 30,
    "is_enabled": true,
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z"
  },

  // Translations (JSON string)
  "translations": {
    "en": {
      "title": "Breakfast Menu",
      "description": "Enjoy our delicious breakfast buffet",
      "is_default": true,
      "overlay_text": {
        "headline": "Breakfast Buffet",
        "hours": "6:00 AM - 10:00 AM"
      }
    },
    "id": {
      "title": "Menu Sarapan",
      "description": "Nikmati prasmanan sarapan lezat kami",
      "overlay_text": {
        "headline": "Prasmanan Sarapan",
        "hours": "06:00 - 10:00"
      }
    },
    "zh-CN": {
      "title": "早餐菜单",
      "description": "享用我们美味的自助早餐",
      "overlay_text": {
        "headline": "自助早餐",
        "hours": "上午6:00 - 上午10:00"
      }
    }
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "content_id": 123,
    "content_group_id": "breakfast-menu-2024",
    "file_path": "/uploads/content/2024/01/breakfast-menu.mp4",
    "file_type": "video",
    "duration": 30,
    "translations": [
      {
        "translation_id": 1,
        "language": "en",
        "title": "Breakfast Menu",
        "is_default": true
      },
      {
        "translation_id": 2,
        "language": "id",
        "title": "Menu Sarapan",
        "is_default": false
      },
      {
        "translation_id": 3,
        "language": "zh-CN",
        "title": "早餐菜单",
        "is_default": false
      }
    ]
  }
}
```

### 2. Upload Language-Specific Media

**Endpoint**: `POST /api/content/{content_id}/translations/{language}/upload`

**Use Case**: Video with burned-in subtitles/voiceover in different language

**Request** (multipart/form-data):
```javascript
{
  "file": <File>,  // breakfast-menu_ja.mp4 (with Japanese voiceover)
  "title": "朝食メニュー",
  "description": "美味しい朝食ビュッフェをお楽しみください",
  "overlay_text": {
    "headline": "朝食ビュッフェ",
    "hours": "午前6時 - 午前10時"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "translation_id": 4,
    "content_id": 123,
    "language": "ja",
    "title": "朝食メニュー",
    "localized_file_path": "/uploads/content/2024/01/breakfast-menu_ja.mp4",
    "file_size": 15728640
  }
}
```

### 3. Get Content in Specific Language

**Endpoint**: `GET /api/content/{content_id}?language={lang}&fallback={true|false}`

**Query Parameters**:
- `language`: Requested language code (e.g., 'id', 'zh-CN')
- `fallback`: Enable fallback chain (default: true)

**Example Request**:
```
GET /api/content/123?language=id&fallback=true
```

**Response**:
```json
{
  "success": true,
  "data": {
    "content_id": 123,
    "content_group_id": "breakfast-menu-2024",
    "file_path": "/uploads/content/2024/01/breakfast-menu.mp4",
    "file_type": "video",
    "duration": 30,
    "is_enabled": true,

    // Translation data
    "language": "id",
    "title": "Menu Sarapan",
    "description": "Nikmati prasmanan sarapan lezat kami",
    "localized_file_path": null,  // Uses main file_path
    "overlay_text": {
      "headline": "Prasmanan Sarapan",
      "hours": "06:00 - 10:00"
    },

    // Metadata
    "translation_fallback_used": false,  // Got exact language match
    "available_languages": ["en", "id", "zh-CN", "ja"]
  }
}
```

**Fallback Example**:
```
GET /api/content/123?language=ko&fallback=true
```

**Response** (Korean translation not available):
```json
{
  "success": true,
  "data": {
    "content_id": 123,
    "language": "en",  // Fell back to English
    "title": "Breakfast Menu",
    "translation_fallback_used": true,
    "requested_language": "ko",
    "fallback_reason": "Translation not available for 'ko', using default 'en'"
  }
}
```

### 4. Get All Translations for Content

**Endpoint**: `GET /api/content/{content_id}/translations`

**Response**:
```json
{
  "success": true,
  "data": {
    "content_id": 123,
    "content_group_id": "breakfast-menu-2024",
    "translations": [
      {
        "translation_id": 1,
        "language": "en",
        "language_name": "English",
        "title": "Breakfast Menu",
        "description": "Enjoy our delicious breakfast buffet",
        "is_default": true,
        "has_localized_media": false,
        "updated_at": "2024-01-15T10:30:00Z"
      },
      {
        "translation_id": 2,
        "language": "id",
        "language_name": "Indonesian",
        "title": "Menu Sarapan",
        "description": "Nikmati prasmanan sarapan lezat kami",
        "is_default": false,
        "has_localized_media": false,
        "updated_at": "2024-01-15T11:00:00Z"
      },
      {
        "translation_id": 4,
        "language": "ja",
        "language_name": "Japanese",
        "title": "朝食メニュー",
        "description": "美味しい朝食ビュッフェをお楽しみください",
        "is_default": false,
        "has_localized_media": true,  // Has separate Japanese video file
        "localized_file_path": "/uploads/content/2024/01/breakfast-menu_ja.mp4",
        "updated_at": "2024-01-16T09:00:00Z"
      }
    ],
    "available_languages": ["en", "id", "ja"],
    "missing_languages": ["zh-CN", "ko", "es", "fr"]  // Enabled but not translated
  }
}
```

### 5. Update Translation

**Endpoint**: `PATCH /api/content/{content_id}/translations/{language}`

**Request**:
```json
{
  "title": "Menu Sarapan (Updated)",
  "description": "Nikmati prasmanan sarapan lezat kami dengan pilihan internasional",
  "overlay_text": {
    "headline": "Prasmanan Sarapan Internasional",
    "hours": "06:00 - 10:30"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "translation_id": 2,
    "content_id": 123,
    "language": "id",
    "title": "Menu Sarapan (Updated)",
    "updated_at": "2024-01-20T14:30:00Z"
  }
}
```

### 6. Delete Translation

**Endpoint**: `DELETE /api/content/{content_id}/translations/{language}`

**Response**:
```json
{
  "success": true,
  "message": "Translation for language 'id' deleted successfully",
  "remaining_translations": ["en", "zh-CN", "ja"]
}
```

**Error Case** (trying to delete default translation):
```json
{
  "success": false,
  "error": "Cannot delete default translation. Set another translation as default first.",
  "error_code": "CANNOT_DELETE_DEFAULT_TRANSLATION"
}
```

### 7. Get Playlist with Language Parameter

**Endpoint**: `GET /api/playlists/devices/{device_id}/active?language={lang}`

**Example Request**:
```
GET /api/playlists/devices/TV-001/active?language=id
```

**Response**:
```json
{
  "success": true,
  "data": {
    "playlist_id": 456,
    "device_id": "TV-001",
    "language": "id",
    "content": [
      {
        "content_id": 123,
        "title": "Menu Sarapan",  // Indonesian translation
        "file_path": "/uploads/content/2024/01/breakfast-menu.mp4",
        "duration": 30,
        "language": "id"
      },
      {
        "content_id": 124,
        "title": "Welcome",  // No Indonesian translation, fell back to English
        "file_path": "/uploads/content/2024/01/welcome.mp4",
        "duration": 15,
        "language": "en",
        "fallback_used": true
      }
    ]
  }
}
```

### 8. Bulk Import Translations

**Endpoint**: `POST /api/content/translations/bulk-import`

**Request** (multipart/form-data):
```javascript
{
  "file": <CSV File>,  // translations.csv
  "language": "id",
  "overwrite_existing": false
}
```

**CSV Format**:
```csv
content_group_id,title,description,overlay_text_json
breakfast-menu-2024,"Menu Sarapan","Nikmati prasmanan sarapan lezat kami","{""headline"":""Prasmanan Sarapan""}"
welcome-2024,"Selamat Datang","Selamat datang di hotel kami","{""greeting"":""Selamat Datang""}"
spa-hours-2024,"Jam Operasional Spa","Spa buka setiap hari 09:00 - 21:00","{""hours"":""09:00 - 21:00""}"
```

**Response**:
```json
{
  "success": true,
  "data": {
    "imported": 3,
    "skipped": 0,
    "errors": 0,
    "details": [
      {
        "content_group_id": "breakfast-menu-2024",
        "content_id": 123,
        "status": "imported",
        "translation_id": 2
      },
      {
        "content_group_id": "welcome-2024",
        "content_id": 124,
        "status": "imported",
        "translation_id": 5
      },
      {
        "content_group_id": "spa-hours-2024",
        "content_id": 125,
        "status": "imported",
        "translation_id": 8
      }
    ]
  }
}
```

### 9. Export Translations

**Endpoint**: `GET /api/content/translations/export?language={lang}&format={csv|json}`

**Example Request**:
```
GET /api/content/translations/export?language=id&format=csv
```

**Response** (CSV file download):
```csv
content_id,content_group_id,language,title,description,has_localized_media,updated_at
123,breakfast-menu-2024,id,"Menu Sarapan","Nikmati prasmanan sarapan lezat kami",false,2024-01-15T11:00:00Z
124,welcome-2024,id,"Selamat Datang","Selamat datang di hotel kami",false,2024-01-15T11:05:00Z
125,spa-hours-2024,id,"Jam Operasional Spa","Spa buka setiap hari 09:00 - 21:00",false,2024-01-15T11:10:00Z
```

### 10. Language Management

**Endpoint**: `GET /api/languages`

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "code": "en",
      "name": "English",
      "native_name": "English",
      "direction": "ltr",
      "is_enabled": true,
      "flag_emoji": "🇺🇸",
      "content_count": 150,  // Number of content with this translation
      "last_updated": "2024-01-20T10:00:00Z"
    },
    {
      "code": "id",
      "name": "Indonesian",
      "native_name": "Bahasa Indonesia",
      "direction": "ltr",
      "is_enabled": true,
      "flag_emoji": "🇮🇩",
      "content_count": 85,
      "last_updated": "2024-01-20T14:30:00Z"
    }
  ]
}
```

---

## Web Admin UI

### Upload Workflow

**Step 1: Upload Content with Primary Language**

```
┌─────────────────────────────────────────────────────┐
│  Upload Content                                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  📁 Drop files here or click to upload              │
│  ┌──────────────────────────────────────────────┐   │
│  │                                              │   │
│  │         [Drag & Drop Area]                   │   │
│  │                                              │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  Primary Language: [English ▼]                      │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ Title *                                     │    │
│  │ [Breakfast Menu                    ]        │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ Description                                 │    │
│  │ [Enjoy our delicious breakfast buffet...]  │    │
│  │                                             │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  [Cancel]  [Upload & Add Translations]  [Upload]    │
└─────────────────────────────────────────────────────┘
```

**Step 2: Add Translations (Modal after upload)**

```
┌─────────────────────────────────────────────────────┐
│  Add Translations - Breakfast Menu              [×] │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Primary Language: English ✓                        │
│  File: breakfast-menu.mp4                           │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ 🇮🇩 Indonesian                     [Edit]   │    │
│  │ ✓ Title: Menu Sarapan                       │    │
│  │ ✓ Description: Nikmati prasmanan...         │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ 🇨🇳 Chinese (Simplified)           [Edit]   │    │
│  │ ✓ Title: 早餐菜单                          │    │
│  │ ✓ Description: 享用我们美味的...            │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ 🇯🇵 Japanese                       [Add]    │    │
│  │ ✗ Not translated                            │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  [+ Add Language]  [Bulk Import CSV]                │
│                                                      │
│  [Skip]           [Save Translations]               │
└─────────────────────────────────────────────────────┘
```

### Translation Management

**Content List with Language Indicators**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Content Library                          [+ Upload]  [Bulk Import]     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  🔍 Search...  [Type: All ▼]  [Language: All ▼]  [Translation Status ▼] │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 📹 Breakfast Menu                          🇺🇸 🇮🇩 🇨🇳 🇯🇵        │ │
│  │ Video • 30s • Created Jan 15               [4 languages]  [⚙️]     │ │
│  │ breakfast-menu-2024                                                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 🖼️ Welcome Message                        🇺🇸 ⚠️                   │ │
│  │ Image • 15s • Created Jan 16              [1 language]  [⚙️]       │ │
│  │ welcome-2024                              Missing: 🇮🇩 🇨🇳 🇯🇵     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 📹 Spa Hours                              🇺🇸 🇮🇩 🇨🇳 🇯🇵 🇰🇷 🇪🇸  │ │
│  │ Video • 20s • Created Jan 17              [6 languages]  [⚙️]      │ │
│  │ spa-hours-2024                                                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Translation Editor (Modal)**

```
┌─────────────────────────────────────────────────────┐
│  Edit Translations - Breakfast Menu             [×] │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Language Tabs:                                     │
│  [🇺🇸 English*] [🇮🇩 Indonesian] [🇨🇳 Chinese]       │
│                                                      │
│  ─────────────────────────────────────────────────  │
│                                                      │
│  🇮🇩 Indonesian Translation                         │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ Title *                                     │    │
│  │ [Menu Sarapan                      ]        │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ Description                                 │    │
│  │ [Nikmati prasmanan sarapan lezat kami      │    │
│  │  dengan pilihan makanan internasional]     │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ Localized Media (optional)                  │    │
│  │ ⚠️ Use only if this language needs a        │    │
│  │    different video/image file               │    │
│  │                                             │    │
│  │ Current: Using primary file                 │    │
│  │ [📁 Upload Indonesian version]              │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ Overlay Text (JSON)              [Format]  │    │
│  │ {                                           │    │
│  │   "headline": "Prasmanan Sarapan",          │    │
│  │   "hours": "06:00 - 10:00"                  │    │
│  │ }                                           │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  Last updated: Jan 15, 2024 by admin                │
│                                                      │
│  [Delete Translation]  [Cancel]  [Save Changes]     │
└─────────────────────────────────────────────────────┘
```

### Bulk Operations

**Bulk Import Translations**

```
┌─────────────────────────────────────────────────────┐
│  Bulk Import Translations                       [×] │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Step 1: Download Template                          │
│  [📥 Download CSV Template]                         │
│                                                      │
│  Step 2: Fill in translations                       │
│  Open the CSV file in Excel/Google Sheets and       │
│  add your translations.                             │
│                                                      │
│  Step 3: Upload completed CSV                       │
│  Target Language: [Indonesian ▼]                    │
│                                                      │
│  📁 Drop CSV file here or click to upload           │
│  ┌──────────────────────────────────────────────┐   │
│  │                                              │   │
│  │      [Drag & Drop CSV File]                  │   │
│  │                                              │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  Options:                                           │
│  ☑️ Overwrite existing translations                 │
│  ☑️ Skip content not found                          │
│  ☐ Create missing content                           │
│                                                      │
│  [Cancel]              [Upload & Import]            │
└─────────────────────────────────────────────────────┘
```

**Import Results**

```
┌─────────────────────────────────────────────────────┐
│  Import Results                                 [×] │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ✓ Successfully imported 85 translations            │
│  ⚠️ Skipped 5 items                                 │
│  ✗ Failed 2 items                                   │
│                                                      │
│  ─────────────────────────────────────────────────  │
│                                                      │
│  ✓ breakfast-menu-2024 → Imported                   │
│  ✓ welcome-2024 → Imported                          │
│  ✓ spa-hours-2024 → Imported                        │
│  ⚠️ pool-rules-2024 → Skipped (already exists)      │
│  ✗ gym-hours-2024 → Failed (content not found)      │
│                                                      │
│  [📥 Download Error Report]  [Close]                │
└─────────────────────────────────────────────────────┘
```

### Preview Functionality

**Preview Modal with Language Switcher**

```
┌─────────────────────────────────────────────────────────────┐
│  Preview - Breakfast Menu                               [×] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Language: [🇺🇸 English ▼]                                   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                                                        │ │
│  │                                                        │ │
│  │                  [Video Preview]                       │ │
│  │              breakfast-menu.mp4                        │ │
│  │                                                        │ │
│  │                    [▶️ Play]                            │ │
│  │                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Title: Breakfast Menu                                      │
│  Description: Enjoy our delicious breakfast buffet from     │
│  6:00 AM to 10:00 AM daily.                                 │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Other Languages:                                           │
│  [🇮🇩 Indonesian]  [🇨🇳 Chinese]  [🇯🇵 Japanese]             │
│                                                              │
│  [Close]                                                    │
└─────────────────────────────────────────────────────────────┘
```

**Device Language Configuration**

```
┌─────────────────────────────────────────────────────┐
│  Edit Device - HILTON-TOKYO-ROOM-502            [×] │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [General] [Display] [Language] [Content] [Advanced]│
│                                                      │
│  ─────────────────────────────────────────────────  │
│                                                      │
│  Language Settings                                  │
│                                                      │
│  Default Language:                                  │
│  [🇯🇵 Japanese ▼]                                    │
│                                                      │
│  Available Languages:                               │
│  ☑️ 🇯🇵 Japanese (default)                          │
│  ☑️ 🇺🇸 English                                      │
│  ☑️ 🇨🇳 Chinese (Simplified)                         │
│  ☑️ 🇰🇷 Korean                                       │
│  ☐ 🇪🇸 Spanish                                       │
│  ☐ 🇫🇷 French                                        │
│                                                      │
│  Guest Options:                                     │
│  ☑️ Allow manual language switching                 │
│  ☐ Show language selector on startup                │
│                                                      │
│  Language Rotation (for multi-language display):    │
│  ☐ Enable language rotation                         │
│  Interval: [30] seconds                             │
│  Rotate through: [All available languages ▼]        │
│                                                      │
│  Fallback Behavior:                                 │
│  ◉ Use English if translation missing               │
│  ○ Use any available language                       │
│  ○ Skip content without translation                 │
│                                                      │
│  [Cancel]              [Save Changes]               │
└─────────────────────────────────────────────────────┘
```

### Dashboard Translation Status Widget

```
┌─────────────────────────────────────────────────────┐
│  Translation Coverage                               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  🇺🇸 English        ████████████████████ 100% (150)  │
│  🇮🇩 Indonesian     ██████████████░░░░░░  70% (105)  │
│  🇨🇳 Chinese        ████████████░░░░░░░░  60% (90)   │
│  🇯🇵 Japanese       ██████████░░░░░░░░░░  50% (75)   │
│  🇰🇷 Korean         ████░░░░░░░░░░░░░░░░  20% (30)   │
│  🇪🇸 Spanish        ██░░░░░░░░░░░░░░░░░░  10% (15)   │
│                                                      │
│  ⚠️ 45 content items missing Indonesian translation │
│                                                      │
│  [View Missing Translations]                        │
└─────────────────────────────────────────────────────┘
```

---

## Viewer Integration

### Language Selection UI

**Option 1: Bottom-Right Language Switcher (Minimal)**

```
┌─────────────────────────────────────────────────┐
│                                                  │
│         [Content Playing Full Screen]            │
│                                                  │
│                                                  │
│                                                  │
│                                             🌐   │ ← Click to open
└─────────────────────────────────────────────────┘

On click:
┌─────────────────────────────────────────────────┐
│                                                  │
│         [Content Playing Full Screen]            │
│                                                  │
│                                                  │
│                              ┌────────────────┐ │
│                              │ 🇺🇸 English    │ │
│                              │ 🇮🇩 Indonesian │ │
│                              │ 🇨🇳 中文        │ │
│                              │ 🇯🇵 日本語     │ │
│                              └────────────────┘ │
└─────────────────────────────────────────────────┘
```

**Option 2: Startup Language Selector (Hotel TV)**

```
┌─────────────────────────────────────────────────┐
│                                                  │
│              Welcome / ようこそ                   │
│          Please select your language             │
│                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │            │  │            │  │            │ │
│  │  🇯🇵        │  │  🇺🇸        │  │  🇨🇳        │ │
│  │  日本語     │  │  English   │  │  中文       │ │
│  │            │  │            │  │            │ │
│  └────────────┘  └────────────┘  └────────────┘ │
│                                                  │
│  ┌────────────┐  ┌────────────┐                 │
│  │            │  │            │                 │
│  │  🇰🇷        │  │  🇪🇸        │                 │
│  │  한국어     │  │  Español   │                 │
│  │            │  │            │                 │
│  └────────────┘  └────────────┘                 │
│                                                  │
│              [Continue to content]               │
└─────────────────────────────────────────────────┘
```

**Option 3: Language Rotation Indicator (Airport)**

```
┌─────────────────────────────────────────────────┐
│                                                  │
│         [Content Playing Full Screen]            │
│                                                  │
│     Flight BA123 to London - Gate 5             │
│                                                  │
│                                                  │
│  🇺🇸 EN (30s) → 🇨🇳 ZH → 🇯🇵 JA → 🇰🇷 KO           │ ← Progress bar
└─────────────────────────────────────────────────┘
```

### Viewer JavaScript Implementation

**File**: `viewer/js/shared/language-manager.js`

```javascript
/**
 * Language Manager for Viewer
 * Handles language selection, fallback, and persistence
 */
class LanguageManager {
    constructor(config = {}) {
        this.defaultLanguage = config.defaultLanguage || 'en';
        this.availableLanguages = config.availableLanguages || ['en'];
        this.allowManualSwitch = config.allowManualSwitch !== false;
        this.languageRotation = config.languageRotation || null;
        this.fallbackChain = ['requested', 'en', 'any'];

        this.currentLanguage = null;
        this.rotationTimer = null;

        this.init();
    }

    init() {
        // Load saved language preference
        this.currentLanguage = this.loadLanguagePreference() || this.defaultLanguage;

        // Start rotation if configured
        if (this.languageRotation?.enabled) {
            this.startRotation();
        }

        // Render language selector if allowed
        if (this.allowManualSwitch) {
            this.renderLanguageSelector();
        }

        console.log('LanguageManager initialized:', {
            current: this.currentLanguage,
            available: this.availableLanguages,
            rotation: this.languageRotation?.enabled
        });
    }

    /**
     * Get current language
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    /**
     * Set language and persist
     */
    async setLanguage(languageCode) {
        if (!this.availableLanguages.includes(languageCode)) {
            console.warn(`Language '${languageCode}' not available, using default`);
            languageCode = this.defaultLanguage;
        }

        this.currentLanguage = languageCode;
        this.saveLanguagePreference(languageCode);

        // Stop rotation if manual selection
        if (this.rotationTimer) {
            clearInterval(this.rotationTimer);
            this.rotationTimer = null;
        }

        // Reload playlist with new language
        await this.reloadPlaylist();

        // Update UI
        this.updateLanguageSelectorUI();

        console.log('Language changed to:', languageCode);
    }

    /**
     * Language rotation for multi-language display
     */
    startRotation() {
        const { interval, languages } = this.languageRotation;
        const rotatableLanguages = languages || this.availableLanguages;

        let currentIndex = 0;

        this.rotationTimer = setInterval(() => {
            currentIndex = (currentIndex + 1) % rotatableLanguages.length;
            const nextLanguage = rotatableLanguages[currentIndex];

            this.currentLanguage = nextLanguage;
            this.reloadPlaylist();
            this.showRotationIndicator(nextLanguage, rotatableLanguages, currentIndex);

            console.log('Language rotated to:', nextLanguage);
        }, (interval || 30) * 1000);

        console.log('Language rotation started:', {
            interval: interval || 30,
            languages: rotatableLanguages
        });
    }

    /**
     * Reload playlist with current language
     */
    async reloadPlaylist() {
        try {
            const deviceId = localStorage.getItem('device_id');
            const response = await fetch(
                `${API_BASE_URL}/api/playlists/devices/${deviceId}/active?language=${this.currentLanguage}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            // Update player with new playlist
            if (window.contentPlayer) {
                window.contentPlayer.loadPlaylist(data.data);
            }

            console.log('Playlist reloaded with language:', this.currentLanguage);
        } catch (error) {
            console.error('Failed to reload playlist:', error);
        }
    }

    /**
     * Render language selector UI
     */
    renderLanguageSelector() {
        // Remove existing selector
        const existing = document.getElementById('language-selector');
        if (existing) existing.remove();

        // Create container
        const container = document.createElement('div');
        container.id = 'language-selector';
        container.className = 'language-selector';

        // Create button
        const button = document.createElement('button');
        button.className = 'language-selector-button';
        button.innerHTML = '🌐';
        button.title = 'Select Language';
        button.onclick = () => this.toggleLanguageMenu();

        // Create menu
        const menu = document.createElement('div');
        menu.className = 'language-menu hidden';
        menu.id = 'language-menu';

        this.availableLanguages.forEach(lang => {
            const option = document.createElement('div');
            option.className = 'language-option';
            option.dataset.language = lang;
            option.innerHTML = `${this.getLanguageFlag(lang)} ${this.getLanguageName(lang)}`;
            option.onclick = () => this.setLanguage(lang);

            if (lang === this.currentLanguage) {
                option.classList.add('active');
            }

            menu.appendChild(option);
        });

        container.appendChild(button);
        container.appendChild(menu);
        document.body.appendChild(container);

        // Add styles
        this.injectStyles();
    }

    /**
     * Toggle language menu
     */
    toggleLanguageMenu() {
        const menu = document.getElementById('language-menu');
        if (menu) {
            menu.classList.toggle('hidden');
        }
    }

    /**
     * Update language selector UI
     */
    updateLanguageSelectorUI() {
        const options = document.querySelectorAll('.language-option');
        options.forEach(option => {
            if (option.dataset.language === this.currentLanguage) {
                option.classList.add('active');
            } else {
                option.classList.remove('active');
            }
        });

        // Hide menu
        const menu = document.getElementById('language-menu');
        if (menu) {
            menu.classList.add('hidden');
        }
    }

    /**
     * Show rotation indicator
     */
    showRotationIndicator(currentLang, allLangs, currentIndex) {
        // Remove existing indicator
        const existing = document.getElementById('rotation-indicator');
        if (existing) existing.remove();

        // Create indicator
        const indicator = document.createElement('div');
        indicator.id = 'rotation-indicator';
        indicator.className = 'rotation-indicator';

        const progress = ((currentIndex + 1) / allLangs.length) * 100;

        indicator.innerHTML = `
            <div class="rotation-languages">
                ${allLangs.map((lang, idx) => `
                    <span class="${idx === currentIndex ? 'active' : ''}">
                        ${this.getLanguageFlag(lang)} ${lang.toUpperCase()}
                    </span>
                `).join(' → ')}
            </div>
            <div class="rotation-progress">
                <div class="rotation-progress-bar" style="width: ${progress}%"></div>
            </div>
        `;

        document.body.appendChild(indicator);

        // Auto-hide after 3 seconds
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.classList.add('fade-out');
                setTimeout(() => indicator.remove(), 500);
            }
        }, 3000);
    }

    /**
     * Save language preference to localStorage
     */
    saveLanguagePreference(languageCode) {
        localStorage.setItem('language', languageCode);
        localStorage.setItem('language_changed_at', new Date().toISOString());
    }

    /**
     * Load language preference from localStorage
     */
    loadLanguagePreference() {
        return localStorage.getItem('language');
    }

    /**
     * Get language flag emoji
     */
    getLanguageFlag(code) {
        const flags = {
            'en': '🇺🇸',
            'id': '🇮🇩',
            'zh': '🇨🇳',
            'zh-CN': '🇨🇳',
            'zh-TW': '🇹🇼',
            'ja': '🇯🇵',
            'ko': '🇰🇷',
            'es': '🇪🇸',
            'fr': '🇫🇷',
            'de': '🇩🇪',
            'ar': '🇸🇦',
            'pt-BR': '🇧🇷',
            'ru': '🇷🇺',
            'th': '🇹🇭',
            'vi': '🇻🇳'
        };
        return flags[code] || '🌐';
    }

    /**
     * Get language name
     */
    getLanguageName(code) {
        const names = {
            'en': 'English',
            'id': 'Indonesian',
            'zh': '中文',
            'zh-CN': '简体中文',
            'zh-TW': '繁體中文',
            'ja': '日本語',
            'ko': '한국어',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'ar': 'العربية',
            'pt-BR': 'Português',
            'ru': 'Русский',
            'th': 'ไทย',
            'vi': 'Tiếng Việt'
        };
        return names[code] || code.toUpperCase();
    }

    /**
     * Inject CSS styles
     */
    injectStyles() {
        if (document.getElementById('language-selector-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'language-selector-styles';
        styles.textContent = `
            .language-selector {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999;
            }

            .language-selector-button {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background: rgba(0, 0, 0, 0.7);
                border: 2px solid rgba(255, 255, 255, 0.3);
                color: white;
                font-size: 24px;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .language-selector-button:hover {
                background: rgba(0, 0, 0, 0.9);
                border-color: rgba(255, 255, 255, 0.5);
                transform: scale(1.1);
            }

            .language-menu {
                position: absolute;
                bottom: 60px;
                right: 0;
                background: rgba(0, 0, 0, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 8px;
                min-width: 200px;
                transition: all 0.3s ease;
            }

            .language-menu.hidden {
                opacity: 0;
                pointer-events: none;
                transform: translateY(10px);
            }

            .language-option {
                padding: 12px 16px;
                cursor: pointer;
                color: white;
                border-radius: 4px;
                transition: all 0.2s ease;
                font-size: 16px;
            }

            .language-option:hover {
                background: rgba(255, 255, 255, 0.1);
            }

            .language-option.active {
                background: rgba(59, 130, 246, 0.5);
                font-weight: bold;
            }

            .rotation-indicator {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0, 0, 0, 0.8);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 12px 20px;
                z-index: 9998;
                transition: opacity 0.5s ease;
            }

            .rotation-indicator.fade-out {
                opacity: 0;
            }

            .rotation-languages {
                color: white;
                font-size: 14px;
                margin-bottom: 8px;
                text-align: center;
            }

            .rotation-languages span {
                opacity: 0.5;
                transition: opacity 0.3s ease;
            }

            .rotation-languages span.active {
                opacity: 1;
                font-weight: bold;
                color: #3b82f6;
            }

            .rotation-progress {
                height: 4px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
                overflow: hidden;
            }

            .rotation-progress-bar {
                height: 100%;
                background: #3b82f6;
                transition: width 0.3s ease;
            }
        `;

        document.head.appendChild(styles);
    }
}

// Export for use in other modules
window.LanguageManager = LanguageManager;
```

### Viewer Initialization with Language Manager

**File**: `viewer/js/player/api.js` (Updated)

```javascript
/**
 * Initialize viewer with language support
 */
async function initializeViewer() {
    try {
        // Get device configuration
        const deviceId = localStorage.getItem('device_id');
        const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}`);
        const deviceData = await response.json();
        const device = deviceData.data;

        // Initialize language manager
        const languageManager = new LanguageManager({
            defaultLanguage: device.default_language || 'en',
            availableLanguages: device.available_languages || ['en'],
            allowManualSwitch: device.allow_manual_switch !== false,
            languageRotation: device.language_rotation
        });

        // Store globally
        window.languageManager = languageManager;

        // Load playlist with current language
        await loadPlaylistWithLanguage(deviceId, languageManager.getCurrentLanguage());

        console.log('Viewer initialized with language support');
    } catch (error) {
        console.error('Failed to initialize viewer:', error);
    }
}

/**
 * Load playlist with language parameter
 */
async function loadPlaylistWithLanguage(deviceId, language) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/api/playlists/devices/${deviceId}/active?language=${language}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Start playing content
        if (window.contentPlayer) {
            window.contentPlayer.loadPlaylist(data.data);
        }

        console.log('Playlist loaded:', {
            language,
            contentCount: data.data.content?.length
        });
    } catch (error) {
        console.error('Failed to load playlist:', error);
    }
}
```

---

## Fallback Strategy

### Language Priority Chain

**Strategy**: Graceful degradation with multiple fallback levels

```javascript
/**
 * Fallback chain implementation
 */
function resolveContentLanguage(content, requestedLanguage) {
    const fallbackChain = [
        requestedLanguage,           // 1. Exact match
        extractPrimaryLanguage(requestedLanguage), // 2. Primary language (zh-CN → zh)
        content.default_language,    // 3. Content default
        'en',                        // 4. English (universal fallback)
        content.available_languages[0] // 5. Any available language
    ];

    for (const lang of fallbackChain) {
        if (content.translations[lang]) {
            return {
                language: lang,
                translation: content.translations[lang],
                fallbackUsed: lang !== requestedLanguage,
                fallbackReason: getFallbackReason(requestedLanguage, lang)
            };
        }
    }

    // No translation available
    return {
        language: null,
        translation: null,
        fallbackUsed: true,
        fallbackReason: 'No translation available for this content'
    };
}

/**
 * Extract primary language from locale code
 */
function extractPrimaryLanguage(locale) {
    // zh-CN → zh, pt-BR → pt, en-US → en
    return locale.split('-')[0];
}

/**
 * Get human-readable fallback reason
 */
function getFallbackReason(requested, resolved) {
    if (resolved === null) {
        return `Content not available in '${requested}'`;
    }

    if (resolved === extractPrimaryLanguage(requested)) {
        return `Locale '${requested}' not available, using primary language '${resolved}'`;
    }

    if (resolved === 'en') {
        return `Translation for '${requested}' not available, using English`;
    }

    return `Translation for '${requested}' not available, using '${resolved}'`;
}
```

### Backend Fallback Implementation

**File**: `backend/app/api/content.py`

```python
from typing import Optional, Dict, Any

def resolve_translation(
    content: Dict[str, Any],
    language: str,
    fallback_enabled: bool = True
) -> Dict[str, Any]:
    """
    Resolve content translation with fallback chain

    Args:
        content: Content dictionary with translations
        language: Requested language code
        fallback_enabled: Enable fallback chain

    Returns:
        Resolved translation dictionary
    """
    translations = content.get('translations', {})

    # 1. Exact match
    if language in translations:
        return {
            'language': language,
            'translation': translations[language],
            'fallback_used': False
        }

    if not fallback_enabled:
        return {
            'language': None,
            'translation': None,
            'fallback_used': True,
            'fallback_reason': f"Translation for '{language}' not available"
        }

    # 2. Primary language (zh-CN → zh)
    primary_language = language.split('-')[0]
    if primary_language != language and primary_language in translations:
        return {
            'language': primary_language,
            'translation': translations[primary_language],
            'fallback_used': True,
            'fallback_reason': f"Locale '{language}' not available, using primary language '{primary_language}'"
        }

    # 3. Default language for this content
    default_translation = next(
        (t for t in translations.values() if t.get('is_default')),
        None
    )
    if default_translation:
        default_lang = next(
            (k for k, v in translations.items() if v == default_translation),
            None
        )
        return {
            'language': default_lang,
            'translation': default_translation,
            'fallback_used': True,
            'fallback_reason': f"Translation for '{language}' not available, using default '{default_lang}'"
        }

    # 4. English (universal fallback)
    if 'en' in translations:
        return {
            'language': 'en',
            'translation': translations['en'],
            'fallback_used': True,
            'fallback_reason': f"Translation for '{language}' not available, using English"
        }

    # 5. Any available language
    if translations:
        first_lang = next(iter(translations.keys()))
        return {
            'language': first_lang,
            'translation': translations[first_lang],
            'fallback_used': True,
            'fallback_reason': f"Translation for '{language}' not available, using '{first_lang}'"
        }

    # No translations available
    return {
        'language': None,
        'translation': None,
        'fallback_used': True,
        'fallback_reason': 'No translations available for this content'
    }
```

### Handling Missing Translations

**Strategy 1: Show with Warning**
- Display content with fallback language
- Show subtle indicator: "Content shown in English"
- Log analytics event for missing translation

**Strategy 2: Skip Content**
- Remove content from playlist if translation unavailable
- Useful for text-heavy content where language matters
- Configuration: `skip_untranslated: true`

**Strategy 3: Mixed Playlist**
- Show some content in requested language, some in fallback
- Best for image/video content where language less critical
- Example: Hotel TV showing mix of localized and English content

```python
def filter_playlist_by_language(
    playlist: List[Dict[str, Any]],
    language: str,
    skip_untranslated: bool = False
) -> List[Dict[str, Any]]:
    """
    Filter playlist content based on language availability
    """
    filtered_content = []

    for content in playlist:
        resolved = resolve_translation(content, language, fallback_enabled=True)

        # Skip if translation missing and skip_untranslated is True
        if skip_untranslated and resolved['fallback_used']:
            continue

        # Add translation info to content
        content['current_language'] = resolved['language']
        content['current_translation'] = resolved['translation']
        content['fallback_used'] = resolved['fallback_used']

        if resolved.get('fallback_reason'):
            content['fallback_reason'] = resolved['fallback_reason']

        filtered_content.append(content)

    return filtered_content
```

---

## Edge Cases

### 1. Content Has No Translation for Requested Language

**Scenario**: Japanese guest requests Japanese content, but only English available

**Solution**:
```javascript
// Backend response includes fallback info
{
  "content_id": 123,
  "title": "Breakfast Menu",
  "language": "en",  // Fell back to English
  "fallback_used": true,
  "requested_language": "ja",
  "fallback_reason": "Translation not available for 'ja', using English"
}

// Viewer shows subtle indicator
┌─────────────────────────────────────────────────┐
│                                                  │
│         [Content Playing]                        │
│                                                  │
│  ℹ️ This content is shown in English             │ ← Small notice
└─────────────────────────────────────────────────┘
```

### 2. Device Switches Language Mid-Playback

**Scenario**: Guest changes language from English to Japanese while content is playing

**Solution**:
```javascript
async setLanguage(languageCode) {
    // Stop current content
    if (window.contentPlayer) {
        window.contentPlayer.pause();
    }

    // Save new language
    this.currentLanguage = languageCode;
    this.saveLanguagePreference(languageCode);

    // Reload playlist
    await this.reloadPlaylist();

    // Resume from beginning of new content
    if (window.contentPlayer) {
        window.contentPlayer.play();
    }

    // Show transition message
    this.showLanguageChangeMessage(languageCode);
}

showLanguageChangeMessage(languageCode) {
    const message = document.createElement('div');
    message.className = 'language-change-message';
    message.textContent = `Language changed to ${this.getLanguageName(languageCode)}`;
    document.body.appendChild(message);

    setTimeout(() => message.remove(), 3000);
}
```

### 3. Mixed Content Playlist (Some Translated, Some Not)

**Scenario**: Playlist has 10 items, only 6 have Japanese translations

**Solution**:
```python
# Backend configuration
device_config = {
    "default_language": "ja",
    "fallback_behavior": "mixed",  # Options: "mixed", "skip_untranslated", "fallback_only"
    "show_language_indicator": True
}

# Playlist response
{
  "playlist_id": 456,
  "device_id": "TV-001",
  "language": "ja",
  "content": [
    {"id": 1, "title": "朝食メニュー", "language": "ja", "fallback_used": false},
    {"id": 2, "title": "スパ営業時間", "language": "ja", "fallback_used": false},
    {"id": 3, "title": "Welcome", "language": "en", "fallback_used": true},  # No Japanese
    {"id": 4, "title": "プール規則", "language": "ja", "fallback_used": false},
    {"id": 5, "title": "Emergency Info", "language": "en", "fallback_used": true}  # No Japanese
  ]
}
```

### 4. Right-to-Left Languages (Arabic, Hebrew)

**Scenario**: Content displayed in Arabic needs RTL text direction

**Solution**:
```javascript
// Backend includes text direction in language metadata
{
  "language": "ar",
  "language_name": "Arabic",
  "direction": "rtl",  // Right-to-left
  "title": "قائمة الإفطار",
  "description": "استمتع بوجبة إفطار لذيذة"
}

// Viewer applies RTL CSS
function applyLanguageDirection(language) {
    const direction = language.direction || 'ltr';
    document.body.setAttribute('dir', direction);
    document.body.classList.toggle('rtl', direction === 'rtl');
}

// CSS adjustments
body.rtl {
    direction: rtl;
    text-align: right;
}

body.rtl .language-selector {
    left: 20px;  /* Flip to left side */
    right: auto;
}

body.rtl .rotation-indicator {
    /* RTL-specific styles */
}
```

### 5. Character Encoding Issues

**Scenario**: Chinese characters display as ��� or boxes

**Solution**:
```python
# Backend ensures UTF-8 encoding
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/content/{content_id}")
async def get_content(content_id: int, language: str = 'en'):
    content = get_content_from_db(content_id, language)

    # Ensure UTF-8 encoding
    return JSONResponse(
        content=content,
        media_type="application/json; charset=utf-8"
    )

# Database configuration
# PostgreSQL: Database encoding should be UTF8
CREATE DATABASE signage_db
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8';

# SQLAlchemy connection with UTF-8
DATABASE_URL = "postgresql://user:pass@host/db?client_encoding=utf8"
```

```html
<!-- Viewer HTML -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Signage Viewer</title>
</head>
<body>
    <!-- Content will display correctly with UTF-8 -->
</body>
</html>
```

### 6. Language-Specific Fonts

**Scenario**: Japanese/Chinese characters need specific fonts for proper display

**Solution**:
```css
/* Language-specific font stacks */
body[lang="ja"],
body[lang="zh"],
body[lang="zh-CN"],
body[lang="zh-TW"] {
    font-family: "Noto Sans CJK", "Microsoft YaHei", "SimHei", "Hiragino Sans", sans-serif;
}

body[lang="ko"] {
    font-family: "Noto Sans KR", "Malgun Gothic", "Apple Gothic", sans-serif;
}

body[lang="ar"] {
    font-family: "Noto Sans Arabic", "Tahoma", "Arial", sans-serif;
}

body[lang="th"] {
    font-family: "Noto Sans Thai", "Leelawadee", "Tahoma", sans-serif;
}

/* Default (Latin scripts) */
body {
    font-family: "Inter", "Roboto", "Helvetica Neue", "Arial", sans-serif;
}
```

---

## Performance Optimization

### 1. Query Optimization

**Problem**: Fetching translations adds database overhead

**Solution**:
```sql
-- Efficient query with JOIN (recommended)
SELECT
    c.id,
    c.content_group_id,
    c.file_path,
    c.duration,
    ct.language,
    ct.title,
    ct.description,
    ct.localized_file_path
FROM contents c
LEFT JOIN content_translations ct
    ON c.id = ct.content_id
    AND ct.language = 'id'  -- Filter translation at JOIN level
WHERE c.is_enabled = true
    AND c.id = 123;

-- Add index for performance
CREATE INDEX idx_translations_content_lang
    ON content_translations(content_id, language);

-- Execution plan should show Index Scan, not Seq Scan
EXPLAIN ANALYZE
SELECT ...;
```

**Python/SQLAlchemy Implementation**:
```python
from sqlalchemy.orm import selectinload, joinedload

def get_content_with_translation(
    db: Session,
    content_id: int,
    language: str
) -> Optional[Content]:
    """
    Optimized query with eager loading
    """
    content = (
        db.query(Content)
        .options(
            joinedload(Content.translations).load_only(
                ContentTranslation.language,
                ContentTranslation.title,
                ContentTranslation.description,
                ContentTranslation.localized_file_path
            )
        )
        .filter(Content.id == content_id)
        .first()
    )

    if not content:
        return None

    # Filter translation in Python (already loaded)
    content.current_translation = next(
        (t for t in content.translations if t.language == language),
        None
    )

    return content
```

### 2. Caching Strategy

**Multi-Level Caching**:

```python
import redis
import json
from functools import wraps

# Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_content_translation(ttl: int = 3600):
    """
    Decorator to cache content with specific language
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(content_id: int, language: str, *args, **kwargs):
            # Cache key
            cache_key = f"content:{content_id}:lang:{language}"

            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Get from database
            result = await func(content_id, language, *args, **kwargs)

            # Store in cache
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, ensure_ascii=False)
            )

            return result

        return wrapper
    return decorator

@cache_content_translation(ttl=3600)
async def get_content_with_language(content_id: int, language: str):
    """
    Get content with translation (cached)
    """
    # Database query here
    pass

# Invalidate cache on update
async def update_translation(content_id: int, language: str, data: dict):
    # Update database
    await db_update_translation(content_id, language, data)

    # Invalidate cache
    cache_key = f"content:{content_id}:lang:{language}"
    redis_client.delete(cache_key)

    # Also invalidate playlist caches that include this content
    redis_client.delete_pattern(f"playlist:*:content:{content_id}:*")
```

**Browser Caching**:
```python
from fastapi import Response

@app.get("/api/content/{content_id}")
async def get_content(
    content_id: int,
    language: str,
    response: Response
):
    content = await get_content_with_language(content_id, language)

    # Set cache headers for browser
    response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour
    response.headers["ETag"] = f'"{content["updated_at"]}"'

    return content
```

### 3. Storage Management

**Problem**: Multiple language-specific media files consume storage

**Solutions**:

**a) Shared Media with Text Overlays** (Recommended):
```javascript
// Most content uses same media file
{
  "content_id": 123,
  "file_path": "/uploads/content/breakfast-menu.mp4",  // Shared
  "translations": {
    "en": {
      "title": "Breakfast Menu",
      "overlay_text": {"headline": "Breakfast Buffet"}  // Text overlays only
    },
    "id": {
      "title": "Menu Sarapan",
      "overlay_text": {"headline": "Prasmanan Sarapan"}
    }
  }
}

// Storage: 1 video file + small text metadata = efficient
```

**b) Language-Specific Media Only When Needed**:
```javascript
// Only Japanese version has separate file (voiceover)
{
  "content_id": 123,
  "file_path": "/uploads/content/breakfast-menu.mp4",  // English/default
  "translations": {
    "en": {"title": "Breakfast Menu"},
    "id": {"title": "Menu Sarapan"},  // Uses default file
    "ja": {
      "title": "朝食メニュー",
      "localized_file_path": "/uploads/content/breakfast-menu_ja.mp4"  // Separate
    }
  }
}

// Storage: 1 default video + 1 Japanese video + metadata
```

**c) CDN & Compression**:
```python
# Upload pipeline with compression
import ffmpeg

async def process_uploaded_video(file_path: str):
    """
    Compress and optimize video for streaming
    """
    output_path = file_path.replace('.mp4', '_optimized.mp4')

    # Compress with ffmpeg
    ffmpeg.input(file_path).output(
        output_path,
        vcodec='libx264',
        crf=23,  # Quality (lower = better, 23 is good balance)
        preset='medium',
        acodec='aac',
        audio_bitrate='128k'
    ).run()

    # Upload to CDN
    cdn_url = await upload_to_cdn(output_path)

    return cdn_url

# Store CDN URLs in database
content.file_path = cdn_url  # https://cdn.example.com/content/breakfast-menu.mp4
```

**d) Storage Monitoring**:
```python
# Admin dashboard endpoint
@app.get("/api/admin/storage-stats")
async def get_storage_stats():
    """
    Get storage usage by language
    """
    stats = await db.execute("""
        SELECT
            language,
            COUNT(*) as file_count,
            SUM(file_size) as total_size
        FROM content_translations
        WHERE localized_file_path IS NOT NULL
        GROUP BY language
        ORDER BY total_size DESC
    """)

    return {
        "total_files": sum(row.file_count for row in stats),
        "total_size_bytes": sum(row.total_size for row in stats),
        "total_size_gb": sum(row.total_size for row in stats) / (1024**3),
        "by_language": [
            {
                "language": row.language,
                "file_count": row.file_count,
                "size_gb": row.total_size / (1024**3)
            }
            for row in stats
        ]
    }
```

### 4. Playlist Loading Optimization

**Problem**: Loading playlist with translations for 50+ content items is slow

**Solution**:
```python
# Batch loading with single query
async def get_active_playlist_with_language(
    device_id: str,
    language: str
) -> dict:
    """
    Optimized playlist loading with translations
    """
    # 1. Get playlist items (single query with JOIN)
    playlist_items = await db.execute("""
        SELECT
            c.id,
            c.content_group_id,
            c.file_path,
            c.duration,
            ct.language,
            ct.title,
            ct.description,
            COALESCE(ct.localized_file_path, c.file_path) as effective_file_path,
            ct.overlay_text,
            CASE
                WHEN ct.language = %s THEN false
                ELSE true
            END as fallback_used
        FROM playlist_items pi
        JOIN playlists p ON pi.playlist_id = p.id
        JOIN contents c ON pi.content_id = c.id
        LEFT JOIN content_translations ct ON c.id = ct.content_id
        WHERE p.device_id = %s
            AND p.is_active = true
            AND c.is_enabled = true
            AND (ct.language = %s OR ct.is_default = true)
        ORDER BY pi.play_order
    """, [language, device_id, language])

    # 2. Build response (minimal processing)
    content_list = []
    for item in playlist_items:
        content_list.append({
            "content_id": item.id,
            "title": item.title,
            "file_path": item.effective_file_path,
            "duration": item.duration,
            "language": item.language,
            "fallback_used": item.fallback_used
        })

    return {
        "device_id": device_id,
        "language": language,
        "content": content_list
    }

# Result: Single database query instead of N+1 queries
# 50 content items: 1 query vs 51 queries (50x faster!)
```

---

## Implementation Plan

### Phase 4.2.1: Database Schema & Migration (Week 1)

**Tasks**:
1. Create `content_translations` table
2. Create `languages` table
3. Add language columns to `devices` table
4. Add system settings for language configuration
5. Create migration script for existing content
6. Test migration on staging database

**Deliverables**:
- SQL migration scripts
- Rollback scripts (in case of issues)
- Migration documentation
- Test coverage for schema changes

**Success Criteria**:
- All existing content migrated to new structure
- Zero downtime during migration
- Backward compatibility maintained
- Database queries < 100ms (with indexes)

---

### Phase 4.2.2: Backend API Implementation (Week 2)

**Tasks**:
1. Update content upload endpoint (support translations)
2. Implement language-specific content retrieval
3. Add translation CRUD endpoints
4. Update playlist API (language parameter)
5. Implement fallback logic
6. Add bulk import/export endpoints
7. Add language management endpoints
8. Write unit tests (80%+ coverage)

**Deliverables**:
- Updated FastAPI endpoints
- API documentation (Swagger)
- Unit tests
- Performance benchmarks

**Success Criteria**:
- All API endpoints working
- Test coverage > 80%
- API response time < 200ms
- Fallback logic tested with edge cases

---

### Phase 4.2.3: Web Admin UI (Week 3)

**Tasks**:
1. Update content upload form (add translations)
2. Build translation editor modal
3. Add language indicators to content list
4. Implement bulk import/export UI
5. Add device language configuration UI
6. Build translation coverage dashboard widget
7. Add preview with language switcher
8. Implement form validation
9. Write component tests

**Deliverables**:
- React components for translation management
- Updated content upload workflow
- Device language configuration screen
- Dashboard widget for translation coverage
- Component tests

**Success Criteria**:
- Intuitive UI/UX (user testing)
- All forms validated
- Preview working for all languages
- Responsive design (mobile-friendly)
- Component test coverage > 70%

---

### Phase 4.2.4: Viewer Integration (Week 4)

**Tasks**:
1. Implement LanguageManager class
2. Add language selector UI (bottom-right button)
3. Implement startup language selector (optional)
4. Add language rotation for multi-language display
5. Implement RTL support (Arabic, Hebrew)
6. Add language change animations
7. Update API calls to include language parameter
8. Test on different devices (desktop, WebOS TV, tablets)

**Deliverables**:
- LanguageManager JavaScript class
- Language selector UI components
- Updated viewer API integration
- RTL CSS styles
- Device testing results

**Success Criteria**:
- Language switching < 2 seconds
- Smooth animations
- RTL languages display correctly
- Works on WebOS TV (actual device test)
- localStorage persistence working

---

### Phase 4.2.5: Migration & Documentation (Week 4)

**Tasks**:
1. Create migration guide for existing deployments
2. Build bulk translation import tool
3. Write user documentation (hotel staff)
4. Write developer documentation
5. Create video tutorials (upload, translate, configure)
6. Performance testing (1000+ content items)
7. Security audit (language parameter injection)
8. Staging deployment & QA testing

**Deliverables**:
- Migration guide
- Bulk import tool (CLI or web-based)
- User documentation (PDF + online)
- Developer documentation
- Video tutorials
- Performance test results
- Security audit report

**Success Criteria**:
- Zero data loss during migration
- Documentation clear & complete
- Video tutorials < 5 min each
- Performance acceptable (< 3s page load)
- No security vulnerabilities

---

## Code Examples

### 1. Backend: Content Upload with Translations

**File**: `backend/app/api/content.py`

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Optional
import json
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/upload")
async def upload_content_with_translations(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    translations: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload content with multiple language translations

    Args:
        file: Media file (video, image)
        metadata: JSON string with content metadata
        translations: JSON string with language translations

    Returns:
        Created content with all translations
    """
    try:
        # Parse JSON
        metadata_dict = json.loads(metadata)
        translations_dict = json.loads(translations)

        # Validate required fields
        if not translations_dict:
            raise HTTPException(status_code=400, detail="At least one translation required")

        # Generate content_group_id if not provided
        content_group_id = metadata_dict.get('content_group_id') or f"content_{uuid.uuid4().hex[:12]}"

        # Upload file to storage
        file_path = await storage.save_file(file)
        file_size = await storage.get_file_size(file_path)

        # Detect file type and duration
        file_type = detect_file_type(file.content_type)
        duration = await extract_duration(file_path) if file_type == 'video' else metadata_dict.get('duration', 10)

        # Create content record
        content = Content(
            content_group_id=content_group_id,
            is_primary=True,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            duration=duration,
            is_enabled=metadata_dict.get('is_enabled', True),
            start_date=metadata_dict.get('start_date'),
            end_date=metadata_dict.get('end_date'),
            created_by=current_user.id
        )
        db.add(content)
        db.flush()  # Get content.id

        # Create translations
        created_translations = []
        default_language = None

        for lang, trans_data in translations_dict.items():
            # Validate language exists
            language = db.query(Language).filter(Language.code == lang).first()
            if not language:
                logger.warning(f"Language '{lang}' not found in system, skipping")
                continue

            # Create translation
            translation = ContentTranslation(
                content_id=content.id,
                language=lang,
                is_default=trans_data.get('is_default', False),
                title=trans_data['title'],
                description=trans_data.get('description', ''),
                overlay_text=trans_data.get('overlay_text'),
                translated_by=current_user.id
            )
            db.add(translation)
            created_translations.append(translation)

            if translation.is_default:
                default_language = lang

        # Ensure at least one default translation
        if not default_language and created_translations:
            created_translations[0].is_default = True

        db.commit()

        # Return response
        return {
            "success": True,
            "data": {
                "content_id": content.id,
                "content_group_id": content.content_group_id,
                "file_path": file_path,
                "file_type": file_type,
                "duration": duration,
                "translations": [
                    {
                        "translation_id": t.id,
                        "language": t.language,
                        "title": t.title,
                        "is_default": t.is_default
                    }
                    for t in created_translations
                ]
            }
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
```

### 2. Backend: Get Content with Language

**File**: `backend/app/api/content.py`

```python
@router.get("/{content_id}")
async def get_content(
    content_id: int,
    language: str = Query('en', description="Language code (e.g., 'en', 'id', 'zh-CN')"),
    fallback: bool = Query(True, description="Enable fallback to other languages"),
    db: Session = Depends(get_db)
):
    """
    Get content with specific language translation

    Args:
        content_id: Content ID
        language: Requested language code
        fallback: Enable fallback chain if translation not available

    Returns:
        Content with translation in requested language
    """
    # Get content
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Get all translations for this content
    translations = db.query(ContentTranslation).filter(
        ContentTranslation.content_id == content_id
    ).all()

    if not translations:
        raise HTTPException(status_code=404, detail="No translations available for this content")

    # Build translations dict
    translations_dict = {
        t.language: {
            "translation_id": t.id,
            "title": t.title,
            "description": t.description,
            "localized_file_path": t.localized_file_path,
            "overlay_text": t.overlay_text,
            "is_default": t.is_default
        }
        for t in translations
    }

    # Resolve translation with fallback
    resolved = resolve_translation_with_fallback(
        translations_dict,
        language,
        fallback_enabled=fallback
    )

    # Build response
    translation_data = resolved['translation']

    return {
        "success": True,
        "data": {
            "content_id": content.id,
            "content_group_id": content.content_group_id,
            "file_path": translation_data.get('localized_file_path') or content.file_path,
            "file_type": content.file_type,
            "duration": content.duration,
            "is_enabled": content.is_enabled,

            # Translation data
            "language": resolved['language'],
            "title": translation_data['title'],
            "description": translation_data['description'],
            "overlay_text": translation_data.get('overlay_text'),

            # Fallback metadata
            "translation_fallback_used": resolved['fallback_used'],
            "requested_language": language,
            "fallback_reason": resolved.get('fallback_reason'),

            # Available languages
            "available_languages": list(translations_dict.keys())
        }
    }


def resolve_translation_with_fallback(
    translations: Dict[str, dict],
    language: str,
    fallback_enabled: bool = True
) -> Dict[str, any]:
    """
    Resolve translation with fallback chain
    """
    # 1. Exact match
    if language in translations:
        return {
            'language': language,
            'translation': translations[language],
            'fallback_used': False
        }

    if not fallback_enabled:
        return {
            'language': None,
            'translation': None,
            'fallback_used': True,
            'fallback_reason': f"Translation for '{language}' not available"
        }

    # 2. Primary language (zh-CN → zh)
    primary_lang = language.split('-')[0]
    if primary_lang != language and primary_lang in translations:
        return {
            'language': primary_lang,
            'translation': translations[primary_lang],
            'fallback_used': True,
            'fallback_reason': f"Locale '{language}' not available, using primary '{primary_lang}'"
        }

    # 3. Default translation
    default_trans = next(
        (t for t in translations.values() if t.get('is_default')),
        None
    )
    if default_trans:
        default_lang = next(
            (k for k, v in translations.items() if v == default_trans),
            None
        )
        return {
            'language': default_lang,
            'translation': default_trans,
            'fallback_used': True,
            'fallback_reason': f"Translation for '{language}' not available, using default '{default_lang}'"
        }

    # 4. English fallback
    if 'en' in translations:
        return {
            'language': 'en',
            'translation': translations['en'],
            'fallback_used': True,
            'fallback_reason': f"Translation for '{language}' not available, using English"
        }

    # 5. Any available
    if translations:
        first_lang = next(iter(translations.keys()))
        return {
            'language': first_lang,
            'translation': translations[first_lang],
            'fallback_used': True,
            'fallback_reason': f"Translation for '{language}' not available, using '{first_lang}'"
        }

    # No translations
    return {
        'language': None,
        'translation': None,
        'fallback_used': True,
        'fallback_reason': 'No translations available'
    }
```

### 3. Frontend: Translation Editor Component

**File**: `web-admin/src/components/content/modals/TranslationEditorModal.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { Modal } from '../../shared/Modal';
import { Button } from '../../shared/Button';
import { FormInput } from '../../shared/FormInput';
import api from '../../../services/api';

interface Translation {
    language: string;
    title: string;
    description: string;
    overlay_text?: Record<string, any>;
    is_default: boolean;
}

interface TranslationEditorModalProps {
    isOpen: boolean;
    onClose: () => void;
    contentId: number;
    contentTitle: string;
    onSave: () => void;
}

export const TranslationEditorModal: React.FC<TranslationEditorModalProps> = ({
    isOpen,
    onClose,
    contentId,
    contentTitle,
    onSave
}) => {
    const [translations, setTranslations] = useState<Record<string, Translation>>({});
    const [activeLanguage, setActiveLanguage] = useState<string>('en');
    const [availableLanguages, setAvailableLanguages] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);

    // Load translations when modal opens
    useEffect(() => {
        if (isOpen) {
            loadTranslations();
            loadAvailableLanguages();
        }
    }, [isOpen, contentId]);

    const loadTranslations = async () => {
        setLoading(true);
        try {
            const response = await api.get(`/api/content/${contentId}/translations`);
            const translationsData = response.data.data.translations;

            const translationsMap: Record<string, Translation> = {};
            translationsData.forEach((t: any) => {
                translationsMap[t.language] = {
                    language: t.language,
                    title: t.title,
                    description: t.description,
                    overlay_text: t.overlay_text,
                    is_default: t.is_default
                };
            });

            setTranslations(translationsMap);

            // Set active language to first available
            if (translationsData.length > 0) {
                setActiveLanguage(translationsData[0].language);
            }
        } catch (error) {
            console.error('Failed to load translations:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadAvailableLanguages = async () => {
        try {
            const response = await api.get('/api/languages');
            setAvailableLanguages(response.data.data);
        } catch (error) {
            console.error('Failed to load languages:', error);
        }
    };

    const handleSaveTranslation = async () => {
        setSaving(true);
        try {
            const translation = translations[activeLanguage];

            await api.patch(
                `/api/content/${contentId}/translations/${activeLanguage}`,
                translation
            );

            onSave();
        } catch (error) {
            console.error('Failed to save translation:', error);
            alert('Failed to save translation. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    const handleAddLanguage = (languageCode: string) => {
        if (!translations[languageCode]) {
            setTranslations({
                ...translations,
                [languageCode]: {
                    language: languageCode,
                    title: '',
                    description: '',
                    is_default: false
                }
            });
            setActiveLanguage(languageCode);
        }
    };

    const currentTranslation = translations[activeLanguage];

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={`Edit Translations - ${contentTitle}`}>
            <div className="translation-editor">
                {loading ? (
                    <div className="loading">Loading translations...</div>
                ) : (
                    <>
                        {/* Language Tabs */}
                        <div className="language-tabs">
                            {Object.keys(translations).map(lang => {
                                const langData = availableLanguages.find(l => l.code === lang);
                                return (
                                    <button
                                        key={lang}
                                        className={`language-tab ${activeLanguage === lang ? 'active' : ''}`}
                                        onClick={() => setActiveLanguage(lang)}
                                    >
                                        {langData?.flag_emoji || '🌐'} {langData?.name || lang}
                                        {translations[lang].is_default && ' ★'}
                                    </button>
                                );
                            })}

                            {/* Add Language Dropdown */}
                            <select
                                className="add-language-select"
                                onChange={(e) => handleAddLanguage(e.target.value)}
                                value=""
                            >
                                <option value="">+ Add Language</option>
                                {availableLanguages
                                    .filter(lang => !translations[lang.code])
                                    .map(lang => (
                                        <option key={lang.code} value={lang.code}>
                                            {lang.flag_emoji} {lang.name}
                                        </option>
                                    ))
                                }
                            </select>
                        </div>

                        {/* Translation Form */}
                        {currentTranslation && (
                            <div className="translation-form">
                                <div className="form-group">
                                    <label>Title *</label>
                                    <input
                                        type="text"
                                        value={currentTranslation.title}
                                        onChange={(e) => setTranslations({
                                            ...translations,
                                            [activeLanguage]: {
                                                ...currentTranslation,
                                                title: e.target.value
                                            }
                                        })}
                                        className="form-input"
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Description</label>
                                    <textarea
                                        value={currentTranslation.description}
                                        onChange={(e) => setTranslations({
                                            ...translations,
                                            [activeLanguage]: {
                                                ...currentTranslation,
                                                description: e.target.value
                                            }
                                        })}
                                        className="form-textarea"
                                        rows={4}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Overlay Text (JSON)</label>
                                    <textarea
                                        value={JSON.stringify(currentTranslation.overlay_text || {}, null, 2)}
                                        onChange={(e) => {
                                            try {
                                                const parsed = JSON.parse(e.target.value);
                                                setTranslations({
                                                    ...translations,
                                                    [activeLanguage]: {
                                                        ...currentTranslation,
                                                        overlay_text: parsed
                                                    }
                                                });
                                            } catch (err) {
                                                // Invalid JSON, ignore
                                            }
                                        }}
                                        className="form-textarea font-mono"
                                        rows={6}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="checkbox-label">
                                        <input
                                            type="checkbox"
                                            checked={currentTranslation.is_default}
                                            onChange={(e) => {
                                                // Unset all other defaults
                                                const updatedTranslations = { ...translations };
                                                Object.keys(updatedTranslations).forEach(lang => {
                                                    updatedTranslations[lang].is_default = false;
                                                });

                                                // Set current as default
                                                updatedTranslations[activeLanguage].is_default = e.target.checked;

                                                setTranslations(updatedTranslations);
                                            }}
                                        />
                                        Set as default language
                                    </label>
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        <div className="modal-actions">
                            <Button variant="secondary" onClick={onClose}>
                                Cancel
                            </Button>
                            <Button
                                variant="primary"
                                onClick={handleSaveTranslation}
                                disabled={saving || !currentTranslation?.title}
                            >
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </div>
                    </>
                )}
            </div>
        </Modal>
    );
};
```

### 4. Viewer: Language Manager Integration

**File**: `viewer/js/player/main.js`

```javascript
/**
 * Main player initialization with language support
 */
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing Digital Signage Viewer with multi-language support...');

    // Check device activation
    const deviceId = localStorage.getItem('device_id');
    if (!deviceId) {
        console.log('Device not activated, showing registration screen');
        window.location.href = '/activate.html';
        return;
    }

    // Load device configuration
    const deviceConfig = await loadDeviceConfiguration(deviceId);

    // Initialize language manager
    window.languageManager = new LanguageManager({
        defaultLanguage: deviceConfig.default_language || 'en',
        availableLanguages: deviceConfig.available_languages || ['en'],
        allowManualSwitch: deviceConfig.allow_manual_switch !== false,
        languageRotation: deviceConfig.language_rotation
    });

    // Initialize content player
    window.contentPlayer = new ContentPlayer();

    // Load initial playlist
    await loadPlaylist();

    // Start playback
    window.contentPlayer.play();

    // Setup heartbeat
    startHeartbeat(deviceId);

    console.log('Viewer initialized successfully');
});

/**
 * Load device configuration from server
 */
async function loadDeviceConfiguration(deviceId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        return data.data;
    } catch (error) {
        console.error('Failed to load device configuration:', error);

        // Return default config
        return {
            default_language: 'en',
            available_languages: ['en'],
            allow_manual_switch: true,
            language_rotation: null
        };
    }
}

/**
 * Load playlist with current language
 */
async function loadPlaylist() {
    try {
        const deviceId = localStorage.getItem('device_id');
        const currentLanguage = window.languageManager.getCurrentLanguage();

        const response = await fetch(
            `${API_BASE_URL}/api/playlists/devices/${deviceId}/active?language=${currentLanguage}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Load playlist into player
        window.contentPlayer.loadPlaylist(data.data);

        console.log('Playlist loaded:', {
            language: currentLanguage,
            contentCount: data.data.content?.length || 0
        });
    } catch (error) {
        console.error('Failed to load playlist:', error);
    }
}
```

---

## Summary

This multi-language content system design provides:

1. **Comprehensive Database Schema**: Dedicated translations table with language metadata
2. **Flexible API**: Support for multiple languages with smart fallback logic
3. **Intuitive Web Admin**: Easy translation management with bulk operations
4. **Seamless Viewer Integration**: Language selector, rotation, RTL support
5. **Performance Optimized**: Query optimization, caching, CDN-ready
6. **Edge Case Handling**: Fallback chain, character encoding, mixed playlists
7. **Clear Implementation Plan**: 4-week phased approach with deliverables

**Key Innovations**:
- Hybrid model (shared media + text translations) for storage efficiency
- Smart fallback chain (requested → primary → default → English → any)
- Language rotation for airports (auto-cycle through languages)
- RTL support for Arabic/Hebrew markets
- Bulk import/export for translation agencies
- Real-time language switching without page reload

**Business Impact**:
- Unlocks international hotel chains (Hilton, Marriott, Hyatt)
- Enables airport signage (multi-language passengers)
- Supports retail stores in multilingual regions
- Improves guest experience (see content in native language)
- Reduces content duplication (one asset, many translations)

**Next Steps**:
1. Review and approve design document
2. Start Phase 4.2.1 (database schema)
3. Set up staging environment for testing
4. Assign developers to each phase
5. Begin user testing with international hotels

Ready to implement Phase 4.2! 🚀🌍