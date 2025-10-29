# Multi-Language UI Demo & Screenshots

## Visual Overview

This document describes the UI elements and user interactions for the multi-language support feature.

---

## 1. Language Selector Button (Bottom-Left)

**Location**: Fixed position, bottom-left corner of player screen

**Appearance**:
```
┌──────────────────┐
│ 🇬🇧 EN ▼        │  ← Floating button
└──────────────────┘
   │
   └─ Semi-transparent black background
      with glass-morphism effect
```

**States**:
- **Default**: `rgba(0, 0, 0, 0.85)` with white border
- **Hover**: Brighter background, blue border glow
- **Active**: Border color changes to blue, arrow rotates 180°

**Components**:
- Flag emoji (e.g., 🇬🇧)
- Language code (e.g., "EN")
- Dropdown arrow (▼)

---

## 2. Language Dropdown Modal

**Location**: Opens above the language button

**Layout**:
```
┌─────────────────────────────────────┐
│ Select Language               ×     │ ← Header with close button
├─────────────────────────────────────┤
│ [🔍 Search language...]             │ ← Search input
├─────────────────────────────────────┤
│ 🇬🇧 English              ✓          │ ← Active language
│    English                          │
├─────────────────────────────────────┤
│ 🇮🇩 Indonesian                      │ ← Other languages
│    Bahasa Indonesia                 │
├─────────────────────────────────────┤
│ 🇨🇳 Chinese                         │
│    中文                              │
├─────────────────────────────────────┤
│ 🇯🇵 Japanese                        │
│    日本語                            │
├─────────────────────────────────────┤
│ ...more languages (scrollable)...   │
├─────────────────────────────────────┤
│ Language Rotation        [  OFF  ]  │ ← Toggle switch
│ Interval: 30s [========○====]       │ ← Slider (5-120s)
└─────────────────────────────────────┘
```

**Features**:
- **Header**: Title + close button (×)
- **Search**: Real-time filtering as you type
- **Language List**: Scrollable, 6-8 items visible
- **Each Item Shows**:
  - Flag emoji
  - English name (top)
  - Native name (bottom)
  - Checkmark (✓) for active language
- **Rotation Controls**: Toggle switch + slider

**Colors**:
- Background: White
- Header: Light gray (`#fafafa`)
- Active item: Light blue background
- Hover: Light gray background
- Text: Dark gray (`#333`)

**Animations**:
- Slide up from bottom with fade-in (0.3s ease-out)
- Item hover: Smooth background color transition
- Toggle switch: Smooth slide animation
- Checkmark: Appears/disappears with fade

---

## 3. Language Startup Modal (First-Time Only)

**Location**: Full-screen overlay on `index.html`

**Layout**:
```
┌────────────────────────────────────────────────┐
│                                                │
│           Welcome / Selamat Datang / 欢迎      │
│                                                │
│       Please select your preferred language    │
│                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   🇬🇧     │  │   🇮🇩     │  │   🇨🇳     │    │
│  │          │  │          │  │          │    │
│  │ English  │  │  Bahasa  │  │   中文    │    │
│  │          │  │Indonesia │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘    │
│                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   🇯🇵     │  │   🇰🇷     │  │   🇸🇦     │    │
│  │          │  │          │  │          │    │
│  │  日本語   │  │  한국어   │  │ العربية  │    │
│  │          │  │          │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘    │
│                                                │
│      Auto-proceeding in 10s with English      │
│                                                │
└────────────────────────────────────────────────┘
```

**Features**:
- **Full-screen**: Covers entire viewport
- **Gradient Background**: Purple gradient (same as activation screen)
- **Glass-morphism Card**: Semi-transparent white with blur
- **6 Language Buttons**: Grid layout (3 columns on desktop, 2 on mobile)
- **Large Touch Targets**: Easy to tap on TV remote or touch screen
- **Countdown Timer**: Auto-proceeds to English after 10 seconds
- **Animation**: Slide up from bottom on page load

**Button States**:
- **Default**: Semi-transparent white with border
- **Hover**: Brighter, lifts up with shadow
- **Active**: Pressed down animation

---

## 4. Language Change Notification

**Location**: Bottom-center of screen

**Appearance**:
```
┌──────────────────────────────────────┐
│ Language changed to Bahasa Indonesia │ ← Toast notification
└──────────────────────────────────────┘
```

**Behavior**:
- Slides up from bottom with fade-in
- Stays for 3 seconds
- Fades out and slides down
- Black background with transparency
- White text
- Glass-morphism effect

---

## 5. RTL Layout (Arabic/Hebrew)

**When RTL Language Selected**:

**Before (LTR)**:
```
┌──────────────────────────────────────┐
│                                      │
│  🇬🇧 EN ▼                            │ ← Button on left
│                                      │
│  [Content in center]                 │
│                                      │
└──────────────────────────────────────┘
```

