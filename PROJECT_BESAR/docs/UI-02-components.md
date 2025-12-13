# UI Components Specification

> Detail spesifikasi komponen UI untuk Enterprise Hospitality Platform.
> Dokumen ini melengkapi [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md).

---

## 1. Buttons

### 1.1 Button Variants

| Variant | Use Case | Style |
|---------|----------|-------|
| **Primary** | Main CTA, primary actions | Solid module color background |
| **Secondary** | Secondary actions | Outlined with module color border |
| **Ghost** | Tertiary actions, toolbar | Transparent, text only |
| **Danger** | Destructive actions (delete, cancel) | Solid red background |
| **Outline** | Medium priority actions | Border with transparent bg |
| **Link** | Inline text actions | Underlined text style |

### 1.2 Button Sizes

| Size | Height | Padding | Font Size | Use Case |
|------|--------|---------|-----------|----------|
| **XS** | 28px | 8px 12px | 12px | Inline actions, compact UI |
| **SM** | 36px | 10px 16px | 13px | Secondary actions, table rows |
| **MD** | 44px | 12px 20px | 14px | Default, most buttons |
| **LG** | 48px | 14px 24px | 15px | Primary CTA, forms (matches input height) |

### 1.3 Button States

| State | Description | Visual Change |
|-------|-------------|---------------|
| **Default** | Normal state | Base styling |
| **Hover** | Mouse over | 5% darker background |
| **Active** | Being clicked | 10% darker, slight scale down |
| **Disabled** | Not interactive | 50% opacity, cursor not-allowed |
| **Focus** | Keyboard focused | 2px outline ring (module color) |
| **Loading** | Action in progress | Spinner icon, text optional |

### 1.4 Button Specifications

```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline' | 'link';
  size: 'xs' | 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}
```

```css
/* Primary Button */
.btn-primary {
  background: var(--module-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-weight: var(--font-semibold);
  transition: all var(--duration-fast) var(--ease-default);
}

.btn-primary:hover {
  background: var(--module-primary-hover);
}

.btn-primary:active {
  background: var(--module-primary-active);
  transform: scale(0.98);
}

.btn-primary:focus-visible {
  outline: 2px solid var(--module-primary);
  outline-offset: 2px;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Loading State */
.btn-loading {
  position: relative;
  color: transparent;
}

.btn-loading::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
```

---

## 2. Layout System

### 2.1 Grid System

```
Type: Hybrid (12-column + CSS Grid)
- 12-column untuk layout standar
- CSS Grid untuk complex dashboard layouts
```

| Breakpoint | Columns | Gutter | Margin |
|------------|---------|--------|--------|
| Mobile (<768px) | 4 | 16px | 16px |
| Tablet (768-1023px) | 8 | 20px | 24px |
| Desktop (1024-1279px) | 12 | 24px | 32px |
| Wide (1280px+) | 12 | 24px | auto |

### 2.2 Container

```css
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

@media (min-width: 768px) {
  .container {
    padding: 0 var(--space-6);
  }
}

@media (min-width: 1024px) {
  .container {
    padding: 0 var(--space-8);
  }
}
```

### 2.3 Z-Index Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--z-base` | 0 | Default layer |
| `--z-sticky` | 100 | Sticky headers, fixed elements |
| `--z-dropdown` | 200 | Dropdowns, selects |
| `--z-overlay` | 300 | Backdrop overlays |
| `--z-modal` | 400 | Modals, drawers |
| `--z-toast` | 500 | Toast notifications |
| `--z-tooltip` | 600 | Tooltips (always on top) |

```css
:root {
  --z-base: 0;
  --z-sticky: 100;
  --z-dropdown: 200;
  --z-overlay: 300;
  --z-modal: 400;
  --z-toast: 500;
  --z-tooltip: 600;
}
```

---

## 3. Loading States

### 3.1 Spinner

```
Style: Module-colored circle
- Warna mengikuti modul aktif
- Ukuran proporsional dengan context
```

| Size | Dimension | Stroke | Use Case |
|------|-----------|--------|----------|
| **SM** | 16px | 2px | Inline, buttons |
| **MD** | 24px | 2px | Cards, sections |
| **LG** | 32px | 3px | Page loading |
| **XL** | 48px | 3px | Full page overlay |

```css
.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--module-primary-light);
  border-top-color: var(--module-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

### 3.2 Skeleton

```
Style: Shimmer/Wave
- Gradient bergerak dari kiri ke kanan
- Cycle duration: 1.5s
```

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-tertiary) 0%,
    var(--bg-secondary) 50%,
    var(--bg-tertiary) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-sm);
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Skeleton variants */
.skeleton-text {
  height: 16px;
  margin-bottom: 8px;
}

.skeleton-title {
  height: 24px;
  width: 60%;
  margin-bottom: 12px;
}

.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
}

.skeleton-card {
  height: 120px;
  border-radius: var(--radius-md);
}
```

