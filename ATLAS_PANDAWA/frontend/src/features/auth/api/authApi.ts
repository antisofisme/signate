/**
 * ATLAS_PANDAWA Frontend - Auth API
 * API calls for authentication
 */

import { apiClient } from '@shared/api/client'
import { LoginRequest, LoginResponse, RegisterRequest, User } from '@shared/types/api'

export const authApi = {
  /**
   * Login user
   */
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', data)
    return response.data
  },

  /**
   * Register new user
   */
  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/api/v1/auth/register', data)
    return response.data
  },

  /**
   * Get current user profile
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/me')
    return response.data
  },

  /**
   * Logout user
   */
  logout: async (): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout')
  },

  /**
   * Refresh access token
   */
  refreshToken: async (refreshToken: string): Promise<{ access_token: string }> => {
    const response = await apiClient.post<{ access_token: string }>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },
}
