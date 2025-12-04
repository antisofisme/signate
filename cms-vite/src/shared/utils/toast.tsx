/**
 * Custom Toast Utility with Copy Button
 *
 * Wraps Sonner toast to add copy-to-clipboard functionality
 */

import { toast as sonnerToast, ExternalToast } from 'sonner';
import { Copy, Check } from 'lucide-react';
import { useState } from 'react';

/**
 * Copy button component for toast messages
 */
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="ml-2 p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors flex-shrink-0"
      title="Copy message"
    >
      {copied ? (
        <Check className="w-3.5 h-3.5 text-green-500" />
      ) : (
        <Copy className="w-3.5 h-3.5 opacity-50 hover:opacity-100" />
      )}
    </button>
  );
}

/**
 * Toast content wrapper with copy button
 */
function ToastContent({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-between gap-2 w-full">
      <span className="flex-1">{message}</span>
      <CopyButton text={message} />
    </div>
  );
}

/**
 * Custom toast functions with copy button
 */
export const toast = {
  success: (message: string, options?: ExternalToast) => {
    return sonnerToast.success(<ToastContent message={message} />, options);
  },

  error: (message: string, options?: ExternalToast) => {
    return sonnerToast.error(<ToastContent message={message} />, options);
  },

  warning: (message: string, options?: ExternalToast) => {
    return sonnerToast.warning(<ToastContent message={message} />, options);
  },

  info: (message: string, options?: ExternalToast) => {
    return sonnerToast.info(<ToastContent message={message} />, options);
  },

  loading: (message: string, options?: ExternalToast) => {
    return sonnerToast.loading(<ToastContent message={message} />, options);
  },

  // For promise-based toasts (loading -> success/error)
  promise: sonnerToast.promise,

  // Dismiss toast
  dismiss: sonnerToast.dismiss,

  // Custom toast (for advanced use cases)
  custom: sonnerToast.custom,

  // Message toast (default)
  message: (message: string, options?: ExternalToast) => {
    return sonnerToast(<ToastContent message={message} />, options);
  },
};

export default toast;
