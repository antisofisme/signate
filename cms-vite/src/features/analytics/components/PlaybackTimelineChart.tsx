/**
 * PlaybackTimelineChart Component
 * Display playback timeline data in a line/area chart
 */

import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { TimelineDataPoint } from '../types'
import { format } from 'date-fns'

interface PlaybackTimelineChartProps {
  data: TimelineDataPoint[]
  isLoading?: boolean
  variant?: 'line' | 'area'
}

export function PlaybackTimelineChart({
  data,
  isLoading,
  variant = 'area',
}: PlaybackTimelineChartProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
        <div className="p-6 pb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Playback Timeline</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Playback activity over time</p>
        </div>
        <div className="p-6 pt-0">
          <div className="h-80 animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg" />
        </div>
      </div>
    )
  }

  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
        <div className="p-6 pb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Playback Timeline</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Playback activity over time</p>
        </div>
        <div className="p-6 pt-0">
          <div className="h-80 flex items-center justify-center text-gray-600 dark:text-gray-400">
            No timeline data available
          </div>
        </div>
      </div>
    )
  }

  // Format dates for display
  const chartData = data.map((item) => ({
    ...item,
    dateFormatted: format(new Date(item.date), 'MMM dd'),
  }))

  const ChartComponent = variant === 'line' ? LineChart : AreaChart

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
      <div className="p-6 pb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Playback Timeline</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Playback activity over time</p>
      </div>
      <div className="p-6 pt-0">
        <ResponsiveContainer width="100%" height={320}>
          <ChartComponent data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
            <XAxis dataKey="dateFormatted" fontSize={12} stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload
                  return (
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg">
                      <p className="font-semibold text-gray-900 dark:text-white">{data.dateFormatted}</p>
                      <p className="text-sm text-gray-700 dark:text-gray-300">Total Plays: {data.plays}</p>
                      <p className="text-sm text-gray-700 dark:text-gray-300">Completed: {data.completed}</p>
                      <p className="text-sm text-gray-700 dark:text-gray-300">Active Devices: {data.devices}</p>
                      <p className="text-sm text-gray-700 dark:text-gray-300">Watch Time: {Math.round(data.watch_time / 60)}m</p>
                    </div>
                  )
                }
                return null
              }}
            />
            <Legend />
            {variant === 'line' ? (
              <>
                <Line
                  type="monotone"
                  dataKey="plays"
                  stroke="#3b82f6"
                  name="Plays"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="completed"
                  stroke="#10b981"
                  name="Completed"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="devices"
                  stroke="#f59e0b"
                  name="Devices"
                  strokeWidth={2}
                />
              </>
            ) : (
              <>
                <Area
                  type="monotone"
                  dataKey="plays"
                  stackId="1"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                  name="Plays"
                />
                <Area
                  type="monotone"
                  dataKey="completed"
                  stackId="2"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.6}
                  name="Completed"
                />
                <Area
                  type="monotone"
                  dataKey="devices"
                  stackId="3"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.6}
                  name="Devices"
                />
              </>
            )}
          </ChartComponent>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
