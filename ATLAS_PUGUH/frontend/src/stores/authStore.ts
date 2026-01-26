/**
 * ATLAS_PUGUH - Auth Store (Zustand)
 * Following ATLAS_PANDAWA standards
 *
 * Manages authentication state:
 * - User info
 * - Access token
 * - Active tenant context
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, UUID } from '@/shared/types'

interface AuthState {
  // State
  user: User | null
  accessToken: string | null
  activeTenantId: UUID | null
  isAuthenticated: boolean
  isLoading: boolean

  // Actions
  setUser: (user: User) => void
  setAccessToken: (token: string) => void
  setActiveTenant: (tenantId: UUID) => void
  login: (user: User, token: string) => void
  logout: () => void
  clearTenant: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      accessToken: null,
      activeTenantId: null,
      isAuthenticated: false,
      isLoading: false,

      // Actions
      setUser: (user) =>
        set({ user, isAuthenticated: true }),

      setAccessToken: (token) =>
        set({ accessToken: token }),

      setActiveTenant: (tenantId) =>
        set({ activeTenantId: tenantId }),

      login: (user, token) =>
        set({
          user,
          accessToken: token,
          isAuthenticated: true,
        }),

      logout: () =>
        set({
          user: null,
          accessToken: null,
          activeTenantId: null,
          isAuthenticated: false,
        }),

      clearTenant: () =>
        set({ activeTenantId: null }),
    }),
    {
      name: 'atlas-puguh-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        activeTenantId: state.activeTenantId,
      }),
    }
  )
)

// Selectors
export const selectUser = (state: AuthState) => state.user
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated
export const selectActiveTenantId = (state: AuthState) => state.activeTenantId
