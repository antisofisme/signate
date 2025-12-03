/**
 * ViewTabs Component
 * Tab navigation for view mode switching
 * Used for Table/Gallery, List/Calendar toggles
 */

import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

interface ViewTab {
  id: string;
  label: string;
  icon?: LucideIcon;
}

interface ViewTabsProps {
  tabs: ViewTab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export function ViewTabs({ tabs, activeTab, onChange, className }: ViewTabsProps) {
  return (
    <div className={cn('mb-4 border-b border-gray-200 dark:border-gray-700', className)}>
      <nav className="-mb-px flex space-x-4" role="tablist">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => onChange(tab.id)}
              className={cn(
                'flex items-center gap-2 py-2 px-1 border-b-2 text-sm font-medium transition-colors',
                isActive
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              )}
            >
              {Icon && <Icon className="w-4 h-4" />}
              {tab.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
}

export default ViewTabs;
