/**
 * Menu Media Upload Queue Panel
 * Floating indicator showing upload progress
 * Reports its height to store for toast positioning
 */

import { useEffect, useRef, useCallback } from 'react';
import {
  Upload,
  X,
  Check,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Trash2,
  Loader2,
  FileImage,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useMenuMediaUploadStore, MenuMediaQueueItem } from '@/lib/stores/menuMediaUploadStore';
import { Z_INDEX } from '@/shared/constants/zIndex';

// Format file size
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Get status icon
const getStatusIcon = (status: MenuMediaQueueItem['status']) => {
  switch (status) {
    case 'pending':
      return <FileImage className="w-4 h-4 text-gray-400" />;
    case 'uploading':
      return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
    case 'success':
      return <Check className="w-4 h-4 text-green-500" />;
    case 'error':
      return <AlertCircle className="w-4 h-4 text-red-500" />;
  }
};

export function MenuMediaUploadQueuePanel() {
  const items = useMenuMediaUploadStore((state) => state.items);
  const isMinimized = useMenuMediaUploadStore((state) => state.isMinimized);
  const isProcessing = useMenuMediaUploadStore((state) => state.isProcessing);
  const toggleMinimize = useMenuMediaUploadStore((state) => state.toggleMinimize);
  const removeFromQueue = useMenuMediaUploadStore((state) => state.removeFromQueue);
  const clearCompleted = useMenuMediaUploadStore((state) => state.clearCompleted);
  const clearQueue = useMenuMediaUploadStore((state) => state.clearQueue);
  const getSummary = useMenuMediaUploadStore((state) => state.getSummary);
  const setPanelHeight = useMenuMediaUploadStore((state) => state.setPanelHeight);

  // Refs for measuring panel height
  const minimizedRef = useRef<HTMLDivElement>(null);
  const expandedRef = useRef<HTMLDivElement>(null);

  const summary = getSummary();

  // Measure and report panel height to store
  const measureHeight = useCallback(() => {
    const ref = isMinimized ? minimizedRef : expandedRef;
    if (ref.current) {
      const rect = ref.current.getBoundingClientRect();
      // Include the bottom offset (bottom-6 = 24px)
      const bottomOffset = 24;
      const totalHeight = rect.height + bottomOffset + 8; // +8 for gap between toast and panel
      setPanelHeight(totalHeight);
    }
  }, [isMinimized, setPanelHeight]);

  // Reset height when unmounted
  useEffect(() => {
    return () => {
      setPanelHeight(0);
    };
  }, [setPanelHeight]);

  // Measure height on mount, minimize toggle, and item changes
  useEffect(() => {
    if (items.length > 0) {
      measureHeight();
    }
  }, [measureHeight, items.length, isMinimized]);

  // Use ResizeObserver for dynamic height changes
  useEffect(() => {
    if (items.length === 0) return;

    const ref = isMinimized ? minimizedRef : expandedRef;
    if (!ref.current) return;

    const observer = new ResizeObserver(() => {
      measureHeight();
    });

    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [isMinimized, measureHeight, items.length]);

  // Don't render if no items
  if (items.length === 0) {
    return null;
  }

  // Determine panel state
  const hasUploading = summary.uploading > 0;
  const hasFailures = summary.error > 0;
  const allComplete = summary.total > 0 && summary.success === summary.total;

  // Panel color based on state
  const getHeaderColor = () => {
    if (hasUploading) return 'bg-blue-500';
    if (hasFailures) return 'bg-red-500';
    if (allComplete) return 'bg-green-500';
    return 'bg-gray-600';
  };

  // Minimized badge view
  if (isMinimized) {
    return (
      <div ref={minimizedRef} className="fixed bottom-6 right-6" style={{ zIndex: Z_INDEX.UPLOAD_QUEUE }}>
        <button
          onClick={toggleMinimize}
          className={cn(
            'relative flex items-center justify-center w-14 h-14 rounded-full text-white shadow-2xl',
            'hover:scale-110 transition-all duration-200 ring-4 ring-white/30',
            getHeaderColor()
          )}
          title="Upload Queue"
        >
          {hasUploading ? (
            <Loader2 className="w-6 h-6 animate-spin" />
          ) : (
            <Upload className="w-6 h-6" />
          )}

          {/* Badge count */}
          <span className="absolute -top-1 -right-1 flex items-center justify-center w-6 h-6 text-xs font-bold bg-white text-gray-900 rounded-full shadow">
            {summary.total}
          </span>
        </button>
      </div>
    );
  }

  // Expanded panel
  return (
    <div
      ref={expandedRef}
      className="fixed bottom-6 right-6 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
      style={{ zIndex: Z_INDEX.UPLOAD_QUEUE }}
    >
      {/* Header */}
      <div
        className={cn(
          'flex items-center justify-between px-4 py-3 text-white cursor-pointer',
          getHeaderColor()
        )}
        onClick={toggleMinimize}
      >
        <div className="flex items-center gap-2">
          {hasUploading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : hasFailures ? (
            <AlertCircle className="w-4 h-4" />
          ) : allComplete ? (
            <Check className="w-4 h-4" />
          ) : (
            <Upload className="w-4 h-4" />
          )}
          <span className="font-medium text-sm">
            {hasUploading
              ? `Uploading ${summary.uploading} of ${summary.total}`
              : allComplete
              ? `${summary.success} uploaded`
              : `${summary.total} in queue`}
          </span>
        </div>
        <ChevronDown className="w-4 h-4" />
      </div>

      {/* Progress bar */}
      {hasUploading && (
        <div className="h-1 bg-gray-200 dark:bg-gray-700">
          <div
            className="h-full bg-blue-400 transition-all duration-300"
            style={{
              width: `${((summary.success + summary.uploading * 0.5) / summary.total) * 100}%`,
            }}
          />
        </div>
      )}

      {/* Items list */}
      <div className="max-h-60 overflow-y-auto">
        {items.map((item) => (
          <div
            key={item.id}
            className={cn(
              'flex items-center gap-3 px-4 py-2 border-b border-gray-100 dark:border-gray-700 last:border-0',
              item.status === 'error' && 'bg-red-50 dark:bg-red-900/20',
              item.status === 'success' && 'bg-green-50 dark:bg-green-900/20'
            )}
          >
            {getStatusIcon(item.status)}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {item.file.name}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {item.error || formatFileSize(item.file.size)}
              </p>
            </div>
            {!isProcessing && item.status !== 'uploading' && (
              <button
                onClick={() => removeFromQueue(item.id)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Footer actions */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={clearCompleted}
          disabled={summary.success === 0}
          className="text-xs text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Clear Completed
        </button>
        <button
          onClick={clearQueue}
          disabled={isProcessing}
          className="text-xs text-red-600 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
        >
          <Trash2 className="w-3 h-3" />
          Clear All
        </button>
      </div>
    </div>
  );
}
