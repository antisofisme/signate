/**
 * Global Type Declarations
 *
 * NOTE: All services now use ServiceRegistry instead of window.* globals
 * This file is kept minimal for TypeScript compliance
 */

declare global {
  interface Window {
    // Legacy browser compatibility flags (if needed)
    // All actual services are now in ServiceRegistry
  }
}

export {};
