# UI Design System Standard

> Standar visual design yang konsisten untuk seluruh Enterprise Hospitality Platform.

---

## 1. Design Philosophy

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Professional & Trustworthy** | Visual yang meyakinkan untuk enterprise hospitality |
| **Modern SaaS** | Balance antara clean dan informative (referensi: Slack, Figma, Vercel) |
| **Module Identity** | Setiap modul memiliki identitas warna unik |
| **Adaptive Complexity** | Struktur menyesuaikan role, bukan visual style |
| **Hospitality-Friendly** | Warm, welcoming, cocok untuk industri hospitality |

### 1.2 Design Style

```
Style: Modern SaaS
- Clean tapi tidak steril
- Informative tanpa overwhelming
- Subtle personality melalui warna dan micro-interactions
- Professional untuk penggunaan 8+ jam sehari
```

---

## 2. Color System

### 2.1 Module Identity Colors

Setiap modul memiliki **primary color** yang merepresentasikan fungsinya:

| Module | Code | Primary Color | Hex | Rationale |
|--------|------|---------------|-----|-----------|
| Property Management | PMS | Blue | `#3B82C4` | Trust, reliability, hospitality core |
| Point of Sale | POS | Orange | `#E07B3C` | Energy, F&B warmth, appetite |
| Accounting | ACC | Green | `#4AA366` | Money, growth, financial stability |
| Inventory | INV | Cyan/Teal | `#2BA8A8` | Flow, logistics, movement |
| Human Resources | HRM | Purple | `#8B5DC4` | People, wisdom, professionalism |
| Channel Manager | CHM | Amber | `#D4A03C` | Distribution, connectivity, premium |
| Procurement | PROC | Bronze | `#A67C52` | Supply chain, earthiness, materials |
| Asset Management | AST | Slate | `#64748B` | Solid, infrastructure, durability |
| Customer Relations | CRM | Rose | `#D46B8C` | Relationships, care, hospitality warmth |
| Project Management | PRJ | Indigo | `#5B6DC4` | Planning, depth, coordination |
| Laundry | LDR | Light Blue | `#5BA8D4` | Clean, fresh, water |
| Spa & Wellness | SPA | Sage | `#6BA87B` | Calm, wellness, nature |
| Gym & Fitness | GYM | Red | `#C45B5B` | Energy, strength, activity |
| IoT & Smart Devices | IOT | Electric Blue | `#3B8EC4` | Technology, connectivity, smart |

### 2.2 Color Tone

```
Tone: Muted/Professional
- Saturasi lebih rendah (~60-70%)
- Tidak mencolok untuk penggunaan lama
- Terlihat enterprise, tidak childish
- Nyaman di mata untuk 8+ jam penggunaan
```

### 2.3 Shared Color Palette

#### Base Colors (Light Mode)

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-primary` | `#FFFFFF` | Main background |
| `--bg-secondary` | `#F8FAFC` | Cards, panels |
| `--bg-tertiary` | `#F1F5F9` | Hover states, zebra rows |
| `--bg-elevated` | `#FFFFFF` | Modals, dropdowns |
| `--border-default` | `#E2E8F0` | Default borders |
| `--border-subtle` | `#F1F5F9` | Subtle separators |

#### Base Colors (Dark Mode - Soft Dark)

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-primary` | `#121218` | Main background |
| `--bg-secondary` | `#1A1A22` | Cards, panels |
| `--bg-tertiary` | `#22222C` | Hover states, zebra rows |
| `--bg-elevated` | `#1E1E28` | Modals, dropdowns |
| `--border-default` | `#2A2A36` | Default borders |
| `--border-subtle` | `#1E1E28` | Subtle separators |

#### Text Colors (Light Mode)

| Token | Value | Usage |
|-------|-------|-------|
| `--text-primary` | `#0F172A` | Main text |
| `--text-secondary` | `#475569` | Secondary text |
| `--text-tertiary` | `#94A3B8` | Placeholder, disabled |
| `--text-inverse` | `#FFFFFF` | Text on dark backgrounds |

