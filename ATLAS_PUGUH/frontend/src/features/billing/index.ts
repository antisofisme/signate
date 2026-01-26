/**
 * Billing Feature Module
 *
 * Export all billing-related types, API functions, and hooks.
 */

// Types
export type {
  PlanFeatures,
  PlanLimits,
  SubscriptionPlan,
  SubscriptionStatus,
  Subscription,
  UsageInfo,
  SubscriptionDetails,
  InvoiceStatus,
  LineItem,
  Invoice,
  CheckoutData,
  CreateCheckoutRequest,
  CancelSubscriptionRequest,
  PlansListResponse,
  SubscriptionDetailsResponse,
  CheckoutResponse,
  InvoicesListResponse,
  InvoiceDetailResponse,
  SuccessResponse,
} from './types'

// API
export * as billingApi from './api'

// Hooks
export {
  billingKeys,
  usePlans,
  useSubscription,
  useCreateCheckout,
  useCancelSubscription,
  useReactivateSubscription,
  useInvoices,
  useInvoice,
} from './hooks'
