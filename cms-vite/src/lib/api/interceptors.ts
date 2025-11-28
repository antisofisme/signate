/**
 * API Interceptors
 * Request and response interceptors for axios
 *
 * CRITICAL: Includes X-Organization-Id header for multi-tenancy support
 */

import { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosRequestHeaders } from 'axios';
import { useAuthStore } from '../stores/authStore';

/**
 * Setup request interceptor - Add auth token and organization header to requests
 *
 * Multi-tenancy support:
 * - Always sends X-Organization-Id header when an organization is selected
 * - For SUPER_ADMIN: Backend uses this header to filter data
 * - For regular users: Backend ignores header (uses JWT org_id for security)
 */
export function setupRequestInterceptor(axiosInstance: AxiosInstance) {
  axiosInstance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const { token, selectedOrgId } = useAuthStore.getState();

      if (!config.headers) {
        config.headers = {} as AxiosRequestHeaders;
      }

      // Add Authorization header
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Add X-Organization-Id header for multi-tenancy
      // This is critical for SUPER_ADMIN to switch between organizations
      if (selectedOrgId) {
        config.headers['X-Organization-Id'] = selectedOrgId.toString();
      }

      return config;
    },
    (error: AxiosError) => {
      return Promise.reject(error);
    }
  );
}

/**
 * Setup response interceptor - Handle 401 and auto-refresh token
 */
export function setupResponseInterceptor(axiosInstance: AxiosInstance) {
  axiosInstance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

      // Handle 401 Unauthorized
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        // Logout user on token expiration
        const { logout } = useAuthStore.getState();
        logout();

        // Redirect to login (handled by React Query or component)
        return Promise.reject(error);
      }

      return Promise.reject(error);
    }
  );
}

/**
 * Initialize all interceptors
 */
export function setupInterceptors(axiosInstance: AxiosInstance) {
  setupRequestInterceptor(axiosInstance);
  setupResponseInterceptor(axiosInstance);
}
