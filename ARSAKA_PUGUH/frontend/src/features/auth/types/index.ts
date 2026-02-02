/**
 * ARSAKA_PUGUH - Auth Types
 * Source: INFRA-LAY2-005-identity-api-contracts.md
 */

export interface User {
  userId: string
  email: string
  displayName: string | null
  avatarUrl?: string | null
}

export interface ProjectInfo {
  projectId: string
  name: string
  slug: string
  isDefault: boolean
}

export interface TenantInfo {
  tenantId: string
  name: string
  slug: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
  projects: ProjectInfo[]
}

// ============================================
// Register
// ============================================

export interface RegisterRequest {
  email: string
  password: string
  displayName: string
}

export interface RegisterResponse {
  success: boolean
  data: {
    userId: string
    email: string
    displayName: string
    status: string
    message: string
  }
}

// ============================================
// Login
// ============================================

export interface LoginRequest {
  email: string
  password: string
  rememberMe?: boolean
}

export interface LoginResponse {
  success: boolean
  data: {
    user: User
    accessToken: string
    refreshToken: string
    expiresIn: number
    tenants: TenantInfo[]
    activeTenant: TenantInfo | null
    activeProject: ProjectInfo | null
    requiresContextSelection: boolean
    redirectUrl: string
  }
}

// ============================================
// Verify Email
// ============================================

export interface VerifyEmailResponse {
  success: boolean
  data: {
    user: {
      userId: string
      email: string
      displayName: string | null
      status: string
    }
    accessToken: string
    refreshToken: string
    expiresIn: number
    tenant: {
      tenantId: string
      name: string
      slug: string
    } | null
    project: {
      projectId: string
      name: string
      slug: string
    } | null
    redirectUrl: string
  }
}

// ============================================
// Forgot/Reset Password
// ============================================

export interface ForgotPasswordRequest {
  email: string
}

export interface ForgotPasswordResponse {
  success: boolean
  data: {
    message: string
  }
}

export interface ResetPasswordRequest {
  token: string
  newPassword: string
}

export interface ResetPasswordResponse {
  success: boolean
  data: {
    message: string
  }
}

// ============================================
// Token Refresh
// ============================================

export interface RefreshResponse {
  success: boolean
  data: {
    accessToken: string
    expiresIn: number
  }
}

// ============================================
// API Error
// ============================================

export interface AuthError {
  success: false
  error: {
    code: string
    message: string
    field?: string
    details?: Record<string, unknown>
    canResend?: boolean
    unlockAt?: string
  }
}
