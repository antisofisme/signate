/**
 * PageToolbar Component
 * Standardized toolbar container for page layouts
 * Left side: Filters, Search, Sort
 * Right side: Action buttons
 */

import { cn } from '@/lib/utils';

interface PageToolbarProps {
  children: React.ReactNode;
  className?: string;
}

interface PageToolbarLeftProps {
  children?: React.ReactNode;
  className?: string;
}

interface PageToolbarRightProps {
  children?: React.ReactNode;
  className?: string;
}

export function PageToolbar({ children, className }: PageToolbarProps) {
  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4',
        className
      )}
    >
      {children}
    </div>
  );
}

PageToolbar.Left = function PageToolbarLeft({ children, className }: PageToolbarLeftProps) {
  return (
    <div className={cn('flex flex-wrap items-center gap-3', className)}>
      {children}
    </div>
  );
};

PageToolbar.Right = function PageToolbarRight({ children, className }: PageToolbarRightProps) {
  return (
    <div className={cn('flex items-center gap-2 ml-auto', className)}>
      {children}
    </div>
  );
};

export default PageToolbar;
