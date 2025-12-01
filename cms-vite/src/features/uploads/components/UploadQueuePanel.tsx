/**
 * UploadQueuePanel Component
 *
 * Fixed panel at bottom-right showing upload queue status
 * Reports its height to store for toast positioning
 */

import { useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ChevronDown,
  ChevronUp,
  Upload,
  X,
  RotateCcw,
  Trash2,
  Check,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { UploadList } from './UploadList';
import { useUploadQueueStore } from '@/lib/stores/uploadQueueStore';
import { useUploadProcessor } from '../hooks/useUploadProcessor';
import { Z_INDEX } from '@/shared/constants/zIndex';

export function UploadQueuePanel() {
  const { t } = useTranslation();

  // Use individual selectors to ensure reactivity
  const items = useUploadQueueStore((state) => state.items);
  const isMinimized = useUploadQueueStore((state) => state.isMinimized);
  const toggleMinimize = useUploadQueueStore((state) => state.toggleMinimize);
  const getSummary = useUploadQueueStore((state) => state.getSummary);
  const clearCompleted = useUploadQueueStore((state) => state.clearCompleted);
  const retryAllFailed = useUploadQueueStore((state) => state.retryAllFailed);
  const clearAll = useUploadQueueStore((state) => state.clearAll);
  const setPanelHeight = useUploadQueueStore((state) => state.setPanelHeight);

  // Refs for measuring panel height
  const minimizedRef = useRef<HTMLDivElement>(null);
  const expandedRef = useRef<HTMLDivElement>(null);

  // Start the upload processor
  useUploadProcessor();

  const summary = getSummary();

  // Measure and report panel height to store
  const measureHeight = useCallback(() => {
    const ref = isMinimized ? minimizedRef : expandedRef;
    if (ref.current) {
      const rect = ref.current.getBoundingClientRect();
      // Include the bottom offset (bottom-6 = 24px for minimized, bottom-4 = 16px for expanded)
      const bottomOffset = isMinimized ? 24 : 16;
      const totalHeight = rect.height + bottomOffset + 8; // +8 for gap between toast and panel
      setPanelHeight(totalHeight);
    }
  }, [isMinimized, setPanelHeight]);

  // Debug: Log on mount
  useEffect(() => {
    console.log('[UploadQueuePanel] Component mounted');
    return () => {
      console.log('[UploadQueuePanel] Component unmounted');
      // Reset height when unmounted
      setPanelHeight(0);
    };
  }, [setPanelHeight]);

  // Measure height on mount, minimize toggle, and item changes
  useEffect(() => {
    measureHeight();
  }, [measureHeight, items.length, isMinimized]);

  // Use ResizeObserver for dynamic height changes
  useEffect(() => {
    const ref = isMinimized ? minimizedRef : expandedRef;
    if (!ref.current) return;

    const observer = new ResizeObserver(() => {
      measureHeight();
    });

    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [isMinimized, measureHeight]);

  // Debug: Log when items change
  useEffect(() => {
    console.log('[UploadQueuePanel] Items changed:', items.length, items);
  }, [items]);

  // Debug logging
  console.log('[UploadQueuePanel] Render - items:', items.length, 'isMinimized:', isMinimized);

  // Don't render if no items - reset height
  if (items.length === 0) {
    console.log('[UploadQueuePanel] No items, not rendering');
    return null;
  }

  // Determine panel state
  const hasUploading = summary.uploading > 0;
  const hasFailures = summary.failed > 0;
  const allComplete = summary.total > 0 && summary.completed === summary.total;

  // Panel color based on state
  const getHeaderColor = () => {
    if (hasUploading) return 'bg-blue-500';
    if (hasFailures) return 'bg-red-500';
    if (allComplete) return 'bg-green-500';
    return 'bg-gray-600';
  };

  // Get status icon
  const getStatusIcon = () => {
    if (hasUploading) return <Upload className="w-4 h-4 animate-pulse" />;
    if (hasFailures) return <AlertCircle className="w-4 h-4" />;
    if (allComplete) return <Check className="w-4 h-4" />;
    return <Upload className="w-4 h-4" />;
  };

  // Minimized badge view - Circular floating button
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
          title={t('uploads.queue.title', 'Upload Queue')}
        >
          {/* Main icon */}
          <Upload className="w-6 h-6" />

          {/* Progress ring overlay when uploading */}
          {hasUploading && (
            <svg className="absolute inset-0 w-14 h-14 -rotate-90">
              <circle
                cx="28"
                cy="28"
                r="24"
                stroke="currentColor"
                strokeWidth="3"
                fill="none"
                className="opacity-30"
              />
              <circle
                cx="28"
                cy="28"
                r="24"
                stroke="white"
                strokeWidth="3"
                fill="none"
                strokeDasharray={`${(summary.overallProgress / 100) * 150.8} 150.8`}
                className="transition-all duration-300"
              />
            </svg>
          )}

          {/* Badge count */}
          <span className="absolute -top-1 -right-1 flex items-center justify-center min-w-5 h-5 px-1.5 text-xs font-bold bg-white text-gray-900 rounded-full shadow">
            {summary.total}
          </span>

          {/* Pulse animation when uploading */}
          {hasUploading && (
            <span className="absolute inset-0 rounded-full animate-ping opacity-30 bg-current" />
          )}
        </button>
      </div>
    );
  }

  // Expanded panel view
  return (
    <div ref={expandedRef} className="fixed bottom-4 right-4 w-80" style={{ zIndex: Z_INDEX.UPLOAD_QUEUE }}>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {/* Header */}
        <div
          className={cn(
            'flex items-center justify-between px-4 py-3 text-white',
            getHeaderColor()
          )}
        >
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="font-medium">
              {t('uploads.queue.title', 'Upload Queue')}
            </span>
          </div>

          <div className="flex items-center gap-1">
            {/* Summary badge */}
            <span className="text-xs bg-white/20 px-2 py-0.5 rounded">
              {summary.completed}/{summary.total}
            </span>

            {/* Minimize button */}
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-white hover:bg-white/20"
              onClick={toggleMinimize}
            >
              <ChevronDown className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Overall progress bar (when uploading) */}
        {hasUploading && (
          <div className="px-4 py-2 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-300 mb-1">
              <span>
                {t('uploads.queue.uploading', {
                  count: summary.uploading,
                  defaultValue: `Uploading ${summary.uploading} file(s)...`,
                })}
              </span>
              <span>{summary.overallProgress}%</span>
            </div>
            <Progress value={summary.overallProgress} className="h-1.5" />
          </div>
        )}

        {/* All complete message */}
        {allComplete && (
          <div className="px-4 py-2 bg-green-50 dark:bg-green-900/30 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2 text-sm text-green-700 dark:text-green-400">
            <Check className="w-4 h-4" />
            {t('uploads.queue.allComplete', 'All uploads complete')}
          </div>
        )}

        {/* Items list */}
        <UploadList items={items} maxHeight="250px" />

        {/* Footer with actions */}
        <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-700 text-xs">
          <div className="flex items-center gap-2">
            {/* Retry all failed */}
            {summary.failed > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs text-blue-600 hover:text-blue-700"
                onClick={retryAllFailed}
              >
                <RotateCcw className="w-3 h-3 mr-1" />
                {t('uploads.actions.retryAll', 'Retry all')}
              </Button>
            )}

            {/* Clear completed */}
            {summary.completed > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs text-gray-600 hover:text-gray-700"
                onClick={clearCompleted}
              >
                <Trash2 className="w-3 h-3 mr-1" />
                {t('uploads.actions.clearCompleted', 'Clear completed')}
              </Button>
            )}
          </div>

          {/* Clear all */}
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs text-red-600 hover:text-red-700"
            onClick={clearAll}
          >
            <X className="w-3 h-3 mr-1" />
            {t('uploads.actions.clearAll', 'Clear all')}
          </Button>
        </div>
      </div>
    </div>
  );
}
