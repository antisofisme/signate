/**
 * ATLAS_PUGUH - Auth API Functions
 * Source: INFRA-LAY2-005-identity-api-contracts.md
 */

import { api } from '@/shared/api/client'
import type {
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  VerifyEmailResponse,
  ForgotPasswordRequest,
  ForgotPasswordResponse,
  ResetPasswordRequest,
  ResetPasswordResponse,
  RefreshResponse,
} from '../types'

const AUTH_BASE = '/v1/auth'

/**
 * Register a new user
 */
export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  const response = await api.post<RegisterResponse['data']>(`${AUTH_BASE}/register`, {
    email: data.email,
    password: data.password,
    display_name: data.displayName,
  })
  return { success: true, data: response.data }
}

/**
 * Login with email and password
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse['data']>(`${AUTH_BASE}/login`, {
    email: data.email,
    password: data.password,
    remember_me: data.rememberMe ?? false,
  })
  return { success: true, data: response.data }
}

/**
 * Verify email with token
 */
export async function verifyEmail(token: string): Promise<VerifyEmailResponse> {
  const response = await api.get<VerifyEmailResponse['data']>(
    `${AUTH_BASE}/verify-email?token=${encodeURIComponent(token)}`
  )
  return { success: true, data: response.data }
}

/**
 * Request password reset
 */
export async function forgotPassword(data: ForgotPasswordRequest): Promise<ForgotPasswordResponse> {
  const response = await api.post<ForgotPasswordResponse['data']>(`${AUTH_BASE}/forgot-password`, {
    email: data.email,
  })
  return { success: true, data: response.data }
}

/**
 * Reset password with token
 */
export async function resetPassword(data: ResetPasswordRequest): Promise<ResetPasswordResponse> {
  const response = await api.post<ResetPasswordResponse['data']>(`${AUTH_BASE}/reset-password`, {
    token: data.token,
    new_password: data.newPassword,
  })
  return { success: true, data: response.data }
}

/**
 * Refresh access token
 */
export async function refreshToken(): Promise<RefreshResponse> {
  const response = await api.post<RefreshResponse['data']>(`${AUTH_BASE}/refresh`)
  return { success: true, data: response.data }
}

/**
 * Logout
 */
export async function logout(): Promise<void> {
  await api.post(`${AUTH_BASE}/logout`)
}