### 3.3 Progress Bar

```
Style: Linear progress with module color
- Determinate: shows percentage
- Indeterminate: continuous animation
```

```typescript
interface ProgressProps {
  value?: number;        // 0-100, undefined = indeterminate
  size?: 'sm' | 'md';    // 4px or 8px height
  showLabel?: boolean;   // Show percentage text
  color?: 'module' | 'success' | 'warning' | 'error';
}
```

```css
.progress-bar {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--module-primary);
  border-radius: var(--radius-full);
  transition: width var(--duration-normal) var(--ease-out);
}

/* Indeterminate */
.progress-indeterminate .progress-fill {
  width: 30%;
  animation: indeterminate 1.5s ease-in-out infinite;
}

@keyframes indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(400%); }
}
```

---

## 4. Avatar

### 4.1 Sizes

| Size | Dimension | Font Size | Use Case |
|------|-----------|-----------|----------|
| **XS** | 20px | 8px | Compact lists, inline mentions |
| **SM** | 28px | 10px | Table rows, comments |
| **MD** | 36px | 12px | Cards, default |
| **LG** | 48px | 16px | Headers, profiles |
| **XL** | 64px | 20px | Profile pages, detail views |

### 4.2 Shapes

| Shape | Use Case | Border Radius |
|-------|----------|---------------|
| **Circle** | People (default) | `--radius-full` |
| **Square** | Companies, entities, rooms | `--radius-md` |

### 4.3 Fallback

```
Priority:
1. Image (if available)
2. Initials (1-2 characters)
3. Default icon (user/building)
```

```typescript
interface AvatarProps {
  src?: string;
  name: string;          // For initials fallback
  size: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  shape?: 'circle' | 'square';
  status?: 'online' | 'offline' | 'busy' | 'away';
}
```

```css
.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--module-primary-muted);
  color: var(--module-primary);
  font-weight: var(--font-semibold);
  overflow: hidden;
}

.avatar-circle {
  border-radius: var(--radius-full);
}

.avatar-square {
  border-radius: var(--radius-md);
}

/* Status indicator */
.avatar-status {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 25%;
  height: 25%;
  border: 2px solid var(--bg-primary);
  border-radius: var(--radius-full);
}

.avatar-status-online { background: var(--semantic-success); }
.avatar-status-offline { background: var(--text-tertiary); }
.avatar-status-busy { background: var(--semantic-error); }
.avatar-status-away { background: var(--semantic-warning); }
```

---

## 5. Tooltip

### 5.1 Style

```
Style: Adaptive
- Light mode: dark background (#1E1E28)
- Dark mode: light background (#F8FAFC)
- Auto-flip positioning
```

### 5.2 Specifications

```typescript
interface TooltipProps {
  content: ReactNode;
  position?: 'top' | 'right' | 'bottom' | 'left';
  delay?: number;        // Default: 300ms
  maxWidth?: number;     // Default: 200px
}
```

```css
.tooltip {
  position: absolute;
  padding: var(--space-2) var(--space-3);
  background: var(--bg-elevated-inverse);
  color: var(--text-inverse);
  font-size: var(--text-sm);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
  max-width: 200px;
  z-index: var(--z-tooltip);
  animation: fadeIn var(--duration-fast) var(--ease-out);
}

/* Arrow */
.tooltip::before {
  content: '';
  position: absolute;
  border: 6px solid transparent;
}

.tooltip-top::before {
  bottom: -12px;
  left: 50%;
  transform: translateX(-50%);
  border-top-color: var(--bg-elevated-inverse);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
```

---

## 6. Tabs

### 6.1 Styles

| Style | Use Case | Visual |
|-------|----------|--------|
| **Underline** | Page navigation (default) | Border bottom on active |
| **Pill** | Filter toggles, segmented control | Background pill on active |

### 6.2 Specifications

```typescript
interface TabsProps {
  items: TabItem[];
  activeKey: string;
  onChange: (key: string) => void;
  variant?: 'underline' | 'pill';
  size?: 'sm' | 'md';
}

interface TabItem {
  key: string;
  label: string;
  icon?: ReactNode;
  badge?: number;
  disabled?: boolean;
}
```

