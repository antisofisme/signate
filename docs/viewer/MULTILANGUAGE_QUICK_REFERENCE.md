# Multi-Language Support - Quick Reference Guide

## Quick Start

### Check Current Language
```javascript
const currentLang = window.LanguageManager.getCurrentLanguage();
console.log(currentLang); // "en", "id", "zh", etc.
```

### Change Language
```javascript
window.LanguageManager.setLanguage('id', 'manual');
```

### Listen for Changes
```javascript
window.LanguageManager.addEventListener('language-changed', (e) => {
    console.log('Changed from', e.detail.oldLang, 'to', e.detail.newLang);
    console.log('Source:', e.detail.source); // "manual", "auto-detected", "rotation"
});
```

---

## Language Manager API

### Properties
```javascript
LanguageManager.currentLanguage        // Current language code
LanguageManager.availableLanguages     // Array of available languages
LanguageManager.rotationMode           // Boolean: is rotation active?
LanguageManager.rotationInterval       // Rotation interval in seconds
```

### Methods
```javascript
// Initialization
await LanguageManager.initialize()

// Language Selection
LanguageManager.setLanguage(code, source)
LanguageManager.getCurrentLanguage()
LanguageManager.getCurrentLanguageInfo()
LanguageManager.getLanguageInfo(code)
LanguageManager.isLanguageAvailable(code)

// Rotation Mode
LanguageManager.startRotation()
LanguageManager.stopRotation()
LanguageManager.setRotationInterval(seconds)
LanguageManager.isRotationActive()

// Storage
LanguageManager.loadLanguageFromStorage()
LanguageManager.saveLanguageToStorage(code, source)
LanguageManager.clearLanguageFromStorage()

// Statistics
LanguageManager.getStatistics()
```

### Events
```javascript
// Language Changed
LanguageManager.addEventListener('language-changed', (e) => {
    e.detail.oldLang      // Previous language
    e.detail.newLang      // New language
    e.detail.source       // "manual", "auto-detected", "rotation"
    e.detail.languageInfo // Full language info object
});

// Rotation Started
LanguageManager.addEventListener('rotation-started', (e) => {
    e.detail.interval     // Rotation interval in seconds
});

// Rotation Stopped
LanguageManager.addEventListener('rotation-stopped', () => {
    // Rotation stopped
});
```

---

## Language Selector UI API

### Initialization
```javascript
const selector = new LanguageSelector(window.LanguageManager);
await selector.initialize();
```

### Methods
```javascript
selector.toggle()           // Toggle dropdown open/close
selector.open()             // Open dropdown
selector.close()            // Close dropdown
selector.selectLanguage(code) // Select language programmatically
selector.showNotification(msg) // Show notification
selector.destroy()          // Clean up
```

### Properties
```javascript
selector.isOpen             // Boolean: is dropdown open?
selector.languageManager    // Reference to LanguageManager
```

---

## API Integration

### Endpoints with Language Support
```javascript
// Playlist
GET /api/client/playlist?device_id={id}&language={lang}

// Content
GET /api/content/{id}?language={lang}

// Languages List
GET /api/languages
```

### API Usage
```javascript
// Automatically includes language parameter
const playlist = await window.PlayerAPI.loadPlaylist();
const content = await window.PlayerAPI.getContent(contentId);
```

---

## Language Object Structure

```javascript
{
    code: "en",                // ISO 639-1 language code
    name: "English",           // English name
    native_name: "English",    // Native name
    is_rtl: false             // Right-to-left script
}
```

---

## Default Languages

| Code | Name | Native Name | RTL | Flag |
|------|------|-------------|-----|------|
| en | English | English | No | 🇬🇧 |
| id | Indonesian | Bahasa Indonesia | No | 🇮🇩 |
| zh | Chinese | 中文 | No | 🇨🇳 |
| ja | Japanese | 日本語 | No | 🇯🇵 |
| ko | Korean | 한국어 | No | 🇰🇷 |
| ar | Arabic | العربية | Yes | 🇸🇦 |
| es | Spanish | Español | No | 🇪🇸 |
| fr | French | Français | No | 🇫🇷 |
| de | German | Deutsch | No | 🇩🇪 |
| ru | Russian | Русский | No | 🇷🇺 |

