/**
 * Toast Notification System
 * Simple toast notifications (can be replaced with react-toastify or sonner later)
 */

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastOptions {
  title?: string;
  message: string;
  type?: ToastType;
  duration?: number;
}

class ToastManager {
  private toasts: Map<string, ToastOptions> = new Map();
  private listeners: Set<(toasts: ToastOptions[]) => void> = new Set();

  show(options: ToastOptions) {
    const id = Date.now().toString();
    const toast = {
      ...options,
      type: options.type || 'info',
      duration: options.duration || 3000,
    };

    this.toasts.set(id, toast);
    this.notifyListeners();

    // Auto remove after duration
    setTimeout(() => {
      this.toasts.delete(id);
      this.notifyListeners();
    }, toast.duration);
  }

  success(message: string, title?: string) {
    this.show({ message, title, type: 'success' });
  }

  error(message: string, title?: string) {
    this.show({ message, title, type: 'error', duration: 5000 });
  }

  warning(message: string, title?: string) {
    this.show({ message, title, type: 'warning' });
  }

  info(message: string, title?: string) {
    this.show({ message, title, type: 'info' });
  }

  subscribe(listener: (toasts: ToastOptions[]) => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners() {
    const toastArray = Array.from(this.toasts.values());
    this.listeners.forEach((listener) => listener(toastArray));
  }
}

export const toast = new ToastManager();

// React hook for toast notifications
export function useToast() {
  return {
    success: toast.success.bind(toast),
    error: toast.error.bind(toast),
    warning: toast.warning.bind(toast),
    info: toast.info.bind(toast),
  };
}
