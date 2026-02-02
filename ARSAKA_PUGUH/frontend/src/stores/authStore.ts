/**
 * ARSAKA_PUGUH - Auth Store (Zustand)
 * Following ARSAKA_PANDAWA standards
 *
 * Manages authentication state:
 * - User info
 * - Active tenant context
 *
 * NOTE: Access tokens are now stored in httpOnly cookies (not accessible via JS)
 * for security. This store only tracks user metadata and auth status.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, UUID } from '@/shared/types'

interface AuthState {
  // State
  user: User | null
  activeTenantId: UUID | null
  isAuthenticated: boolean
  isLoading: boolean

  // Actions
  setUser: (user: User) => void
  setActiveTenant: (tenantId: UUID) => void
  login: (user: User, tenantId?: UUID) => void
  logout: () => void
  clearTenant: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      activeTenantId: null,
      isAuthenticated: false,
      isLoading: false,

      // Actions
      setUser: (user) =>
        set({ user, isAuthenticated: true }),

      setActiveTenant: (tenantId) => {
        // Also store in localStorage for API client
        localStorage.setItem('activeTenantId', tenantId)
        set({ activeTenantId: tenantId })
      },

      login: (user, tenantId) => {
        if (tenantId) {
          localStorage.setItem('activeTenantId', tenantId)
        }
        set({
          user,
          activeTenantId: tenantId || null,
          isAuthenticated: true,
        })
      },

      logout: () => {
        localStorage.removeItem('activeTenantId')
        set({
          user: null,
          activeTenantId: null,
          isAuthenticated: false,
        })
      },

      clearTenant: () => {
        localStorage.removeItem('activeTenantId')
        set({ activeTenantId: null })
      },
    }),
    {
      name: 'arsaka-puguh-auth',
      // Only persist non-sensitive data
      // Tokens are in httpOnly cookies (secure, not accessible via JS)
      partialize: (state) => ({
        user: state.user,
        activeTenantId: state.activeTenantId,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// Selectors
export const selectUser = (state: AuthState) => state.user
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated
export const selectActiveTenantId = (state: AuthState) => state.activeTenantId
