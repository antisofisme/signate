/**
 * Auth Store - Mock Authentication for Phase A+
 * IMPORTANT: This is mock authentication only for visibility testing
 * Real authentication will be implemented in Phase B+
 */

import { create } from 'zustand'

interface User {
  user_id: string
  username: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  login: (username: string) => void
  logout: () => void
}

// Mock users for Phase A+ testing
const MOCK_USERS: Record<string, User> = {
  admin: {
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    username: 'admin',
    role: 'ADMIN',
  },
  manager: {
    user_id: '550e8400-e29b-41d4-a716-446655440001',
    username: 'manager',
    role: 'MANAGER',
  },
  user: {
    user_id: '550e8400-e29b-41d4-a716-446655440002',
    username: 'user',
    role: 'USER',
  },
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,

  login: (username: string) => {
    const user = MOCK_USERS[username]
    if (user) {
      const mockToken = `mock-jwt-token-${username}-phase-a-plus`
      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('auth_user', JSON.stringify(user))

      set({
        user,
        token: mockToken,
      })
    } else {
      alert(`User "${username}" not found. Use: admin, manager, or user`)
    }
  },

  logout: () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    set({ user: null, token: null })
  },
}))