```css
/* Underline Tabs */
.tabs-underline {
  display: flex;
  border-bottom: 1px solid var(--border-default);
}

.tab-underline {
  padding: var(--space-3) var(--space-4);
  color: var(--text-secondary);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all var(--duration-fast);
}

.tab-underline:hover {
  color: var(--text-primary);
}

.tab-underline.active {
  color: var(--module-primary);
  border-bottom-color: var(--module-primary);
}

/* Pill Tabs */
.tabs-pill {
  display: inline-flex;
  background: var(--bg-tertiary);
  padding: var(--space-1);
  border-radius: var(--radius-md);
}

.tab-pill {
  padding: var(--space-2) var(--space-4);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  transition: all var(--duration-fast);
}

.tab-pill.active {
  background: var(--bg-primary);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}
```

---

## 7. Breadcrumb

### 7.1 Style

```
Separator: Slash ( / )
- Simple dan clean
- Clickable except last item
```

```typescript
interface BreadcrumbProps {
  items: BreadcrumbItem[];
  maxItems?: number;     // Collapse middle items if exceeded
}

interface BreadcrumbItem {
  label: string;
  href?: string;         // Last item has no href
  icon?: ReactNode;      // Optional icon (usually only first)
}
```

```css
.breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.breadcrumb-link {
  color: var(--text-secondary);
  text-decoration: none;
}

.breadcrumb-link:hover {
  color: var(--module-primary);
  text-decoration: underline;
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

.breadcrumb-separator {
  color: var(--text-tertiary);
}
```

---

## 8. Pagination

### 8.1 Style

```
Style: Numbered + Info
- Page numbers with prev/next
- "Showing X-Y of Z" info text
```

```typescript
interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  showInfo?: boolean;    // Default: true
  siblingCount?: number; // Pages shown around current (default: 1)
}
```

```css
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.pagination-info {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.pagination-btn {
  min-width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  transition: all var(--duration-fast);
}

.pagination-btn:hover:not(:disabled) {
  border-color: var(--module-primary);
  color: var(--module-primary);
}

.pagination-btn.active {
  background: var(--module-primary);
  border-color: var(--module-primary);
  color: white;
}

.pagination-ellipsis {
  padding: 0 var(--space-2);
  color: var(--text-tertiary);
}
```

---

## 9. Date & Time Picker

### 9.1 Date Picker

```
Style: Calendar + Range + Presets
- Dropdown calendar
- Date range selection support
- Quick presets (Today, Yesterday, Last 7 days, etc.)
```

```typescript
interface DatePickerProps {
  value?: Date | DateRange;
  onChange: (date: Date | DateRange) => void;
  mode?: 'single' | 'range';
  presets?: DatePreset[];
  minDate?: Date;
  maxDate?: Date;
  disabled?: boolean;
}

interface DatePreset {
  label: string;         // "Last 7 days"
  getValue: () => DateRange;
}

const defaultPresets: DatePreset[] = [
  { label: 'Today', getValue: () => ({ start: today, end: today }) },
  { label: 'Yesterday', getValue: () => ({ start: yesterday, end: yesterday }) },
  { label: 'Last 7 days', getValue: () => ({ start: minus7, end: today }) },
  { label: 'Last 30 days', getValue: () => ({ start: minus30, end: today }) },
  { label: 'This month', getValue: () => ({ start: monthStart, end: today }) },
  { label: 'Last month', getValue: () => ({ start: lastMonthStart, end: lastMonthEnd }) },
];
```

```css
.datepicker-dropdown {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: var(--z-dropdown);
}

.datepicker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3);
  border-bottom: 1px solid var(--border-subtle);
}

.datepicker-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: var(--space-1);
  padding: var(--space-3);
}

.datepicker-day {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--duration-fast);
}

.datepicker-day:hover {
  background: var(--module-primary-light);
}

.datepicker-day.selected {
  background: var(--module-primary);
  color: white;
}

.datepicker-day.in-range {
  background: var(--module-primary-light);
}

.datepicker-day.today {
  font-weight: var(--font-bold);
  border: 1px solid var(--module-primary);
}

/* Presets sidebar */
.datepicker-presets {
  width: 140px;
  border-right: 1px solid var(--border-subtle);
  padding: var(--space-2);
}

.datepicker-preset {
  display: block;
  width: 100%;
  padding: var(--space-2) var(--space-3);
  text-align: left;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
}

.datepicker-preset:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}
```

### 9.2 Time Picker

```
Style: Scroll wheel (iOS-style)
- Hour, Minute columns
- Optional AM/PM for 12-hour format
- Scroll to select
```

```typescript
interface TimePickerProps {
  value?: Time;
  onChange: (time: Time) => void;
  format?: '12h' | '24h';
  minuteStep?: 1 | 5 | 10 | 15 | 30;
  disabled?: boolean;
}
```

