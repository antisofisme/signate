/**
 * Billing React Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as billingApi from '../api'
import type { CreateCheckoutRequest, CancelSubscriptionRequest } from '../types'

// Query Keys
export const billingKeys = {
  all: ['billing'] as const,
  plans: () => [...billingKeys.all, 'plans'] as const,
  subscription: () => [...billingKeys.all, 'subscription'] as const,
  invoices: () => [...billingKeys.all, 'invoices'] as const,
  invoice: (id: string) => [...billingKeys.invoices(), id] as const,
}

/**
 * Get subscription plans
 */
export function usePlans() {
  return useQuery({
    queryKey: billingKeys.plans(),
    queryFn: billingApi.getPlans,
    staleTime: 1000 * 60 * 60, // 1 hour - plans rarely change
  })
}

/**
 * Get current subscription
 */
export function useSubscription() {
  return useQuery({
    queryKey: billingKeys.subscription(),
    queryFn: billingApi.getSubscription,
    staleTime: 1000 * 60, // 1 minute
  })
}

/**
 * Create checkout session
 */
export function useCreateCheckout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateCheckoutRequest) => billingApi.createCheckout(data),
    onSuccess: () => {
      // Invalidate subscription to refresh after payment
      queryClient.invalidateQueries({ queryKey: billingKeys.subscription() })
    },
  })
}

/**
 * Cancel subscription
 */
export function useCancelSubscription() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data?: CancelSubscriptionRequest) => billingApi.cancelSubscription(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.subscription() })
    },
  })
}

/**
 * Reactivate subscription
 */
export function useReactivateSubscription() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: billingApi.reactivateSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.subscription() })
    },
  })
}

/**
 * Get invoices
 */
export function useInvoices(limit = 50, offset = 0) {
  return useQuery({
    queryKey: [...billingKeys.invoices(), { limit, offset }],
    queryFn: () => billingApi.getInvoices(limit, offset),
  })
}

/**
 * Get specific invoice
 */
export function useInvoice(invoiceId: string) {
  return useQuery({
    queryKey: billingKeys.invoice(invoiceId),
    queryFn: () => billingApi.getInvoice(invoiceId),
    enabled: !!invoiceId,
  })
}
