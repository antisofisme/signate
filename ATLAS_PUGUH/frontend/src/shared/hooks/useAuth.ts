/**
 * ATLAS_PUGUH - useAuth Hook
 * Provides authentication utilities
 */

import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/stores'
import type { User } from '@/shared/types'

export function useAuth() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const {
    user,
    accessToken,
    activeTenantId,
    isAuthenticated,
    login: storeLogin,
    logout: storeLogout,
    setActiveTenant,
  } = useAuthStore()

  // Login handler
  const login = useCallback(
    async (email: string, _password: string) => {
      // In real app, call API
      // const response = await api.post('/auth/login', { email, password: _password })
      // For now, mock login
      const mockUser: User = {
        id: '1',
        email,
        name: 'Admin User',
        role: 'ADMIN',
        tenants: [
          {
            tenantId: '1',
            tenantName: 'Demo Tenant',
            role: 'ADMIN',
            permissions: ['*'],
          },
        ],
        permissions: ['*'],
        createdAt: new Date().toISOString(),
      }
      const mockToken = 'mock-jwt-token'

      storeLogin(mockUser, mockToken)
      localStorage.setItem('accessToken', mockToken)

      // If user has multiple tenants, redirect to tenant picker
      if (mockUser.tenants.length > 1) {
        navigate('/auth/select-tenant')
      } else if (mockUser.tenants.length === 1) {
        // Auto-select single tenant
        switchTenant(mockUser.tenants[0].tenantId)
      }
    },
    [storeLogin, navigate]
  )

  // Logout handler
  const logout = useCallback(() => {
    storeLogout()
    localStorage.removeItem('accessToken')
    localStorage.removeItem('activeTenantId')
    queryClient.clear() // Clear all cached data
    navigate('/auth/login')
  }, [storeLogout, queryClient, navigate])

  // Switch tenant
  const switchTenant = useCallback(
    (tenantId: string) => {
      // Validate user has access
      if (!user?.tenants.find((t) => t.tenantId === tenantId)) {
        throw new Error('Access denied to this tenant')
      }

      // Update state
      setActiveTenant(tenantId)
      localStorage.setItem('activeTenantId', tenantId)

      // Clear all queries (prevent stale tenant data)
      queryClient.clear()

      // Navigate to dashboard
      navigate('/workflow/pending')
    },
    [user, setActiveTenant, queryClient, navigate]
  )

  // Check permission
  const hasPermission = useCallback(
    (permission: string): boolean => {
      if (!user) return false
      if (user.permissions.includes('*')) return true
      return user.permissions.includes(permission)
    },
    [user]
  )

  return {
    user,
    accessToken,
    activeTenantId,
    isAuthenticated,
    login,
    logout,
    switchTenant,
    hasPermission,
  }
}