```css
.timepicker-wheel {
  display: flex;
  height: 200px;
  overflow: hidden;
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
}

.timepicker-column {
  flex: 1;
  overflow-y: auto;
  scroll-snap-type: y mandatory;
  -webkit-overflow-scrolling: touch;
}

.timepicker-option {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-md);
  color: var(--text-tertiary);
  scroll-snap-align: center;
  transition: all var(--duration-fast);
}

.timepicker-option.selected {
  color: var(--text-primary);
  font-weight: var(--font-semibold);
  background: var(--module-primary-light);
}

/* Selection indicator */
.timepicker-indicator {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 40px;
  transform: translateY(-50%);
  border-top: 1px solid var(--border-default);
  border-bottom: 1px solid var(--border-default);
  pointer-events: none;
}
```

---

## 10. File Upload

### 10.1 Style

```
Style: Dropzone + Preview + Progress
- Drag & drop area
- File preview thumbnails
- Upload progress per file
```

```typescript
interface FileUploadProps {
  accept?: string[];           // ['image/*', '.pdf']
  maxSize?: number;            // Bytes
  maxFiles?: number;
  multiple?: boolean;
  onUpload: (files: File[]) => Promise<void>;
  onRemove?: (file: UploadedFile) => void;
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  url?: string;
  progress: number;            // 0-100
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}
```

```css
.dropzone {
  border: 2px dashed var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  text-align: center;
  cursor: pointer;
  transition: all var(--duration-fast);
}

.dropzone:hover,
.dropzone.dragover {
  border-color: var(--module-primary);
  background: var(--module-primary-light);
}

.dropzone-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto var(--space-4);
  color: var(--text-tertiary);
}

.dropzone-text {
  font-size: var(--text-base);
  color: var(--text-secondary);
}

.dropzone-hint {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-top: var(--space-2);
}

/* File preview */
.file-preview {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-top: var(--space-3);
}

.file-thumbnail {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
  object-fit: cover;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.file-progress {
  height: 4px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  margin-top: var(--space-2);
  overflow: hidden;
}

.file-progress-fill {
  height: 100%;
  background: var(--module-primary);
  transition: width var(--duration-normal);
}
```

---

## 11. Charts & Data Visualization

### 11.1 Color Palette

```
Strategy: Categorical + Sequential
- Categorical: untuk pie, bar, line (distinct colors)
- Sequential: untuk heatmap, gradient (single hue scale)
```

#### Categorical Palette (8 colors)

| Index | Color | Hex | Usage |
|-------|-------|-----|-------|
| 1 | Blue | `#3B82F6` | Primary series |
| 2 | Green | `#22C55E` | Secondary series |
| 3 | Orange | `#F97316` | Tertiary series |
| 4 | Purple | `#8B5CF6` | Fourth series |
| 5 | Pink | `#EC4899` | Fifth series |
| 6 | Cyan | `#06B6D4` | Sixth series |
| 7 | Yellow | `#EAB308` | Seventh series |
| 8 | Red | `#EF4444` | Eighth series |

#### Sequential Palette (Module-based)

```css
/* Blue sequence (PMS) */
--chart-seq-1: #DBEAFE;
--chart-seq-2: #BFDBFE;
--chart-seq-3: #93C5FD;
--chart-seq-4: #60A5FA;
--chart-seq-5: #3B82F6;
--chart-seq-6: #2563EB;
--chart-seq-7: #1D4ED8;

/* Dapat diganti berdasarkan module aktif */
```

### 11.2 Chart Guidelines

```typescript
interface ChartConfig {
  colors: string[];              // Use categorical palette
  gridColor: 'var(--border-subtle)';
  textColor: 'var(--text-secondary)';
  fontSize: 12;
  fontFamily: 'var(--font-primary)';
  animation: {
    duration: 300;
    easing: 'ease-out';
  };
}
```

---

## 12. Alerts & Banners

### 12.1 Styles

| Style | Use Case | Position |
|-------|----------|----------|
| **Top Banner** | System-wide alerts | Fixed top, full width |
| **Inline Alert** | Contextual messages | Within content flow |

### 12.2 Variants

| Variant | Icon | Background | Border | Use Case |
|---------|------|------------|--------|----------|
| **Info** | Info circle | `--semantic-info` 10% | `--semantic-info` | General information |
| **Success** | Check circle | `--semantic-success` 10% | `--semantic-success` | Success messages |
| **Warning** | Alert triangle | `--semantic-warning` 10% | `--semantic-warning` | Warnings |
| **Error** | X circle | `--semantic-error` 10% | `--semantic-error` | Errors |
| **Neutral** | Info | `--bg-tertiary` | `--border-default` | Neutral info |
| **Tip** | Lightbulb | `--module-primary` 10% | `--module-primary` | Helpful hints |

