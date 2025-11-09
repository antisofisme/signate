# 🚀 PHASE 5: ADVANCED FEATURES (OPTIONAL) - IMPLEMENTATION GUIDE

**Timeline:** Week 8-9 (after Phase 4)
**Duration:** 10-14 days
**Risk Level:** Low (Optional Features)
**Downtime:** None

---

## 📋 OVERVIEW

Phase 5 adds advanced optional features:
- ✅ Template system for dynamic content
- ✅ Multi-language support
- ✅ Advanced scheduling
- ✅ Widget system
- ✅ Firebird hotel integration

**What changes:**
- Database: 5 new tables (templates, translations, schedules, widgets, firebird_config)
- Backend: Template engine, translation service, scheduler
- CMS: Template editor, language manager, schedule builder
- Player: Dynamic content rendering

**Note:** This phase is OPTIONAL. Skip to Phase 6 if these features are not needed.

---

## 🎯 WEEK-BY-WEEK PLAN

### **Week 8: Backend + Database (Days 1-7)**
### **Week 9: Frontend + Player (Days 8-14)**

---

## 📅 WEEK 8: BACKEND + DATABASE

### Day 1-2: Database Migrations

**Migration 020: Templates**
```sql
-- database/fix-database/migrations/020_add_templates.sql

BEGIN;

-- Templates for dynamic content
CREATE TABLE templates (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  template_type VARCHAR(50) NOT NULL, -- 'text', 'image', 'video', 'html'
  content TEXT NOT NULL, -- Template content with variables
  variables JSONB, -- Variable definitions
  preview_data JSONB, -- Sample data for preview
  is_active BOOLEAN DEFAULT true,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(organization_id, name)
);

CREATE INDEX idx_templates_org ON templates(organization_id);
CREATE INDEX idx_templates_type ON templates(template_type);

COMMIT;
```

**Migration 021: Translations**
```sql
-- database/fix-database/migrations/021_add_translations.sql

BEGIN;

-- Multi-language support
CREATE TABLE translations (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  entity_type VARCHAR(50) NOT NULL, -- 'content', 'playlist', 'template'
  entity_id INTEGER NOT NULL,
  language_code VARCHAR(5) NOT NULL, -- 'en', 'id', 'zh'
  field_name VARCHAR(100) NOT NULL, -- 'title', 'description'
  translated_value TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(entity_type, entity_id, language_code, field_name)
);

CREATE INDEX idx_translations_entity ON translations(entity_type, entity_id);
CREATE INDEX idx_translations_lang ON translations(language_code);

COMMIT;
```

**Migration 022: Advanced Scheduling**
```sql
-- database/fix-database/migrations/022_add_advanced_scheduling.sql

BEGIN;

-- Enhanced scheduling with recurrence
CREATE TABLE schedules (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  playlist_id INTEGER REFERENCES playlists(id) ON DELETE CASCADE,

  -- Time range
  start_date DATE NOT NULL,
  end_date DATE,
  start_time TIME,
  end_time TIME,

  -- Recurrence
  recurrence_type VARCHAR(20), -- 'daily', 'weekly', 'monthly'
  recurrence_pattern JSONB, -- Detailed pattern
  exceptions JSONB, -- Exception dates

  -- Priority
  priority INTEGER DEFAULT 0,

  -- Status
  is_active BOOLEAN DEFAULT true,

  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_schedules_org ON schedules(organization_id);
CREATE INDEX idx_schedules_playlist ON schedules(playlist_id);
CREATE INDEX idx_schedules_dates ON schedules(start_date, end_date);

COMMIT;
```

