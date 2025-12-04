/**
 * API Client - Centralized Axios Instance
 *
 * Features:
 * - Auto JWT token injection
 * - Organization ID header
 * - Auto logout on 401
 * - Request/response interceptors
 * - Smart network detection (LAN vs Internet)
 */

import axios, { AxiosError } from 'axios';
import { toast } from '@/shared/utils/toast';
import { getSmartApiUrl } from '../config/network-detector';

// Environment variables with smart detection
const API_BASE_URL = getSmartApiUrl();
const API_VERSION = import.meta.env.VITE_API_VERSION || 'v1';
const IS_DEV = import.meta.env.DEV;

/**
 * Axios client instance
 *
 * ⚠️ IMPORTANT:
 * - baseURL set to backend API URL from environment variable
 * - Endpoints in endpoints.ts include /api/v1 prefix
 * - Direct connection to backend (no nginx proxy)
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
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
 * Response interceptor - Handle errors globally & unwrap response data
 */
apiClient.interceptors.response.use(
  (response) => {
    // Unwrap backend standard response format intelligently
    // Backend returns: { success: true, data: {...}, message?, timestamp, pagination? }

    // Don't unwrap if response has pagination or other important fields
    const hasImportantFields = response.data && (
      'pagination' in response.data ||
      'total' in response.data ||
      'organizations' in response.data
    );

    if (hasImportantFields) {
      // Keep the whole response structure for paginated/complex responses
      return response;
    }

    // For simple responses, unwrap the 'data' field
    if (response.data && typeof response.data === 'object' && 'data' in response.data) {
      response.data = response.data.data;
    }

    return response;
  },
  (error: AxiosError<{ message?: string; code?: string; detail?: string }>) => {
    // Handle 401 Unauthorized - Check for specific error codes
    if (error.response?.status === 401) {
      const errorCode = error.response?.data?.code;
      const errorMessage = error.response?.data?.message || error.response?.data?.detail;

      if (errorCode === 'SESSION_REVOKED') {
        toast.error('Sesi Anda telah berakhir. Silakan login kembali.');
      } else if (errorCode === 'TOKEN_EXPIRED') {
        toast.error('Token kadaluarsa. Mengarahkan ke halaman login...');
      } else {
        console.warn('[API] 401 Unauthorized - Logging out...', errorMessage);
      }

      localStorage.removeItem('auth-token');
      localStorage.removeItem('selected-org-id');
      window.location.href = '/login';
    }

    // Handle 403 Forbidden - No permission with user notification
    if (error.response?.status === 403) {
      const errorMessage = error.response?.data?.message || error.response?.data?.detail;
      console.error('[API] 403 Forbidden - No permission:', errorMessage);
      toast.error(errorMessage || 'Anda tidak memiliki izin untuk operasi ini');
    }

    // Handle network errors - but not for cancelled requests
    if (!error.response) {
      // Don't show toast for cancelled/aborted requests
      if (axios.isCancel(error) || error.code === 'ERR_CANCELED') {
        console.log('[API] Request cancelled:', error.message);
        return Promise.reject(error);
      }

      // Don't show toast for timeout on non-critical requests
      if (error.code === 'ECONNABORTED') {
        console.warn('[API] Request timeout:', error.config?.url);
        return Promise.reject(error);
      }

      // Only show network error toast for actual network failures
      console.error('[API] Network error:', error.message, error.code);
      // Uncomment below if you want to show toast for real network errors
      // toast.error('Koneksi gagal. Periksa jaringan Anda.');
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
