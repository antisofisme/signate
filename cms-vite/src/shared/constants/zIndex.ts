/**
 * Z-Index Constants
 * Centralized z-index values for consistent layering across the application
 *
 * Hierarchy (lowest to highest):
 * 1. Base content: 0-10
 * 2. Dropdowns/Popovers: 50
 * 3. Sticky headers: 100
 * 4. Upload Queue Panel: 9000 (persistent, non-blocking)
 * 5. Modals/Dialogs: 9999 (blocks interaction)
 * 6. Toast notifications: 10000 (above everything, temporary)
 */

export const Z_INDEX = {
  // Base layers
  BASE: 0,
  DROPDOWN: 50,
  STICKY_HEADER: 100,

  // Floating panels (persistent, non-blocking)
  UPLOAD_QUEUE: 9000,

  // Blocking layers
  MODAL_BACKDROP: 9998,
  MODAL: 9999,

  // Top-most layers (temporary notifications)
  TOAST: 10000,

  // Absolute maximum (for debugging overlays)
  MAX: 99999,
} as const;

export type ZIndexKey = keyof typeof Z_INDEX;