**Migration 023: Widgets**
```sql
-- database/fix-database/migrations/023_add_widgets.sql

BEGIN;

-- Widget system
CREATE TABLE widgets (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  widget_type VARCHAR(50) NOT NULL, -- 'clock', 'weather', 'news', 'custom'
  config JSONB NOT NULL, -- Widget configuration
  layout JSONB, -- Position, size
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Widget assignments to playlists
CREATE TABLE playlist_widgets (
  id SERIAL PRIMARY KEY,
  playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
  widget_id INTEGER NOT NULL REFERENCES widgets(id) ON DELETE CASCADE,
  position INTEGER DEFAULT 0,

  UNIQUE(playlist_id, widget_id)
);

CREATE INDEX idx_widgets_org ON widgets(organization_id);
CREATE INDEX idx_widgets_type ON widgets(widget_type);
CREATE INDEX idx_playlist_widgets_playlist ON playlist_widgets(playlist_id);

COMMIT;
```

**Migration 024: Firebird Integration**
```sql
-- database/fix-database/migrations/024_add_firebird_integration.sql

BEGIN;

-- Firebird hotel PMS integration
CREATE TABLE firebird_configs (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  host VARCHAR(255) NOT NULL,
  port INTEGER DEFAULT 3050,
  database_path TEXT NOT NULL,
  username VARCHAR(100),
  password VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  last_sync TIMESTAMP,
  sync_interval INTEGER DEFAULT 300, -- seconds
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(organization_id)
);

-- Cached hotel data from Firebird
CREATE TABLE firebird_hotel_data (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  room_number VARCHAR(20),
  guest_name VARCHAR(255),
  check_in DATE,
  check_out DATE,
  room_type VARCHAR(50),
  status VARCHAR(20), -- 'occupied', 'vacant', 'dirty'
  synced_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(organization_id, room_number)
);

CREATE INDEX idx_firebird_configs_org ON firebird_configs(organization_id);
CREATE INDEX idx_firebird_hotel_org ON firebird_hotel_data(organization_id);
CREATE INDEX idx_firebird_hotel_room ON firebird_hotel_data(room_number);

COMMIT;
```

**Run All Migrations:**
```bash
cd /home/gzjbbk/signate

# Run all phase 5 migrations
for migration in 020 021 022 023 024; do
  docker exec -i signage-postgres psql -U signage_user -d signage_db \
    < database/fix-database/migrations/${migration}_*.sql
done

# Verify tables
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT table_name FROM information_schema.tables
  WHERE table_name IN ('templates', 'translations', 'schedules', 'widgets', 'firebird_configs');"
```

### Day 3-4: Template Service

```python
# backend-python/services/template/template_service.py

from sqlalchemy.orm import Session
from typing import Dict, Any
import re
from jinja2 import Template
from .models import Template as TemplateModel

class TemplateService:
    def __init__(self, db: Session):
        self.db = db

    def create_template(
        self,
        organization_id: int,
        name: str,
        template_type: str,
        content: str,
        variables: Dict[str, Any] = None,
        preview_data: Dict[str, Any] = None
    ) -> TemplateModel:
        """Create template"""
        template = TemplateModel(
            organization_id=organization_id,
            name=name,
            template_type=template_type,
            content=content,
            variables=variables or {},
            preview_data=preview_data or {}
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        return template

    def render_template(
        self,
        template_id: int,
        data: Dict[str, Any]
    ) -> str:
        """Render template with data"""
        template_obj = self.db.query(TemplateModel).filter(
            TemplateModel.id == template_id
        ).first()

        if not template_obj:
            raise ValueError("Template not found")

        # Use Jinja2 for rendering
        template = Template(template_obj.content)
        rendered = template.render(**data)

        return rendered

    def extract_variables(self, content: str) -> list:
        """Extract variable names from template"""
        # Find all {{variable}} patterns
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        variables = re.findall(pattern, content)

        return list(set(variables))

    def validate_template(
        self,
        content: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate template syntax and variables"""
        try:
            template = Template(content)

            # Try to render with preview data
            template.render(**variables)

            return {
                'valid': True,
                'message': 'Template is valid'
            }
        except Exception as e:
            return {
                'valid': False,
                'message': str(e)
            }
```

