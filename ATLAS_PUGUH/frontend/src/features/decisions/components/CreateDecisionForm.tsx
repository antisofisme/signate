/**
 * Create Decision Form Component - Phase A+
 * Simple form to submit new decision requests
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm, type SubmitHandler } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { createDecision } from '../api/decisions'
import type { CreateDecisionRequest } from '../types/Decision'

// Zod validation schema
const decisionFormSchema = z.object({
  decision_type: z.string().min(1, 'Decision type is required'),
  amount: z.number().min(0, 'Amount must be positive').optional(),
  description: z.string().optional(),
  requester_user_id: z.string().optional(),
})

type DecisionFormData = z.infer<typeof decisionFormSchema>

export function CreateDecisionForm() {
  const navigate = useNavigate()
  const [submitResult, setSubmitResult] = useState<{
    decision_id: string
    outcome: string
    rule_matched_id: string | null
    workflow_id: string | null
  } | null>(null)

  // React Hook Form setup
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<DecisionFormData>({
    resolver: zodResolver(decisionFormSchema),
    defaultValues: {
      decision_type: 'purchase_request',
      amount: 0,
      description: '',
    },
  })

  // Mutation for creating decision
  const createMutation = useMutation({
    mutationFn: (data: CreateDecisionRequest) => createDecision(data),
    onSuccess: (response) => {
      setSubmitResult(response)
      // Auto-redirect after 3 seconds
      setTimeout(() => {
        navigate(`/decisions/${response.decision_id}`)
      }, 3000)
    },
  })

  // Form submit handler
  const onSubmit: SubmitHandler<DecisionFormData> = (data) => {
    const request: CreateDecisionRequest = {
      tenant_id: 'f47ac10b-58cc-4372-a567-0e02b2c3d479', // Mock tenant ID for Phase A+
      decision_type: data.decision_type,
      context: {
        amount: data.amount,
        description: data.description,
      },
      requester_user_id: data.requester_user_id,
      trace_id: `trace-${Date.now()}`,
    }

    createMutation.mutate(request)
  }

  // If submission succeeded, show result card
  if (submitResult) {
    const outcomeColors = {
      ALLOWED: 'bg-green-50 border-green-200 text-green-800',
      DENIED: 'bg-red-50 border-red-200 text-red-800',
      REQUIRE_APPROVAL: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    } as const

    const outcomeColor =
      outcomeColors[submitResult.outcome as keyof typeof outcomeColors] ||
      'bg-gray-50 border-gray-200 text-gray-800'

    return (
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Success Card */}
        <div className={`border-2 rounded-lg p-6 ${outcomeColor}`}>
          <h2 className="text-2xl font-bold mb-4">Decision Created Successfully</h2>

          <div className="space-y-3">
            <div>
              <span className="font-semibold">Decision ID:</span>
              <div className="font-mono text-sm mt-1 bg-white bg-opacity-50 p-2 rounded">
                {submitResult.decision_id}
              </div>
            </div>

            <div>
              <span className="font-semibold">Outcome:</span>
              <div className="mt-1">
                <span className="px-3 py-1 rounded bg-white bg-opacity-70 font-semibold">
                  {submitResult.outcome}
                </span>
              </div>
            </div>

            {submitResult.rule_matched_id && (
              <div>
                <span className="font-semibold">Rule Matched:</span>
                <div className="font-mono text-sm mt-1">{submitResult.rule_matched_id}</div>
              </div>
            )}

            {submitResult.workflow_id && (
              <div>
                <span className="font-semibold">Workflow Created:</span>
                <div className="font-mono text-sm mt-1">{submitResult.workflow_id}</div>
                <p className="text-sm mt-1">
                  This decision requires approval. Check the Approval Inbox.
                </p>
              </div>
            )}
          </div>

          <div className="mt-6 text-sm text-gray-600">
            Redirecting to decision detail in 3 seconds...
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={() => navigate(`/decisions/${submitResult.decision_id}`)}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-semibold"
          >
            View Decision Now
          </button>
          <button
            onClick={() => {
              setSubmitResult(null)
              reset()
            }}
            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded font-semibold"
          >
            Create Another
          </button>
        </div>
      </div>
    )
  }

  // Form UI
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white border rounded-lg p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Create New Decision</h1>
          <p className="text-sm text-gray-600 mt-1">
            Submit a decision request and see the rule engine outcome
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {/* Decision Type */}
          <div>
            <label htmlFor="decision_type" className="block text-sm font-semibold text-gray-700 mb-2">
              Decision Type *
            </label>
            <select
              id="decision_type"
              {...register('decision_type')}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="purchase_request">Purchase Request</option>
              <option value="expense_approval">Expense Approval</option>
              <option value="leave_request">Leave Request</option>
              <option value="contract_signing">Contract Signing</option>
            </select>
            {errors.decision_type && (
              <p className="text-red-600 text-sm mt-1">{errors.decision_type.message}</p>
            )}
          </div>

          {/* Amount */}
          <div>
            <label htmlFor="amount" className="block text-sm font-semibold text-gray-700 mb-2">
              Amount (USD)
            </label>
            <input
              id="amount"
              type="number"
              step="0.01"
              {...register('amount')}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter amount"
            />
            {errors.amount && (
              <p className="text-red-600 text-sm mt-1">{errors.amount.message}</p>
            )}
            <p className="text-xs text-gray-500 mt-1">
              Example: $5,000 might trigger approval workflow if threshold is $1,000
            </p>
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-semibold text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="description"
              rows={4}
              {...register('description')}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Optional description or notes"
            />
            {errors.description && (
              <p className="text-red-600 text-sm mt-1">{errors.description.message}</p>
            )}
          </div>

          {/* Requester User ID (Optional - for testing) */}
          <div>
            <label
              htmlFor="requester_user_id"
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Requester User ID (Optional)
            </label>
            <input
              id="requester_user_id"
              type="text"
              {...register('requester_user_id')}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="UUID of requester (optional)"
            />
            {errors.requester_user_id && (
              <p className="text-red-600 text-sm mt-1">{errors.requester_user_id.message}</p>
            )}
          </div>

          {/* Error Display */}
          {createMutation.isError && (
            <div className="bg-red-50 border border-red-200 rounded p-4">
              <p className="text-red-800 font-semibold">Error creating decision</p>
              <p className="text-red-600 text-sm mt-1">
                {createMutation.error instanceof Error
                  ? createMutation.error.message
                  : 'Unknown error occurred'}
              </p>
            </div>
          )}

          {/* Submit Buttons */}
          <div className="flex gap-4 pt-4 border-t">
            <button
              type="submit"
              disabled={isSubmitting || createMutation.isPending}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting || createMutation.isPending ? 'Submitting...' : 'Submit Decision'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/decisions')}
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded font-semibold"
            >
              Cancel
            </button>
          </div>
        </form>

        {/* Phase A+ Note */}
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
          <strong>Phase A+ Visibility Mode:</strong> This form submits to the existing decision
          engine. No new business logic added.
        </div>
      </div>
    </div>
  )
}
