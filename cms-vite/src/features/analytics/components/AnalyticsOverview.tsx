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

  // Add null safety for all stats
  const safeStats = {
    total_plays: stats?.total_plays || 0,
    completed_plays: stats?.completed_plays || 0,
    unique_content: stats?.unique_content || 0,
    unique_devices: stats?.unique_devices || 0,
    total_watch_time_hours: stats?.total_watch_time_hours || 0,
    total_watch_time_seconds: stats?.total_watch_time_seconds || 0,
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
      <StatCard
        title="Total Plays"
        value={formatNumber(safeStats.total_plays)}
        icon={Play}
        description="Total content playback"
      />

      <StatCard
        title="Completed"
        value={formatNumber(safeStats.completed_plays)}
        icon={CheckCircle}
        description="Completed playback"
      />

      <StatCard
        title="Unique Content"
        value={formatNumber(safeStats.unique_content)}
        icon={FileVideo}
        description="Different content played"
      />

      <StatCard
        title="Active Devices"
        value={formatNumber(safeStats.unique_devices)}
        icon={Monitor}
        description="Devices with playback"
      />

      <StatCard
        title="Watch Time"
        value={formatHours(safeStats.total_watch_time_hours)}
        icon={Clock}
        description={`${formatNumber(safeStats.total_watch_time_seconds)}s total`}
      />
    </div>
  )
}
