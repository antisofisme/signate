# Template Management - Quick Start Guide

## 🚀 Quick Start

### Access Templates Page
1. Navigate to **http://localhost:3000/templates**
2. Or click **Templates** in the sidebar navigation

### Create Your First Template

```typescript
// 1. Click "Create Template" button
// 2. Fill in the form:
Name: "Welcome Message"
Category: text
Description: "Welcome message for lobby display"

// 3. Write your template:
<div class="welcome">
  <h1>Welcome to {{ device.name }}</h1>
  <p>Today is {{ day_name }}, {{ current_date }}</p>
  <p>Current time: {{ current_time }}</p>
</div>

// 4. Click variables from the picker to insert
// 5. See live preview on the right
// 6. Click "Save Template"
```

## 📝 Template Syntax (Jinja2)

### Output Variables
```jinja2
{{ variable_name }}           # Output a variable
{{ device.name }}             # Access object property
{{ weather.temperature }}°C   # Combine with text
```

### Conditionals
```jinja2
{% if weather.temperature > 30 %}
  <p class="hot">It's hot outside!</p>
{% elif weather.temperature > 20 %}
  <p class="warm">Nice weather today</p>
{% else %}
  <p class="cold">It's cold outside</p>
{% endif %}
```

### Loops
```jinja2
<ul>
{% for tag in device.tags %}
  <li>{{ tag }}</li>
{% endfor %}
</ul>
```

### Filters
```jinja2
{{ device.name | upper }}           # DEVICE NAME
{{ weather.temperature | round }}   # 28
{{ current_date | format_date("%B %d, %Y") }}  # January 28, 2025
```

## 🔧 Available Variables

### System Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `current_date` | Current date | 2025-01-28 |
| `current_time` | Current time | 14:30:00 |
| `day_name` | Day of week | Monday |
| `month_name` | Month name | January |
| `year` | Current year | 2025 |

### Weather Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `weather.temperature` | Temperature in °C | 28 |
| `weather.condition` | Weather condition | Sunny |
| `weather.humidity` | Humidity % | 65 |
| `weather.wind_speed` | Wind speed km/h | 12 |
| `weather.location` | City name | Jakarta |
| `weather.icon` | Weather icon URL | http://... |

### Device Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `device.name` | Device name | Reception Display |
| `device.location` | Device location | Main Lobby |
| `device.ip_address` | Device IP | 192.168.1.100 |
| `device.tags` | Device tags array | ['lobby', 'main'] |

### Firebird Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `firebird.query_result` | SQL query results | [{...}, {...}] |
| `firebird.connection_status` | Connection status | connected |

## 📚 Template Examples

### Example 1: Simple Welcome Screen
```html
<div style="text-align: center; padding: 50px;">
  <h1 style="font-size: 48px;">Welcome!</h1>
  <p style="font-size: 24px;">{{ day_name }}, {{ current_date }}</p>
  <p style="font-size: 36px;">{{ current_time }}</p>
</div>
```

### Example 2: Weather Display
```html
<div class="weather-widget">
  <h2>🌤️ Weather</h2>
  <div class="temp" style="font-size: 72px;">
    {{ weather.temperature }}°C
  </div>
  <div class="condition" style="font-size: 24px;">
    {{ weather.condition }}
  </div>
  <div style="margin-top: 20px;">
    <p>💧 Humidity: {{ weather.humidity }}%</p>
    <p>💨 Wind: {{ weather.wind_speed }} km/h</p>
  </div>
</div>
```

### Example 3: Device Info Panel
```html
<div class="info-panel">
  <h1>{{ device.name }}</h1>
  <p>📍 Location: {{ device.location }}</p>
  <p>🌐 IP: {{ device.ip_address }}</p>

  {% if device.tags %}
  <div class="tags">
    Tags:
    {% for tag in device.tags %}
      <span class="tag">{{ tag }}</span>
    {% endfor %}
  </div>
  {% endif %}
</div>
```