---

## localStorage Keys

```javascript
// Language Preference
localStorage.getItem('language')                  // Current language code
localStorage.getItem('language_source')           // How it was set
localStorage.getItem('language_updated_at')       // Last update timestamp
localStorage.getItem('language_modal_shown')      // Startup modal shown?

// Rotation Settings
localStorage.getItem('language_rotation_enabled') // Rotation active?
localStorage.getItem('language_rotation_interval') // Rotation interval
```

---

## Common Tasks

### Reset Language to Default
```javascript
localStorage.removeItem('language');
localStorage.removeItem('language_source');
location.reload();
```

### Skip First-Time Modal
```javascript
localStorage.setItem('language_modal_shown', 'true');
```

### Enable Rotation on Startup
```javascript
localStorage.setItem('language_rotation_enabled', 'true');
localStorage.setItem('language_rotation_interval', '30');
```

### Check if Language is RTL
```javascript
const langInfo = LanguageManager.getLanguageInfo('ar');
if (langInfo.is_rtl) {
    console.log('Arabic is RTL');
}
```

### Get All Available Languages
```javascript
const languages = LanguageManager.getAvailableLanguages();
languages.forEach(lang => {
    console.log(lang.code, lang.native_name);
});
```

---

## Debugging

### Enable Debug Mode
```javascript
// Check current state
console.log('Current Language:', LanguageManager.getCurrentLanguage());
console.log('Available Languages:', LanguageManager.availableLanguages);
console.log('Rotation Active:', LanguageManager.isRotationActive());
console.log('Statistics:', LanguageManager.getStatistics());

// Check localStorage
console.log('Stored Language:', localStorage.getItem('language'));
console.log('Language Source:', localStorage.getItem('language_source'));
```

### Test Language Changes
```javascript
// Test manual selection
LanguageManager.setLanguage('id', 'test');

// Test rotation
LanguageManager.setRotationInterval(5); // 5 seconds for testing
LanguageManager.startRotation();

// Wait and observe...
setTimeout(() => {
    LanguageManager.stopRotation();
    console.log('Rotation stopped');
}, 20000); // Stop after 20 seconds
```

### Verify API Calls
```javascript
// Check if language parameter is included
console.log('API Base URL:', window.PlayerState.API_BASE_URL);
console.log('Current Language:', window.PlayerAPI.getCurrentLanguage());

// Monitor API calls
const originalFetch = window.fetch;
window.fetch = async (...args) => {
    console.log('[API Call]', args[0]);
    return originalFetch(...args);
};
```

---

## Troubleshooting

### Language Not Changing?
1. Check if language is available: `LanguageManager.isLanguageAvailable('xx')`
2. Check console for errors
3. Verify API endpoint returns translations
4. Clear localStorage and retry

### Dropdown Not Opening?
1. Check z-index conflicts with other elements
2. Verify CSS is loaded
3. Check JavaScript console for errors
4. Try `selector.open()` manually

### Rotation Not Working?
1. Check if rotation is enabled: `LanguageManager.isRotationActive()`
2. Verify interval is reasonable (5-120 seconds)
3. Check if languages are available (need 2+ languages)
4. Look for JavaScript errors in console

### RTL Layout Broken?
1. Verify language has `is_rtl: true`
2. Check if `document.documentElement.dir` is set to "rtl"
3. Verify CSS RTL rules are loaded
4. Test with known RTL language (Arabic "ar")

---

## Performance Tips

### Minimize Language Changes
```javascript
// Bad: Changing language repeatedly
for (let i = 0; i < 100; i++) {
    LanguageManager.setLanguage('en');
    LanguageManager.setLanguage('id');
}

// Good: Change once
LanguageManager.setLanguage('id');
```

