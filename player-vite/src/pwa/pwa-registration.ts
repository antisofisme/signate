/**
 * PWA Registration
 * Handles Service Worker registration, updates, and lifecycle management
 *
 * @features
 * - Register PWA Service Worker
 * - Handle SW updates gracefully
 * - Coordinate with version-checker.ts
 * - Emit events for update notifications
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus, EventNames } from '@shared/events/shared-event-bus';
import { PWA_CONFIG, isPWAEnabled, isServiceWorkerSupported, isSecureContext } from './pwa-config';

/**
 * PWA Registration State
 */
interface PWARegistrationState {
  registered: boolean;
  registration: ServiceWorkerRegistration | null;
  updateAvailable: boolean;
  error: Error | null;
}

/**
 * Global PWA state
 */
const state: PWARegistrationState = {
  registered: false,
  registration: null,
  updateAvailable: false,
  error: null,
};

/**
 * Register the PWA Service Worker
 * @param deviceId - Optional device ID for rollout check
 * @returns Promise<boolean> - true if registration successful
 */
export async function registerPWA(deviceId?: string): Promise<boolean> {
  SharedLogger.log('[PWA] Starting registration check...');

  // Check if PWA is enabled for this device
  if (!isPWAEnabled(deviceId)) {
    SharedLogger.log('[PWA] PWA disabled by config or rollout');
    return false;
  }

  // Check if Service Worker is supported
  if (!isServiceWorkerSupported()) {
    SharedLogger.warn('[PWA] Service Workers not supported');
    return false;
  }

  // Check if running in secure context
  if (!isSecureContext()) {
    SharedLogger.warn('[PWA] Not running in secure context (HTTPS required)');
    return false;
  }

  try {
    SharedLogger.log('[PWA] Registering Service Worker...');

    // Register the service worker
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    });

    state.registration = registration;
    state.registered = true;

    SharedLogger.log('[PWA] Service Worker registered successfully', {
      scope: registration.scope,
      active: !!registration.active,
      waiting: !!registration.waiting,
      installing: !!registration.installing,
    });

    // Set up update handlers
    setupUpdateHandlers(registration);

    // Check for updates periodically
    setupPeriodicUpdateCheck(registration);

    return true;
  } catch (error) {
    state.error = error as Error;
    SharedLogger.error('[PWA] Service Worker registration failed:', error);
    return false;
  }
}

/**
 * Setup handlers for SW updates
 */
function setupUpdateHandlers(registration: ServiceWorkerRegistration): void {
  // Handle installing state
  registration.addEventListener('updatefound', () => {
    const newWorker = registration.installing;

    if (newWorker) {
      SharedLogger.log('[PWA] New Service Worker found, installing...');

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed') {
          if (navigator.serviceWorker.controller) {
            // New SW installed, waiting to activate
            state.updateAvailable = true;
            SharedLogger.log('[PWA] New version available, waiting for activation');

            // Emit event for UI notification
            SharedEventBus.emit(EventNames.PWA_UPDATE_AVAILABLE, {
              registration,
            });

            // Show notification if configured
            if (PWA_CONFIG.UPDATE.SHOW_UPDATE_NOTIFICATION) {
              showUpdateNotification();
            }

            // Auto-update if configured
            if (PWA_CONFIG.UPDATE.REGISTER_TYPE === 'autoUpdate') {
              setTimeout(() => {
                skipWaiting();
              }, PWA_CONFIG.UPDATE.AUTO_UPDATE_DELAY);
            }
          } else {
            // First install, no previous SW
            SharedLogger.log('[PWA] Service Worker installed (first time)');
          }
        }
      });
    }
  });

  // Handle controller change (when new SW takes over)
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    SharedLogger.log('[PWA] New Service Worker activated');
    // The page will reload to use the new SW
  });
}

/**
 * Setup periodic update check
 */
function setupPeriodicUpdateCheck(registration: ServiceWorkerRegistration): void {
  // Check for updates every 30 minutes
  const updateInterval = 30 * 60 * 1000;

  setInterval(() => {
    SharedLogger.log('[PWA] Checking for updates...');
    registration.update().catch((error) => {
      SharedLogger.warn('[PWA] Update check failed:', error);
    });
  }, updateInterval);

  // Also check on visibility change (when tab becomes active)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      registration.update().catch((error) => {
        SharedLogger.warn('[PWA] Update check failed:', error);
      });
    }
  });
}

/**
 * Skip waiting and activate new SW immediately
 * This will cause the page to reload
 */
export function skipWaiting(): void {
  const registration = state.registration;

  if (registration?.waiting) {
    SharedLogger.log('[PWA] Skipping waiting, activating new SW...');
    registration.waiting.postMessage({ type: 'SKIP_WAITING' });
  }
}

/**
 * Show update notification (simple toast-style)
 */
function showUpdateNotification(): void {
  // Use SharedToast if available, otherwise log
  try {
    const { SharedToast } = require('@shared/ui/shared-toast');
    SharedToast.show({
      message: 'Update available! Click to refresh.',
      type: 'info',
      duration: 0, // Persistent
      onClick: () => {
        skipWaiting();
        window.location.reload();
      },
    });
  } catch {
    SharedLogger.log('[PWA] Update available - reload to apply');
  }
}

/**
 * Unregister all service workers
 * Used for factory reset or troubleshooting
 */
export async function unregisterAllSW(): Promise<boolean> {
  try {
    const registrations = await navigator.serviceWorker.getRegistrations();

    for (const registration of registrations) {
      await registration.unregister();
      SharedLogger.log('[PWA] Unregistered SW:', registration.scope);
    }

    state.registered = false;
    state.registration = null;

    return true;
  } catch (error) {
    SharedLogger.error('[PWA] Failed to unregister SWs:', error);
    return false;
  }
}

/**
 * Get current PWA state
 */
export function getPWAState(): PWARegistrationState {
  return { ...state };
}

/**
 * Check if SW is active and controlling the page
 */
export function isControlled(): boolean {
  return !!navigator.serviceWorker.controller;
}

/**
 * Force update check
 */
export async function checkForUpdates(): Promise<void> {
  if (state.registration) {
    await state.registration.update();
  }
}
