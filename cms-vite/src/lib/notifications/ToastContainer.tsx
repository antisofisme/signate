/**
 * Toast Container Component
 * Displays toast notifications in the bottom-right corner
 */

import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import { toast } from './toast';

interface ToastItem {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  title?: string;
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    // Subscribe to toast manager
    const unsubscribe = toast.subscribe((toastData) => {
      setToasts(
        toastData.map((t, index) => ({
          id: `${Date.now()}-${index}`,
          type: t.type || 'info',
          message: t.message,
          title: t.title,
        }))
      );
    });

    return unsubscribe;
  }, []);

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5" />;
      case 'error':
        return <XCircle className="w-5 h-5" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5" />;
      case 'info':
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  const getColors = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 dark:bg-green-900 border-green-200 dark:border-green-700 text-green-800 dark:text-green-200';
      case 'error':
        return 'bg-red-50 dark:bg-red-900 border-red-200 dark:border-red-700 text-red-800 dark:text-red-200';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900 border-yellow-200 dark:border-yellow-700 text-yellow-800 dark:text-yellow-200';
      case 'info':
      default:
        return 'bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-700 text-blue-800 dark:text-blue-200';
    }
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-start gap-3 p-4 rounded-lg border shadow-lg max-w-md pointer-events-auto animate-slide-in-right ${getColors(
            toast.type
          )}`}
        >
          <div className="flex-shrink-0 mt-0.5">{getIcon(toast.type)}</div>

          <div className="flex-1 min-w-0">
            {toast.title && (
              <h4 className="font-semibold text-sm mb-1">{toast.title}</h4>
            )}
            <p className="text-sm">{toast.message}</p>
          </div>

          <button
            onClick={() => removeToast(toast.id)}
            className="flex-shrink-0 hover:opacity-70 transition-opacity"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
