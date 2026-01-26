/**
 * Pricing Page
 *
 * Displays available subscription plans with comparison.
 */

import { useState } from 'react'
import { Check, X, Loader2, CreditCard } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { usePlans, useSubscription, useCreateCheckout } from '@/features/billing'
import type { SubscriptionPlan } from '@/features/billing'

// Declare Midtrans Snap types
declare global {
  interface Window {
    snap?: {
      pay: (token: string, options: {
        onSuccess?: (result: unknown) => void
        onPending?: (result: unknown) => void
        onError?: (result: unknown) => void
        onClose?: () => void
      }) => void
    }
  }
}

export function PricingPage() {
  const { data: plansData, isLoading: plansLoading } = usePlans()
  const { data: subscriptionData } = useSubscription()
  const createCheckout = useCreateCheckout()
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)

  const plans = plansData?.data || []
  const currentPlanId = subscriptionData?.data?.plan_id

  const handleSelectPlan = async (planId: string) => {
    if (planId === currentPlanId) return
    if (planId === 'free') {
      // Downgrade handled differently
      alert('To downgrade to Free, please cancel your subscription.')
      return
    }
    if (planId === 'enterprise') {
      // Contact sales
      window.open('mailto:sales@atlaspuguh.com?subject=Enterprise Plan Inquiry', '_blank')
      return
    }

    setSelectedPlan(planId)

    try {
      const result = await createCheckout.mutateAsync({ plan_id: planId })

      // Open Midtrans Snap popup
      if (window.snap && result.data.snap_token) {
        window.snap.pay(result.data.snap_token, {
          onSuccess: () => {
            window.location.reload()
          },
          onPending: () => {
            alert('Payment pending. Please complete the payment.')
          },
          onError: () => {
            alert('Payment failed. Please try again.')
          },
          onClose: () => {
            setSelectedPlan(null)
          },
        })
      } else {
        // Fallback to redirect
        window.location.href = result.data.redirect_url
      }
    } catch (error) {
      console.error('Checkout error:', error)
      alert('Failed to create checkout. Please try again.')
    } finally {
      setSelectedPlan(null)
    }
  }

  const formatPrice = (plan: SubscriptionPlan) => {
    if (plan.price_cents === 0) {
      if (plan.plan_id === 'enterprise') return 'Custom'
      return 'Free'
    }
    const amount = plan.price_cents / 100
    return `Rp ${amount.toLocaleString()}`
  }

  const formatLimit = (value: number | null) => {
    if (value === null) return 'Unlimited'
    return value.toLocaleString()
  }

  if (plansLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Choose Your Plan</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Start for free, upgrade as you grow. All plans include core features.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
        {plans.map((plan) => {
          const isCurrent = plan.plan_id === currentPlanId
          const isPopular = plan.plan_id === 'pro'
          const isLoading = selectedPlan === plan.plan_id && createCheckout.isPending

          return (
            <Card
              key={plan.plan_id}
              className={cn(
                'relative flex flex-col',
                isPopular && 'border-primary shadow-lg',
                isCurrent && 'bg-muted/50'
              )}
            >
              {isPopular && (
                <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">
                  Most Popular
                </Badge>
              )}

              <CardHeader>
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <CardDescription>
                  <span className="text-3xl font-bold text-foreground">
                    {formatPrice(plan)}
                  </span>
                  {plan.price_cents > 0 && (
                    <span className="text-muted-foreground">/{plan.billing_interval}</span>
                  )}
                </CardDescription>
              </CardHeader>

              <CardContent className="flex-1">
                <ul className="space-y-3 text-sm">
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-500" />
                    {formatLimit(plan.limits.max_projects)} projects
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-500" />
                    {formatLimit(plan.limits.max_decisions_per_month)} decisions/mo
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-500" />
                    {formatLimit(plan.limits.max_team_members)} team members
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-500" />
                    {formatLimit(plan.limits.max_rules)} rules
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-500" />
                    {plan.limits.audit_retention_days} days audit retention
                  </li>

                  <li className="pt-2 border-t">
                    {plan.features.api_access ? (
                      <span className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-green-500" />
                        API Access
                      </span>
                    ) : (
                      <span className="flex items-center gap-2 text-muted-foreground">
                        <X className="h-4 w-4" />
                        API Access
                      </span>
                    )}
                  </li>

                  {plan.features.sso && (
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-green-500" />
                      SSO
                    </li>
                  )}

                  {plan.features.priority_support && (
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-green-500" />
                      Priority Support
                    </li>
                  )}

                  {plan.features.dedicated_support && (
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-green-500" />
                      Dedicated Support
                    </li>
                  )}

                  {plan.trial_days > 0 && (
                    <li className="flex items-center gap-2 text-primary">
                      <Check className="h-4 w-4" />
                      {plan.trial_days}-day free trial
                    </li>
                  )}
                </ul>
              </CardContent>

              <CardFooter>
                <Button
                  className="w-full"
                  variant={isPopular ? 'default' : 'outline'}
                  disabled={isCurrent || isLoading}
                  onClick={() => handleSelectPlan(plan.plan_id)}
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <CreditCard className="h-4 w-4 mr-2" />
                  )}
                  {isCurrent
                    ? 'Current Plan'
                    : plan.plan_id === 'enterprise'
                    ? 'Contact Sales'
                    : plan.plan_id === 'free'
                    ? 'Downgrade'
                    : 'Upgrade'}
                </Button>
              </CardFooter>
            </Card>
          )
        })}
      </div>

      <div className="mt-12 text-center text-sm text-muted-foreground">
        <p>All prices are in Indonesian Rupiah (IDR).</p>
        <p>Payment powered by Midtrans. Supports Credit Card, GoPay, OVO, Bank Transfer.</p>
      </div>
    </div>
  )
}

export default PricingPage
