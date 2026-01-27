/**
 * ATLAS_PANDAWA Frontend - Auth Types
 * Feature-specific types for authentication
 */

// Re-export shared types
export type { User, Tenant, LoginRequest, RegisterRequest } from '@shared/types/api'

// Feature-specific types
export interface AuthFormData {
  username: string
  password: string
  tenant_slug?: string
}

export interface RegisterFormData {
  username: string
  email: string
  password: string
  confirmPassword: string
  full_name?: string
  create_tenant?: boolean
  tenant_name?: string
}