#### Text Colors (Dark Mode)

| Token | Value | Usage |
|-------|-------|-------|
| `--text-primary` | `#F1F5F9` | Main text |
| `--text-secondary` | `#94A3B8` | Secondary text |
| `--text-tertiary` | `#64748B` | Placeholder, disabled |
| `--text-inverse` | `#0F172A` | Text on light backgrounds |

### 2.4 Semantic Colors

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--semantic-success` | `#22C55E` | `#4ADE80` | Success states |
| `--semantic-warning` | `#F59E0B` | `#FBBF24` | Warning states |
| `--semantic-error` | `#EF4444` | `#F87171` | Error states |
| `--semantic-info` | `#3B82F6` | `#60A5FA` | Info states |

### 2.5 Module Color Application

```typescript
// Contoh penggunaan warna modul
interface ModuleTheme {
  primary: string;      // Warna utama modul
  primaryHover: string; // Hover state (5% darker)
  primaryActive: string; // Active state (10% darker)
  primaryLight: string; // Light variant (10% opacity)
  primaryMuted: string; // Muted variant (20% opacity)
}

// PMS Example
const pmsTheme: ModuleTheme = {
  primary: '#3B82C4',
  primaryHover: '#3374B0',
  primaryActive: '#2B669C',
  primaryLight: 'rgba(59, 130, 196, 0.1)',
  primaryMuted: 'rgba(59, 130, 196, 0.2)',
};
```

### 2.6 Shared vs Module-Specific Elements

| Category | Shared (Konsisten) | Module-Specific |
|----------|-------------------|-----------------|
| **Colors** | Background, text, borders, semantic | Primary, accent, icon tint |
| **States** | Disabled, loading | Active, selected, focus ring |
| **Components** | Buttons, forms, modals | Header accent, sidebar highlight |
| **Feedback** | Error red, success green | Module progress bars |

---

## 3. Typography

### 3.1 Font Family

```css
--font-primary: 'Nunito Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

**Rationale**: Nunito Sans
- Rounded letterforms = friendly & approachable
- Tetap professional untuk enterprise
- Excellent readability di berbagai sizes
- Cocok untuk hospitality industry
- Support multilingual (termasuk Indonesia)

### 3.2 Type Scale

| Token | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| `--text-xs` | 11px | 400 | 1.4 | Badges, micro labels |
| `--text-sm` | 13px | 400 | 1.5 | Secondary text, captions |
| `--text-base` | 15px | 400 | 1.6 | Body text, inputs |
| `--text-md` | 17px | 500 | 1.5 | Subheadings, emphasized |
| `--text-lg` | 20px | 600 | 1.4 | Section titles |
| `--text-xl` | 24px | 600 | 1.3 | Page titles |
| `--text-2xl` | 30px | 700 | 1.2 | Dashboard metrics |
| `--text-3xl` | 36px | 700 | 1.2 | Hero numbers |

### 3.3 Font Weights

| Token | Weight | Usage |
|-------|--------|-------|
| `--font-normal` | 400 | Body text |
| `--font-medium` | 500 | Emphasized text, labels |
| `--font-semibold` | 600 | Headings, buttons |
| `--font-bold` | 700 | Strong emphasis, metrics |

---

## 4. Spacing System

### 4.1 Base Unit

```css
--spacing-unit: 4px;
```

### 4.2 Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight gaps |
| `--space-2` | 8px | Icon gaps, inline spacing |
| `--space-3` | 12px | Input padding, small gaps |
| `--space-4` | 16px | Default component padding |
| `--space-5` | 20px | Card padding |
| `--space-6` | 24px | Section spacing |
| `--space-8` | 32px | Large section gaps |
| `--space-10` | 40px | Page section gaps |
| `--space-12` | 48px | Major separations |
| `--space-16` | 64px | Page margins |

### 4.3 Data Density

```
Density: Balanced
- Row height: 48-52px
- Seimbang antara informasi dan whitespace
- Tidak terlalu cramped, tidak terlalu sparse
- Optimal untuk mixed use (viewing + editing)
```

---

## 5. Shape & Effects

### 5.1 Border Radius

```
Corner Style: Medium Rounded (12-16px)
- Modern tapi tidak terlalu playful
- Konsisten dengan Modern SaaS aesthetic
```

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 6px | Small inputs, badges |
| `--radius-md` | 12px | Buttons, cards |
| `--radius-lg` | 16px | Modals, large cards |
| `--radius-xl` | 24px | Hero sections |
| `--radius-full` | 9999px | Pills, avatars |

### 5.2 Shadows

```
Shadow Style: Subtle
- Lembut, tidak harsh
- Memberikan depth tanpa distraksi
- Cocok untuk Light + Dark mode
```

| Token | Light Mode | Dark Mode |
|-------|------------|-----------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | `0 1px 2px rgba(0,0,0,0.3)` |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.07)` | `0 4px 6px rgba(0,0,0,0.4)` |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | `0 10px 15px rgba(0,0,0,0.5)` |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.1)` | `0 20px 25px rgba(0,0,0,0.6)` |

---

## 6. Animation & Motion

### 6.1 Animation Philosophy

```
Animation Style: Subtle (150-300ms)
- Memberikan polish tanpa mengganggu
- Quick enough untuk tidak delay workflow
- Smooth transitions untuk state changes
```

### 6.2 Duration Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--duration-fast` | 100ms | Micro-interactions (hover) |
| `--duration-normal` | 200ms | Standard transitions |
| `--duration-slow` | 300ms | Complex transitions |
| `--duration-enter` | 250ms | Elements entering |
| `--duration-exit` | 200ms | Elements exiting |

