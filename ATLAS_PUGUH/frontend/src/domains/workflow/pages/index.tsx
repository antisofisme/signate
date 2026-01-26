/**
 * Workflow Domain - Pages Barrel Export
 * 4 MUTATIONS: Approve, Reject, Escalate, Cancel
 */

export { MyPending } from './MyPending'
export { WorkflowApprove } from './WorkflowApprove'

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { DomainPage, ReadOnlyNotice, MutationWarning } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowUpRight,
  Loader2,
  FileText,
  Activity,
} from 'lucide-react'
import {
  useGetWorkflows,
  useGetWorkflow,
  useGetWorkflowStats,
  useRejectWorkflow,
  useEscalateWorkflow,
} from '../api'
import { WORKFLOW_STATUS_LABELS, WORKFLOW_STATUS_COLORS, WORKFLOW_STATUS_BADGE_VARIANTS } from '../types'
import type { WorkflowStatus, Priority } from '@/shared/types'

// ============================================
// All Workflows Page
// ============================================

export function AllWorkflows() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<WorkflowStatus | 'all'>('all')
  const [searchTerm, setSearchTerm] = useState('')

  const filters = {
    status: statusFilter === 'all' ? undefined : statusFilter,
    search: searchTerm || undefined,
  }

  const { data, isLoading, error } = useGetWorkflows(filters)
  const { data: stats } = useGetWorkflowStats()

  const priorityColors: Record<Priority, 'destructive' | 'warning' | 'secondary'> = {
    high: 'destructive',
    medium: 'warning',
    low: 'secondary',
  }

  return (
    <DomainPage
      domain="workflow"
      title="All Workflows"
      description="View and manage all workflows in the system"
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
            <div className="text-2xl font-bold text-workflow">{stats?.pending || 0}</div>
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
            <div className="text-2xl font-bold text-red-600">{stats?.highPriority || 0}</div>
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
            <div className="text-2xl font-bold text-green-600">{stats?.approvedToday || 0}</div>
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
            <div className="text-2xl font-bold text-gray-600">{stats?.rejectedToday || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search workflows..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select
              value={statusFilter}
              onValueChange={(v) => setStatusFilter(v as WorkflowStatus | 'all')}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
                <SelectItem value="ESCALATED">Escalated</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={() => { setSearchTerm(''); setStatusFilter('all'); }}>
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Workflows Table */}
      <Card>
        <CardContent className="pt-6">
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="py-12 text-center text-red-500">
              <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load workflows</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Subject</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Requested By</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items?.map((workflow) => (
                  <TableRow key={workflow.id}>
                    <TableCell className="font-medium">{workflow.subject}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{workflow.type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={priorityColors[workflow.priority]}>
                        {workflow.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={WORKFLOW_STATUS_COLORS[workflow.status] as 'success' | 'warning' | 'destructive' | 'secondary'}>
                        {WORKFLOW_STATUS_LABELS[workflow.status]}
                      </Badge>
                    </TableCell>
                    <TableCell>{workflow.requestedByName}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(workflow.createdAt).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/workflow/${workflow.id}`)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {(!data?.items || data.items.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12 text-muted-foreground">
                      No workflows found
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
// Workflow Detail Page
// ============================================

export function WorkflowDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: workflow, isLoading, error } = useGetWorkflow(id || '')

  const priorityColors: Record<Priority, 'destructive' | 'warning' | 'secondary'> = {
    high: 'destructive',
    medium: 'warning',
    low: 'secondary',
  }

  if (isLoading) {
    return (
      <DomainPage domain="workflow" title="Loading..." backTo="/workflow">
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

  if (error || !workflow) {
    return (
      <DomainPage domain="workflow" title="Error" backTo="/workflow">
        <Card>
          <CardContent className="py-12 text-center text-red-500">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
            <p>Failed to load workflow</p>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="workflow"
      title={workflow.subject}
      description={`Workflow ID: ${workflow.id}`}
      badge={{
        label: WORKFLOW_STATUS_LABELS[workflow.status],
        variant: WORKFLOW_STATUS_BADGE_VARIANTS[workflow.status]
      }}
      backTo="/workflow"
      actions={
        workflow.status === 'PENDING' && (
          <div className="flex gap-2">
            <Button
              variant="workflow"
              onClick={() => navigate(`/workflow/${id}/approve`)}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Approve
            </Button>
            <Button
              variant="destructive"
              onClick={() => navigate(`/workflow/${id}/reject`)}
            >
              <XCircle className="h-4 w-4 mr-2" />
              Reject
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(`/workflow/${id}/escalate`)}
            >
              <ArrowUpRight className="h-4 w-4 mr-2" />
              Escalate
            </Button>
          </div>
        )
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Workflow Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-muted-foreground">Type</Label>
                    <p className="mt-1">
                      <Badge variant="outline">{workflow.type}</Badge>
                    </p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Priority</Label>
                    <p className="mt-1">
                      <Badge variant={priorityColors[workflow.priority]}>
                        {workflow.priority}
                      </Badge>
                    </p>
                  </div>
                </div>
                <div>
                  <Label className="text-muted-foreground">Subject</Label>
                  <p className="mt-1 font-medium">{workflow.subject}</p>
                </div>
                {workflow.description && (
                  <div>
                    <Label className="text-muted-foreground">Description</Label>
                    <p className="mt-1">{workflow.description}</p>
                  </div>
                )}
                {workflow.context && (
                  <div>
                    <Label className="text-muted-foreground">Context Data</Label>
                    <pre className="mt-1 p-4 bg-muted rounded-md text-sm overflow-x-auto">
                      {JSON.stringify(workflow.context, null, 2)}
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
              <CardTitle className="text-base">Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-muted-foreground text-xs">Requested By</Label>
                <p className="text-sm font-medium">{workflow.requestedByName}</p>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">Created</Label>
                <p className="text-sm">{new Date(workflow.createdAt).toLocaleString()}</p>
              </div>
              {workflow.dueAt && (
                <div>
                  <Label className="text-muted-foreground text-xs">Due Date</Label>
                  <p className="text-sm">{new Date(workflow.dueAt).toLocaleString()}</p>
                </div>
              )}
              {workflow.assignedTo && (
                <div>
                  <Label className="text-muted-foreground text-xs">Assigned To</Label>
                  <p className="text-sm">{workflow.assignedToName}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Activity Log
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="p-1 bg-blue-100 rounded-full">
                    <Clock className="h-3 w-3 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-xs font-medium">Created</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(workflow.createdAt).toLocaleString()}
                    </p>
                  </div>
                </div>
                {workflow.processedAt && (
                  <div className="flex items-start gap-3">
                    <div className="p-1 bg-green-100 rounded-full">
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    </div>
                    <div>
                      <p className="text-xs font-medium">Processed</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(workflow.processedAt).toLocaleString()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DomainPage>
  )
}

// ============================================
// Workflow Reject Page (MUTATION)
// ============================================

export function WorkflowReject() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: workflow, isLoading: loadingWorkflow } = useGetWorkflow(id || '')
  const [reason, setReason] = useState('')
  const [showConfirm, setShowConfirm] = useState(false)
  const rejectWorkflow = useRejectWorkflow()

  const handleReject = async () => {
    if (!reason.trim()) return
    try {
      await rejectWorkflow.mutateAsync({
        workflowId: id!,
        reason,
      })
      navigate('/workflow/pending', {
        state: { message: 'Workflow rejected successfully' }
      })
    } catch (err) {
      console.error('Failed to reject workflow:', err)
    }
    setShowConfirm(false)
  }

  if (loadingWorkflow) {
    return (
      <DomainPage domain="workflow" title="Loading..." backTo="/workflow">
        <Skeleton className="h-64 w-full" />
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="workflow"
      title="Reject Workflow"
      description={`Workflow: ${workflow?.subject}`}
      badge={{ label: 'MUTATION', variant: 'warning' }}
      backTo={`/workflow/${id}`}
    >
      <MutationWarning
        action="REJECT this workflow"
        consequences={[
          'Create a decision record with REJECTED status',
          'Update workflow status to REJECTED',
          'Cancel any associated pending actions',
          'Generate an audit trail entry',
          'Emit workflow.rejected event',
          'Notify the requester',
        ]}
      />

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <XCircle className="h-5 w-5 text-destructive" />
            Rejection Reason
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-muted rounded-lg">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Workflow:</span>
                <span className="ml-2 font-medium">{workflow?.subject}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Requested By:</span>
                <span className="ml-2">{workflow?.requestedByName}</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="reason">Reason for Rejection *</Label>
            <Textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this workflow is being rejected..."
              rows={4}
            />
            {reason.length < 10 && reason.length > 0 && (
              <p className="text-sm text-red-500">Please provide a detailed reason (min 10 characters)</p>
            )}
          </div>

          <div className="flex gap-4 pt-4">
            <Button
              variant="outline"
              onClick={() => navigate(`/workflow/${id}`)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => setShowConfirm(true)}
              disabled={reason.length < 10}
            >
              <XCircle className="h-4 w-4 mr-2" />
              Reject Workflow
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Confirm Rejection
            </AlertDialogTitle>
            <AlertDialogDescription>
              You are about to reject this workflow. This action cannot be undone and will be recorded in the audit trail.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={rejectWorkflow.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleReject}
              disabled={rejectWorkflow.isPending}
              className="bg-destructive hover:bg-destructive/90"
            >
              {rejectWorkflow.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Rejecting...
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 mr-2" />
                  Confirm Rejection
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DomainPage>
  )
}

// ============================================
// Escalations Page
// ============================================

export function Escalations() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useGetWorkflows({ status: 'ESCALATED' })

  const priorityColors: Record<Priority, 'destructive' | 'warning' | 'secondary'> = {
    high: 'destructive',
    medium: 'warning',
    low: 'secondary',
  }

  return (
    <DomainPage
      domain="workflow"
      title="Escalations"
      description="View all escalated workflows"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
    >
      <ReadOnlyNotice domain="workflow" />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ArrowUpRight className="h-5 w-5 text-blue-500" />
            Escalated Workflows
          </CardTitle>
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
              <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load escalations</p>
            </div>
          ) : data?.items?.length === 0 ? (
            <div className="py-12 text-center">
              <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
              <h3 className="text-lg font-semibold">No Escalations</h3>
              <p className="text-muted-foreground">There are no escalated workflows at the moment.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Subject</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Escalated By</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items?.map((workflow) => (
                  <TableRow key={workflow.id}>
                    <TableCell className="font-medium">{workflow.subject}</TableCell>
                    <TableCell>
                      <Badge variant={priorityColors[workflow.priority]}>
                        {workflow.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>{workflow.requestedByName}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(workflow.createdAt).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/workflow/${workflow.id}`)}
                      >
                        View
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
// Workflow Escalate Page (MUTATION)
// ============================================

export function WorkflowEscalate() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: workflow, isLoading: loadingWorkflow } = useGetWorkflow(id || '')
  const [reason, setReason] = useState('')
  const [showConfirm, setShowConfirm] = useState(false)
  const escalateWorkflow = useEscalateWorkflow()

  const handleEscalate = async () => {
    if (!reason.trim()) return
    try {
      await escalateWorkflow.mutateAsync({
        workflowId: id!,
        reason,
      })
      navigate('/workflow/pending', {
        state: { message: 'Workflow escalated successfully' }
      })
    } catch (err) {
      console.error('Failed to escalate workflow:', err)
    }
    setShowConfirm(false)
  }

  if (loadingWorkflow) {
    return (
      <DomainPage domain="workflow" title="Loading..." backTo="/workflow">
        <Skeleton className="h-64 w-full" />
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="workflow"
      title="Escalate Workflow"
      description={`Workflow: ${workflow?.subject}`}
      badge={{ label: 'MUTATION', variant: 'warning' }}
      backTo={`/workflow/${id}`}
    >
      <MutationWarning
        action="ESCALATE this workflow"
        consequences={[
          'Update workflow status to ESCALATED',
          'Assign to higher authority',
          'Generate an audit trail entry',
          'Emit workflow.escalated event',
          'Notify the escalation team',
        ]}
      />

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ArrowUpRight className="h-5 w-5 text-blue-500" />
            Escalation Reason
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-muted rounded-lg">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Workflow:</span>
                <span className="ml-2 font-medium">{workflow?.subject}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Requested By:</span>
                <span className="ml-2">{workflow?.requestedByName}</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="reason">Reason for Escalation *</Label>
            <Textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this workflow needs to be escalated..."
              rows={4}
            />
            {reason.length < 10 && reason.length > 0 && (
              <p className="text-sm text-red-500">Please provide a detailed reason (min 10 characters)</p>
            )}
          </div>

          <div className="flex gap-4 pt-4">
            <Button
              variant="outline"
              onClick={() => navigate(`/workflow/${id}`)}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={() => setShowConfirm(true)}
              disabled={reason.length < 10}
            >
              <ArrowUpRight className="h-4 w-4 mr-2" />
              Escalate Workflow
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Confirm Escalation
            </AlertDialogTitle>
            <AlertDialogDescription>
              You are about to escalate this workflow to a higher authority. This will be recorded in the audit trail.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={escalateWorkflow.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleEscalate}
              disabled={escalateWorkflow.isPending}
            >
              {escalateWorkflow.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Escalating...
                </>
              ) : (
                <>
                  <ArrowUpRight className="h-4 w-4 mr-2" />
                  Confirm Escalation
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DomainPage>
  )
}
