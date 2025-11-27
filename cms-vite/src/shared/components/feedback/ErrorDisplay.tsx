/**
 * ErrorDisplay Component
 * Display error messages with optional retry action
 */
import { AlertCircle, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ErrorDisplayProps {
  title?: string;
  message?: string;
  error?: Error | null;
  onRetry?: () => void;
  className?: string;
}

export function ErrorDisplay({
  title,
  message,
  error,
  onRetry,
  className,
}: ErrorDisplayProps) {
  const { t } = useTranslation();

  const errorMessage =
    message || error?.message || t('common.error', 'An error occurred');
  const errorTitle = title || t('common.errorTitle', 'Error');

  return (
    <div
      className={cn(
        'rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-4',
        className
      )}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-red-800 dark:text-red-300">
            {errorTitle}
          </h3>
          <p className="mt-1 text-sm text-red-700 dark:text-red-400">
            {errorMessage}
          </p>
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="mt-3 text-red-700 dark:text-red-300 border-red-300 dark:border-red-700 hover:bg-red-100 dark:hover:bg-red-900/40"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              {t('common.retry', 'Retry')}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

interface InlineErrorProps {
  message: string;
  className?: string;
}

export function InlineError({ message, className }: InlineErrorProps) {
  return (
    <p
      className={cn('text-sm text-red-500 dark:text-red-400', className)}
      role="alert"
    >
      {message}
    </p>
  );
}
