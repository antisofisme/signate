/**
 * Shared Toast Notification System
 * Displays temporary notification messages to users
 *
 * @features
 * - Multiple toast types (success, error, warning, info)
 * - Auto-dismiss after duration
 * - Stack multiple toasts vertically
 * - Programmatic dismiss
 * - Inject CSS styles dynamically
 * - Position: top-right corner
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus, EventNames } from '@shared/events/shared-event-bus';
import { ServiceRegistry } from '@shared/services/service-registry';

/**
 * Toast notification types
 */
export type ToastType = 'success' | 'error' | 'warning' | 'info';

/**
 * Toast notification options
 */
export interface ToastOptions {
  message: string;
  type?: ToastType;
  duration?: number; // milliseconds, 0 = no auto-dismiss
  dismissible?: boolean; // show close button
}

/**
 * Toast instance interface
 */
interface ToastInstance {
  id: string;
  element: HTMLElement;
  timeout?: number;
}

/**
 * Toast type configuration
 */
const TOAST_CONFIG: Record<ToastType, { icon: string; color: string; bgColor: string }> = {
  success: {
    icon: '✓',
    color: '#155724',
    bgColor: '#d4edda',
  },
  error: {
    icon: '✕',
    color: '#721c24',
    bgColor: '#f8d7da',
  },
  warning: {
    icon: '⚠',
    color: '#856404',
    bgColor: '#fff3cd',
  },
  info: {
    icon: 'ℹ',
    color: '#004085',
    bgColor: '#d1ecf1',
  },
};

/**
 * Shared Toast Class
 * Singleton pattern for global toast notifications
 */
class SharedToastClass {
  private toasts: Map<string, ToastInstance> = new Map();
  private container: HTMLElement | null = null;
  private toastCounter = 0;