### 6.3 Easing Functions

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | Standard ease |
| `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Accelerate |
| `--ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | Decelerate |
| `--ease-bounce` | `cubic-bezier(0.68, -0.55, 0.265, 1.55)` | Playful bounce |

### 6.4 Animation Guidelines

```typescript
// DO: Subtle, purposeful animations
transition: transform var(--duration-normal) var(--ease-out);

// DON'T: Excessive or slow animations
animation: bounce 2s infinite; // Too distracting
transition: all 500ms; // Too slow
```

---

## 7. Iconography

### 7.1 Icon Style

```
Style: Outlined/Stroke
- Stroke width: 1.5-2px
- Clean, modern appearance
- Consistent dengan Modern SaaS aesthetic
- Recommended library: Lucide Icons
```

### 7.2 Icon Sizes

| Token | Size | Usage |
|-------|------|-------|
| `--icon-xs` | 14px | Inline with small text |
| `--icon-sm` | 16px | Buttons, inputs |
| `--icon-md` | 20px | Default size |
| `--icon-lg` | 24px | Navigation, emphasized |
| `--icon-xl` | 32px | Empty states, features |
| `--icon-2xl` | 48px | Hero icons |

### 7.3 Icon Colors

```typescript
// Default: mengikuti text color
color: var(--text-secondary);

// Module-specific: menggunakan module primary
color: var(--module-primary);

// Semantic: mengikuti semantic colors
color: var(--semantic-success);
```

---

## 8. Components

### 8.1 Navigation - Sidebar Fixed

```
Style: Fixed Sidebar
- Width: 240px (expanded), 64px (collapsed)
- Always visible untuk quick access
- Module highlight menggunakan module primary color
```

```typescript
interface SidebarStyle {
  width: {
    expanded: '240px';
    collapsed: '64px';
  };
  background: 'var(--bg-secondary)';
  activeItem: {
    background: 'var(--module-primary-light)';
    borderLeft: '3px solid var(--module-primary)';
    textColor: 'var(--module-primary)';
  };
}
```

### 8.2 Status Indicators - Colored Badge/Pill

```
Style: Colored Badge/Pill
- Soft background dengan text color sesuai
- Border radius: full (pill shape)
- Readable dan professional
```