### Day 5: Translation Service

```python
# backend-python/services/translation/translation_service.py

from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from .models import Translation

class TranslationService:
    def __init__(self, db: Session):
        self.db = db

    def add_translation(
        self,
        organization_id: int,
        entity_type: str,
        entity_id: int,
        language_code: str,
        field_name: str,
        translated_value: str
    ) -> Translation:
        """Add or update translation"""
        # Check if exists
        translation = self.db.query(Translation).filter(
            Translation.entity_type == entity_type,
            Translation.entity_id == entity_id,
            Translation.language_code == language_code,
            Translation.field_name == field_name
        ).first()

        if translation:
            # Update existing
            translation.translated_value = translated_value
        else:
            # Create new
            translation = Translation(
                organization_id=organization_id,
                entity_type=entity_type,
                entity_id=entity_id,
                language_code=language_code,
                field_name=field_name,
                translated_value=translated_value
            )
            self.db.add(translation)

        self.db.commit()
        self.db.refresh(translation)

        return translation

    def get_translations(
        self,
        entity_type: str,
        entity_id: int,
        language_code: str
    ) -> Dict[str, str]:
        """Get all translations for entity"""
        translations = self.db.query(Translation).filter(
            Translation.entity_type == entity_type,
            Translation.entity_id == entity_id,
            Translation.language_code == language_code
        ).all()

        return {
            t.field_name: t.translated_value
            for t in translations
        }

    def bulk_import(
        self,
        organization_id: int,
        translations: List[Dict]
    ):
        """Bulk import translations"""
        for item in translations:
            self.add_translation(
                organization_id=organization_id,
                entity_type=item['entity_type'],
                entity_id=item['entity_id'],
                language_code=item['language_code'],
                field_name=item['field_name'],
                translated_value=item['translated_value']
            )

    def get_supported_languages(
        self,
        organization_id: int
    ) -> List[str]:
        """Get list of supported languages"""
        languages = self.db.query(Translation.language_code).filter(
            Translation.organization_id == organization_id
        ).distinct().all()

        return [lang[0] for lang in languages]
```

### Day 6-7: Firebird Integration Service

```python
# backend-python/services/firebird/firebird_service.py

import fdb
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from .models import FirebirdConfig, FirebirdHotelData

class FirebirdService:
    def __init__(self, db: Session):
        self.db = db
        self.connection = None

    def connect(self, config: FirebirdConfig):
        """Connect to Firebird database"""
        try:
            self.connection = fdb.connect(
                host=config.host,
                port=config.port,
                database=config.database_path,
                user=config.username,
                password=config.password
            )
            return True
        except Exception as e:
            print(f"[Firebird] Connection failed: {e}")
            return False

    def sync_hotel_data(self, organization_id: int):
        """Sync hotel data from Firebird"""
        config = self.db.query(FirebirdConfig).filter(
            FirebirdConfig.organization_id == organization_id,
            FirebirdConfig.is_active == True
        ).first()

        if not config:
            raise ValueError("Firebird config not found")

        if not self.connect(config):
            raise Exception("Failed to connect to Firebird")

        try:
            # Query hotel data
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    room_number,
                    guest_name,
                    check_in,
                    check_out,
                    room_type,
                    status
                FROM rooms
                WHERE status != 'inactive'
            """)

            rows = cursor.fetchall()

            # Update local cache
            for row in rows:
                self.update_cached_data(organization_id, {
                    'room_number': row[0],
                    'guest_name': row[1],
                    'check_in': row[2],
                    'check_out': row[3],
                    'room_type': row[4],
                    'status': row[5]
                })

            # Update last sync
            config.last_sync = datetime.utcnow()
            self.db.commit()

        finally:
            if self.connection:
                self.connection.close()

    def update_cached_data(
        self,
        organization_id: int,
        data: Dict[str, Any]
    ):
        """Update cached hotel data"""
        cached = self.db.query(FirebirdHotelData).filter(
            FirebirdHotelData.organization_id == organization_id,
            FirebirdHotelData.room_number == data['room_number']
        ).first()

        if cached:
            # Update existing
            for key, value in data.items():
                setattr(cached, key, value)
            cached.synced_at = datetime.utcnow()
        else:
            # Create new
            cached = FirebirdHotelData(
                organization_id=organization_id,
                **data
            )
            self.db.add(cached)

        self.db.commit()

    def get_room_data(
        self,
        organization_id: int,
        room_number: str
    ) -> FirebirdHotelData:
        """Get cached room data"""
        return self.db.query(FirebirdHotelData).filter(
            FirebirdHotelData.organization_id == organization_id,
            FirebirdHotelData.room_number == room_number
        ).first()

    def get_all_rooms(self, organization_id: int) -> List[FirebirdHotelData]:
        """Get all cached room data"""
        return self.db.query(FirebirdHotelData).filter(
            FirebirdHotelData.organization_id == organization_id
        ).all()
```

