/**
 * ATLAS_PANDAWA Frontend - Auth Store
 * Zustand global state for authentication
 */

import { create } from 'zustand'
import { User, Tenant } from '@shared/types/api'

interface AuthState {
  // State
  user: User | null
  tenant: Tenant | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean

  // Actions
  setAuth: (user: User, tenant: Tenant | null, accessToken: string, refreshToken: string) => void
  clearAuth: () => void
  updateUser: (user: User) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  // Initial state
  user: null,
  tenant: null,
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),

  // Actions
  setAuth: (user, tenant, accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    set({
      user,
      tenant,
      accessToken,
      refreshToken,
      isAuthenticated: true,
    })
  },

  clearAuth: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({
      user: null,
      tenant: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    })
  },

  updateUser: (user) => {
    set({ user })
  },
}))