| Status | Background | Text Color |
|--------|------------|------------|
| Active | `rgba(34, 197, 94, 0.1)` | `#16A34A` |
| Pending | `rgba(245, 158, 11, 0.1)` | `#D97706` |
| Inactive | `rgba(148, 163, 184, 0.1)` | `#64748B` |
| Error | `rgba(239, 68, 68, 0.1)` | `#DC2626` |

```tsx
// Badge Component
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="neutral">Draft</Badge>
<Badge variant="error">Failed</Badge>
```

### 8.3 Toast Notifications - Detailed

```
Style: Detailed Toast with Action
- Title + description
- Optional action button
- Auto-dismiss dengan progress
- Position: top-right
```

```typescript
interface ToastStyle {
  position: 'top-right';
  width: '380px';
  padding: 'var(--space-4)';
  borderRadius: 'var(--radius-md)';
  shadow: 'var(--shadow-lg)';
  hasProgressBar: true;
  hasAction: true;
  autoDismiss: {
    success: 4000;
    error: 8000;
    info: 5000;
  };
}
```

```tsx
// Toast Usage
toast.success({
  title: 'Booking Confirmed',
  description: 'Room 301 booked for John Doe (Dec 20-22)',
  action: { label: 'View', onClick: () => navigate('/booking/123') }
});
```

### 8.4 Empty States - Contextual Illustrated

```
Style: Contextual Illustration per Module
- Ilustrasi simple yang relevan dengan modul
- Tidak generic placeholder
- Helpful message + CTA
```

```tsx
// Empty State Structure
interface EmptyState {
  illustration: ReactNode; // Module-specific illustration
  title: string;           // "No Reservations Yet"
  description: string;     // "Start by creating your first booking"
  action: {
    label: string;         // "Create Reservation"
    onClick: () => void;
  };
}

// Example per Module
const emptyStates = {
  PMS: {
    reservations: {
      illustration: <CalendarIllustration color={pmsTheme.primary} />,
      title: 'No Reservations Yet',
      description: 'Create your first booking to get started',
    }
  },
  POS: {
    orders: {
      illustration: <ReceiptIllustration color={posTheme.primary} />,
      title: 'No Orders Today',
      description: 'Orders will appear here when created',
    }
  },
  // ... per module
};
```

### 8.5 Tables - Zebra Striping

```
Style: Zebra Striping
- Alternating row colors
- Better readability untuk data-heavy tables
- Hover state tetap ada
```

```typescript
interface TableStyle {
  headerBg: 'var(--bg-tertiary)';
  rowOdd: 'var(--bg-primary)';
  rowEven: 'var(--bg-tertiary)';
  rowHover: 'var(--module-primary-light)';
  borderColor: 'var(--border-subtle)';
  cellPadding: 'var(--space-3) var(--space-4)';
  rowHeight: '48px';
}
```

```css
/* Table Zebra Styling */
.table-row:nth-child(odd) {
  background: var(--bg-primary);
}

.table-row:nth-child(even) {
  background: var(--bg-tertiary);
}

.table-row:hover {
  background: var(--module-primary-light);
}
```

### 8.6 Forms - Floating Label

```
Style: Floating Label
- Label floats up on focus/filled
- Clean, modern appearance
- Space-efficient
```

```typescript
interface InputStyle {
  height: '48px';
  padding: 'var(--space-3) var(--space-4)';
  borderRadius: 'var(--radius-md)';
  borderColor: {
    default: 'var(--border-default)';
    focus: 'var(--module-primary)';
    error: 'var(--semantic-error)';
  };
  label: {
    position: 'floating';
    fontSize: {
      default: 'var(--text-base)';
      floated: 'var(--text-xs)';
    };
  };
}
```

```tsx
// Floating Label Input
<FloatingInput
  label="Email Address"
  type="email"
  error={errors.email}
/>
```

### 8.7 Modals & Drawers - Hybrid Approach

```
Strategy: Hybrid
- Simple confirmations → Modal (centered)
- Complex forms/details → Drawer (side panel)
```

