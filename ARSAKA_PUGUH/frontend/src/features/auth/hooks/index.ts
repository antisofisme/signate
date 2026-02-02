/**
 * Auth Hooks
 *
 * NOTE: Access tokens are now stored in httpOnly cookies by the server.
 * We only track user metadata and tenant context in the store.
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
      const { user, activeTenant, redirectUrl } = response.data

      // Store auth state (tokens are in httpOnly cookies, not accessible here)
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
        activeTenant?.tenantId
      )

      // Navigate to redirect URL or default dashboard
      navigate(redirectUrl || '/app')
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
      const { user, tenant, redirectUrl } = response.data

      // Store auth state (tokens are in httpOnly cookies)
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
        tenant?.tenantId
      )

      // Navigate to redirect URL
      navigate(redirectUrl || '/app')
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

      // Clear all queries
      queryClient.clear()

      // Navigate to home
      navigate('/')
    },
    onError: () => {
      // Even on error, clear local state and redirect
      // (cookies will be expired on server side)
      logout()
      queryClient.clear()
      navigate('/')
    },
  })
}
