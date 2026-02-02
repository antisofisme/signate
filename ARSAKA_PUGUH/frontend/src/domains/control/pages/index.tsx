/**
 * Control Domain - Pages
 * READ-ONLY domain - no mutations
 */

import { useParams, useNavigate } from 'react-router-dom'
import { DomainPage, ReadOnlyNotice } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  FileText,
  Activity,
  AlertCircle,
  BarChart3,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
} from 'lucide-react'
import {
  useGetAuditRecords,
  useGetAuditRecord,
  useGetEvents,
  useGetEvent,
  useGetDLQEvents,
  useGetMetricsSummary,
  useGetMetricsTrends,
} from '../api'
import { useAuditFilters, useEventFilters, useEventStatusBadge } from '../hooks'
import type { EventStatus } from '../types'
import { EVENT_STATUS_BADGE_VARIANTS } from '../types'

// ============================================
// Audit Trail Page
// ============================================

export function AuditTrail() {
  const navigate = useNavigate()
  const { filters, updateFilter, resetFilters } = useAuditFilters()
  const { data, isLoading, error, refetch } = useGetAuditRecords(filters)

  return (
    <DomainPage
      domain="control"
      title="Audit Trail"
      description="View all system audit records"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      actions={
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      }
    >
      <ReadOnlyNotice domain="control" />

      {/* Filters */}
      <Card className="mb-4">
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search by action or resource..."
                value={filters.action || ''}
                onChange={(e) => updateFilter('action', e.target.value)}
              />
            </div>
            <div className="w-[180px]">
              <Input
                placeholder="Actor..."
                value={filters.actor || ''}
                onChange={(e) => updateFilter('actor', e.target.value)}
              />
            </div>
            <Button variant="outline" onClick={resetFilters}>
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Audit Records Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Recent Audit Records
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="py-12 text-center text-red-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load audit records</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items?.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell>
                      <Badge variant="outline">{record.action}</Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {record.resource}
                    </TableCell>
                    <TableCell>{record.actor}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(record.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/app/control/audit/${record.id}`)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {(!data?.items || data.items.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                      No audit records found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Audit Detail Page
// ============================================

export function AuditDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: record, isLoading, error } = useGetAuditRecord(id || '')

  if (isLoading) {
    return (
      <DomainPage domain="control" title="Loading..." backTo="/app/control/audit">
        <Card>
          <CardContent className="py-12">
            <div className="space-y-4">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-4 w-64" />
              <Skeleton className="h-32 w-full" />
            </div>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  if (error || !record) {
    return (
      <DomainPage domain="control" title="Error" backTo="/app/control/audit">
        <Card>
          <CardContent className="py-12 text-center text-red-500">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>Failed to load audit record</p>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="control"
      title={`Audit Record: ${record.action}`}
      description={`Record ID: ${record.id}`}
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      backTo="/app/control/audit"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Record Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-muted-foreground">Action</Label>
                    <p className="mt-1">
                      <Badge variant="outline">{record.action}</Badge>
                    </p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Actor</Label>
                    <p className="mt-1 font-medium">{record.actor}</p>
                  </div>
                </div>
                <div>
                  <Label className="text-muted-foreground">Resource</Label>
                  <p className="mt-1 font-mono text-sm">{record.resource}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Timestamp</Label>
                  <p className="mt-1">{new Date(record.timestamp).toLocaleString()}</p>
                </div>
                {record.metadata && (
                  <div>
                    <Label className="text-muted-foreground">Metadata</Label>
                    <pre className="mt-1 p-4 bg-muted rounded-md text-sm overflow-x-auto">
                      {JSON.stringify(record.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Context</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-muted-foreground text-xs">Trace ID</Label>
                <p className="text-sm font-mono">{record.traceId || 'N/A'}</p>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">IP Address</Label>
                <p className="text-sm">{record.ipAddress || 'N/A'}</p>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">User Agent</Label>
                <p className="text-sm text-muted-foreground truncate">
                  {record.userAgent || 'N/A'}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DomainPage>
  )
}

// ============================================
// Event Timeline Page
// ============================================

export function EventTimeline() {
  const navigate = useNavigate()
  const { filters, updateFilter, resetFilters } = useEventFilters()
  const { data, isLoading, error, refetch } = useGetEvents(filters)
  const { getStatusLabel, getStatusVariant } = useEventStatusBadge()

  return (
    <DomainPage
      domain="control"
      title="Event Timeline"
      description="View all system events"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      actions={
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      }
    >
      <ReadOnlyNotice domain="control" />

      {/* Filters */}
      <Card className="mb-4">
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search by type..."
                value={filters.type || ''}
                onChange={(e) => updateFilter('type', e.target.value)}
              />
            </div>
            <Select
              value={filters.status || 'all'}
              onValueChange={(v) => updateFilter('status', v === 'all' ? undefined : v as EventStatus)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="PROCESSED">Processed</SelectItem>
                <SelectItem value="FAILED">Failed</SelectItem>
                <SelectItem value="DLQ">DLQ</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={resetFilters}>
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Events Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Recent Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="py-12 text-center text-red-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load events</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items?.map((event) => (
                  <TableRow key={event.id}>
                    <TableCell>
                      <Badge variant="outline">{event.type}</Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {event.source}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(event.status) as 'success' | 'warning' | 'destructive' | 'outline'}>
                        {getStatusLabel(event.status)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(event.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/app/control/events/${event.id}`)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {(!data?.items || data.items.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                      No events found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Event Detail Page
// ============================================

export function EventDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: event, isLoading, error } = useGetEvent(id || '')
  const { getStatusLabel, getStatusVariant } = useEventStatusBadge()

  if (isLoading) {
    return (
      <DomainPage domain="control" title="Loading..." backTo="/app/control/events">
        <Skeleton className="h-64 w-full" />
      </DomainPage>
    )
  }

  if (error || !event) {
    return (
      <DomainPage domain="control" title="Error" backTo="/app/control/events">
        <Card>
          <CardContent className="py-12 text-center text-red-500">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>Failed to load event</p>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="control"
      title={`Event: ${event.type}`}
      description={`Event ID: ${event.id}`}
      badge={{
        label: getStatusLabel(event.status),
        variant: EVENT_STATUS_BADGE_VARIANTS[event.status]
      }}
      backTo="/app/control/events"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Event Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-muted-foreground">Type</Label>
                    <p className="mt-1">
                      <Badge variant="outline">{event.type}</Badge>
                    </p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Source</Label>
                    <p className="mt-1 font-mono text-sm">{event.source}</p>
                  </div>
                </div>
                <div>
                  <Label className="text-muted-foreground">Timestamp</Label>
                  <p className="mt-1">{new Date(event.timestamp).toLocaleString()}</p>
                </div>
                {event.payload && (
                  <div>
                    <Label className="text-muted-foreground">Payload</Label>
                    <pre className="mt-1 p-4 bg-muted rounded-md text-sm overflow-x-auto">
                      {JSON.stringify(event.payload, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Processing Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-muted-foreground text-xs">Status</Label>
                <p className="text-sm">
                  <Badge variant={getStatusVariant(event.status) as 'success' | 'warning' | 'destructive' | 'outline'}>
                    {getStatusLabel(event.status)}
                  </Badge>
                </p>
              </div>
              {event.processedAt && (
                <div>
                  <Label className="text-muted-foreground text-xs">Processed At</Label>
                  <p className="text-sm">{new Date(event.processedAt).toLocaleString()}</p>
                </div>
              )}
              {event.error && (
                <div>
                  <Label className="text-muted-foreground text-xs">Error</Label>
                  <p className="text-sm text-red-500">{event.error}</p>
                </div>
              )}
              <div>
                <Label className="text-muted-foreground text-xs">Retry Count</Label>
                <p className="text-sm">{event.retryCount || 0}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DomainPage>
  )
}

// ============================================
// DLQ View Page
// ============================================

export function DLQView() {
  const navigate = useNavigate()
  const { data: dlqEvents, isLoading, error, refetch } = useGetDLQEvents()

  return (
    <DomainPage
      domain="control"
      title="Dead Letter Queue"
      description="View failed events"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      actions={
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      }
    >
      <ReadOnlyNotice domain="control" />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-500" />
            DLQ Events
          </CardTitle>
          <CardDescription>
            Events that failed processing and were moved to the dead letter queue
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="py-12 text-center text-red-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load DLQ events</p>
            </div>
          ) : dlqEvents?.length === 0 ? (
            <div className="py-12 text-center">
              <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
              <h3 className="text-lg font-semibold">All Clear!</h3>
              <p className="text-muted-foreground">
                No events in dead letter queue. All events processed successfully.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Event Type</TableHead>
                  <TableHead>Original Event ID</TableHead>
                  <TableHead>Error</TableHead>
                  <TableHead>Failed At</TableHead>
                  <TableHead>Retry Count</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dlqEvents?.map((event) => (
                  <TableRow key={event.id}>
                    <TableCell>
                      <Badge variant="outline">{event.eventType}</Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {event.originalEventId}
                    </TableCell>
                    <TableCell className="text-red-500 max-w-[200px] truncate">
                      {event.error}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(event.failedAt).toLocaleString()}
                    </TableCell>
                    <TableCell>{event.retryCount}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/app/control/events/${event.originalEventId}`)}
                      >
                        View Original
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Metrics Dashboard Page
// ============================================

export function MetricsDashboard() {
  const { data: summary, isLoading: loadingSummary, refetch: refetchSummary } = useGetMetricsSummary()
  const { data: trends, isLoading: loadingTrends } = useGetMetricsTrends()

  const getTrendIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="h-4 w-4 text-green-500" />
    if (change < 0) return <TrendingDown className="h-4 w-4 text-red-500" />
    return <Minus className="h-4 w-4 text-gray-500" />
  }

  const getTrendColor = (change: number) => {
    if (change > 0) return 'text-green-600'
    if (change < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  return (
    <DomainPage
      domain="control"
      title="Metrics Dashboard"
      description="System health and performance metrics"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      actions={
        <Button variant="outline" onClick={() => refetchSummary()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      }
    >
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Decisions Today</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingSummary ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold">{summary?.decisionsToday || 0}</div>
                <div className="flex items-center gap-1 text-xs">
                  {getTrendIcon(summary?.decisionsChange || 0)}
                  <span className={getTrendColor(summary?.decisionsChange || 0)}>
                    {Math.abs(summary?.decisionsChange || 0)}% from yesterday
                  </span>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Approval Rate</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingSummary ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold text-green-600">
                  {summary?.approvalRate || 0}%
                </div>
                <p className="text-xs text-muted-foreground">Last 7 days</p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingSummary ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold">{summary?.avgResponseTime || 0}ms</div>
                <p className="text-xs text-muted-foreground">P95 latency</p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">DLQ Size</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingSummary ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className={`text-2xl font-bold ${(summary?.dlqSize || 0) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {summary?.dlqSize || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  {(summary?.dlqSize || 0) === 0 ? 'No failed events' : 'Failed events'}
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Decision Trends Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Decision Trends
          </CardTitle>
          <CardDescription>
            Daily decisions, approvals, and rejections over the past week
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingTrends ? (
            <div className="space-y-4">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : trends && trends.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Total Decisions</TableHead>
                  <TableHead className="text-right">Approvals</TableHead>
                  <TableHead className="text-right">Rejections</TableHead>
                  <TableHead className="text-right">Approval Rate</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trends.map((trend) => {
                  const rate = trend.decisions > 0
                    ? Math.round((trend.approvals / trend.decisions) * 100)
                    : 0
                  return (
                    <TableRow key={trend.date}>
                      <TableCell className="font-medium">
                        {new Date(trend.date).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">{trend.decisions}</TableCell>
                      <TableCell className="text-right text-green-600">
                        {trend.approvals}
                      </TableCell>
                      <TableCell className="text-right text-red-600">
                        {trend.rejections}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant={rate >= 90 ? 'success' : rate >= 70 ? 'warning' : 'destructive'}>
                          {rate}%
                        </Badge>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="py-12 text-center text-muted-foreground">
              <Clock className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
              <p>No trend data available yet</p>
              <p className="text-sm">Trends will appear once decisions are processed</p>
            </div>
          )}
        </CardContent>
      </Card>
    </DomainPage>
  )
}
