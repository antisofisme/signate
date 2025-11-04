/**
 * API Client - Centralized Axios Instance
 *
 * Features:
 * - Auto JWT token injection
 * - Organization ID header
 * - Auto logout on 401
 * - Request/response interceptors
 */

import axios, { AxiosError } from 'axios';

// Environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001';
const API_VERSION = import.meta.env.VITE_API_VERSION || 'v1';

/**
 * Axios client instance
 * Base URL: http://192.168.5.12:8001/api/v1
 */
export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/${API_VERSION}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor - Add auth token & org ID
 */
apiClient.interceptors.request.use(
  (config) => {
    // Add JWT token from localStorage
    const token = localStorage.getItem('auth-token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add Organization ID header
    const orgId = localStorage.getItem('selected-org-id');
    if (orgId) {
      config.headers['X-Organization-Id'] = orgId;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - Handle errors globally
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle 401 Unauthorized - Auto logout
    if (error.response?.status === 401) {
      console.warn('[API] 401 Unauthorized - Logging out...');
      localStorage.removeItem('auth-token');
      localStorage.removeItem('selected-org-id');
      window.location.href = '/login';
    }

    // Handle 403 Forbidden - No permission
    if (error.response?.status === 403) {
      console.error('[API] 403 Forbidden - No permission');
    }

    // Handle network errors
    if (!error.response) {
      console.error('[API] Network error:', error.message);
    }

    return Promise.reject(error);
  }
);

/**
 * API Response wrapper type
 */
export interface APIResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
}

/**
 * API Error response type
 */
export interface APIError {
  message: string;
  field?: string;
  details?: Record<string, any>;
}
