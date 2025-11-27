/**
 * DateRangePicker Component
 * Quick date range selection for analytics
 */

import { Calendar } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export type DateRange = '7d' | '30d' | '90d' | 'custom';

interface DateRangePickerProps {
  value: DateRange;
  onChange: (value: DateRange) => void;
  className?: string;
}

export function DateRangePicker({ value, onChange, className = '' }: DateRangePickerProps) {
  const { t } = useTranslation();

  const options: { value: DateRange; label: string }[] = [
    { value: '7d', label: t('analytics.last7Days', 'Last 7 Days') },
    { value: '30d', label: t('analytics.last30Days', 'Last 30 Days') },
    { value: '90d', label: t('analytics.last90Days', 'Last 90 Days') },
  ];

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Calendar className="h-4 w-4 text-gray-500" />
      <div className="flex rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden">
        {options.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`px-3 py-1.5 text-sm font-medium transition-colors ${
              value === option.value
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