**After (RTL)**:
```
┌──────────────────────────────────────┐
│                                      │
│                            ▼ AR 🇸🇦  │ ← Button flipped to right
│                                      │
│  [Content in center]                 │
│                                      │
└──────────────────────────────────────┘
```

**RTL Changes**:
- Language button moves to right side
- Dropdown opens from right
- Text alignment right-to-left
- Language list items mirror layout
- Entire UI direction flips

---

## 6. Rotation Mode Active

**Visual Indicator**:
```
┌──────────────────────────────────────┐
│ Select Language               ×      │
├──────────────────────────────────────┤
│ ...language list...                  │
├──────────────────────────────────────┤
│ Language Rotation        [  ON   ]   │ ← Toggle is ON (blue)
│ Interval: 30s [====○========]        │ ← Slider shows interval
└──────────────────────────────────────┘
```

**When Active**:
- Toggle switch slides to right
- Toggle background turns blue
- Language changes every N seconds
- Notification appears on each change
- Current language indicator updates

**Notification During Rotation**:
```
┌──────────────────────────────────────┐
│ Language changed to 日本語 (rotation) │ ← Shows "(rotation)"
└──────────────────────────────────────┘
```

---

## 7. Search Functionality

**Empty State**:
```
┌─────────────────────────────────────┐
│ [🔍 Search language...]             │ ← Placeholder text
└─────────────────────────────────────┘
```

**Searching**:
```
┌─────────────────────────────────────┐
│ [🔍 indo]                           │ ← User typing
├─────────────────────────────────────┤
│ 🇮🇩 Indonesian                      │ ← Filtered results
│    Bahasa Indonesia                 │
└─────────────────────────────────────┘
```

**No Results**:
```
┌─────────────────────────────────────┐
│ [🔍 xyz]                            │
├─────────────────────────────────────┤
│                                     │
│        No languages found           │ ← Empty state
│                                     │
└─────────────────────────────────────┘
```

---

## 8. Mobile/Responsive View

**Desktop (>768px)**:
- Dropdown: 320px wide
- Language grid: 3 columns
- Full language names shown
- Large touch targets

**Mobile (<768px)**:
```
┌──────────────────────┐
│ Select Lang    ×     │ ← Narrower
├──────────────────────┤
│ [Search...]          │
├──────────────────────┤
│ 🇬🇧 English      ✓  │ ← Compact
├──────────────────────┤
│ 🇮🇩 Indonesian       │
├──────────────────────┤
│ ...                  │
└──────────────────────┘
```

**Changes**:
- Dropdown: 280px wide
- Language grid: 2 columns
- Smaller padding
- Larger touch targets

---

## 9. Color Palette

**Primary Colors**:
- **Button Background**: `rgba(0, 0, 0, 0.85)` (dark, semi-transparent)
- **Button Border**: `rgba(255, 255, 255, 0.3)` (light, subtle)
- **Button Hover**: `rgba(34, 139, 230, 0.8)` (blue glow)

**Dropdown Colors**:
- **Background**: `#FFFFFF` (white)
- **Header**: `#FAFAFA` (light gray)
- **Border**: `#F0F0F0` (very light gray)
- **Active Item**: `rgba(34, 139, 230, 0.1)` (light blue)
- **Text**: `#333333` (dark gray)
- **Secondary Text**: `#666666` (medium gray)

**Rotation Colors**:
- **Toggle ON**: `rgba(34, 139, 230, 1)` (blue)
- **Toggle OFF**: `#CCCCCC` (gray)
- **Slider Track**: `#E0E0E0` (light gray)
- **Slider Thumb**: `rgba(34, 139, 230, 1)` (blue)

**Notification Colors**:
- **Background**: `rgba(0, 0, 0, 0.9)` (dark, semi-transparent)
- **Text**: `#FFFFFF` (white)

---

## 10. Animations & Transitions

**Language Button**:
- Hover: Scale up 1.05x, 0.3s ease
- Active: Border color change, 0.2s ease
- Arrow rotation: 180°, 0.3s ease

**Dropdown**:
- Open: Slide up + fade in, 0.3s ease-out
- Close: Fade out, 0.3s ease
- Transform: `translateY(20px) → translateY(0)`

**Language Items**:
- Hover: Background color change, 0.2s ease
- Click: Ripple effect (optional)

**Toggle Switch**:
- Slide: 0.3s ease
- Background color: 0.3s ease

**Notification**:
- Enter: Slide up + fade in, 0.3s ease-out
- Exit: Fade out, 0.3s ease
- Duration: 3 seconds visible

**Startup Modal**:
- Enter: Slide up + fade in, 0.5s ease-out
- Exit: Fade out, 0.3s ease
- Buttons: Scale on hover, 0.3s ease