```typescript
interface AlertProps {
  variant: 'info' | 'success' | 'warning' | 'error' | 'neutral' | 'tip';
  title?: string;
  children: ReactNode;
  dismissible?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}
```

```css
.alert {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  border-left: 4px solid;
}

.alert-info {
  background: rgba(59, 130, 246, 0.1);
  border-color: var(--semantic-info);
}

.alert-success {
  background: rgba(34, 197, 94, 0.1);
  border-color: var(--semantic-success);
}

.alert-warning {
  background: rgba(245, 158, 11, 0.1);
  border-color: var(--semantic-warning);
}

.alert-error {
  background: rgba(239, 68, 68, 0.1);
  border-color: var(--semantic-error);
}

.alert-tip {
  background: var(--module-primary-light);
  border-color: var(--module-primary);
}

/* Top Banner */
.banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-sticky);
  padding: var(--space-3) var(--space-4);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
}
```

---

## 13. Form Controls

### 13.1 Toggle / Switch

```
Style: iOS-style
- Pill dengan circle slider
- Module color when active
```

```typescript
interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  size?: 'sm' | 'md';
  label?: string;
}
```

```css
.toggle {
  position: relative;
  width: 44px;
  height: 24px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: background var(--duration-fast);
}

.toggle.checked {
  background: var(--module-primary);
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-sm);
  transition: transform var(--duration-fast);
}

.toggle.checked .toggle-thumb {
  transform: translateX(20px);
}

.toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Small variant */
.toggle-sm {
  width: 36px;
  height: 20px;
}

.toggle-sm .toggle-thumb {
  width: 16px;
  height: 16px;
}

.toggle-sm.checked .toggle-thumb {
  transform: translateX(16px);
}
```

### 13.2 Checkbox

```
Style: Rounded square
- Border radius: var(--radius-sm)
- Checkmark icon when checked
```

```css
.checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-default);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--duration-fast);
}

.checkbox:hover {
  border-color: var(--module-primary);
}

.checkbox.checked {
  background: var(--module-primary);
  border-color: var(--module-primary);
}

.checkbox-icon {
  color: white;
  opacity: 0;
  transform: scale(0.5);
  transition: all var(--duration-fast);
}

.checkbox.checked .checkbox-icon {
  opacity: 1;
  transform: scale(1);
}

.checkbox:focus-visible {
  outline: 2px solid var(--module-primary);
  outline-offset: 2px;
}

/* Indeterminate state */
.checkbox.indeterminate {
  background: var(--module-primary);
  border-color: var(--module-primary);
}

.checkbox.indeterminate .checkbox-icon {
  opacity: 1;
  /* Show minus icon instead of check */
}
```

### 13.3 Radio Button

```
Style: Filled circle
- Circle penuh saat selected
- Module color
```

```css
.radio {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-default);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--duration-fast);
}

.radio:hover {
  border-color: var(--module-primary);
}

.radio.checked {
  border-color: var(--module-primary);
}

.radio-dot {
  width: 10px;
  height: 10px;
  background: var(--module-primary);
  border-radius: var(--radius-full);
  opacity: 0;
  transform: scale(0);
  transition: all var(--duration-fast);
}

.radio.checked .radio-dot {
  opacity: 1;
  transform: scale(1);
}

.radio:focus-visible {
  outline: 2px solid var(--module-primary);
  outline-offset: 2px;
}
```

---

## 14. Tags & Chips

### 14.1 Style

```
Style: Outlined
- Border dengan background transparan
- Display only (tidak removable)
```

```typescript
interface TagProps {
  children: ReactNode;
  color?: 'default' | 'module' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md';
}
```

```css
.tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  background: transparent;
}

.tag-md {
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-sm);
}

.tag-module {
  border-color: var(--module-primary);
  color: var(--module-primary);
}

.tag-success {
  border-color: var(--semantic-success);
  color: var(--semantic-success);
}

.tag-warning {
  border-color: var(--semantic-warning);
  color: var(--semantic-warning);
}

.tag-error {
  border-color: var(--semantic-error);
  color: var(--semantic-error);
}
```

---

## 15. Search Input

### 15.1 Style

```
Style: Icon left + Clear button
- Search icon di kiri
- Clear (X) button muncul saat ada teks
```

```typescript
interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onSearch?: (value: string) => void;  // On enter
  debounce?: number;                    // Debounce ms
  size?: 'sm' | 'md';
}
```

