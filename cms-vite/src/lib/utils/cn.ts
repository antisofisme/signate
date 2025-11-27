/**
 * Tailwind CSS Class Name Merger
 *
 * Combines clsx and tailwind-merge for better class composition
 *
 * Usage:
 *   cn("px-2 py-1", "bg-blue-500", { "text-white": isActive })
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ============================================================================
// Focus State Utilities
// ============================================================================
// Standardized focus states for consistent keyboard navigation and accessibility

/**
 * Base focus ring styles (without color)
 * Use with focusRing* variants for specific colors
 */
export const focusBase = 'focus:outline-none focus:ring-2 focus:ring-offset-2';

/**
 * Focus ring color variants
 * Combines base focus styles with specific ring colors
 */
export const focusRing = {
  /** Default blue focus ring - primary actions */
  primary: `${focusBase} focus:ring-blue-500`,
  /** Red focus ring - destructive/danger actions */
  danger: `${focusBase} focus:ring-red-500`,
  /** Green focus ring - success/confirm actions */
  success: `${focusBase} focus:ring-green-500`,
  /** Orange focus ring - warning actions */
  warning: `${focusBase} focus:ring-orange-500`,
  /** Purple focus ring - special/highlight actions */
  purple: `${focusBase} focus:ring-purple-500`,
  /** Gray focus ring - neutral/secondary actions */
  secondary: `${focusBase} focus:ring-gray-400`,
} as const;

/**
 * Focus visible variants (only show on keyboard navigation)
 * Better for interactive elements that shouldn't show focus on click
 */
export const focusVisible = {
  primary: 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500',
  danger: 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-red-500',
  success: 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-green-500',
  secondary: 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-gray-400',
} as const;

/**
 * Focus within variants (for container elements)
 * Shows focus ring when any child element is focused
 */
export const focusWithin = {
  primary: 'focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500',
  danger: 'focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-red-500',
} as const;

// ============================================================================
// Interactive Element Utilities
// ============================================================================

/**
 * Standard interactive button styles
 * Includes disabled state handling
 */
export const interactiveStyles = {
  /** Base interactive styles without color */
  base: 'transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
  /** Button with primary focus */
  button: `transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${focusRing.primary}`,
  /** Danger button */
  buttonDanger: `transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${focusRing.danger}`,
  /** Icon button (smaller hit area) */
  iconButton: `p-2 rounded-lg transition-colors ${focusRing.primary}`,
  /** Link style */
  link: `${focusRing.primary} rounded`,
} as const;
