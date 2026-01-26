/**
 * Billing Settings Page
 *
 * Displays current subscription and usage, manage billing.
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  CreditCard,
  Calendar,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ArrowUpRight,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Textarea } from '@/components/ui/textarea'
import { UsageMeter } from '@/components/UsageMeter'
import {
  useSubscription,
  useCancelSubscription,
  useReactivateSubscription,
} from '@/features/billing'

export function BillingSettingsPage() {
  const { data, isLoading, error } = useSubscription()
  const cancelMutation = useCancelSubscription()
  const reactivateMutation = useReactivateSubscription()
  const [cancelReason, setCancelReason] = useState('')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Failed to load billing information.</p>
      </div>
    )
  }

  const { subscription, plan, usage } = data

  const getStatusBadge = () => {
    switch (subscription.status) {
      case 'active':
        return <Badge className="bg-green-500">Active</Badge>
      case 'trialing':
        return <Badge className="bg-blue-500">Trial</Badge>
      case 'past_due':
        return <Badge className="bg-yellow-500">Past Due</Badge>
      case 'cancelled':
        return <Badge variant="destructive">Cancelled</Badge>
      case 'paused':
        return <Badge variant="secondary">Paused</Badge>
      default:
        return <Badge variant="outline">{subscription.status}</Badge>
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  const handleCancel = async () => {
    try {
      await cancelMutation.mutateAsync({ reason: cancelReason })
    } catch (error) {
      console.error('Cancel error:', error)
    }
  }

  const handleReactivate = async () => {
    try {
      await reactivateMutation.mutateAsync()
    } catch (error) {
      console.error('Reactivate error:', error)
    }
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Billing & Subscription</h1>
          <p className="text-muted-foreground">Manage your subscription and billing details</p>
        </div>
        <Link to="/app/billing/pricing">
          <Button variant="outline">
            View Plans
            <ArrowUpRight className="ml-2 h-4 w-4" />
          </Button>
        </Link>
      </div>

      <div className="grid gap-6">
        {/* Current Plan */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Current Plan
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">{plan.name}</p>
                <p className="text-muted-foreground">{plan.price_display}</p>
              </div>
              <div className="text-right">
                {getStatusBadge()}
                {subscription.cancel_at_period_end && (
                  <p className="text-sm text-yellow-600 mt-1">
                    Cancels at period end
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>
                  {subscription.status === 'trialing' ? 'Trial ends' : 'Renews'}:{' '}
                  {formatDate(subscription.current_period_end)}
                </span>
              </div>
              <div>
                {subscription.days_until_renewal} days remaining
              </div>
            </div>

            <div className="flex gap-2 pt-4">
              {plan.plan_id !== 'enterprise' && (
                <Link to="/app/billing/pricing">
                  <Button>Upgrade Plan</Button>
                </Link>
              )}

              {subscription.cancel_at_period_end ? (
                <Button
                  variant="outline"
                  onClick={handleReactivate}
                  disabled={reactivateMutation.isPending}
                >
                  {reactivateMutation.isPending && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  Reactivate
                </Button>
              ) : (
                plan.plan_id !== 'free' && (
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline">Cancel Subscription</Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Cancel Subscription?</AlertDialogTitle>
                        <AlertDialogDescription>
                          Your subscription will remain active until{' '}
                          {formatDate(subscription.current_period_end)}. After that,
                          you'll be downgraded to the Free plan.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <div className="py-4">
                        <label className="text-sm font-medium">
                          Reason for cancellation (optional)
                        </label>
                        <Textarea
                          value={cancelReason}
                          onChange={(e) => setCancelReason(e.target.value)}
                          placeholder="Help us improve..."
                          className="mt-2"
                        />
                      </div>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Keep Subscription</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={handleCancel}
                          className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                          {cancelMutation.isPending && (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          )}
                          Cancel Subscription
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                )
              )}
            </div>
          </CardContent>
        </Card>

        {/* Usage */}
        <Card>
          <CardHeader>
            <CardTitle>Usage This Month</CardTitle>
            <CardDescription>
              Your usage resets on the 1st of each month
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <UsageMeter
              label="Decisions"
              used={usage.decisions_used}
              limit={usage.decisions_limit}
            />

            {usage.is_near_limit && !usage.is_over_limit && (
              <div className="flex items-center gap-2 p-4 bg-yellow-50 text-yellow-800 rounded-lg">
                <AlertTriangle className="h-5 w-5" />
                <div>
                  <p className="font-medium">Approaching limit</p>
                  <p className="text-sm">
                    You've used {Math.round(usage.usage_percentage)}% of your monthly
                    decisions. Consider upgrading to avoid interruptions.
                  </p>
                </div>
              </div>
            )}

            {usage.is_over_limit && (
              <div className="flex items-center gap-2 p-4 bg-red-50 text-red-800 rounded-lg">
                <XCircle className="h-5 w-5" />
                <div>
                  <p className="font-medium">Limit exceeded</p>
                  <p className="text-sm">
                    You've exceeded your monthly decision limit. Upgrade your plan
                    to continue creating decisions.
                  </p>
                  <Link to="/app/billing/pricing" className="text-sm underline">
                    Upgrade now
                  </Link>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Invoice History Link */}
        <Card>
          <CardHeader>
            <CardTitle>Invoice History</CardTitle>
            <CardDescription>View and download past invoices</CardDescription>
          </CardHeader>
          <CardContent>
            <Link to="/app/billing/invoices">
              <Button variant="outline">
                View Invoices
                <ArrowUpRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default BillingSettingsPage
