import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI } from '../services/api'
import logger from '../utils/logger'
import type { User, LoginCredentials, LoginResponse } from '../types/api'

/**
 * AuthContext
 *
 * Provides authentication state and functions throughout the application
 * Eliminates prop drilling for isAuthenticated and setIsAuthenticated
 *
 * Features:
 * - Persistent authentication via localStorage
 * - Auto-redirect on logout
 * - User profile management
 * - Token management
 */

// Type Definitions - extended from api.ts types

export interface AuthContextValue {
  // State
  isAuthenticated: boolean
  user: User | null
  isLoading: boolean

  // Functions
  login: (credentials: LoginCredentials) => Promise<User>
  logout: () => Promise<void>
  updateUser: (updates: Partial<User>) => void
  setIsAuthenticated: (value: boolean) => void // For backward compatibility
}

interface AuthProviderProps {
  children: ReactNode
}

// Context Creation
const AuthContext = createContext<AuthContextValue | undefined>(undefined)

// Provider Component
export function AuthProvider({ children }: AuthProviderProps) {
  const navigate = useNavigate()
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    () => !!localStorage.getItem('token')
  )
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  /**
   * Initialize auth state
   * Check if user is already logged in and fetch user data
   */
  useEffect(() => {
    const initializeAuth = async (): Promise<void> => {
      const token = localStorage.getItem('token')

      if (token) {
        try {
          // Verify token and get user info
          const response = await authAPI.me()
          setUser(response.data as User)
          setIsAuthenticated(true)
          logger.debug('[Auth] User authenticated:', response.data.username)
        } catch (error) {
          // Token invalid or expired
          logger.warn('[Auth] Token invalid, logging out')
          logout()
        }
      }

      setIsLoading(false)
    }

    initializeAuth()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /**
   * Login function
   * @param credentials - { username, password }
   * @returns User data
   */
  const login = async (credentials: LoginCredentials): Promise<User> => {
    try {
      const response = await authAPI.login(credentials)
      const loginData = response.data as LoginResponse

      // Store token
      localStorage.setItem('token', loginData.access_token)

      // Update state
      setIsAuthenticated(true)

      // Fetch user data after successful login
      const userResponse = await authAPI.me()
      const userData = userResponse.data as User
      setUser(userData)

      logger.info('[Auth] User logged in:', userData.username)

      return userData
    } catch (error) {
      logger.error('[Auth] Login failed:', error)
      throw error
    }
  }

  /**
   * Logout function
   * Clears token and user data, redirects to login
   */
  const logout = async (): Promise<void> => {
    try {
      // Call logout API to invalidate session
      await authAPI.logout()
    } catch (error) {
      // Continue with logout even if API call fails
      logger.warn('[Auth] Logout API call failed:', error)
    }

    // Clear local state
    localStorage.removeItem('token')
    setIsAuthenticated(false)
    setUser(null)

    logger.info('[Auth] User logged out')

    // Redirect to login
    navigate('/login')
  }

  /**
   * Update user profile
   * @param updates - User data updates
   */
  const updateUser = (updates: Partial<User>): void => {
    setUser(prev => prev ? {
      ...prev,
      ...updates
    } : null)
  }

  const value: AuthContextValue = {
    // State
    isAuthenticated,
    user,
    isLoading,

    // Functions
    login,
    logout,
    updateUser,
    setIsAuthenticated, // For backward compatibility (can be removed later)
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Custom hook to use auth context
 * @returns Auth context value
 * @throws Error if used outside AuthProvider
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }

  return context
}

export default AuthContext