---

## 11. User Interaction Flow

### Flow 1: First-Time User
```
Page Load
    ↓
Startup Modal Appears
    ↓
[User Selects Language] ─── OR ─── [Wait 10s]
    ↓                                 ↓
Language Saved                  Default to English
    ↓                                 ↓
Modal Closes ─────────────────────────┘
    ↓
Viewer Continues
```

### Flow 2: Changing Language
```
User Clicks Language Button
    ↓
Dropdown Opens (Slide Up)
    ↓
[User Can]:
├─ Search Languages
├─ Select Language ──→ Notification ──→ Dropdown Closes ──→ Playlist Reloads
├─ Enable Rotation ──→ Languages Auto-Rotate
└─ Adjust Interval ──→ Rotation Speed Changes
```

### Flow 3: Language Rotation
```
Rotation Enabled
    ↓
Wait N Seconds (interval)
    ↓
Switch to Next Language
    ↓
Show Notification
    ↓
Reload Playlist
    ↓
Repeat Until:
├─ User Disables Rotation
└─ User Manually Selects Language
```

---

## 12. Accessibility Features

**Keyboard Navigation**:
- `Tab`: Navigate through language items
- `Enter`/`Space`: Select language
- `Escape`: Close dropdown
- Arrow keys: Navigate list (optional)

**Screen Readers**:
- ARIA labels on buttons
- Role attributes on modal
- Focus management
- Announcement of language changes

**Touch Targets**:
- Minimum 44x44px (iOS guideline)
- Large buttons in startup modal
- Good spacing between items

**Visual Feedback**:
- Clear hover states
- Active state indicators
- Focus outlines
- Loading states

---

## 13. Error States

### Network Error
```
┌─────────────────────────────────────┐
│ ⚠️  Failed to load languages        │
│                                     │
│ Using default language set          │
│ [Retry]                             │
└─────────────────────────────────────┘
```

### Invalid Language
```
┌─────────────────────────────────────┐
│ ⚠️  Language not available          │
│                                     │
│ Falling back to English             │
└─────────────────────────────────────┘
```

### Translation Missing
```
┌─────────────────────────────────────┐
│ ℹ️  Translation not available       │
│                                     │
│ Showing in default language         │
└─────────────────────────────────────┘
```

---

## 14. Special Features

### Feature 1: Flag Emoji Fallback
If flag emojis not supported:
```
┌──────────────────┐
│ 🌐 EN ▼        │ ← Globe emoji as fallback
└──────────────────┘
```

### Feature 2: Language Count Badge
When many languages available:
```
┌──────────────────┐
│ 🇬🇧 EN ▼ (10)   │ ← Shows count in parentheses
└──────────────────┘
```

### Feature 3: Recently Used
Track recently used languages:
```
┌─────────────────────────────────────┐
│ Recently Used:                      │
│ 🇮🇩 Indonesian    🇯🇵 Japanese      │
├─────────────────────────────────────┤
│ All Languages:                      │
│ 🇬🇧 English                      ✓ │
│ ...                                 │
└─────────────────────────────────────┘
```

---

## 15. Debug Mode UI

When debug mode enabled:
```
┌──────────────────────────────────────┐
│ 🇬🇧 EN ▼                             │
│                                      │
│ [DEBUG MODE]                         │
│ Language: en                         │
│ Source: manual                       │
│ Updated: 2025-10-28 16:00:00        │
│ Rotation: OFF                        │
│ Available: 10                        │
└──────────────────────────────────────┘
```

---

## Color Reference

### CSS Variables (Suggested)
```css
:root {
    --lang-btn-bg: rgba(0, 0, 0, 0.85);
    --lang-btn-border: rgba(255, 255, 255, 0.3);
    --lang-btn-hover: rgba(34, 139, 230, 0.8);

    --lang-dropdown-bg: #FFFFFF;
    --lang-dropdown-header: #FAFAFA;
    --lang-dropdown-border: #F0F0F0;

    --lang-item-active: rgba(34, 139, 230, 0.1);
    --lang-item-hover: #F5F5F5;

    --lang-text-primary: #333333;
    --lang-text-secondary: #666666;

    --lang-accent: rgba(34, 139, 230, 1);
}
```

---

## Conclusion

The multi-language UI is designed with:
- ✅ Modern, clean aesthetics
- ✅ Intuitive interactions
- ✅ Smooth animations
- ✅ Accessibility features
- ✅ RTL support
- ✅ Touch-friendly design
- ✅ Responsive layout
- ✅ Clear visual feedback

Perfect for digital signage in hotels, airports, malls, and international venues!

---

**Generated**: October 28, 2025
**For**: Digital Signage Viewer v1.0
