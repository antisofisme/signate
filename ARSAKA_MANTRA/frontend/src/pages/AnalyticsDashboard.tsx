import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  analyticsApi,
  AnalyticsSummary,
  HealthDistribution,
} from '@/shared/api'

export default function AnalyticsDashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [healthDist, setHealthDist] = useState<HealthDistribution | null>(null)
  const [hotDecisions, setHotDecisions] = useState<string[]>([])
  const [staleDecisions, setStaleDecisions] = useState<string[]>([])
  const [problematicDecisions, setProblematicDecisions] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [staleDays, setStaleDays] = useState(30)

  useEffect(() => {
    loadData()
  }, [staleDays])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [summaryData, healthData, hotData, staleData, probData] = await Promise.all([
        analyticsApi.getSummary(),
        analyticsApi.getHealthDistribution(),
        analyticsApi.getHotDecisions(10),
        analyticsApi.getStaleDecisions(staleDays),
        analyticsApi.getProblematicDecisions(),
      ])
      setSummary(summaryData)
      setHealthDist(healthData)
      setHotDecisions(hotData.decisions)
      setStaleDecisions(staleData.decisions)
      setProblematicDecisions(probData.decisions)
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }

  const healthColors: Record<string, string> = {
    HEALTHY: 'bg-green-500',
    GOOD: 'bg-blue-500',
    WARNING: 'bg-yellow-500',
    POOR: 'bg-orange-500',
    CRITICAL: 'bg-red-500',
    NEW: 'bg-gray-400',
  }

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Usage Analytics</h1>
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Usage Analytics</h1>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-600">{error}</p>
            <Button onClick={loadData} className="mt-4">Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Usage Analytics</h1>
        <Button onClick={loadData} variant="outline">Refresh</Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Tracked</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary?.total_decisions_tracked || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Events</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary?.total_events || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Feedback</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary?.total_feedback || 0}</p>
          </CardContent>
        </Card>
        <Card className="bg-green-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-green-600">Hot</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-700">{summary?.hot_decisions_count || 0}</p>
          </CardContent>
        </Card>
        <Card className="bg-yellow-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-yellow-600">Stale</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-yellow-700">{summary?.stale_decisions_count || 0}</p>
          </CardContent>
        </Card>
        <Card className="bg-red-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-red-600">Problematic</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-red-700">{summary?.problematic_decisions_count || 0}</p>
          </CardContent>
        </Card>
      </div>

      {/* Health Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Health Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 flex-wrap">
            {healthDist && Object.entries(healthDist.distribution).map(([status, count]) => (
              <div key={status} className="flex items-center gap-2">
                <div className={`w-4 h-4 rounded ${healthColors[status] || 'bg-gray-400'}`}></div>
                <span className="text-sm">
                  {status}: <strong>{count}</strong>
                </span>
              </div>
            ))}
          </div>
          {healthDist && healthDist.total > 0 && (
            <div className="mt-4 h-4 rounded-full bg-gray-200 overflow-hidden flex">
              {Object.entries(healthDist.distribution).map(([status, count]) => {
                const pct = (count / healthDist.total) * 100
                if (pct === 0) return null
                return (
                  <div
                    key={status}
                    className={`h-full ${healthColors[status] || 'bg-gray-400'}`}
                    style={{ width: `${pct}%` }}
                    title={`${status}: ${count} (${pct.toFixed(1)}%)`}
                  />
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Decision Lists */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Hot Decisions */}
        <Card>
          <CardHeader className="bg-green-50">
            <CardTitle className="text-green-700 flex items-center gap-2">
              <span className="text-xl">🔥</span> Hot Decisions
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            {hotDecisions.length === 0 ? (
              <p className="text-gray-500 text-sm">No hot decisions yet</p>
            ) : (
              <ul className="space-y-2">
                {hotDecisions.map((id) => (
                  <li key={id} className="text-sm font-mono bg-green-50 px-2 py-1 rounded">
                    <a href={`/decisions/${id}`} className="hover:underline">{id}</a>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Stale Decisions */}
        <Card>
          <CardHeader className="bg-yellow-50">
            <CardTitle className="text-yellow-700 flex items-center gap-2">
              <span className="text-xl">⏰</span> Stale Decisions
              <select
                value={staleDays}
                onChange={(e) => setStaleDays(Number(e.target.value))}
                className="ml-auto text-sm border rounded px-2 py-1"
              >
                <option value={7}>7 days</option>
                <option value={14}>14 days</option>
                <option value={30}>30 days</option>
                <option value={60}>60 days</option>
                <option value={90}>90 days</option>
              </select>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            {staleDecisions.length === 0 ? (
              <p className="text-gray-500 text-sm">No stale decisions</p>
            ) : (
              <ul className="space-y-2">
                {staleDecisions.slice(0, 10).map((id) => (
                  <li key={id} className="text-sm font-mono bg-yellow-50 px-2 py-1 rounded">
                    <a href={`/decisions/${id}`} className="hover:underline">{id}</a>
                  </li>
                ))}
                {staleDecisions.length > 10 && (
                  <li className="text-sm text-gray-500">+{staleDecisions.length - 10} more</li>
                )}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Problematic Decisions */}
        <Card>
          <CardHeader className="bg-red-50">
            <CardTitle className="text-red-700 flex items-center gap-2">
              <span className="text-xl">⚠️</span> Problematic Decisions
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            {problematicDecisions.length === 0 ? (
              <p className="text-gray-500 text-sm">No problematic decisions</p>
            ) : (
              <ul className="space-y-2">
                {problematicDecisions.map((id) => (
                  <li key={id} className="text-sm font-mono bg-red-50 px-2 py-1 rounded">
                    <a href={`/decisions/${id}`} className="hover:underline">{id}</a>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Info */}
      <Card className="bg-gray-50">
        <CardContent className="pt-6">
          <h3 className="font-semibold mb-2">About Analytics</h3>
          <ul className="text-sm text-gray-600 space-y-1">
            <li><strong>Hot:</strong> Frequently accessed decisions (high view/apply counts)</li>
            <li><strong>Stale:</strong> Decisions not accessed in N days (may need review)</li>
            <li><strong>Problematic:</strong> Decisions with negative feedback (need attention)</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