  /**
   * Initialize toast container
   */
  private initContainer(): void {
    if (this.container) return;

    try {
      if (!document.body) {
        SharedLogger.error('[Toast] document.body not available - cannot initialize');
        return;
      }

      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);

      // Verify container was added to DOM
      if (!document.getElementById('toast-container')) {
        SharedLogger.error('[Toast] Container creation failed - element not in DOM');
        this.container = null;
        return;
      }

      this.injectStyles();
      SharedLogger.log('[Toast] ✅ Container initialized successfully');
    } catch (error) {
      SharedLogger.error('[Toast] ❌ Failed to initialize container:', error);
      this.container = null;
    }
  }

  /**
   * Public init method - call at app startup to pre-initialize container
   */
  public init(): void {
    SharedLogger.log('[Toast] Initializing SharedToast...');
    this.initContainer();
  }

  /**
   * Show a toast notification
   */
  show(message: string, type: ToastType = 'info', duration = 3000): string {
    return this.showToast({ message, type, duration, dismissible: true });
  }

  /**
   * Show success toast
   */
  success(message: string, duration = 3000): string {
    return this.show(message, 'success', duration);
  }

  /**
   * Show error toast
   */
  error(message: string, duration = 5000): string {
    return this.show(message, 'error', duration);
  }

  /**
   * Show warning toast
   */
  warning(message: string, duration = 4000): string {
    return this.show(message, 'warning', duration);
  }

  /**
   * Show info toast
   */
  info(message: string, duration = 3000): string {
    return this.show(message, 'info', duration);
  }

  /**
   * Show toast with full options
   */
  showToast(options: ToastOptions): string {
    this.initContainer();

    const { message, type = 'info', duration = 3000, dismissible = true } = options;

    const id = `toast-${++this.toastCounter}`;
    const config = TOAST_CONFIG[type];

    // Create toast element
    const toast = document.createElement('div');
    toast.id = id;
    toast.className = `toast toast-${type}`;
    toast.style.borderLeftColor = config.color;
    toast.innerHTML = `
      <div class="toast-icon" style="color: ${config.color}">
        ${config.icon}
      </div>
      <div class="toast-message">${this.escapeHtml(message)}</div>
      ${dismissible ? '<button class="toast-close">&times;</button>' : ''}
    `;

    // Add event listeners
    if (dismissible) {
      const closeBtn = toast.querySelector('.toast-close');
      closeBtn?.addEventListener('click', () => this.dismiss(id));
    }

    // Add click to dismiss
    toast.addEventListener('click', () => {
      if (dismissible) this.dismiss(id);
    });

    // Append to container
    this.container?.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
      toast.classList.add('toast-show');
    });

    // Auto-dismiss after duration
    let timeout: number | undefined;
    if (duration > 0) {
      timeout = window.setTimeout(() => {
        this.dismiss(id);
      }, duration);
    }

    // Store toast instance
    this.toasts.set(id, { id, element: toast, timeout });

    // Emit event
    SharedEventBus.emit(EventNames.UI_TOAST_SHOW, { id, message, type, duration });
    SharedLogger.log(`[Toast] Showing ${type} toast:`, message);

    return id;
  }

  /**
   * Dismiss a specific toast
   */
  dismiss(id: string): void {
    const toast = this.toasts.get(id);
    if (!toast) return;

    // Clear timeout
    if (toast.timeout) {
      clearTimeout(toast.timeout);
    }

    // Animate out
    toast.element.classList.remove('toast-show');
    toast.element.classList.add('toast-hide');

    // Remove from DOM after animation
    setTimeout(() => {
      toast.element.remove();
      this.toasts.delete(id);
      SharedLogger.log('[Toast] Dismissed:', id);
    }, 300);
  }

  /**
   * Dismiss all toasts
   */
  dismissAll(): void {
    this.toasts.forEach((_, id) => this.dismiss(id));
    SharedLogger.log('[Toast] Dismissed all toasts');
  }

  /**
   * Get active toast count
   */
  getActiveCount(): number {
    return this.toasts.size;
  }

  /**
   * Escape HTML to prevent XSS
   */
  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Inject CSS styles
   */
  private injectStyles(): void {
    if (document.getElementById('shared-toast-styles')) return;

    const style = document.createElement('style');
    style.id = 'shared-toast-styles';
    style.textContent = `
      .toast-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 200000;
        display: flex;
        flex-direction: column-reverse;
        gap: 12px;
        max-width: 420px;
        pointer-events: none;
      }

      .toast {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        border-left: 4px solid;
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        opacity: 0;
        transform: translateY(120%);
        transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        cursor: pointer;
        pointer-events: auto;
        min-width: 300px;
      }

      .toast-show {
        opacity: 1;
        transform: translateY(0);
      }

      .toast-hide {
        opacity: 0;
        transform: translateY(120%);
      }

      .toast-icon {
        font-size: 20px;
        font-weight: bold;
        flex-shrink: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.1);
      }

      .toast-message {
        flex: 1;
        font-size: 14px;
        line-height: 1.5;
        color: rgba(255, 255, 255, 0.95);
        word-wrap: break-word;
      }

      .toast-close {
        background: none;
        border: none;
        font-size: 24px;
        color: rgba(255, 255, 255, 0.5);
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        transition: color 0.2s;
      }

      .toast-close:hover {
        color: rgba(255, 255, 255, 0.9);
      }

      .toast-success {
        border-left-color: #22c55e;
      }

      .toast-success .toast-icon {
        color: #22c55e;
      }

      .toast-error {
        border-left-color: #ef4444;
      }

      .toast-error .toast-icon {
        color: #ef4444;
      }

      .toast-warning {
        border-left-color: #f59e0b;
      }

      .toast-warning .toast-icon {
        color: #f59e0b;
      }

      .toast-info {
        border-left-color: #3b82f6;
      }

      .toast-info .toast-icon {
        color: #3b82f6;
      }

      /* Responsive */
      @media (max-width: 768px) {
        .toast-container {
          bottom: 10px;
          right: 10px;
          left: 10px;
          max-width: none;
        }

        .toast {
          min-width: auto;
        }
      }

      /* Animation for TV remote */
      @keyframes toast-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
      }

      .toast:focus {
        outline: 2px solid #4CAF50;
        animation: toast-pulse 0.5s;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Cleanup all toasts and remove container
   */
  destroy(): void {
    this.dismissAll();
    this.container?.remove();
    this.container = null;
    SharedLogger.log('[Toast] Destroyed');
  }
}

// Export singleton instance
export const SharedToast = new SharedToastClass();

// Make available globally for compatibility
declare global {
  interface Window {
    SharedToast: typeof SharedToast;
  }
}

if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('SharedToast', SharedToast);
}
