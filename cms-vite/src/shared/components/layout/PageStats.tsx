/**
 * PageStats Component
 * Minimalist inline stats display
 * Format: "45 items • 32 active • 13 inactive"
 */

import { cn } from '@/lib/utils';

interface Stat {
  label: string;
  value: number;
  color?: string;
}

interface PageStatsProps {
  total: number;
  totalLabel?: string;
  stats?: Stat[];
  className?: string;
}

export function PageStats({
  total,
  totalLabel = 'items',
  stats = [],
  className,
}: PageStatsProps) {
  return (
    <div
      className={cn(
        'text-sm text-gray-600 dark:text-gray-400 mb-4',
        className
      )}
    >
      <span className="font-medium">{total}</span> {totalLabel}
      {stats.map((stat, i) => (
        <span key={i}>
          {' • '}
          <span className={cn('font-medium', stat.color)}>{stat.value}</span>{' '}
          {stat.label}
        </span>
      ))}
    </div>
  );
}

export default PageStats;
