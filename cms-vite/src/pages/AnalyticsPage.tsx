/**
 * Analytics Page
 * Main analytics dashboard page
 */

import { useState } from 'react'
import { BarChart3, RefreshCw } from 'lucide-react'
import { AnalyticsOverview } from '@/features/analytics/components/AnalyticsOverview'
import { ContentPerformanceChart } from '@/features/analytics/components/ContentPerformanceChart'
import { PlaybackTimelineChart } from '@/features/analytics/components/PlaybackTimelineChart'
import {
  useAnalyticsStats,
  useContentPerformance,
  usePlaybackTimeline,
} from '@/features/analytics/hooks'

export function AnalyticsPage() {
  const [interval, setInterval] = useState<'day' | 'week' | 'month'>('day')
  const [limit, setLimit] = useState(10)

  // Fetch analytics data
  const { data: stats, isLoading: statsLoading } = useAnalyticsStats()
  const { data: contentPerformance, isLoading: contentLoading } = useContentPerformance({
    limit,
  })
  const { data: timeline, isLoading: timelineLoading } = usePlaybackTimeline({
    interval,
  })

  const handleRefresh = () => {
    window.location.reload()
  }

  return (
    <>
      {/* Action Bar */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {/* Stats Overview */}
        <AnalyticsOverview stats={stats!} isLoading={statsLoading} />

        {/* Charts Section */}
        <div className="grid gap-4 md:grid-cols-2">
        <ContentPerformanceChart data={contentPerformance || []} isLoading={contentLoading} />

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Playback Timeline</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">Activity over time</p>
            </div>
            <select
              value={interval}
              onChange={(e) => setInterval(e.target.value as 'day' | 'week' | 'month')}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="day">Daily</option>
              <option value="week">Weekly</option>
              <option value="month">Monthly</option>
            </select>
          </div>
          <PlaybackTimelineChart
            data={timeline || []}
            isLoading={timelineLoading}
            variant="area"
          />
        </div>
        </div>

        {/* Additional Info */}
        <div className="rounded-lg border p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Auto-refresh enabled</h3>
            <p className="text-sm text-muted-foreground">
              Dashboard updates automatically every 30 seconds
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            {stats?.period_start && stats?.period_end && (
              <span>
                Showing data from last 30 days
              </span>
            )}
          </div>
        </div>
        </div>
      </div>
    </>
  )
}
