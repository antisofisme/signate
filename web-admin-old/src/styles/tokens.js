/**
 * Design Tokens - Centralized Design System
 *
 * This file contains all design tokens (colors, spacing, typography)
 * that will be used throughout the application.
 *
 * Usage:
 * import { colors, spacing, typography } from '@/styles/tokens'
 */

// =============================================================================
// COLOR TOKENS
// =============================================================================

export const colors = {
  // Primary Brand Color (Blue)
  primary: {
    50: '#EFF6FF',
    100: '#DBEAFE',
    200: '#BFDBFE',
    300: '#93C5FD',
    400: '#60A5FA',
    500: '#3B82F6',
    600: '#2563EB',   // Main brand color
    700: '#1D4ED8',
    800: '#1E40AF',
    900: '#1E3A8A',
  },

  // Success State (Green)
  success: {
    50: '#F0FDF4',
    100: '#DCFCE7',
    200: '#BBF7D0',
    300: '#86EFAC',
    400: '#4ADE80',
    500: '#22C55E',
    600: '#16A34A',   // Main success color
    700: '#15803D',
    800: '#166534',
    900: '#14532D',
  },

  // Warning State (Yellow/Orange)
  warning: {
    50: '#FFFBEB',
    100: '#FEF3C7',
    200: '#FDE68A',
    300: '#FCD34D',
    400: '#FBBF24',
    500: '#F59E0B',
    600: '#D97706',   // Main warning color
    700: '#B45309',
    800: '#92400E',
    900: '#78350F',
  },

  // Danger/Error State (Red)
  danger: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    200: '#FECACA',
    300: '#FCA5A5',
    400: '#F87171',
    500: '#EF4444',
    600: '#DC2626',   // Main danger color
    700: '#B91C1C',
    800: '#991B1B',
    900: '#7F1D1D',
  },

  // Info State (Blue - lighter than primary)
  info: {
    50: '#F0F9FF',
    100: '#E0F2FE',
    200: '#BAE6FD',
    300: '#7DD3FC',
    400: '#38BDF8',
    500: '#0EA5E9',
    600: '#0284C7',   // Main info color
    700: '#0369A1',
    800: '#075985',
    900: '#0C4A6E',
  },

  // Neutral/Gray Scale
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
  },
}

// =============================================================================
// SEMANTIC COLOR MAPPING
// =============================================================================

// Map semantic meanings to colors for easier usage
export const semanticColors = {
  // Backgrounds
  bgPrimary: 'bg-white',
  bgSecondary: 'bg-gray-50',
  bgTertiary: 'bg-gray-100',

  // Text
  textPrimary: 'text-gray-900',
  textSecondary: 'text-gray-600',
  textTertiary: 'text-gray-500',
  textDisabled: 'text-gray-400',

  // Borders
  borderLight: 'border-gray-200',
  borderMedium: 'border-gray-300',
  borderDark: 'border-gray-400',

  // Interactive
  interactive: 'text-primary-600 hover:text-primary-700',
  interactiveBg: 'bg-primary-600 hover:bg-primary-700',
}

// =============================================================================
// STATUS COLOR MAPPING
// =============================================================================

export const statusColors = {
  active: {
    bg: 'bg-success-100 dark:bg-success-900/30',
    text: 'text-success-700 dark:text-success-400',
    border: 'border-success-200 dark:border-success-600',
    badge: 'success',
    dot: 'bg-success-600',
  },
  pending: {
    bg: 'bg-warning-100 dark:bg-warning-900/30',
    text: 'text-warning-700 dark:text-warning-400',
    border: 'border-warning-200 dark:border-warning-600',
    badge: 'warning',
    dot: 'bg-warning-600',
  },
  inactive: {
    bg: 'bg-gray-100 dark:bg-gray-700',
    text: 'text-gray-700 dark:text-gray-300',
    border: 'border-gray-200 dark:border-gray-600',
    badge: 'gray',
    dot: 'bg-gray-400',
  },
  online: {
    bg: 'bg-success-100 dark:bg-success-900/30',
    text: 'text-success-700 dark:text-success-400',
    border: 'border-success-200 dark:border-success-600',
    badge: 'success',
    dot: 'bg-success-600',
  },
  offline: {
    bg: 'bg-gray-100 dark:bg-gray-700',
    text: 'text-gray-700 dark:text-gray-300',
    border: 'border-gray-200 dark:border-gray-600',
    badge: 'gray',
    dot: 'bg-gray-400',
  },
  error: {
    bg: 'bg-danger-100 dark:bg-danger-900/30',
    text: 'text-danger-700 dark:text-danger-400',
    border: 'border-danger-200 dark:border-danger-600',
    badge: 'danger',
    dot: 'bg-danger-600',
  },
}