---

## 📅 WEEK 9: FRONTEND + PLAYER

### Day 8-10: CMS Features

**Template Editor:**
```typescript
// cms-vite/src/features/templates/components/TemplateEditor.tsx

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { templateApi } from '../api'
import CodeEditor from '@uiw/react-textarea-code-editor'
import { Button } from '@/components/ui/button'

export function TemplateEditor() {
  const [content, setContent] = useState('')
  const [previewData, setPreviewData] = useState({})
  const [preview, setPreview] = useState('')

  const validateTemplate = useMutation({
    mutationFn: templateApi.validate,
    onSuccess: (data) => {
      if (data.valid) {
        setPreview(data.rendered)
      }
    }
  })

  const handlePreview = () => {
    validateTemplate.mutate({
      content,
      variables: previewData
    })
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Editor */}
      <div>
        <h3 className="font-bold mb-2">Template Content</h3>
        <CodeEditor
          value={content}
          language="html"
          onChange={(e) => setContent(e.target.value)}
          padding={15}
          style={{
            fontSize: 14,
            backgroundColor: '#f5f5f5',
            fontFamily: 'ui-monospace,SFMono-Regular,SF Mono,Consolas,monospace'
          }}
        />

        <h3 className="font-bold mt-4 mb-2">Preview Data (JSON)</h3>
        <CodeEditor
          value={JSON.stringify(previewData, null, 2)}
          language="json"
          onChange={(e) => {
            try {
              setPreviewData(JSON.parse(e.target.value))
            } catch {}
          }}
          padding={15}
        />

        <Button onClick={handlePreview} className="mt-4">
          Preview
        </Button>
      </div>

      {/* Preview */}
      <div>
        <h3 className="font-bold mb-2">Preview</h3>
        <div
          className="border p-4 bg-white"
          dangerouslySetInnerHTML={{ __html: preview }}
        />
      </div>
    </div>
  )
}
```

**Language Manager:**
```typescript
// cms-vite/src/features/translations/components/TranslationManager.tsx

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { translationApi } from '../api'
import { Table } from '@/components/ui/table'

interface Props {
  entityType: string
  entityId: number
}

export function TranslationManager({ entityType, entityId }: Props) {
  const [selectedLanguage, setSelectedLanguage] = useState('id')

  const { data: translations } = useQuery({
    queryKey: ['translations', entityType, entityId, selectedLanguage],
    queryFn: () => translationApi.getTranslations(entityType, entityId, selectedLanguage)
  })

  const updateTranslation = useMutation({
    mutationFn: translationApi.update
  })

  return (
    <div className="space-y-4">
      {/* Language Selector */}
      <select
        value={selectedLanguage}
        onChange={(e) => setSelectedLanguage(e.target.value)}
        className="border rounded px-3 py-2"
      >
        <option value="en">English</option>
        <option value="id">Bahasa Indonesia</option>
        <option value="zh">中文</option>
      </select>

      {/* Translation Fields */}
      <Table>
        <thead>
          <tr>
            <th>Field</th>
            <th>Original</th>
            <th>Translation</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(translations || {}).map(([field, value]) => (
            <tr key={field}>
              <td>{field}</td>
              <td>{/* Original value */}</td>
              <td>
                <input
                  type="text"
                  value={value as string}
                  onChange={(e) => {
                    updateTranslation.mutate({
                      entity_type: entityType,
                      entity_id: entityId,
                      language_code: selectedLanguage,
                      field_name: field,
                      translated_value: e.target.value
                    })
                  }}
                  className="border rounded px-2 py-1 w-full"
                />
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  )
}
```

