/**
 * AccessDenied Component
 * Display when user doesn't have permission
 */
import { ShieldX } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import Button from '../common/Button';

interface AccessDeniedProps {
  title?: string;
  message?: string;
  showBackButton?: boolean;
  className?: string;
}

export function AccessDenied({
  title,
  message,
  showBackButton = true,
  className,
}: AccessDeniedProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 px-4',
        className
      )}
    >
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
        <ShieldX className="h-10 w-10 text-red-500" />
      </div>
      <h2 className="mt-6 text-xl font-semibold text-gray-900 dark:text-white">
        {title || t('common.accessDenied', 'Access Denied')}
      </h2>
      <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 text-center max-w-md">
        {message ||
          t(
            'common.accessDeniedMessage',
            "You don't have permission to access this page."
          )}
      </p>
      {showBackButton && (
        <Button variant="outline" onClick={() => navigate(-1)} className="mt-6">
          {t('common.goBack', 'Go Back')}
        </Button>
      )}
    </div>
  );
}
