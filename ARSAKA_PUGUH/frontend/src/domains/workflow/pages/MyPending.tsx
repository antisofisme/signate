/**
 * Workflow Domain - My Pending Approvals
 * Shows workflows assigned to current user
 * Following ARSAKA_PANDAWA standards
 */

import { DomainPage } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useNavigate } from 'react-router-dom'
import { Clock, CheckCircle, XCircle, AlertTriangle, Loader2 } from 'lucide-react'
import { useGetPendingWorkflows, useGetWorkflowStats } from '../api'

export function MyPending() {
  const navigate = useNavigate()

  // Use real API hooks
  const { data: pendingData, isLoading: isPendingLoading, error: pendingError } = useGetPendingWorkflows()
  const { data: statsData, isLoading: isStatsLoading } = useGetWorkflowStats()

  const workflows = pendingData || []
  const isLoading = isPendingLoading || isStatsLoading

  const stats = {
    pending: statsData?.pending || workflows.length,
    highPriority: 0, // API doesn't provide this, could filter workflows by priority if available
    approvedToday: statsData?.approved || 0,
    rejectedToday: statsData?.rejected || 0,
  }

  if (isLoading) {
    return (
      <DomainPage domain="workflow" title="My Pending Approvals">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-workflow" />
        </div>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="workflow"
      title="My Pending Approvals"
      description={`${stats.pending} workflow(s) waiting for your action`}
      badge={{ label: `${stats.pending} pending`, variant: 'warning' }}
    >
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-workflow">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              High Priority
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.highPriority}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Approved Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.approvedToday}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <XCircle className="h-4 w-4 text-gray-500" />
              Rejected Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{stats.rejectedToday}</div>
          </CardContent>
        </Card>
      </div>

      {/* Error state */}
      {pendingError && (
        <Card className="border-destructive">
          <CardContent className="py-6 text-center">
            <AlertTriangle className="h-8 w-8 mx-auto text-destructive mb-2" />
            <p className="text-sm text-muted-foreground">
              Failed to load pending workflows. Please try again.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Pending List */}
      <div className="space-y-4">
        {workflows.map((workflow: Record<string, unknown>) => (
          <Card key={String(workflow.id)} className="hover:border-workflow/50 transition-colors">
            <CardContent className="p-6">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="warning">
                      {String(workflow.current_state || workflow.status || 'PENDING')}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {String(workflow.approver_role || workflow.type || 'Approval')}
                    </span>
                  </div>
                  <h3 className="font-semibold">
                    {String(workflow.subject || `Workflow ${String(workflow.id).slice(0, 8)}...`)}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {workflow.requestedByName ? (
                      <>Requested by <strong>{String(workflow.requestedByName)}</strong> on{' '}</>
                    ) : (
                      'Created on '
                    )}
                    {workflow.created_at || workflow.createdAt
                      ? new Date(String(workflow.created_at || workflow.createdAt)).toLocaleDateString()
                      : 'Unknown date'}
                  </p>
                  {(workflow.dueAt || workflow.escalation_timeout_at) && (
                    <p className="text-xs text-muted-foreground">
                      Due: {new Date(String(workflow.dueAt || workflow.escalation_timeout_at)).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    onClick={() => navigate(`/app/workflow/${workflow.id}`)}
                  >
                    View Details
                  </Button>
                  <Button
                    variant="workflow"
                    onClick={() => navigate(`/app/workflow/${workflow.id}/approve`)}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => navigate(`/app/workflow/${workflow.id}/reject`)}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {workflows.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
            <h3 className="text-lg font-semibold">All caught up!</h3>
            <p className="text-muted-foreground">No pending approvals at the moment.</p>
          </CardContent>
        </Card>
      )}
    </DomainPage>
  )
}