// =============================================================================
// SPACING TOKENS
// =============================================================================

export const spacing = {
  // Spacing scale (in rem)
  xs: '0.25rem',    // 4px  - Tight spacing (icon margins, button icon gaps)
  sm: '0.5rem',     // 8px  - Small gaps (button groups, chip spacing)
  md: '1rem',       // 16px - Default spacing (card padding, form fields)
  lg: '1.5rem',     // 24px - Large spacing (section margins, card gaps)
  xl: '2rem',       // 32px - Extra large (page padding, major sections)
  '2xl': '3rem',    // 48px - Section separators
  '3xl': '4rem',    // 64px - Large section separators
}

// Semantic spacing for specific use cases
export const layout = {
  // Page-level spacing
  pageContent: 'p-8',           // xl spacing for page wrapper
  pageContentY: 'py-8',         // Vertical page padding
  pageContentX: 'px-8',         // Horizontal page padding

  // Section spacing
  section: 'mb-6',              // lg spacing between sections
  sectionGap: 'gap-6',          // lg gap for section grids

  // Card spacing
  cardPadding: 'p-6',           // lg spacing for card content
  cardGap: 'gap-4',             // md gap between cards

  // Form spacing
  formGroup: 'space-y-4',       // md spacing between form groups
  formField: 'mb-4',            // md spacing after each field
  formLabel: 'mb-1',            // xs spacing after labels

  // Button spacing
  buttonGroup: 'gap-2',         // sm spacing in button groups
  buttonContent: 'gap-2',       // sm spacing between button icon and text

  // Grid spacing
  gridGap: 'gap-4',             // md spacing for content grids
  gridGapLarge: 'gap-6',        // lg spacing for feature grids
}

// =============================================================================
// TYPOGRAPHY TOKENS
// =============================================================================

export const typography = {
  // Font sizes (matching Tailwind)
  sizes: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '1rem',       // 16px (default)
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '1.875rem',  // 30px
    '4xl': '2.25rem',   // 36px
  },

  // Font weights
  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // Line heights
  lineHeights: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },

  // Heading styles (pre-composed)
  headings: {
    h1: 'text-3xl font-bold leading-tight',           // Page titles
    h2: 'text-2xl font-bold leading-tight',           // Section titles
    h3: 'text-xl font-semibold leading-normal',       // Modal titles, card headers
    h4: 'text-lg font-semibold leading-normal',       // Subsection titles
    h5: 'text-base font-semibold leading-normal',     // Minor headings
    h6: 'text-sm font-semibold leading-normal',       // Tiny headings
  },

  // Body text styles
  body: {
    large: 'text-lg font-normal leading-relaxed',
    default: 'text-base font-normal leading-normal',
    small: 'text-sm font-normal leading-normal',
    tiny: 'text-xs font-normal leading-normal',
  },

  // Special text styles
  label: 'text-sm font-medium text-gray-700',         // Form labels
  caption: 'text-xs text-gray-500',                   // Small descriptive text
  overline: 'text-xs font-semibold uppercase tracking-wide text-gray-600',
}

// =============================================================================
// BORDER RADIUS TOKENS
// =============================================================================

