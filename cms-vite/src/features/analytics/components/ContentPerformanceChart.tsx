/**
 * ContentPerformanceChart Component
 * Display content performance data in a bar chart
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { ContentPerformance } from '../types'

interface ContentPerformanceChartProps {
  data: ContentPerformance[]
  isLoading?: boolean
}

export function ContentPerformanceChart({ data, isLoading }: ContentPerformanceChartProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
        <div className="p-6 pb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Top Content Performance</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Most played content in the selected period</p>
        </div>
        <div className="p-6 pt-0">
          <div className="h-80 animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg" />
        </div>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
        <div className="p-6 pb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Top Content Performance</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Most played content in the selected period</p>
        </div>
        <div className="p-6 pt-0">
          <div className="h-80 flex items-center justify-center text-gray-600 dark:text-gray-400">
            No content performance data available
          </div>
        </div>
      </div>
    )
  }

  // Format data for chart (limit title length)
  const chartData = data.map((item) => ({
    ...item,
    name: item.title.length > 20 ? item.title.substring(0, 20) + '...' : item.title,
    fullTitle: item.title,
  }))

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
      <div className="p-6 pb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Top Content Performance</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Most played content in the selected period</p>
      </div>
      <div className="p-6 pt-0">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
            <XAxis
              dataKey="name"
              fontSize={12}
              angle={-45}
              textAnchor="end"
              height={100}
              stroke="#6b7280"
            />
            <YAxis stroke="#6b7280" />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload
                  return (
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg">
                      <p className="font-semibold text-gray-900 dark:text-white">{data.fullTitle}</p>
                      <p className="text-sm text-gray-700 dark:text-gray-300">Total Plays: {data.total_plays}</p>
                      <p className="text-sm text-gray-700 dark:text-gray-300">Completed: {data.completed_plays}</p>
                      <p className="text-sm text-gray-700 dark:text-gray-300">Unique Devices: {data.unique_devices}</p>
                      {data.completion_rate && (
                        <p className="text-sm text-gray-700 dark:text-gray-300">Completion Rate: {data.completion_rate.toFixed(1)}%</p>
                      )}
                    </div>
                  )
                }
                return null
              }}
            />
            <Legend />
            <Bar dataKey="total_plays" fill="#3b82f6" name="Total Plays" />
            <Bar dataKey="completed_plays" fill="#10b981" name="Completed" />
            <Bar dataKey="unique_devices" fill="#f59e0b" name="Unique Devices" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
