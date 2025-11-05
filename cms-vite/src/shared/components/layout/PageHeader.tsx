/**
 * Page Header Component
 *
 * LAYER 1: PRESENTATION
 * Sticky page header with title and description
 * Same design as web-admin
 */

import { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
}

export default function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="fixed top-0 left-0 right-0 lg:left-64 z-40 h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-md transition-colors">
      <div className="h-full px-4 sm:px-6 lg:px-8">
        <div className="h-full flex items-center justify-between pl-12 lg:pl-0">
          {/* Title & Description */}
          <div>
            <h1 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white leading-tight">
              {title}
            </h1>
            {description && (
              <p className="text-xs text-gray-600 dark:text-gray-300 leading-tight">
                {description}
              </p>
            )}
          </div>

          {/* Optional Actions (buttons, filters, etc.) */}
          {actions && (
            <div className="flex items-center gap-2">
              {actions}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