export const radius = {
  none: '0',
  sm: '0.125rem',     // 2px
  default: '0.25rem', // 4px
  md: '0.375rem',     // 6px
  lg: '0.5rem',       // 8px
  xl: '0.75rem',      // 12px
  '2xl': '1rem',      // 16px
  '3xl': '1.5rem',    // 24px
  full: '9999px',     // Fully rounded
}

// Semantic border radius
export const componentRadius = {
  button: 'rounded-lg',         // 8px
  input: 'rounded-lg',          // 8px
  card: 'rounded-xl',           // 12px
  modal: 'rounded-2xl',         // 16px
  badge: 'rounded-full',        // Fully rounded
  avatar: 'rounded-full',       // Fully rounded
}

// =============================================================================
// SHADOW TOKENS
// =============================================================================

export const shadows = {
  // Matching Tailwind shadows
  sm: 'shadow-sm',              // Subtle shadow
  default: 'shadow',            // Default shadow
  md: 'shadow-md',              // Medium shadow
  lg: 'shadow-lg',              // Large shadow
  xl: 'shadow-xl',              // Extra large shadow
  '2xl': 'shadow-2xl',          // Huge shadow
  inner: 'shadow-inner',        // Inset shadow
  none: 'shadow-none',          // No shadow
}

// Semantic shadow usage
export const componentShadows = {
  card: 'shadow-md hover:shadow-lg',
  cardHover: 'shadow-lg hover:shadow-xl',
  modal: 'shadow-2xl',
  dropdown: 'shadow-lg',
  button: 'shadow-sm hover:shadow-md',
}

// =============================================================================
// ICON SIZE TOKENS
// =============================================================================

export const iconSizes = {
  xs: 'w-3 h-3',      // 12px - Very small icons
  sm: 'w-4 h-4',      // 16px - Inline with text
  default: 'w-5 h-5', // 20px - Default UI icons
  md: 'w-6 h-6',      // 24px - Prominent icons
  lg: 'w-8 h-8',      // 32px - Large buttons, feature icons
  xl: 'w-12 h-12',    // 48px - Hero icons
  '2xl': 'w-16 h-16', // 64px - Empty states, large features
  '3xl': 'w-20 h-20', // 80px - Extra large illustrations
}

// Semantic icon size usage
export const iconUsage = {
  buttonIcon: iconSizes.sm,           // Icons inside buttons
  headerIcon: iconSizes.default,      // Icons in headers/titles
  tableIcon: iconSizes.sm,            // Icons in table cells
  cardIcon: iconSizes.md,             // Icons in card headers
  navIcon: iconSizes.md,              // Navigation icons
  emptyStateIcon: iconSizes['2xl'],   // Large icons for empty states
  featureIcon: iconSizes.xl,          // Feature highlight icons
}

// =============================================================================
// TRANSITION & ANIMATION
// =============================================================================

export const transitions = {
  // Duration
  fast: 'duration-150',
  default: 'duration-200',
  slow: 'duration-300',
  slower: 'duration-500',

  // Easing
  easeIn: 'ease-in',
  easeOut: 'ease-out',
  easeInOut: 'ease-in-out',
  linear: 'linear',

  // Pre-composed transitions
  all: 'transition-all duration-200 ease-in-out',
  colors: 'transition-colors duration-200 ease-in-out',
  transform: 'transition-transform duration-200 ease-in-out',
  opacity: 'transition-opacity duration-200 ease-in-out',
  shadow: 'transition-shadow duration-200 ease-in-out',
}

// =============================================================================
// Z-INDEX SCALE
// =============================================================================

export const zIndex = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  fixed: 30,
  modalBackdrop: 40,
  modal: 50,
  popover: 60,
  tooltip: 70,
}

// =============================================================================
// BREAKPOINT HELPERS (for reference)
// =============================================================================

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
}

// =============================================================================
// EXPORTS FOR EASY USAGE
// =============================================================================

// Default export with all tokens
export default {
  colors,
  semanticColors,
  statusColors,
  spacing,
  layout,
  typography,
  radius,
  componentRadius,
  shadows,
  componentShadows,
  iconSizes,
  iconUsage,
  transitions,
  zIndex,
  breakpoints,
}
