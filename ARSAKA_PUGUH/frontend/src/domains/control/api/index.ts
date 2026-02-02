/**
 * Control Domain - API Hooks (TanStack Query)
 * READ-ONLY domain - no mutations
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { AuditRecord, SystemEvent, DLQEvent, PaginatedResponse } from '@/shared/types'
import type { AuditFilters, EventFilters, MetricsSummary, MetricsTrend } from '../types'

// Query Keys
export const controlKeys = {
  all: ['control'] as const,
  audit: () => [...controlKeys.all, 'audit'] as const,
  auditList: (filters: AuditFilters) => [...controlKeys.audit(), 'list', filters] as const,
  auditDetail: (id: string) => [...controlKeys.audit(), 'detail', id] as const,
  events: () => [...controlKeys.all, 'events'] as const,
  eventList: (filters: EventFilters) => [...controlKeys.events(), 'list', filters] as const,
  eventDetail: (id: string) => [...controlKeys.events(), 'detail', id] as const,
  dlq: () => [...controlKeys.all, 'dlq'] as const,
  metrics: () => [...controlKeys.all, 'metrics'] as const,
  metricsTrends: () => [...controlKeys.metrics(), 'trends'] as const,
}

// ============================================
// Audit Queries
// ============================================

export function useGetAuditRecords(filters?: AuditFilters) {
  return useQuery({
    queryKey: controlKeys.auditList(filters || {}),
    queryFn: () => api.get<PaginatedResponse<AuditRecord>>('/control/audit', { params: filters }),
    select: (response) => response.data,
    staleTime: 30 * 1000,
  })
}

export function useGetAuditRecord(id: string) {
  return useQuery({
    queryKey: controlKeys.auditDetail(id),
    queryFn: () => api.get<AuditRecord>(`/control/audit/${id}`),
    select: (response) => response.data,
    enabled: !!id,
  })
}

// ============================================
// Event Queries
// ============================================

export function useGetEvents(filters?: EventFilters) {
  return useQuery({
    queryKey: controlKeys.eventList(filters || {}),
    queryFn: () => api.get<PaginatedResponse<SystemEvent>>('/control/events', { params: filters }),
    select: (response) => response.data,
    staleTime: 30 * 1000,
  })
}

export function useGetEvent(id: string) {
  return useQuery({
    queryKey: controlKeys.eventDetail(id),
    queryFn: () => api.get<SystemEvent>(`/control/events/${id}`),
    select: (response) => response.data,
    enabled: !!id,
  })
}

// ============================================
// DLQ Queries
// ============================================

export function useGetDLQEvents() {
  return useQuery({
    queryKey: controlKeys.dlq(),
    queryFn: () => api.get<DLQEvent[]>('/control/dlq'),
    select: (response) => response.data,
    staleTime: 60 * 1000,
  })
}

// ============================================
// Metrics Queries
// ============================================

export function useGetMetricsSummary() {
  return useQuery({
    queryKey: controlKeys.metrics(),
    queryFn: () => api.get<MetricsSummary>('/control/metrics'),
    select: (response) => response.data,
    staleTime: 60 * 1000,
  })
}

export function useGetMetricsTrends() {
  return useQuery({
    queryKey: controlKeys.metricsTrends(),
    queryFn: () => api.get<MetricsTrend[]>('/control/metrics/trends'),
    select: (response) => response.data,
    staleTime: 5 * 60 * 1000,
  })
}