```css
.search-input {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: var(--space-3);
  color: var(--text-tertiary);
  pointer-events: none;
}

.search-input input {
  width: 100%;
  height: 44px;
  padding: 0 var(--space-10) 0 var(--space-10);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  background: var(--bg-primary);
  transition: border-color var(--duration-fast);
}

.search-input input:focus {
  outline: none;
  border-color: var(--module-primary);
}

.search-input input::placeholder {
  color: var(--text-tertiary);
}

.search-clear {
  position: absolute;
  right: var(--space-3);
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--duration-fast);
}

.search-input.has-value .search-clear {
  opacity: 1;
}

.search-clear:hover {
  color: var(--text-primary);
}
```

---

## 16. Progress Steps / Stepper

### 16.1 Style

```
Style: Numbered + Label
- Circle dengan nomor
- Label text di bawah
- Connected line between steps
```

### 16.2 States

| State | Circle Style | Label Style |
|-------|--------------|-------------|
| **Pending** | Border only, gray | Gray text |
| **Active** | Solid module color | Bold, primary text |
| **Completed** | Solid module color + check | Primary text |
| **Error** | Solid error color | Error text |
| **Disabled** | Gray, 50% opacity | Gray, 50% opacity |

```typescript
interface StepperProps {
  steps: Step[];
  currentStep: number;
  orientation?: 'horizontal' | 'vertical';
}

interface Step {
  label: string;
  description?: string;
  status?: 'pending' | 'active' | 'completed' | 'error' | 'disabled';
}
```

```css
.stepper {
  display: flex;
  align-items: flex-start;
}

.step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.step-indicator {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  border: 2px solid var(--border-default);
  background: var(--bg-primary);
  color: var(--text-tertiary);
  z-index: 1;
}

.step.active .step-indicator {
  border-color: var(--module-primary);
  background: var(--module-primary);
  color: white;
}

.step.completed .step-indicator {
  border-color: var(--module-primary);
  background: var(--module-primary);
  color: white;
}

.step.error .step-indicator {
  border-color: var(--semantic-error);
  background: var(--semantic-error);
  color: white;
}

.step.disabled .step-indicator {
  opacity: 0.5;
}

.step-label {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  text-align: center;
}

.step.active .step-label {
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

/* Connector line */
.step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 16px;
  left: calc(50% + 20px);
  right: calc(-50% + 20px);
  height: 2px;
  background: var(--border-default);
}

.step.completed:not(:last-child)::after {
  background: var(--module-primary);
}
```

---

## 17. Divider

### 17.1 Style

```
Style: Solid + With label option
- Default: solid line 1px
- Optional: dengan text di tengah
```

```typescript
interface DividerProps {
  label?: string;
  orientation?: 'horizontal' | 'vertical';
}
```

```css
.divider {
  display: flex;
  align-items: center;
  color: var(--text-tertiary);
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-default);
}

.divider:not(.divider-labeled)::after {
  display: none;
}

.divider:not(.divider-labeled)::before {
  flex: none;
  width: 100%;
}

.divider-label {
  padding: 0 var(--space-3);
  font-size: var(--text-sm);
  white-space: nowrap;
}

/* Vertical */
.divider-vertical {
  flex-direction: column;
  height: 100%;
  width: auto;
}

.divider-vertical::before,
.divider-vertical::after {
  width: 1px;
  height: auto;
  flex: 1;
}

.divider-vertical .divider-label {
  padding: var(--space-2) 0;
}
```

---

## 18. Cards

### 18.1 Variants

| Variant | Interactive | Use Case |
|---------|-------------|----------|
| **Static** | No | Display information |
| **Clickable** | Yes (hover effect) | Navigate to detail |
| **Selectable** | Yes (checkbox) | Multi-select items |
| **With Image** | Optional | Media content |
| **Expandable** | Yes (collapse/expand) | Show/hide content |

```typescript
interface CardProps {
  variant?: 'static' | 'clickable' | 'selectable' | 'expandable';
  selected?: boolean;        // For selectable
  expanded?: boolean;        // For expandable
  image?: {
    src: string;
    alt: string;
    position?: 'top' | 'left';
  };
  onClick?: () => void;
  onSelect?: (selected: boolean) => void;
  onExpand?: (expanded: boolean) => void;
}
```

```css
.card {
  background: var(--bg-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.card-clickable {
  cursor: pointer;
  transition: all var(--duration-fast);
}

.card-clickable:hover {
  border-color: var(--module-primary);
  box-shadow: var(--shadow-md);
}

.card-selectable {
  position: relative;
}

.card-selectable.selected {
  border-color: var(--module-primary);
  background: var(--module-primary-light);
}

.card-checkbox {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
}

.card-image {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
}

.card-image-left {
  display: flex;
}

.card-image-left .card-image {
  width: 120px;
  aspect-ratio: 1;
}

.card-content {
  padding: var(--space-4);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  cursor: pointer;
}

.card-expand-icon {
  transition: transform var(--duration-fast);
}

.card-expandable.expanded .card-expand-icon {
  transform: rotate(180deg);
}

.card-body {
  padding: 0 var(--space-4) var(--space-4);
}

.card-expandable:not(.expanded) .card-body {
  display: none;
}
```

