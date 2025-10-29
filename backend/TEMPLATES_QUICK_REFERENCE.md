# Template Variables API - Quick Reference
**File**: `/backend/app/api/templates.py`
**Status**: ✅ 100% Quick Wins Compliant

---

## Endpoints at a Glance

```
POST   /api/templates/validate              - Validate template syntax/security
POST   /api/templates/render                - Render template with context
POST   /api/templates/preview               - Preview with sample data
GET    /api/templates/variables             - List available variables
POST   /api/templates/custom-variables      - Create custom variable
GET    /api/templates/custom-variables      - List custom variables
PUT    /api/templates/custom-variables/{id} - Update custom variable (TODO)
DELETE /api/templates/custom-variables/{id} - Delete custom variable (TODO)
```

**Total**: 6 implemented + 2 TODO = 8 endpoints

---

## Quick Test Commands

```bash
# Set API base URL
API_URL="http://192.168.5.12:8001"

# 1. Validate template
curl -X POST $API_URL/api/templates/validate \
  -H "Content-Type: application/json" \
  -d '{
    "template": "Welcome {{device.name}}! Today is {{datetime.weekday}}",
    "engine": "jinja2",
    "strict_mode": true
  }'

# 2. Preview template (no auth required)
curl -X POST $API_URL/api/templates/preview \
  -H "Content-Type: application/json" \
  -d '{
    "template": "Temperature: {{weather.temp}}°C, {{weather.condition}}",
    "use_sample_data": true
  }'

# 3. List available variables
curl $API_URL/api/templates/variables

# 4. Render template (requires auth)
curl -X POST $API_URL/api/templates/render \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "Welcome to {{hotel_name}}!",
    "context": {"hotel_name": "Grand Hotel"},
    "device_id": 1
  }'

# 5. Create custom variable (requires editor/admin role)
curl -X POST $API_URL/api/templates/custom-variables \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "special_offer",
    "value": "20% off spa treatments",
    "description": "Current promotion",
    "is_global": true
  }'

# 6. List custom variables
curl $API_URL/api/templates/custom-variables
```

---

## Available Variables

### System Variables (Always Available)
```
device.id              - Unique device identifier
device.name            - Display name
device.location        - Physical location
device.tag             - Device tag
device.status          - Online/offline status
device.ip_address      - IP address

datetime.now           - Current datetime (ISO format)
datetime.today         - Today's date
datetime.time          - Current time
datetime.year          - Current year
datetime.month         - Current month
datetime.day           - Current day
datetime.weekday       - Day of week (Monday, Tuesday, etc.)
datetime.hour          - Current hour (0-23)
datetime.minute        - Current minute (0-59)
```

### External Variables (Depends on Integration)
```
weather.temp           - Temperature in Celsius
weather.feels_like     - Feels like temperature
weather.condition      - Weather condition (Sunny, Cloudy, etc.)
weather.humidity       - Humidity percentage
weather.wind_speed     - Wind speed in km/h
weather.icon           - Weather icon code

firebird.event_name    - Event name from PMS
firebird.room          - Event room/location
firebird.start_time    - Event start time
firebird.end_time      - Event end time
firebird.attendees     - Number of attendees
firebird.organizer     - Event organizer
```

### Custom Variables (User-Defined)
```
<custom_name>          - Any user-created variable
```

---

## Template Examples

### 1. Simple Device Info
```jinja2
Device: {{device.name}}
Location: {{device.location}}
Status: {{device.status}}
```

### 2. Date/Time Display
```jinja2
Today is {{datetime.weekday}}, {{datetime.month}}/{{datetime.day}}/{{datetime.year}}
Current time: {{datetime.hour}}:{{datetime.minute}}
```

### 3. Weather Display
```jinja2
Current Weather
Temperature: {{weather.temp}}°C (feels like {{weather.feels_like}}°C)
Condition: {{weather.condition}}
Humidity: {{weather.humidity}}%
Wind: {{weather.wind_speed}} km/h
```

### 4. Firebird Event Schedule
```jinja2
Today's Events
{{firebird.event_name}}
Room: {{firebird.room}}
Time: {{firebird.start_time}} - {{firebird.end_time}}
Attendees: {{firebird.attendees}}
Organizer: {{firebird.organizer}}
```

### 5. Hotel Welcome Message
```jinja2
Welcome to {{hotel_name}}!

Special Offer: {{special_offer}}

Tonight's Event: {{event_title}}
Restaurant Special: {{restaurant_special}}

Today is {{datetime.weekday}}, {{datetime.month}}/{{datetime.day}}
Temperature: {{weather.temp}}°C
```

### 6. Conditional Display
```jinja2
{% if weather.temp > 25 %}
  It's hot today! Stay cool with our spa services.
{% elif weather.temp < 15 %}
  Cold weather? Warm up in our lounge!
{% else %}
  Perfect weather for exploring!
{% endif %}
```

