/**
 * API Interceptors
 * Request and response interceptors for axios
 */

import { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosRequestHeaders } from 'axios';
import { useAuthStore } from '../stores/authStore';

/**
 * Setup request interceptor - Add auth token to requests
 */
export function setupRequestInterceptor(axiosInstance: AxiosInstance) {
  axiosInstance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const { token } = useAuthStore.getState();

      if (token) {
        if (!config.headers) {
          config.headers = {} as AxiosRequestHeaders;
        }
        config.headers.Authorization = `Bearer ${token}`;
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