### Day 11-13: Player Features

**Dynamic Template Renderer:**
```typescript
// player-vite/src/components/TemplateRenderer.tsx

import { useEffect, useState } from 'react'
import { templateApi } from '../services/api'

interface Props {
  templateId: number
  data: Record<string, any>
}

export function TemplateRenderer({ templateId, data }: Props) {
  const [rendered, setRendered] = useState('')

  useEffect(() => {
    const render = async () => {
      const result = await templateApi.render(templateId, data)
      setRendered(result)
    }

    render()
  }, [templateId, data])

  return (
    <div
      dangerouslySetInnerHTML={{ __html: rendered }}
    />
  )
}
```

**Widget System:**
```typescript
// player-vite/src/components/widgets/WidgetRenderer.tsx

import { ClockWidget } from './ClockWidget'
import { WeatherWidget } from './WeatherWidget'
import { HotelWidget } from './HotelWidget'

interface Props {
  widget: {
    widget_type: string
    config: Record<string, any>
    layout: {
      x: number
      y: number
      width: number
      height: number
    }
  }
}

export function WidgetRenderer({ widget }: Props) {
  const renderWidget = () => {
    switch (widget.widget_type) {
      case 'clock':
        return <ClockWidget config={widget.config} />
      case 'weather':
        return <WeatherWidget config={widget.config} />
      case 'hotel':
        return <HotelWidget config={widget.config} />
      default:
        return null
    }
  }

  return (
    <div
      className="absolute"
      style={{
        left: `${widget.layout.x}%`,
        top: `${widget.layout.y}%`,
        width: `${widget.layout.width}%`,
        height: `${widget.layout.height}%`
      }}
    >
      {renderWidget()}
    </div>
  )
}
```

### Day 14: Testing & Deployment

```bash
# Test template rendering
curl -X POST http://localhost:8001/api/v1/templates/1/render \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "guest_name": "John Doe",
    "room_number": "101",
    "check_out": "2025-12-01"
  }'

# Test Firebird sync
curl -X POST http://localhost:8001/api/v1/firebird/sync \
  -H "Authorization: Bearer $TOKEN"

# Deploy
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/signate

  # Run migrations
  for migration in 020 021 022 023 024; do
    docker exec -i signage-postgres psql -U signage_user -d signage_db \
      < database/fix-database/migrations/${migration}_*.sql
  done

  # Deploy backend
  docker-compose -f docker/docker-compose.yml up -d --build backend-api
EOF
```

---

## ✅ SUCCESS CRITERIA

- ✅ Template system working with variable substitution
- ✅ Multi-language content displaying correctly
- ✅ Advanced scheduling with recurrence
- ✅ Widgets overlaying on content
- ✅ Firebird data syncing every 5 minutes

---

## 🎯 DELIVERABLES

- ✅ Template engine with Jinja2
- ✅ Translation management system
- ✅ Advanced scheduler
- ✅ Widget system (clock, weather, hotel)
- ✅ Firebird integration service

**Phase 5 Complete! Ready for Phase 6.** 🚀