```typescript
interface ModalStyle {
  type: 'modal';
  maxWidth: '480px';
  borderRadius: 'var(--radius-lg)';
  padding: 'var(--space-6)';
  overlay: 'rgba(0, 0, 0, 0.5)';
  useCase: ['confirmation', 'alert', 'simple-form'];
}

interface DrawerStyle {
  type: 'drawer';
  width: '560px';     // Default
  widthLarge: '720px'; // For complex forms
  position: 'right';
  useCase: ['detail-view', 'complex-form', 'multi-step'];
}
```

```tsx
// Usage Decision
if (isSimpleAction) {
  return <Modal>{content}</Modal>;
} else {
  return <Drawer>{content}</Drawer>;
}
```

---

## 9. Responsive Design

### 9.1 Strategy

```
Approach: Responsive Web Only
- Single codebase, responsive design
- Mobile-first thinking
- No separate native apps initially
- PWA-ready for mobile access
```

### 9.2 Breakpoints

| Token | Value | Description |
|-------|-------|-------------|
| `--bp-mobile` | 0px | Mobile phones |
| `--bp-tablet` | 768px | Tablets portrait |
| `--bp-laptop` | 1024px | Tablets landscape, small laptops |
| `--bp-desktop` | 1280px | Standard desktops |
| `--bp-wide` | 1536px | Wide screens |

### 9.3 Responsive Behaviors

```typescript
interface ResponsiveBehavior {
  sidebar: {
    mobile: 'hidden (hamburger)';
    tablet: 'collapsed';
    desktop: 'expanded';
  };
  tables: {
    mobile: 'card view / horizontal scroll';
    tablet: 'simplified columns';
    desktop: 'full columns';
  };
  forms: {
    mobile: 'single column';
    tablet: 'single column';
    desktop: 'multi-column where appropriate';
  };
}
```

---

## 10. Dark Mode

### 10.1 Strategy

```
Style: Soft Dark
- Base: #121218 (not pure black)
- Easier on the eyes
- Maintains depth and hierarchy
- Auto-detect system preference
- User can override
```

### 10.2 Color Adjustments

```typescript
// Module colors in dark mode
// Slightly increased brightness for visibility
const darkModeAdjustment = {
  PMS: '#4A91D3',  // Brighter blue
  POS: '#E8894D',  // Brighter orange
  ACC: '#5BB577',  // Brighter green
  // ... etc
};
```

### 10.3 Implementation

```tsx
// Theme Provider
<ThemeProvider defaultTheme="system" storageKey="ui-theme">
  <App />
</ThemeProvider>

// Usage
const { theme, setTheme } = useTheme();
// theme: 'light' | 'dark' | 'system'
```

---

## 11. Adaptive Complexity

### 11.1 Philosophy

```
Approach: Structure-based Adaptation
- BUKAN perubahan visual style
- TAPI perubahan struktur/layout berdasarkan role
- Visual consistency tetap terjaga
```

### 11.2 Role-based Adaptations

| Aspect | Staff/Operational | Manager/Owner |
|--------|------------------|---------------|
| Sidebar | Collapsed by default | Expanded by default |
| Dashboard | Task-focused widgets | Analytics-focused widgets |
| Tables | Essential columns | More detail columns |
| Charts | Simplified | Detailed with drill-down |
| Navigation | Flat, quick access | Hierarchical, comprehensive |

### 11.3 Implementation

```typescript
interface UserPreferences {
  role: 'staff' | 'supervisor' | 'manager' | 'owner';
  complexity: 'simple' | 'standard' | 'detailed';
  sidebarState: 'collapsed' | 'expanded';
  dashboardLayout: 'operational' | 'analytical';
}

// Components adapt based on preferences
<DataTable
  columns={getColumnsForRole(user.role)}
  density={user.preferences.complexity}
/>
```

---

## 12. Design Tokens Summary

### 12.1 CSS Custom Properties