---

## 19. Select / Dropdown

### 19.1 Style

```
Style: Searchable + Multi-select
- Custom dropdown (not native)
- Search filter dalam dropdown
- Multi-select dengan chips
```

```typescript
interface SelectProps {
  options: SelectOption[];
  value: string | string[];
  onChange: (value: string | string[]) => void;
  multiple?: boolean;
  searchable?: boolean;
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
}

interface SelectOption {
  value: string;
  label: string;
  icon?: ReactNode;
  disabled?: boolean;
  group?: string;
}
```

```css
.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 44px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  cursor: pointer;
  transition: border-color var(--duration-fast);
}

.select-trigger:hover {
  border-color: var(--text-tertiary);
}

.select-trigger.open {
  border-color: var(--module-primary);
}

.select-value {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
}

.select-placeholder {
  color: var(--text-tertiary);
}

.select-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}

.select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: var(--space-1);
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: var(--z-dropdown);
  max-height: 300px;
  overflow: hidden;
}

.select-search {
  padding: var(--space-2);
  border-bottom: 1px solid var(--border-subtle);
}

.select-search input {
  width: 100%;
  padding: var(--space-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}

.select-options {
  max-height: 240px;
  overflow-y: auto;
  padding: var(--space-1);
}

.select-option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--duration-fast);
}

.select-option:hover {
  background: var(--bg-tertiary);
}

.select-option.selected {
  background: var(--module-primary-light);
  color: var(--module-primary);
}

.select-option.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.select-group-label {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--text-tertiary);
  text-transform: uppercase;
}
```

---

## 20. Textarea

### 20.1 Style

```
Style: Auto-grow + Max + Character count
- Tinggi otomatis menyesuaikan konten
- Max height limit
- Character counter
```

```typescript
interface TextareaProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  maxLength?: number;
  showCount?: boolean;
  minRows?: number;       // Default: 3
  maxRows?: number;       // Default: 10
  disabled?: boolean;
  error?: string;
}
```

```css
.textarea-wrapper {
  position: relative;
}

.textarea {
  width: 100%;
  min-height: 88px;       /* ~3 rows */
  max-height: 280px;      /* ~10 rows */
  padding: var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-family: var(--font-primary);
  font-size: var(--text-base);
  line-height: 1.6;
  resize: none;
  overflow-y: auto;
  transition: border-color var(--duration-fast);
}

.textarea:focus {
  outline: none;
  border-color: var(--module-primary);
}

.textarea.error {
  border-color: var(--semantic-error);
}

.textarea::placeholder {
  color: var(--text-tertiary);
}

.textarea-count {
  position: absolute;
  bottom: var(--space-2);
  right: var(--space-3);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.textarea-count.warning {
  color: var(--semantic-warning);
}

.textarea-count.error {
  color: var(--semantic-error);
}
```

---

## 21. Additional Components

### 21.1 Menu / Dropdown Menu

```
Style: With icons, dividers, keyboard nav
```

```css
.menu {
  min-width: 180px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: var(--space-1);
  z-index: var(--z-dropdown);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--text-primary);
  cursor: pointer;
  transition: background var(--duration-fast);
}

.menu-item:hover,
.menu-item.focused {
  background: var(--bg-tertiary);
}

.menu-item.danger {
  color: var(--semantic-error);
}

.menu-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.menu-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: var(--space-1) 0;
}

.menu-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

.menu-shortcut {
  margin-left: auto;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}
```

### 21.2 Popover

```
Style: Adaptive positioning + arrow
```

```css
.popover {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: var(--z-dropdown);
  animation: fadeIn var(--duration-fast) var(--ease-out);
}

.popover-arrow {
  position: absolute;
  width: 12px;
  height: 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  transform: rotate(45deg);
}

.popover-content {
  padding: var(--space-4);
}
```

### 21.3 Accordion

```
Style: Multiple open allowed + chevron icon
```

```css
.accordion-item {
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-2);
  overflow: hidden;
}

.accordion-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--space-4);
  background: var(--bg-primary);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: background var(--duration-fast);
}

.accordion-trigger:hover {
  background: var(--bg-secondary);
}

.accordion-icon {
  transition: transform var(--duration-fast);
}

.accordion-item.open .accordion-icon {
  transform: rotate(180deg);
}

.accordion-content {
  padding: 0 var(--space-4) var(--space-4);
  display: none;
}

.accordion-item.open .accordion-content {
  display: block;
}
```

