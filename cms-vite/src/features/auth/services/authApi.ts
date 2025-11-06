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
  RegisterResponse,
  User,
  ForgotPasswordRequest,
  ForgotPasswordResponse,
  ResetPasswordRequest,
  ResetPasswordResponse,
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
    const { data } = await apiClient.post<LoginResponse['data']>(
      API_ENDPOINTS.AUTH.LOGIN,
      credentials
    );
    // Response interceptor already unwraps { success, data } -> data
    return data;
  },

  /**
   * Register new user
   * @param userData - Registration data
   * @returns Created user
   */
  register: async (userData: RegisterRequest): Promise<User> => {
    const { data } = await apiClient.post<User>(
      API_ENDPOINTS.AUTH.REGISTER,
      userData
    );
    // Response interceptor already unwraps
    return data;
  },

  /**
   * Get current user info
   * @returns Current user
   */
  me: async (): Promise<User> => {
    const { data } = await apiClient.get<User>(API_ENDPOINTS.AUTH.ME);
    // Response interceptor already unwraps
    return data;
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
    const { data } = await apiClient.post<{ token: string }>(API_ENDPOINTS.AUTH.REFRESH);
    // Response interceptor already unwraps
    return data.token;
  },

  /**
   * Request password reset
   * @param email - User's email address
   * @returns Message and reset token (in development mode)
   */
  forgotPassword: async (
    email: ForgotPasswordRequest
  ): Promise<ForgotPasswordResponse> => {
    const { data } = await apiClient.post<ForgotPasswordResponse>(
      API_ENDPOINTS.AUTH.FORGOT_PASSWORD,
      email
    );
    return data;
  },

  /**
   * Reset password with token
   * @param resetData - Token and new password
   * @returns Success message
   */
  resetPassword: async (
    resetData: ResetPasswordRequest
  ): Promise<ResetPasswordResponse> => {
    const { data } = await apiClient.post<ResetPasswordResponse>(
      API_ENDPOINTS.AUTH.RESET_PASSWORD,
      resetData
    );
    return data;
  },
};
