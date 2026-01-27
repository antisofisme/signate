/**
 * ATLAS_PANDAWA Frontend - Auth Hooks
 * TanStack Query hooks for authentication
 */

import { useMutation, useQuery } from '@tanstack/react-query'
import { authApi } from '../api/authApi'
import { useAuthStore } from '@stores/authStore'
import { LoginRequest, RegisterRequest } from '@shared/types/api'

/**
 * Login mutation
 */
export function useLogin() {
  const setAuth = useAuthStore((state) => state.setAuth)

  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setAuth(data.user, data.tenant || null, data.access_token, data.refresh_token)
    },
  })
}

/**
 * Register mutation
 */
export function useRegister() {
  return useMutation({
    mutationFn: authApi.register,
  })
}

/**
 * Logout mutation
 */
export function useLogout() {
  const clearAuth = useAuthStore((state) => state.clearAuth)

  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      clearAuth()
    },
  })
}

/**
 * Get current user query
 */
export function useCurrentUser() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const updateUser = useAuthStore((state) => state.updateUser)

  return useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: isAuthenticated,
    onSuccess: (data) => {
      updateUser(data)
    },
  })
}
