# Player Advanced Features Documentation

## Overview
This document provides comprehensive documentation for all advanced features implemented in the player-vite application.

## Table of Contents
1. [Widget Rendering](#widget-rendering)
2. [Template Processing](#template-processing)
3. [Multi-language Support (i18n)](#multi-language-support-i18n)
4. [Advanced Scheduling](#advanced-scheduling)

---

## Widget Rendering

### Overview
The widget rendering system allows dynamic overlay of interactive components on top of media content.

### Supported Widget Types

#### 1. Clock Widget
Displays current time with customizable formats and styles.

**Configuration:**
```javascript
{
  type: 'clock',
  position: { x: 100, y: 100, width: 300, height: 100 },
  config: {
    style: 'digital' | 'analog',
    format: '12h' | '24h',
    show_seconds: boolean,
    timezone: 'Asia/Jakarta',
    font_size: 32,
    color: '#ffffff'
  }
}
```

#### 2. Text Widget
Displays static or dynamic text with template variable support.

**Configuration:**
```javascript
{
  type: 'text',
  position: { x: 100, y: 200, width: 400, height: 100 },
  config: {
    text: 'Welcome {{guest.name}}!',
    font_size: 24,
    color: '#ffffff',
    background_color: 'rgba(0,0,0,0.5)',
    text_align: 'left' | 'center' | 'right',
    padding: '10px'
  }
}
```

#### 3. Weather Widget
Shows current weather and forecast information.

**Configuration:**
```javascript
{
  type: 'weather',
  position: { x: 100, y: 300, width: 300, height: 200 },
  config: {
    location: 'Jakarta',
    units: 'metric' | 'imperial',
    show_forecast: boolean,
    days: 3,
    update_interval: 3600 // seconds
  }
}
```

#### 4. Calendar Widget
Displays a monthly calendar view.

**Configuration:**
```javascript
{
  type: 'calendar',
  position: { x: 100, y: 400, width: 350, height: 300 },
  config: {
    show_weekends: boolean,
    first_day_of_week: 0, // 0=Sunday, 1=Monday
    highlight_today: boolean,
    theme: 'light' | 'dark'
  }
}
```

#### 5. HTML Widget
Renders custom HTML content with full styling support.

**Configuration:**
```javascript
{
  type: 'html',
  position: { x: 100, y: 500, width: 500, height: 200 },
  config: {
    html: '<div class="custom">{{content}}</div>',
    css: '.custom { color: red; }'
  }
}
```

### Widget Renderer API

```typescript
// Render a widget
await widgetRenderer.renderWidget(widget, {
  container: HTMLElement,
  variables: Record<string, any>,
  locale: string,
  theme: 'light' | 'dark'
});

// Update widget content
await widgetRenderer.updateWidget(widgetId, context);

// Destroy widget
widgetRenderer.destroyWidget(widgetId);
```

### Integration with Content

Widgets are embedded in content items with type "widget":

```json
{
  "id": 1,
  "type": "widget",
  "title": "Welcome Screen",
  "widget_data": [
    {
      "id": "clock-1",
      "type": "clock",
      "position": { "x": 50, "y": 50, "width": 300, "height": 100 },
      "config": { "style": "digital", "format": "24h" }
    }
  ]
}
```

---

## Template Processing

### Overview
Template processing enables dynamic content by replacing variables with real-time data.

### Variable Categories

#### 1. Guest Variables (PMS Integration)
```javascript
{
  guest: {
    name: 'John Doe',
    first_name: 'John',
    last_name: 'Doe',
    title: 'Mr.',
    room: '505',
    language: 'en',
    check_in: '2024-11-11',
    check_out: '2024-11-15',
    vip_status: false,
    preferences: {
      wake_up_time: '07:00',
      do_not_disturb: false
    }
  }
}
```

#### 2. Hotel Variables
```javascript
{
  hotel: {
    name: 'Grand Hotel',
    logo_url: '/assets/logo.png',
    address: '123 Main Street',
    phone: '+62 21 1234567',
    email: 'info@grandhotel.com',
    weather: {
      temp: 28,
      condition: 'Sunny',
      humidity: 65,
      forecast: [...]
    },
    facilities: ['Pool', 'Gym', 'Spa'],
    events: [...]
  }
}
```

#### 3. System Variables
```javascript
{
  device: {
    id: 'ABC123',
    name: 'Lobby Display 1',
    type: 'display',
    resolution: '1920x1080',
    orientation: 'landscape'
  },
  player: {
    version: '1.0.0',
    uptime: 3600,
    last_sync: '2024-11-11T10:30:00Z'
  }
}
```

#### 4. Time Variables
```javascript
{
  time: {
    full: '2024-11-11 10:30:45',
    date: '2024-11-11',
    time: '10:30:45',
    hour: '10',
    minute: '30',
    second: '45',
    day: '11',
    month: '11',
    year: '2024',
    weekday: 'Monday',
    month_name: 'November'
  }
}
```

### Template Syntax

```handlebars
<!-- Basic variable -->
Welcome {{guest.name}}!

<!-- Nested variables -->
Room: {{guest.room}} | Check-out: {{guest.check_out}}

<!-- Default values -->
Hello {{guest.name|Guest}}!

<!-- Conditionals -->
{{#if guest.vip_status}}VIP Guest{{/if}}

<!-- Loops -->
{{#each hotel.facilities}}
  <li>{{this}}</li>
{{/each}}
```

### Template Processor API

```typescript
// Initialize with device ID
await templateProcessor.initialize(deviceId);

// Process template string
const result = templateProcessor.processTemplate(template);

// Update specific variable category
await templateProcessor.updatePMSVariables(guestData);
templateProcessor.updateCustomVariables({ key: 'value' });

// Get all variables
const allVars = templateProcessor.getAllVariables();
```

---

## Multi-language Support (i18n)

### Overview
Comprehensive internationalization system supporting 6 languages with automatic language detection.

### Supported Languages

| Code | Language | Direction | Native Name |
|------|----------|-----------|-------------|
| en | English | LTR | English |
| id | Indonesian | LTR | Bahasa Indonesia |
| zh | Chinese | LTR | 中文 |
| ja | Japanese | LTR | 日本語 |
| ko | Korean | LTR | 한국어 |
| ar | Arabic | RTL | العربية |

### Features

#### 1. Language Detection
- Browser language preference
- PMS guest language preference
- Manual selection via UI
- Persistent storage

#### 2. Translation Management
```typescript
// Get translation
i18n.t('activation.title'); // "Digital Signage"
i18n.t('common.loading'); // "Loading..."

// With parameters
i18n.t('welcome.message', { name: 'John' }); // "Welcome John!"

// With default value
i18n.t('custom.key', { defaultValue: 'Default Text' });
```

#### 3. Locale-based Formatting

```typescript
// Date formatting
i18n.formatDate(new Date()); // "11/11/2024" (US) or "11.11.2024" (EU)

// Time formatting
i18n.formatTime(new Date()); // "10:30 AM" or "10:30"

// Number formatting
i18n.formatNumber(1234567.89); // "1,234,567.89" or "1.234.567,89"

// Currency formatting
i18n.formatCurrency(1234.56, 'USD'); // "$1,234.56" or "US$ 1.234,56"
```

#### 4. RTL Support
Automatic direction switching for Arabic:
```typescript
i18n.setLanguage('ar');
// document.dir = 'rtl'
// UI components automatically flip
```

### Translation Keys Structure

```
common.*          - Common UI elements
activation.*      - Device activation screen
player.*          - Player UI
schedule.*        - Scheduling features
days.*            - Days of week
months.*          - Months of year
errors.*          - Error messages
```

### i18n Service API

```typescript
// Initialize with organization
await i18n.initialize(organizationId);

// Language management
i18n.setLanguage('id');
const currentLang = i18n.getLanguage(); // 'id'
const languages = i18n.getAvailableLanguages();

// Get locale info
const locale = i18n.getLocale(); // 'id-ID'
const direction = i18n.getDirection(); // 'ltr' or 'rtl'

// Add runtime translations
i18n.addTranslation('en', 'custom.key', 'Custom Value');
i18n.addTranslations('en', { 'key1': 'value1', 'key2': 'value2' });
```

---

## Advanced Scheduling

### Overview
Intelligent playlist scheduling based on time, date, and recurrence patterns.

### Schedule Configuration

```typescript
interface Schedule {
  id: number;
  name: string;
  playlist_id: number;
  organization_id: number;
  start_date: string;         // YYYY-MM-DD
  end_date: string | null;    // YYYY-MM-DD or null for indefinite
  start_time: string;         // HH:MM:SS
  end_time: string;           // HH:MM:SS
  recurrence_type: 'once' | 'daily' | 'weekly' | 'monthly' | 'yearly';
  recurrence_pattern?: {
    interval?: number;        // For daily: every N days
    days?: number[];          // For weekly: [1-7], monthly: [1-31]
    day_of_month?: number;    // For yearly
    month?: number;           // For yearly
  };
  exceptions?: string[];      // Blackout dates (YYYY-MM-DD)
  priority: number;           // Higher priority wins
  is_active: boolean;
}
```

### Recurrence Patterns

#### 1. Once
Plays only on the specified start_date.
```javascript
{
  recurrence_type: 'once',
  start_date: '2024-12-25'
}
```

#### 2. Daily
Repeats every day or every N days.
```javascript
{
  recurrence_type: 'daily',
  recurrence_pattern: { interval: 2 } // Every 2 days
}
```

#### 3. Weekly
Specific days of the week (1=Monday, 7=Sunday).
```javascript
{
  recurrence_type: 'weekly',
  recurrence_pattern: { days: [1, 3, 5] } // Mon, Wed, Fri
}
```

#### 4. Monthly
Specific days of the month.
```javascript
{
  recurrence_type: 'monthly',
  recurrence_pattern: { days: [1, 15] } // 1st and 15th
}
```

#### 5. Yearly
Specific date each year.
```javascript
{
  recurrence_type: 'yearly',
  recurrence_pattern: { 
    month: 12,        // December
    day_of_month: 25  // 25th
  }
}
```

### Schedule Priority

When multiple schedules overlap, the one with highest priority wins:
- Default playlist: priority 0
- Regular schedules: priority 1-99
- Special events: priority 100+

### Exception Dates

Blackout specific dates:
```javascript
{
  exceptions: ['2024-12-24', '2024-12-31'] // Skip these dates
}
```

### Schedule Manager API

```typescript
// Initialize schedule manager
await playerScheduleManager.initialize();

// Manual sync
await playerScheduleManager.syncSchedules();

// Get current active schedule
const current = playerScheduleManager.getCurrentSchedule();

// Get active schedule info
const info = await playerScheduleManager.getActiveSchedule();

// Listen for schedule changes
eventBus.on('schedule:changed', (event) => {
  console.log('New schedule:', event.schedule);
  console.log('Playlist ID:', event.playlist_id);
});
```

### Integration with Player

The playlist sync service automatically respects active schedules:
1. Schedule manager checks for active schedule every minute
2. When schedule changes, emits 'schedule:changed' event
3. Playlist sync picks up the event and loads new playlist
4. Player seamlessly transitions to scheduled content

### Schedule Info Display

Press 'S' key to toggle schedule info overlay showing:
- Current active schedule name
- Time range
- Recurrence pattern
- Current time

---

## Testing

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| P | Toggle player debug info |
| N | Skip to next content |
| R | Reload playlist |
| S | Toggle schedule info |

### Test Pages

1. **Comprehensive Test Suite**: `/test-all-features.html`
   - Tests all widget types
   - Validates template processing
   - Checks i18n functionality
   - Verifies scheduling logic

2. **Widget Test**: `/test-widgets.html`
   - Individual widget testing
   - Visual preview
   - Configuration playground

3. **Template Test**: `/test-template-processing.html`
   - Variable inspection
   - Template preview
   - Live editing

### API Testing

Use browser console:
```javascript
// Test widgets
widgetRenderer.renderWidget(widget, { container });

// Test templates
templateProcessor.processTemplate('Hello {{guest.name}}!');

// Test i18n
i18n.setLanguage('id');
i18n.t('common.loading');

// Test scheduling
playerScheduleManager.getCurrentSchedule();
```

---

## Configuration

### Environment Variables

```env
# API Configuration
VITE_API_BASE_URL=http://192.168.5.12:8001

# Feature Flags
VITE_ENABLE_SCHEDULING=true
VITE_ENABLE_WIDGETS=true
VITE_ENABLE_TEMPLATES=true
VITE_ENABLE_I18N=true

# Default Language
VITE_DEFAULT_LANGUAGE=en

# Debug Mode
VITE_DEBUG=false
```

### Widget Content Type

Enable widgets in CMS by creating content with type "widget":
```json
{
  "type": "widget",
  "duration": 0, // 0 = indefinite
  "widget_data": [/* widget configurations */]
}
```

### Schedule Creation

Create schedules via CMS API:
```bash
POST /api/v1/schedules
{
  "name": "Morning Schedule",
  "playlist_id": 1,
  "start_time": "06:00:00",
  "end_time": "12:00:00",
  "recurrence_type": "daily",
  "priority": 10,
  "is_active": true
}
```

---

## Troubleshooting

### Common Issues

1. **Widgets not displaying**
   - Check if content type is "widget"
   - Verify widget position is within viewport
   - Check browser console for errors

2. **Templates not processing**
   - Ensure template processor is initialized
   - Check variable availability
   - Verify template syntax

3. **Wrong language displayed**
   - Check browser language settings
   - Verify PMS guest language data
   - Check localStorage for saved preference

4. **Schedule not activating**
   - Verify schedule is within date range
   - Check time zone settings
   - Ensure schedule is marked as active
   - Check priority conflicts

### Debug Mode

Enable debug logging:
```javascript
localStorage.setItem('DEBUG', 'true');
location.reload();
```

View logs in browser console for detailed information.

---

## Performance Considerations

1. **Widget Rendering**
   - Limit widgets per screen: 5-10 recommended
   - Use efficient update intervals
   - Destroy unused widgets

2. **Template Processing**
   - Cache processed templates when possible
   - Minimize complex conditionals
   - Batch variable updates

3. **i18n**
   - Translations are cached in memory
   - Language changes require re-render
   - Use default translations as fallback

4. **Scheduling**
   - Schedules sync every 5 minutes
   - Active schedule checked every minute
   - Priority calculation is lightweight

---

## Future Enhancements

1. **Additional Widget Types**
   - News ticker
   - Social media feed
   - Video widget
   - QR code generator

2. **Advanced Templates**
   - Custom filters
   - Helper functions
   - Partial templates

3. **More Languages**
   - Spanish
   - French
   - German
   - Portuguese

4. **Schedule Features**
   - Schedule groups
   - Conditional scheduling
   - Event triggers
   - A/B testing support