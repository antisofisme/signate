/**
 * Auth Hooks
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import * as authApi from '../api'
import type {
  RegisterRequest,
  LoginRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
} from '../types'

/**
 * Hook for user registration
 */
export function useRegister() {
  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
  })
}

/**
 * Hook for user login
 */
export function useLogin() {
  const { login } = useAuthStore()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: (response) => {
      const { user, accessToken, activeTenant, redirectUrl } = response.data

      // Store auth state
      login(
        {
          id: user.userId,
          email: user.email,
          name: user.displayName || user.email,
          role: 'OPERATOR', // Default role, will be updated with tenant context
          tenants: [],
          permissions: [],
          createdAt: new Date().toISOString(),
        },
        accessToken
      )

      // Store tokens
      localStorage.setItem('accessToken', accessToken)
      if (activeTenant) {
        localStorage.setItem('activeTenantId', activeTenant.tenantId)
      }

      // Navigate to redirect URL
      navigate(redirectUrl)
    },
  })
}

/**
 * Hook for email verification
 */
export function useVerifyEmail() {
  const { login } = useAuthStore()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (token: string) => authApi.verifyEmail(token),
    onSuccess: (response) => {
      const { user, accessToken, tenant, redirectUrl } = response.data

      // Store auth state
      login(
        {
          id: user.userId,
          email: user.email,
          name: user.displayName || user.email,
          role: 'OPERATOR',
          tenants: [],
          permissions: [],
          createdAt: new Date().toISOString(),
        },
        accessToken
      )

      // Store tokens
      localStorage.setItem('accessToken', accessToken)
      if (tenant) {
        localStorage.setItem('activeTenantId', tenant.tenantId)
      }

      // Navigate to redirect URL
      navigate(redirectUrl)
    },
  })
}

/**
 * Hook for forgot password
 */
export function useForgotPassword() {
  return useMutation({
    mutationFn: (data: ForgotPasswordRequest) => authApi.forgotPassword(data),
  })
}

/**
 * Hook for reset password
 */
export function useResetPassword() {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: ResetPasswordRequest) => authApi.resetPassword(data),
    onSuccess: () => {
      // Navigate to login after successful reset
      navigate('/login?reset=success')
    },
  })
}

/**
 * Hook for logout
 */
export function useLogout() {
  const { logout } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      // Clear auth state
      logout()
      localStorage.removeItem('accessToken')
      localStorage.removeItem('activeTenantId')

      // Clear all queries
      queryClient.clear()

      // Navigate to home
      navigate('/')
    },
  })
}
