# Template Variables System - Quick Start Guide

**Fast setup guide for Phase 4.1 Secure Template Variables**

---

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
cd /mnt/g/khoirul/signate/backend
pip install Jinja2==3.1.2 MarkupSafe==2.1.3
```

### 2. Configure (Optional)
```bash
# .env
OPENWEATHER_API_KEY=your_key  # For weather variables
```

### 3. Test Installation
```bash
pytest tests/test_template_security.py -v
```

---

## 💡 Basic Usage

### Render a Simple Template
```python
from app.services.template_service import SecureTemplateRenderer

renderer = SecureTemplateRenderer()

result = await renderer.render(
    "Hello {{name|upper}}!",
    {"name": "world"},
    user_role='admin'
)

print(result['output'])  # "Hello WORLD!"
```

### With Device & Weather Variables
```python
from app.services.variable_providers import get_template_context

# Get all variables automatically
context = await get_template_context(
    device_id=1,
    content_id=5,
    db=db_session,
    redis_client=redis
)

# Render with full context
result = await renderer.render(
    "{{device.name}} - {{weather.temp}}°C",
    context,
    user_role='editor'
)
```

---

## 📝 Template Syntax

### Variables
```jinja2
{{device.name}}              # Device name
{{datetime.today}}           # Today's date
{{weather.temp}}             # Temperature
{{custom.hotel_name}}        # Custom variable
```

### Filters
```jinja2
{{text|upper}}               # UPPERCASE
{{text|lower}}               # lowercase
{{date|date('%Y-%m-%d')}}    # Format date
{{price|currency('USD')}}    # $1,234.56
{{long_text|truncate(100)}}  # Truncate...
{{optional|default('N/A')}}  # Fallback value
```

### Conditions
```jinja2
{% if weather.temp > 30 %}
  Hot day!
{% else %}
  Nice weather
{% endif %}
```

### Loops
```jinja2
{% for item in items %}
  {{item.name}}
{% endfor %}
```

---

## 🔒 Security

### What's BLOCKED ✅
- Code execution (`eval`, `exec`, `__import__`)
- File access (`open`, `include`)
- Private attributes (`_internal`, `__dict__`)
- Dangerous functions (all blocked)

### What's ALLOWED ✅
- Safe variables (whitelisted)
- Safe filters (upper, lower, date, currency)
- Loops and conditions (with limits)

---

## 🎯 Common Use Cases

### 1. Hotel Welcome Screen
```jinja2
<h1>Welcome to {{custom.hotel_name}}!</h1>
<p>{{datetime.weekday}}, {{datetime.today|date('%B %d')}}</p>
<p>Temperature: {{weather.temp}}°C</p>
<p>Check-in: {{custom.check_in_time}}</p>
```

### 2. Meeting Room Display
```jinja2
<h2>{{device.location}}</h2>
{% if firebird.event_name %}
  <h3>{{firebird.event_name}}</h3>
  <p>{{firebird.start_time|time('%H:%M')}} - {{firebird.end_time|time('%H:%M')}}</p>
{% else %}
  <p>Available</p>
{% endif %}
```

### 3. Retail Price Display
```jinja2
<h1>{{custom.product_name}}</h1>
<p class="price">{{custom.price|currency('IDR')}}</p>
{% if custom.discount %}
  <span>Save {{custom.discount}}%!</span>
{% endif %}
```

---

## 📊 Available Variables

### Device Variables
```python
device.id           # Device ID
device.name         # Display name
device.location     # Physical location
device.tag          # Tag/group
device.status       # online/offline
device.ip_address   # Masked IP
```

### DateTime Variables
```python
datetime.now        # Current datetime
datetime.today      # Today's date
datetime.time       # Current time
datetime.year       # 2024
datetime.month      # 10
datetime.day        # 28
datetime.weekday    # "Monday"
datetime.hour       # 14
datetime.minute     # 30
```

### Weather Variables (5 min cache)
```python
weather.temp        # 25.0 (Celsius)
weather.feels_like  # 26.0
weather.condition   # "Clear"
weather.humidity    # 60 (%)
weather.wind_speed  # 5.2 (m/s)
weather.icon        # "01d"
```

### Firebird PMS (1 min cache)
```python
firebird.event_name     # "Board Meeting"
firebird.room           # "Conference Room A"
firebird.start_time     # datetime
firebird.end_time       # datetime
firebird.attendees      # 15
firebird.organizer      # "John Doe"
```

### Content Variables
```python
content.title       # Content title
content.description # Description
content.duration    # Duration (seconds)
content.sequence    # Position in playlist
```

### Custom Variables
```python
custom.*            # User-defined
# Example:
custom.hotel_name
custom.check_in_time
custom.product_name
custom.special_offer
```

---

## ⚡ Performance Tips

### 1. Enable Caching
```python
result = await renderer.render(
    template,
    context,
    use_cache=True  # ✅ Default, recommended
)
```

### 2. Keep Templates Simple
- ✅ DO: `{{device.name}}`
- ❌ AVOID: Complex nested loops

### 3. Use Appropriate Timeout
```python
# Quick renders
await renderer.render(template, context, timeout=2)

# Complex renders
await renderer.render(template, context, timeout=10)
```

---

## 🐛 Troubleshooting

### TemplateSecurityError
**Cause**: Blocked keyword or unsafe operation
**Fix**: Check template for:
- `__import__`, `eval`, `exec`
- Private attributes (`_*`)
- Dangerous functions

### TemplateTimeoutError
**Cause**: Render exceeded timeout
**Fix**:
- Simplify template
- Increase timeout
- Check for infinite loops

### Undefined Variable
**Cause**: Variable not in context
**Fix**: Use default filter
```jinja2
{{optional_var|default('N/A')}}
```

---

## 🧪 Testing

### Validate Template
```python
validation = await renderer.validate_template(
    "Hello {{name}}!"
)

if validation['valid']:
    print("✅ Valid")
else:
    print(f"❌ {validation['error']}")
```

### Test Render
```python
result = await renderer.render(
    "Hello {{name}}!",
    {"name": "World"},
    user_role='admin'
)

print(f"Output: {result['output']}")
print(f"Time: {result['render_time_ms']}ms")
print(f"Cached: {result['cached']}")
```

---

## 📚 Full Documentation

See: `PHASE_4.1_TEMPLATE_SERVICE_IMPLEMENTATION.md`

---

## 🆘 Support

**Issues?** Check:
1. Dependencies installed: `pip list | grep -i jinja`
2. Tests passing: `pytest tests/test_template_security.py`
3. Redis running (for caching)
4. Environment variables set

**Security Concerns?**
- All templates sandboxed by default
- 60+ security tests validate protections
- Code execution impossible
- XSS automatically prevented

---

**Ready to use!** 🎉