```css
:root {
  /* Colors - Light Mode */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F8FAFC;
  --bg-tertiary: #F1F5F9;
  --text-primary: #0F172A;
  --text-secondary: #475569;
  --text-tertiary: #94A3B8;
  --border-default: #E2E8F0;
  --border-subtle: #F1F5F9;

  /* Semantic */
  --semantic-success: #22C55E;
  --semantic-warning: #F59E0B;
  --semantic-error: #EF4444;
  --semantic-info: #3B82F6;

  /* Typography */
  --font-primary: 'Nunito Sans', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --text-base: 15px;
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  /* Spacing */
  --spacing-unit: 4px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  /* Shape */
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Animation */
  --duration-fast: 100ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);

  /* Icons */
  --icon-sm: 16px;
  --icon-md: 20px;
  --icon-lg: 24px;
}

[data-theme="dark"] {
  --bg-primary: #121218;
  --bg-secondary: #1A1A22;
  --bg-tertiary: #22222C;
  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --text-tertiary: #64748B;
  --border-default: #2A2A36;
  --border-subtle: #1E1E28;
}
```

### 12.2 Module Theme Variables

```css
/* Set per module */
[data-module="pms"] {
  --module-primary: #3B82C4;
  --module-primary-hover: #3374B0;
  --module-primary-light: rgba(59, 130, 196, 0.1);
}

[data-module="pos"] {
  --module-primary: #E07B3C;
  --module-primary-hover: #CC6E35;
  --module-primary-light: rgba(224, 123, 60, 0.1);
}

/* ... etc for all 14 modules */
```

---

## 13. Implementation Checklist

### 13.1 Setup

- [ ] Install Nunito Sans font
- [ ] Configure CSS custom properties
- [ ] Setup theme provider (light/dark)
- [ ] Configure module theme context
- [ ] Install Lucide Icons

### 13.2 Core Components

- [ ] Button (primary, secondary, ghost, danger, outline, link)
- [ ] Input (text, floating label, with icon)
- [ ] Select (single, multi, searchable)
- [ ] Badge (status variants)
- [ ] Card (standard, interactive)
- [ ] Table (sortable, zebra, responsive)
- [ ] Modal & Drawer
- [ ] Toast notification
- [ ] Empty state

### 13.3 Layout Components

- [ ] Sidebar (collapsible, module-aware)
- [ ] Header (with module indicator)
- [ ] Page container
- [ ] Section divider
- [ ] Grid system

### 13.4 Documentation

- [ ] Storybook setup
- [ ] Component documentation
- [ ] Usage examples
- [ ] Accessibility guidelines

---

## 14. Accessibility Guidelines

### 14.1 Color Contrast

```
Minimum contrast ratios:
- Normal text: 4.5:1
- Large text (18px+): 3:1
- UI components: 3:1
- Focus indicators: 3:1
```

### 14.2 Focus States

```css
/* Focus ring style */
:focus-visible {
  outline: 2px solid var(--module-primary);
  outline-offset: 2px;
}
```

### 14.3 Screen Reader Support

- All interactive elements have labels
- Images have alt text
- Form errors announced
- Loading states communicated
- Skip links for navigation

---

## 15. Quick Reference Card

| Aspect | Decision |
|--------|----------|
| **Style** | Modern SaaS |
| **Tone** | Muted/Professional |
| **Corners** | Medium Rounded (12-16px) |
| **Shadows** | Subtle |
| **Dark Mode** | Soft Dark (#121218) |
| **Font** | Nunito Sans |
| **Density** | Balanced |
| **Animation** | Subtle (150-300ms) |
| **Icons** | Outlined (Lucide) |
| **Navigation** | Sidebar Fixed |
| **Status** | Colored Badge/Pill |
| **Toast** | Detailed with Action |
| **Empty State** | Contextual Illustrated |
| **Tables** | Zebra Striping |
| **Forms** | Floating Label |
| **Modal** | Hybrid (simple→modal, complex→drawer) |
| **Responsive** | Web Only |

---

*Last Updated: 2025-12-12*
*Category: Shared Standard (applies to all modules)*
*Companion: [UI_COMPONENTS.md](./UI_COMPONENTS.md) for detailed component specs*
