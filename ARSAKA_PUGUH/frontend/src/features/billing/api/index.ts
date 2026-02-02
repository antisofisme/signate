/**
 * Billing API Functions
 */

import { apiClient } from '@/lib/api-client'
import type {
  PlansListResponse,
  SubscriptionDetailsResponse,
  CheckoutResponse,
  CreateCheckoutRequest,
  InvoicesListResponse,
  InvoiceDetailResponse,
  CancelSubscriptionRequest,
  SuccessResponse,
} from '../types'

const BASE_URL = '/billing'

/**
 * Get available subscription plans
 */
export async function getPlans(): Promise<PlansListResponse> {
  const response = await apiClient.get<PlansListResponse>(`${BASE_URL}/plans`)
  return response.data
}

/**
 * Get current subscription details
 */
export async function getSubscription(): Promise<SubscriptionDetailsResponse> {
  const response = await apiClient.get<SubscriptionDetailsResponse>(`${BASE_URL}/subscription`)
  return response.data
}

/**
 * Create checkout session for plan upgrade
 */
export async function createCheckout(data: CreateCheckoutRequest): Promise<CheckoutResponse> {
  const response = await apiClient.post<CheckoutResponse>(`${BASE_URL}/checkout`, data)
  return response.data
}

/**
 * Cancel subscription
 */
export async function cancelSubscription(data: CancelSubscriptionRequest = {}): Promise<SuccessResponse> {
  const response = await apiClient.post<SuccessResponse>(`${BASE_URL}/cancel`, data)
  return response.data
}

/**
 * Reactivate cancelled subscription
 */
export async function reactivateSubscription(): Promise<SuccessResponse> {
  const response = await apiClient.post<SuccessResponse>(`${BASE_URL}/reactivate`)
  return response.data
}

/**
 * List invoices
 */
export async function getInvoices(limit = 50, offset = 0): Promise<InvoicesListResponse> {
  const response = await apiClient.get<InvoicesListResponse>(`${BASE_URL}/invoices`, {
    params: { limit, offset },
  })
  return response.data
}

/**
 * Get specific invoice
 */
export async function getInvoice(invoiceId: string): Promise<InvoiceDetailResponse> {
  const response = await apiClient.get<InvoiceDetailResponse>(`${BASE_URL}/invoices/${invoiceId}`)
  return response.data
}
