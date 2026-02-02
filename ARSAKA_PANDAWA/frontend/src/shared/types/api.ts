/**
 * ARSAKA_PANDAWA Frontend - Shared API Types
 * Type definitions matching backend DTOs
 */

// ============================================
// API Response Types (CORE-STD-01)
// ============================================

export interface ApiSuccessResponse<T> {
  success: true
  data: T
  meta?: {
    total?: number
    page?: number
    limit?: number
  }
}

export interface ApiErrorResponse {
  success: false
  error: {
    code: string
    message: string
    details?: Record<string, any>
  }
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse

// ============================================
// User & Auth Types
// ============================================

export interface User {
  id: string
  username: string
  email: string
  full_name?: string
  phone?: string
  is_active: boolean
  is_verified: boolean
  created_at: string
}

export interface Tenant {
  id: string
  name: string
  slug: string
  description?: string
  subscription_status: 'trial' | 'active' | 'suspended' | 'cancelled'
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
  tenant_slug?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
  tenant?: Tenant
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
  phone?: string
  create_tenant?: boolean
  tenant_name?: string
}

// ============================================
// Module Types (Phase 2+)
// ============================================

// PMS Types
export interface Room {
  id: string
  room_number: string
  room_type_id: string
  status: 'available' | 'occupied' | 'maintenance' | 'reserved'
  floor: number
  is_active: boolean
}

export interface Reservation {
  id: string
  guest_id: string
  room_id: string
  check_in: string
  check_out: string
  status: 'pending' | 'confirmed' | 'checked_in' | 'checked_out' | 'cancelled'
  total_amount: number
}

// POS Types
export interface Product {
  id: string
  name: string
  category_id: string
  price: number
  stock: number
  is_active: boolean
}

export interface Order {
  id: string
  order_number: string
  total_amount: number
  status: 'pending' | 'processing' | 'completed' | 'cancelled'
  created_at: string
}
