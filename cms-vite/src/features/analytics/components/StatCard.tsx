/**
 * StatCard Component
 * Display statistics in a card format
 */

import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  icon?: LucideIcon
  description?: string
  trend?: {
    value: number
    isPositive: boolean
  }
}

export function StatCard({ title, value, icon: Icon, description, trend }: StatCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
      <div className="flex flex-row items-center justify-between space-y-0 p-6 pb-2">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">{title}</h3>
        {Icon && <Icon className="h-4 w-4 text-gray-500 dark:text-gray-400" />}
      </div>
      <div className="p-6 pt-0">
        <div className="text-2xl font-bold text-gray-900 dark:text-white">{value}</div>
        {description && (
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{description}</p>
        )}
        {trend && (
          <p
            className={`text-xs mt-1 ${
              trend.isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            }`}
          >
            {trend.isPositive ? '+' : ''}
            {trend.value}% from last period
          </p>
        )}
      </div>
    </div>
  )
}
