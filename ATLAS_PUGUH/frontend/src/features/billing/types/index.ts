/**
 * Billing Feature Types
 */

// Plan types
export interface PlanFeatures {
  api_access: boolean
  sso: boolean
  priority_support: boolean
  dedicated_support: boolean
  sla_guarantee: boolean
  custom_branding: boolean
}

export interface PlanLimits {
  max_projects: number | null
  max_decisions_per_month: number | null
  max_team_members: number | null
  max_rules: number | null
  audit_retention_days: number
}

export interface SubscriptionPlan {
  plan_id: string
  name: string
  price_cents: number
  currency: string
  billing_interval: 'month' | 'year'
  limits: PlanLimits
  features: PlanFeatures
  trial_days: number
  is_active: boolean
  display_order: number
  price_display: string
}

// Subscription types
export type SubscriptionStatus = 'trialing' | 'active' | 'past_due' | 'cancelled' | 'paused'

export interface Subscription {
  subscription_id: string
  tenant_id: string
  plan_id: string
  status: SubscriptionStatus
  current_period_start: string
  current_period_end: string
  trial_end_at: string | null
  cancel_at_period_end: boolean
  cancelled_at: string | null
  decisions_this_month: number
  days_until_renewal: number
}

export interface UsageInfo {
  decisions_used: number
  decisions_limit: number | null
  usage_percentage: number
  is_near_limit: boolean
  is_over_limit: boolean
}

export interface SubscriptionDetails {
  subscription: Subscription
  plan: SubscriptionPlan
  usage: UsageInfo
}

// Invoice types
export type InvoiceStatus = 'draft' | 'pending' | 'paid' | 'failed' | 'cancelled' | 'refunded'

export interface LineItem {
  description: string
  quantity: number
  unit_price_cents: number
  amount_cents: number
}

export interface Invoice {
  invoice_id: string
  tenant_id: string
  invoice_number: string
  amount_cents: number
  currency: string
  line_items: LineItem[]
  tax_rate: number
  tax_amount_cents: number
  total_cents: number
  status: InvoiceStatus
  invoice_date: string
  due_date: string
  paid_at: string | null
  created_at: string
  amount_display: string
}

// Checkout types
export interface CheckoutData {
  invoice_id: string
  invoice_number: string
  amount_cents: number
  currency: string
  snap_token: string
  redirect_url: string
}

// Request types
export interface CreateCheckoutRequest {
  plan_id: string
}

export interface CancelSubscriptionRequest {
  reason?: string
  immediate?: boolean
}

// Response types
export interface PlansListResponse {
  success: boolean
  data: SubscriptionPlan[]
}

export interface SubscriptionDetailsResponse {
  success: boolean
  data: Subscription
  plan: SubscriptionPlan
  usage: UsageInfo
}

export interface CheckoutResponse {
  success: boolean
  data: CheckoutData
}

export interface InvoicesListResponse {
  success: boolean
  data: Invoice[]
}

export interface InvoiceDetailResponse {
  success: boolean
  data: Invoice
}

export interface SuccessResponse {
  success: boolean
  message: string
}
