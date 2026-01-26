/**
 * Workflow Domain - My Pending Approvals
 * Shows workflows assigned to current user
 * Following ATLAS_PANDAWA standards
 */

import { DomainPage } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useNavigate } from 'react-router-dom'
import { Clock, CheckCircle, XCircle, AlertTriangle, Loader2 } from 'lucide-react'
import type { Priority, Workflow } from '@/shared/types'

// Mock data - will be replaced with TanStack Query
const mockPendingWorkflows: Workflow[] = [
  {
    id: 'wf-001',
    type: 'RULE_ACTIVATION',
    status: 'PENDING',
    subject: 'Activate rule: high-value-purchase',
    requestedBy: '1',
    requestedByName: 'operator1',
    priority: 'high',
    dueAt: '2026-01-25T08:00:00Z',
    createdAt: '2026-01-24T08:00:00Z',
  },
  {
    id: 'wf-002',
    type: 'RULE_ACTIVATION',
    status: 'PENDING',
    subject: 'Activate rule: suspicious-activity',
    requestedBy: '2',
    requestedByName: 'admin',
    priority: 'medium',
    dueAt: '2026-01-26T07:30:00Z',
    createdAt: '2026-01-24T07:30:00Z',
  },
  {
    id: 'wf-003',
    type: 'RULE_ACTIVATION',
    status: 'PENDING',
    subject: 'Activate rule: auto-approve-small',
    requestedBy: '3',
    requestedByName: 'operator2',
    priority: 'low',
    dueAt: '2026-01-28T15:00:00Z',
    createdAt: '2026-01-23T15:00:00Z',
  },
]

const priorityColors: Record<Priority, 'destructive' | 'warning' | 'secondary'> = {
  high: 'destructive',
  medium: 'warning',
  low: 'secondary',
}

export function MyPending() {
  const navigate = useNavigate()

  // TODO: Replace with TanStack Query
  // const { data: workflows, isLoading, error } = useGetPendingWorkflows()
  const workflows = mockPendingWorkflows
  const isLoading = false

  const stats = {
    pending: workflows.length,
    highPriority: workflows.filter((w) => w.priority === 'high').length,
    approvedToday: 5,
    rejectedToday: 1,
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

      {/* Pending List */}
      <div className="space-y-4">
        {workflows.map((workflow) => (
          <Card key={workflow.id} className="hover:border-workflow/50 transition-colors">
            <CardContent className="p-6">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={priorityColors[workflow.priority]}>
                      {workflow.priority}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{workflow.type}</span>
                  </div>
                  <h3 className="font-semibold">{workflow.subject}</h3>
                  <p className="text-sm text-muted-foreground">
                    Requested by <strong>{workflow.requestedByName}</strong> on{' '}
                    {new Date(workflow.createdAt).toLocaleDateString()}
                  </p>
                  {workflow.dueAt && (
                    <p className="text-xs text-muted-foreground">
                      Due: {new Date(workflow.dueAt).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    onClick={() => navigate(`/workflow/${workflow.id}`)}
                  >
                    View Details
                  </Button>
                  <Button
                    variant="workflow"
                    onClick={() => navigate(`/workflow/${workflow.id}/approve`)}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => navigate(`/workflow/${workflow.id}/reject`)}
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