### Debounce Rotation
```javascript
// Rotation already debounced internally
// Minimum interval: 5 seconds
// Recommended interval: 30 seconds for UX
```

### Cache Language Info
```javascript
// Bad: Repeated calls
const info1 = LanguageManager.getLanguageInfo('en');
const info2 = LanguageManager.getLanguageInfo('en');
const info3 = LanguageManager.getLanguageInfo('en');

// Good: Cache result
const langInfo = LanguageManager.getLanguageInfo('en');
// Use langInfo multiple times
```

---

## CSS Customization

### Change Language Button Position
```css
.language-selector {
    bottom: 20px;
    left: 20px;
    /* Change to: */
    bottom: 20px;
    right: 20px; /* Move to right */
}
```

### Customize Colors
```css
.language-btn {
    background: rgba(0, 0, 0, 0.85);
    /* Change to: */
    background: rgba(34, 139, 230, 0.9); /* Blue */
}
```

### Adjust Dropdown Size
```css
.language-dropdown {
    min-width: 320px;
    max-height: 500px;
    /* Change to: */
    min-width: 400px;
    max-height: 600px;
}
```

---

## Integration Examples

### Example 1: Auto-Detect from URL Parameter
```javascript
// Parse URL: ?lang=id
const urlParams = new URLSearchParams(window.location.search);
const langParam = urlParams.get('lang');

if (langParam && LanguageManager.isLanguageAvailable(langParam)) {
    LanguageManager.setLanguage(langParam, 'url-parameter');
}
```

### Example 2: Language Picker for Web Admin
```javascript
// In web admin, create dropdown
const languages = await fetch('/api/languages').then(r => r.json());

const select = document.createElement('select');
languages.forEach(lang => {
    const option = document.createElement('option');
    option.value = lang.code;
    option.textContent = `${lang.flag} ${lang.native_name}`;
    select.appendChild(option);
});

select.addEventListener('change', (e) => {
    LanguageManager.setLanguage(e.target.value, 'admin-picker');
});
```

### Example 3: Sync Language Across Windows
```javascript
// Listen for storage changes (from other tabs/windows)
window.addEventListener('storage', (e) => {
    if (e.key === 'language' && e.newValue !== e.oldValue) {
        console.log('Language changed in another tab:', e.newValue);
        LanguageManager.setLanguage(e.newValue, 'sync');
    }
});
```

---

## Testing Checklist

```javascript
// 1. First-time modal
localStorage.clear();
location.reload();
// → Should show language startup modal

// 2. Manual selection
window.LanguageManager.setLanguage('id', 'manual');
// → Should change to Indonesian

// 3. Rotation
window.LanguageManager.startRotation();
// → Should rotate every 30s

// 4. RTL
window.LanguageManager.setLanguage('ar', 'manual');
// → Should flip layout to RTL

// 5. API calls
// Open network tab, reload playlist
// → Should see ?language=xx parameter
```

---

## Browser Console Commands

```javascript
// Quick access to Language Manager
lang = window.LanguageManager;

// Common commands
lang.setLanguage('id')          // Switch to Indonesian
lang.setLanguage('en')          // Back to English
lang.startRotation()            // Start rotating
lang.stopRotation()             // Stop rotating
lang.getCurrentLanguage()       // Check current
lang.getStatistics()            // View stats

// Clear and reset
localStorage.clear();
location.reload();

// Test all languages
lang.availableLanguages.forEach(l => {
    console.log(l.code, l.native_name);
});
```

---

## File Locations

```
viewer/
├── js/shared/
│   ├── language-manager.js       # Language management logic
│   └── language-selector.js      # UI component
├── player.html                   # Player with selector UI
└── index.html                    # Shell with startup modal
```

---

## Support

For issues or questions:
1. Check console logs
2. Verify localStorage state
3. Test API endpoints
4. Review this guide
5. Check main documentation: `PHASE_4.2_MULTILANGUAGE_COMPLETE.md`

---

**Last Updated**: October 28, 2025
**Version**: 1.0.0
