/**
 * Refresh Button Component
 *
 * Reusable button for manual data refresh.
 * Used in pages where auto-polling was removed for performance.
 */

import { memo } from 'react';
import { RefreshCw, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils/cn';

interface RefreshButtonProps {
  onClick: () => void;
  isLoading?: boolean;
  label?: string;
  variant?: 'default' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  showLabel?: boolean;
  title?: string;
}

const RefreshButton = memo<RefreshButtonProps>(function RefreshButton({
  onClick,
  isLoading = false,
  label,
  variant = 'outline',
  size = 'md',
  className,
  showLabel = true,
  title,
}) {
  const { t } = useTranslation();
  const displayLabel = label || t('common.refresh', 'Refresh');

  // Size variants
  const sizeStyles = {
    sm: 'px-2 py-1 text-xs gap-1',
    md: 'px-3 py-1.5 text-sm gap-1.5',
    lg: 'px-4 py-2 text-base gap-2',
  };

  const iconSize = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  // Variant styles
  const variantStyles = {
    default: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    ghost: 'bg-transparent text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:ring-gray-400',
    outline: 'bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:ring-gray-400',
  };

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isLoading}
      title={title || displayLabel}
      aria-label={displayLabel}
      className={cn(
        'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        sizeStyles[size],
        variantStyles[variant],
        className
      )}
    >
      {isLoading ? (
        <Loader2 className={cn(iconSize[size], 'animate-spin')} />
      ) : (
        <RefreshCw className={cn(iconSize[size], 'transition-transform hover:rotate-45')} />
      )}
      {showLabel && <span>{displayLabel}</span>}
    </button>
  );
});

export default RefreshButton;
