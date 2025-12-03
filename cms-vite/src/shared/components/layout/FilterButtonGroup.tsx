/**
 * FilterButtonGroup Component
 * Button group for status/filter selection
 * Used for All/Active/Inactive type filters
 */

import { cn } from '@/lib/utils';

interface FilterOption {
  id: string;
  label: string;
  count?: number;
}

interface FilterButtonGroupProps {
  options: FilterOption[];
  activeFilter: string;
  onChange: (filterId: string) => void;
  className?: string;
}

export function FilterButtonGroup({
  options,
  activeFilter,
  onChange,
  className,
}: FilterButtonGroupProps) {
  return (
    <div
      className={cn(
        'inline-flex rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden',
        className
      )}
    >
      {options.map((option, index) => {
        const isActive = activeFilter === option.id;
        const isFirst = index === 0;
        const isLast = index === options.length - 1;

        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onChange(option.id)}
            className={cn(
              'px-3 py-1.5 text-sm font-medium transition-colors',
              isActive
                ? 'bg-blue-500 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700',
              !isFirst && !isActive && 'border-l border-gray-300 dark:border-gray-600',
              isFirst && 'rounded-l-lg',
              isLast && 'rounded-r-lg'
            )}
          >
            {option.label}
            {option.count !== undefined && (
              <span
                className={cn(
                  'ml-1.5 text-xs',
                  isActive ? 'opacity-80' : 'opacity-60'
                )}
              >
                ({option.count})
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export default FilterButtonGroup;