---

## Response Format

All endpoints return standardized response:

```json
{
  "success": true,
  "data": {
    // Endpoint-specific data
  },
  "meta": {
    "timestamp": "2025-10-28T...",
    "request_id": "abc123...",
    "version": "1.0.0"
  }
}
```

---

## Security Features

### 1. Sandboxed Execution
- No filesystem access
- No network access
- No system calls
- No dangerous imports

### 2. Role-Based Access
- **Admin**: All variables
- **Editor**: Standard + custom variables
- **Viewer**: Safe variables only

### 3. Input Validation
- Template size: Max 50KB (render), 10KB (preview)
- Variable names: Alphanumeric + underscore
- Reserved names blocked: device, datetime, system, weather, firebird

### 4. Rate Limiting
- Validate: 10 requests/minute
- Render: 5 requests/minute per user
- Preview: 20 requests/minute

### 5. Timeout Protection
- Default: 5 seconds
- Maximum: 30 seconds
- Prevents infinite loops

---

## Error Handling

### Validation Errors
```json
{
  "success": true,
  "data": {
    "is_valid": false,
    "errors": ["Undefined variable: unknown_var"],
    "warnings": [],
    "required_variables": [],
    "detected_functions": []
  }
}
```

### Render Errors
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Template rendering failed",
    "details": {
      "error": "Variable 'device_name' is undefined"
    }
  }
}
```

---

## Common Use Cases

### 1. Dynamic Content Personalization
Use device-specific variables to show different content per display:
```jinja2
Welcome to {{device.location}}!
Display ID: {{device.name}}
```

### 2. Real-Time Information
Show live weather and time:
```jinja2
{{datetime.hour}}:{{datetime.minute}}
{{weather.temp}}°C {{weather.condition}}
```

### 3. Event Management
Display PMS events:
```jinja2
{{firebird.event_name}}
{{firebird.room}} | {{firebird.start_time}}
```

### 4. Promotional Content
Use custom variables for easy updates:
```jinja2
Special Offer: {{special_offer}}
Valid until {{offer_end_date}}
```

---

## Schema Reference

### Request Schemas
```python
TemplateValidationRequest
  - template: str (1-51200 chars)
  - engine: "jinja2" | "simple"
  - strict_mode: bool

TemplateRenderRequest
  - template: str (1-51200 chars)
  - context: dict
  - device_id: int (optional)
  - content_id: int (optional)
  - engine: "jinja2" | "simple"
  - safe_mode: bool (default: true)
  - use_cache: bool (default: true)
  - timeout: int (1-30, default: 5)

TemplatePreviewRequest
  - template: str (1-10000 chars)
  - use_sample_data: bool (default: true)
  - custom_context: dict (optional)
  - engine: "jinja2" | "simple"

CustomVariableCreate
  - name: str (alphanumeric + underscore)
  - value: any JSON-serializable
  - description: str (optional)
  - is_global: bool (default: false)
  - expires_at: datetime (optional)
```

### Response Schemas
```python
TemplateValidationResponse
  - is_valid: bool
  - errors: list[str]
  - warnings: list[str]
  - required_variables: list[str]
  - detected_functions: list[str]

TemplateRenderResponse
  - success: bool
  - rendered: str
  - error: str (optional)
  - execution_time_ms: float
  - truncated: bool

TemplatePreviewResponse
  - preview: str
  - sample_context: dict
  - warnings: list[str]

CustomVariableResponse
  - id: int
  - name: str
  - value: any
  - description: str
  - is_global: bool
  - expires_at: datetime
  - created_at: datetime
  - updated_at: datetime
  - created_by: str
```

---

## Quick Wins Compliance Checklist

- ✅ Structured logging with `StructuredLogger`
- ✅ Custom exceptions (no `HTTPException`)
- ✅ Response wrapping with `success_response()`
- ✅ Request ID tracking
- ✅ Comprehensive Pydantic schemas
- ✅ Generic type response models
- ✅ Error handling best practices
- ✅ Security-first design
- ✅ Performance optimization
- ✅ Audit logging

**Compliance**: 100% (6/6 implemented endpoints)

---

## Related Files

```
/backend/app/api/templates.py              - API endpoints (692 lines)
/backend/app/schemas/template.py           - Pydantic schemas (401 lines)
/backend/app/services/template_service.py  - Template renderer service
/backend/app/core/logging.py               - StructuredLogger
/backend/app/core/exceptions.py            - Custom exceptions
/backend/app/schemas/common.py             - Response helpers
```

---

## Migration Status

**Status**: ✅ ALREADY MIGRATED TO QUICK WINS PATTERN
**Date**: 2025-10-28
**Endpoints**: 6/6 (100%)
**Breaking Changes**: None
**Frontend Updates Required**: None

---

**For detailed analysis, see**: `TEMPLATES_API_MIGRATION_REPORT.md`
