/**
 * Workflow Domain - Approve Workflow
 * MUTATION - Requires confirmation
 */

import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { DomainPage, MutationWarning } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
import { CheckCircle, AlertTriangle, Loader2 } from 'lucide-react'
import { useGetWorkflow, useApproveWorkflow } from '../api'

export function WorkflowApprove() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [showConfirm, setShowConfirm] = useState(false)
  const [comment, setComment] = useState('')

  // Fetch workflow details from API
  const { data: workflowData, isLoading: isLoadingWorkflow, error: workflowError } = useGetWorkflow(id || '')

  // Use the approve mutation hook
  const approveMutation = useApproveWorkflow()

  // Handle both frontend type and backend response structure
  const workflow = workflowData as Record<string, unknown> | undefined

  const handleApprove = async () => {
    if (!id) return

    try {
      await approveMutation.mutateAsync({
        workflowId: id,
        comment: comment || undefined,
      })

      navigate('/app/workflow/pending', {
        state: { message: 'Workflow approved successfully' }
      })
    } catch (error) {
      console.error('Error approving workflow:', error)
    } finally {
      setShowConfirm(false)
    }
  }

  // Loading state
  if (isLoadingWorkflow) {
    return (
      <DomainPage domain="workflow" title="Approve Workflow">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-workflow" />
        </div>
      </DomainPage>
    )
  }

  // Error state
  if (workflowError || !workflow) {
    return (
      <DomainPage domain="workflow" title="Approve Workflow">
        <Card className="border-destructive">
          <CardContent className="py-12 text-center">
            <AlertTriangle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <h3 className="text-lg font-semibold">Workflow not found</h3>
            <p className="text-muted-foreground">The requested workflow could not be loaded.</p>
            <Button variant="outline" className="mt-4" onClick={() => navigate('/app/workflow/pending')}>
              Back to Pending
            </Button>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="workflow"
      title="Approve Workflow"
      description={`Workflow ID: ${id}`}
      badge={{ label: 'MUTATION', variant: 'warning' }}
      backTo={`/app/workflow/${id}`}
    >
      {/* Workflow Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-workflow" />
            Workflow Details
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Status</div>
              <Badge variant="workflow">
                {String(workflow.current_state || workflow.status || 'PENDING')}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Approver Role</div>
              <div className="font-medium">
                {String(workflow.approver_role || workflow.requestedByName || 'N/A')}
              </div>
            </div>
            <div className="col-span-2">
              <div className="text-sm text-muted-foreground">Workflow ID</div>
              <div className="font-medium font-mono text-sm">{String(workflow.id)}</div>
            </div>
            <div className="col-span-2">
              <div className="text-sm text-muted-foreground">Created At</div>
              <div className="text-sm">
                {workflow.created_at || workflow.createdAt
                  ? new Date(String(workflow.created_at || workflow.createdAt)).toLocaleString()
                  : 'Unknown'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Warning */}
      <MutationWarning
        action="APPROVE this workflow"
        consequences={[
          'Create a decision record',
          'Update workflow status to APPROVED',
          'Activate the associated rule',
          'Generate an audit trail entry',
          'Emit workflow.approved event',
        ]}
      />

      {/* Comment & Action */}
      <Card>
        <CardHeader>
          <CardTitle>Approval Comment (Optional)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Add a comment for the audit trail..."
            className="w-full min-h-[100px] p-3 border rounded-md text-sm"
          />

          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => navigate(`/app/workflow/${id}`)}
            >
              Cancel
            </Button>
            <Button
              variant="workflow"
              onClick={() => setShowConfirm(true)}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Approve Workflow
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Mutation error display */}
      {approveMutation.error && (
        <Card className="border-destructive">
          <CardContent className="py-4">
            <p className="text-sm text-destructive">
              Failed to approve workflow. Please try again.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Confirmation Dialog */}
      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Confirm Approval
            </AlertDialogTitle>
            <AlertDialogDescription>
              You are about to approve this workflow. This action:
              <ul className="mt-2 space-y-1 text-sm">
                <li>• Will activate the rule in production</li>
                <li>• Cannot be undone</li>
                <li>• Will be recorded in the audit trail</li>
              </ul>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={approveMutation.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleApprove}
              disabled={approveMutation.isPending}
              className="bg-workflow hover:bg-workflow/90"
            >
              {approveMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Approving...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Confirm Approval
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DomainPage>
  )
}
