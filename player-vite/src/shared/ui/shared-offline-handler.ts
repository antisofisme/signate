/**
 * Shared Offline Handler
 * Monitors network connection and displays offline/online indicators
 *
 * @features
 * - Monitor navigator.onLine status
 * - Show banner when offline
 * - Hide banner when back online
 * - Listen to EventBus CONNECTION_ONLINE/OFFLINE events
 * - Auto-initialize on import
 * - Inject CSS styles dynamically
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus, EventNames } from '@shared/events/shared-event-bus';

/**
 * Shared Offline Handler Class
 * Singleton pattern for network status monitoring
 */
class SharedOfflineHandlerClass {
  private isOnline = navigator.onLine;
  private banner: HTMLElement | null = null;
  private initialized = false;

  /**
   * Initialize offline handler
   */
  init(): void {
    if (this.initialized) {
      SharedLogger.warn('[OfflineHandler] Already initialized');
      return;
    }

    this.initialized = true;

    // Listen to browser events
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);

    // Listen to EventBus events (from connection status monitor)
    SharedEventBus.on(EventNames.CONNECTION_ONLINE, this.handleOnline, 'offline-handler');
    SharedEventBus.on(EventNames.CONNECTION_OFFLINE, this.handleOffline, 'offline-handler');
    SharedEventBus.on(EventNames.CONNECTION_RESTORED, this.handleRestored, 'offline-handler');
    SharedEventBus.on(EventNames.CONNECTION_LOST, this.handleLost, 'offline-handler');

    // Inject styles
    this.injectStyles();

    // Check initial state
    if (!navigator.onLine) {
      this.showOfflineBanner();
    }

    SharedLogger.log('[OfflineHandler] Initialized - Online:', navigator.onLine);
  }

  /**
   * Handle online event
   */
  private handleOnline = (): void => {
    if (this.isOnline) return; // Already online

    this.isOnline = true;
    this.hideOfflineBanner();
    // Toast disabled - status shown via connection status icons
    SharedLogger.log('[OfflineHandler] Connection online');
  };

  /**
   * Handle offline event
   */
  private handleOffline = (): void => {
    if (!this.isOnline) return; // Already offline

    this.isOnline = false;
    this.showOfflineBanner();
    // Toast disabled - status shown via connection status icons
    SharedLogger.warn('[OfflineHandler] Connection offline');
  };

  /**
   * Handle connection restored (after being lost)
   */
  private handleRestored = (): void => {
    this.handleOnline();
    // Toast disabled - status shown via connection status icons
  };

  /**
   * Handle connection lost (while online)
   */
  private handleLost = (): void => {
    this.handleOffline();
    // Toast disabled - status shown via connection status icons
  };

  /**
   * Show offline banner
   * DISABLED - Status already shown via connection status icons
   */
  private showOfflineBanner(): void {
    // Banner disabled - we use connection status icons instead
    SharedLogger.log('[OfflineHandler] Offline detected (banner disabled, using status icons)');
  }

  /**
   * Hide offline banner
   */
  private hideOfflineBanner(): void {
    if (!this.banner) return;

    this.banner.classList.remove('offline-banner-show');
    this.banner.classList.add('offline-banner-hide');

    setTimeout(() => {
      this.banner?.remove();
      this.banner = null;
    }, 300);

    SharedLogger.log('[OfflineHandler] Banner hidden');
  }

  /**
   * Get current online status
   */
  getStatus(): boolean {
    return this.isOnline;
  }

  /**
   * Manually trigger offline state (for testing)
   */
  simulateOffline(): void {
    SharedLogger.warn('[OfflineHandler] Simulating offline mode');
    this.handleOffline();
  }

  /**
   * Manually trigger online state (for testing)
   */
  simulateOnline(): void {
    SharedLogger.log('[OfflineHandler] Simulating online mode');
    this.handleOnline();
  }

  /**
   * Inject CSS styles
   */
  private injectStyles(): void {
    if (document.getElementById('shared-offline-handler-styles')) return;

    const style = document.createElement('style');
    style.id = 'shared-offline-handler-styles';
    style.textContent = `
      .offline-banner {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 9999;
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        color: white;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        transform: translateY(-100%);
        transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
      }

      .offline-banner-show {
        transform: translateY(0);
      }

      .offline-banner-hide {
        transform: translateY(-100%);
      }

      .offline-banner-content {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px 24px;
        max-width: 1200px;
        margin: 0 auto;
      }

      .offline-icon {
        font-size: 32px;
        animation: offline-pulse 2s infinite;
      }

      @keyframes offline-pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.1); }
      }

      .offline-text {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .offline-text strong {
        font-size: 16px;
        font-weight: 600;
      }

      .offline-text span {
        font-size: 14px;
        opacity: 0.9;
      }

      .offline-dismiss {
        background: none;
        border: none;
        color: white;
        font-size: 28px;
        cursor: pointer;
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: background 0.2s;
      }

      .offline-dismiss:hover {
        background: rgba(255, 255, 255, 0.2);
      }

      /* Responsive */
      @media (max-width: 768px) {
        .offline-banner-content {
          padding: 12px 16px;
        }

        .offline-icon {
          font-size: 24px;
        }

        .offline-text strong {
          font-size: 14px;
        }

        .offline-text span {
          font-size: 12px;
        }
      }

      /* TV remote focus */
      .offline-dismiss:focus {
        outline: 2px solid white;
        outline-offset: 2px;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Cleanup event listeners
   */
  destroy(): void {
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
    SharedEventBus.removeNamespace('offline-handler');
    this.hideOfflineBanner();
    this.initialized = false;
    SharedLogger.log('[OfflineHandler] Destroyed');
  }
}

// Export singleton instance
export const SharedOfflineHandler = new SharedOfflineHandlerClass();

// Make available globally for compatibility
declare global {
  interface Window {
    SharedOfflineHandler: typeof SharedOfflineHandler;
  }
}

if (typeof window !== 'undefined') {
  window.SharedOfflineHandler = SharedOfflineHandler;
}

// Auto-initialize when module is imported
SharedOfflineHandler.init();