### Example 4: Dynamic Table from Firebird
```html
<div class="data-table">
  <h2>📊 Live Data</h2>

  {% if firebird.connection_status == 'connected' %}
    <table style="width: 100%; border-collapse: collapse;">
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        {% for row in firebird.query_result %}
        <tr>
          <td>{{ row.id }}</td>
          <td>{{ row.name }}</td>
          <td>{{ row.value }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p>⚠️ Database not connected</p>
  {% endif %}
</div>
```

### Example 5: Conditional Weather Alerts
```html
<div class="weather-alert">
  {% if weather.temperature > 35 %}
    <div class="alert-hot">
      🔥 <strong>Heat Alert!</strong> Stay hydrated. Temperature: {{ weather.temperature }}°C
    </div>
  {% elif weather.temperature < 10 %}
    <div class="alert-cold">
      ❄️ <strong>Cold Alert!</strong> Dress warmly. Temperature: {{ weather.temperature }}°C
    </div>
  {% else %}
    <div class="alert-normal">
      ✅ Comfortable temperature: {{ weather.temperature }}°C
    </div>
  {% endif %}
</div>
```

## 🎨 Editor Features

### View Modes
- **Editor Only** - Focus on writing
- **Split View** - Editor + Preview side-by-side
- **Preview Only** - See full rendered output

### Variable Picker
- Click any variable to insert at cursor
- Hover to see examples
- Search variables by name
- Organized by category

### Live Preview
- Updates automatically as you type
- Shows validation errors
- Lists variables used
- Security warnings

### Keyboard Shortcuts
- `Ctrl/Cmd + S` - Save template (coming soon)
- `Ctrl/Cmd + F` - Find in template (coming soon)

## ⚠️ Common Issues

### Variable Not Showing in Preview
```jinja2
❌ Wrong: {{ device_name }}
✅ Correct: {{ device.name }}
```

### Syntax Errors
```jinja2
❌ Wrong: {% if temp > 30 %} (missing endif)
✅ Correct:
{% if temp > 30 %}
  Hot!
{% endif %}
```

### Security Warnings
```jinja2
❌ Unsafe: {{ config }}
❌ Unsafe: {{ __import__('os') }}
✅ Safe: Use only provided variables
```

## 🔍 Testing Templates

1. **Use Preview Pane** - See real-time rendering
2. **Check Validation** - Look for red error indicators
3. **Test with Device Context** - Select device from dropdown
4. **Review Variables Used** - Ensure all required variables are available

## 🚢 Deployment Checklist

Before using templates in production:

- [ ] Test template with real device data
- [ ] Check for validation errors
- [ ] Review security warnings
- [ ] Test on different screen sizes
- [ ] Verify all variables are available
- [ ] Set appropriate category
- [ ] Add clear description
- [ ] Test with sample data
- [ ] Mark as Active

## 📦 API Endpoints (for Backend Team)

```typescript
// List all templates
GET /api/templates?category=weather&search=temp

// Create template
POST /api/templates
{
  "name": "Weather Widget",
  "content": "<div>{{ weather.temperature }}</div>",
  "category": "weather",
  "is_active": true
}

// Update template
PATCH /api/templates/{id}
{
  "content": "Updated content"
}

// Preview template
POST /api/templates/preview
{
  "content": "{{ device.name }}",
  "device_id": "device-123"
}

// Validate template
POST /api/templates/validate
{
  "content": "{% for item in items %}{{ item }}{% endfor %}"
}
```

## 💡 Pro Tips

1. **Start Simple** - Begin with static HTML, then add variables
2. **Use Preview** - Always check preview before saving
3. **Test Edge Cases** - What if variable is null or empty?
4. **Add Fallbacks** - Use `{% if variable %}` to check existence
5. **Keep It Clean** - Use proper indentation and spacing
6. **Comment Complex Logic** - Use `{# comment #}` for notes
7. **Reuse Templates** - Duplicate and modify instead of starting from scratch

## 🆘 Need Help?

- Check validation errors in the editor
- Hover over variables for examples
- Review example templates above
- Check documentation for Jinja2 syntax
- Contact development team for custom variables

---

**Happy Templating! 🎉**
