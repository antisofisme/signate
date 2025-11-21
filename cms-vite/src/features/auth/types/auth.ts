/**
 * Auth Types & Interfaces
 * Maps to backend DTOs from services/auth/dtos.py
 */

// =============================================================================
// USER & ORGANIZATION TYPES
// =============================================================================

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'user';
  organization_id: number | null;
  is_active: boolean;

  // RBAC fields (extended for permission checking)
  role_id?: number;
  role_name?: string;
  permissions?: Record<string, string[]>;  // {resource: [actions]}
}

export interface Organization {
  id: number;
  name: string;
  organization_pin?: string; // REMOVED: Organization PIN (No-PIN flow)
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// =============================================================================
// AUTH STATE
// =============================================================================

export interface AuthState {
  user: User | null;
  token: string | null;
  organizations: Organization[];
  selectedOrgId: number | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// =============================================================================
// LOGIN
// =============================================================================

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  data: {
    user: User;
    token: string;
    organizations: Organization[];
  };
  message: string;
}

// =============================================================================
// REGISTER
// =============================================================================

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
  organization_id?: number | null;
}

export interface RegisterResponse {
  success: boolean;
  data: User;
  message: string;
}

// =============================================================================
// FORGOT PASSWORD
// =============================================================================

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  message: string;
  reset_token?: string;  // Only included in development mode
  expires_in_minutes?: number;
}

// =============================================================================
// RESET PASSWORD
// =============================================================================

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ResetPasswordResponse {
  message: string;
}

// =============================================================================
// ERROR RESPONSE
// =============================================================================

export interface AuthError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

// =============================================================================
// FORM VALIDATION
// =============================================================================

export interface LoginFormErrors {
  username?: string;
  password?: string;
}

export interface RegisterFormErrors {
  username?: string;
  email?: string;
  password?: string;
  full_name?: string;
  organization_id?: string;
}

export interface ForgotPasswordFormErrors {
  email?: string;
}

export interface ResetPasswordFormErrors {
  token?: string;
  new_password?: string;
  confirm_password?: string;
}

// =============================================================================
// RBAC PERMISSION TYPES
// =============================================================================

export type Permission = Record<string, string[]>;
export type Resource = string;
export type Action = string;

export interface PermissionCheck {
  hasPermission: boolean;
  resource: string;
  action: string;
}
