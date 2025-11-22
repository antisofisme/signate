/**
 * Reusable Tabs Component
 * Generic tab navigation with TypeScript generics
 */

import { ReactNode } from 'react';

export interface Tab {
  id: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  disabled?: boolean;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className = '' }: TabsProps) {
  return (
    <div className={`border-b border-gray-200 dark:border-gray-700 ${className}`}>
      <nav className="flex -mb-px overflow-x-auto" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;

          return (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && onChange(tab.id)}
              disabled={tab.disabled}
              className={`
                group relative min-w-0 flex-1 overflow-hidden px-4 py-3 text-sm font-medium text-center
                border-b-2 transition-colors whitespace-nowrap
                ${
                  isActive
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }
                ${tab.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
              aria-current={isActive ? 'page' : undefined}
            >
              <div className="flex items-center justify-center gap-2">
                {Icon && (
                  <Icon
                    className={`w-4 h-4 ${
                      isActive
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
                    }`}
                  />
                )}
                <span>{tab.label}</span>
                {tab.badge !== undefined && (
                  <span
                    className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                      isActive
                        ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </nav>
    </div>
  );
}

interface TabPanelProps {
  activeTab: string;
  tabId: string;
  children: ReactNode;
  className?: string;
}

export function TabPanel({ activeTab, tabId, children, className = '' }: TabPanelProps) {
  if (activeTab !== tabId) return null;

  return <div className={className}>{children}</div>;
}
