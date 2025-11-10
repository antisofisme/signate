/**
 * AnalyticsOverview Component
 * Display overall statistics cards
 */

import { Play, CheckCircle, FileVideo, Monitor, Clock } from 'lucide-react'
import { StatCard } from './StatCard'
import type { PlaybackStats } from '../types'

interface AnalyticsOverviewProps {
  stats: PlaybackStats
  isLoading?: boolean
}

export function AnalyticsOverview({ stats, isLoading }: AnalyticsOverviewProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-32 animate-pulse bg-muted rounded-lg" />
        ))}
      </div>
    )
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('id-ID').format(num)
  }

  const formatHours = (hours: number) => {
    if (hours < 1) {
      return `${Math.round(hours * 60)}m`
    }
    return `${hours.toFixed(1)}h`
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
      <StatCard
        title="Total Plays"
        value={formatNumber(stats.total_plays)}
        icon={Play}
        description="Total content playback"
      />

      <StatCard
        title="Completed"
        value={formatNumber(stats.completed_plays)}
        icon={CheckCircle}
        description="Completed playback"
      />

      <StatCard
        title="Unique Content"
        value={formatNumber(stats.unique_content)}
        icon={FileVideo}
        description="Different content played"
      />

      <StatCard
        title="Active Devices"
        value={formatNumber(stats.unique_devices)}
        icon={Monitor}
        description="Devices with playback"
      />

      <StatCard
        title="Watch Time"
        value={formatHours(stats.total_watch_time_hours)}
        icon={Clock}
        description={`${formatNumber(stats.total_watch_time_seconds)}s total`}
      />
    </div>
  )
}
