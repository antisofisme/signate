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
import { sdk } from '@/sdk'

// Mock workflow data
const mockWorkflow = {
  id: 'wf-001',
  type: 'RULE_ACTIVATION',
  subject: 'Activate rule: high-value-purchase',
  requestedBy: 'operator1',
  requestedAt: '2026-01-24T08:00:00Z',
  description: 'Activate the high-value-purchase detection rule for production use.',
  ruleId: 'rule-123',
  ruleName: 'high-value-purchase',
  conditions: { amount: { gte: 10000 } },
}

export function WorkflowApprove() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [showConfirm, setShowConfirm] = useState(false)
  const [comment, setComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleApprove = async () => {
    setIsSubmitting(true)
    try {
      // Generate idempotency key for mutation
      const idempotencyKey = sdk.generateIdempotencyKey()
      const traceId = sdk.generateTraceId()

      // This would call the SDK
      // await sdk.workflow.approve({
      //   tenant_id: currentTenant,
      //   subject_id: currentUser,
      //   subject_type: 'user',
      //   trace_id: traceId,
      //   idempotency_key: idempotencyKey,
      // }, id!, comment)

      console.log('Approving workflow:', {
        workflowId: id,
        comment,
        idempotencyKey,
        traceId,
      })

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))

      navigate('/workflow/pending', {
        state: { message: 'Workflow approved successfully' }
      })
    } catch (error) {
      console.error('Error approving workflow:', error)
    } finally {
      setIsSubmitting(false)
      setShowConfirm(false)
    }
  }

  return (
    <DomainPage
      domain="workflow"
      title="Approve Workflow"
      description={`Workflow ID: ${id}`}
      badge={{ label: 'MUTATION', variant: 'warning' }}
      backTo={`/workflow/${id}`}
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
              <div className="text-sm text-muted-foreground">Type</div>
              <Badge variant="workflow">{mockWorkflow.type}</Badge>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Requested By</div>
              <div className="font-medium">{mockWorkflow.requestedBy}</div>
            </div>
            <div className="col-span-2">
              <div className="text-sm text-muted-foreground">Subject</div>
              <div className="font-medium">{mockWorkflow.subject}</div>
            </div>
            <div className="col-span-2">
              <div className="text-sm text-muted-foreground">Description</div>
              <div className="text-sm">{mockWorkflow.description}</div>
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
              onClick={() => navigate(`/workflow/${id}`)}
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
            <AlertDialogCancel disabled={isSubmitting}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleApprove}
              disabled={isSubmitting}
              className="bg-workflow hover:bg-workflow/90"
            >
              {isSubmitting ? (
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