### 21.4 Notification Badge

```
Style: Number + dot option
```

```css
.badge-notification {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: var(--semantic-error);
  color: white;
  font-size: 11px;
  font-weight: var(--font-bold);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-dot {
  width: 8px;
  height: 8px;
  background: var(--semantic-error);
  border-radius: var(--radius-full);
  position: absolute;
  top: 0;
  right: 0;
}
```

### 21.5 Data Table Features

```
Features: Sortable, filterable, resizable columns
```

```css
/* Sortable header */
.table-header-sortable {
  cursor: pointer;
  user-select: none;
}

.table-header-sortable:hover {
  background: var(--bg-tertiary);
}

.table-sort-icon {
  margin-left: var(--space-1);
  opacity: 0.3;
}

.table-header-sortable.sorted .table-sort-icon {
  opacity: 1;
  color: var(--module-primary);
}

/* Resizable */
.table-resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  background: transparent;
}

.table-resize-handle:hover,
.table-resize-handle.resizing {
  background: var(--module-primary);
}

/* Filter */
.table-filter-trigger {
  padding: var(--space-1);
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
}

.table-filter-trigger:hover,
.table-filter-trigger.active {
  background: var(--bg-tertiary);
  color: var(--module-primary);
}
```

### 21.6 Sidebar Menu Items

```
Style: With icons, collapsible groups, module highlight
```

```css
.sidebar-menu {
  padding: var(--space-2);
}

.sidebar-group {
  margin-bottom: var(--space-2);
}

.sidebar-group-label {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--duration-fast);
}

.sidebar-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.sidebar-item.active {
  background: var(--module-primary-light);
  color: var(--module-primary);
  border-left: 3px solid var(--module-primary);
  margin-left: -3px;
}

.sidebar-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-badge {
  font-size: var(--text-xs);
  padding: 2px 6px;
  background: var(--semantic-error);
  color: white;
  border-radius: var(--radius-full);
}

/* Collapsible group */
.sidebar-group-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--space-2) var(--space-3);
  cursor: pointer;
}

.sidebar-group-icon {
  transition: transform var(--duration-fast);
}

.sidebar-group.collapsed .sidebar-group-icon {
  transform: rotate(-90deg);
}

.sidebar-group.collapsed .sidebar-group-items {
  display: none;
}

/* Collapsed sidebar (icon only) */
.sidebar.collapsed .sidebar-label,
.sidebar.collapsed .sidebar-group-label,
.sidebar.collapsed .sidebar-badge {
  display: none;
}

.sidebar.collapsed .sidebar-item {
  justify-content: center;
  padding: var(--space-3);
}
```

---

## 22. Component Checklist

### Core Components

- [ ] Button (6 variants, 4 sizes, 6 states)
- [ ] Input (floating label, with icon, search)
- [ ] Textarea (auto-grow, character count)
- [ ] Select (searchable, multi-select)
- [ ] Checkbox (rounded, indeterminate)
- [ ] Radio (filled circle)
- [ ] Toggle (iOS-style)
- [ ] Date Picker (calendar, range, presets)
- [ ] Time Picker (scroll wheel)
- [ ] File Upload (dropzone, preview, progress)

### Feedback Components

- [ ] Spinner (module-colored)
- [ ] Skeleton (shimmer)
- [ ] Progress Bar (determinate, indeterminate)
- [ ] Toast (detailed, with action)
- [ ] Alert (6 variants)
- [ ] Badge (status)
- [ ] Tag (outlined)

### Navigation Components

- [ ] Tabs (underline, pill)
- [ ] Breadcrumb (slash separator)
- [ ] Pagination (numbered, info)
- [ ] Sidebar (collapsible, module-aware)
- [ ] Menu (with icons, keyboard nav)

### Layout Components

- [ ] Card (5 variants)
- [ ] Accordion (multiple open)
- [ ] Divider (with label option)
- [ ] Stepper (5 states)

### Data Components

- [ ] Table (zebra, sortable, filterable, resizable)
- [ ] Avatar (5 sizes, 2 shapes)
- [ ] Tooltip (adaptive)
- [ ] Popover (with arrow)
- [ ] Notification Badge (count, dot)

### Chart Components

- [ ] Line Chart
- [ ] Bar Chart
- [ ] Pie Chart
- [ ] Area Chart
- [ ] Heatmap

---

*Last Updated: 2025-12-12*
*Companion to: [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md)*
