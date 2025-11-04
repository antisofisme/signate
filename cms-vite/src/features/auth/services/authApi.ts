/**
 * Authentication API Service
 *
 * LAYER 3: DATA ACCESS
 * Handles all authentication-related API calls
 */

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
} from '@/features/auth/types/auth';

/**
 * Login user
 */
export const authApi = {
  /**
   * Login with username & password
   * @param credentials - Login credentials
   * @returns User, token, and organizations
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse['data']> => {
    const { data } = await apiClient.post<LoginResponse>(
      API_ENDPOINTS.AUTH.LOGIN,
      credentials
    );
    return data.data;
  },

  /**
   * Register new user
   * @param userData - Registration data
   * @returns Created user
   */
  register: async (userData: RegisterRequest): Promise<User> => {
    const { data } = await apiClient.post(
      API_ENDPOINTS.AUTH.REGISTER,
      userData
    );
    return data.data;
  },

  /**
   * Get current user info
   * @returns Current user
   */
  me: async (): Promise<User> => {
    const { data } = await apiClient.get(API_ENDPOINTS.AUTH.ME);
    return data.data;
  },

  /**
   * Logout user
   */
  logout: async (): Promise<void> => {
    await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
  },

  /**
   * Refresh JWT token
   * @returns New token
   */
  refresh: async (): Promise<string> => {
    const { data } = await apiClient.post(API_ENDPOINTS.AUTH.REFRESH);
    return data.data.token;
  },
};
