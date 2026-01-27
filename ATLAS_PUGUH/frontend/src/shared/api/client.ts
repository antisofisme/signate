/**
 * ATLAS_PUGUH - Centralized API Client
 * Following ATLAS_PANDAWA standards
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios'

// API Response types
export interface ApiResponse<T = unknown> {
  success: boolean
  data: T
  meta?: {
    page?: number
    limit?: number
    total?: number
    totalPages?: number
  }
}

export interface ApiError {
  success: false
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
}

// Generate unique request ID
function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// Convert snake_case to camelCase
function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

// Recursively transform object keys from snake_case to camelCase
function transformKeys(obj: unknown): unknown {
  if (obj === null || obj === undefined) {
    return obj
  }

  if (Array.isArray(obj)) {
    return obj.map(transformKeys)
  }

  if (typeof obj === 'object') {
    const transformed: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      const camelKey = snakeToCamel(key)
      transformed[camelKey] = transformKeys(value)
    }
    return transformed
  }

  return obj
}

// Create API client instance
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - Add auth & tenant context
apiClient.interceptors.request.use(
  (config) => {
    // Get tokens from localStorage
    const token = localStorage.getItem('accessToken')
    const tenantId = localStorage.getItem('activeTenantId')

    // Add headers
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId
    }
    config.headers['X-Request-ID'] = generateRequestId()

    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - Transform keys & handle errors
apiClient.interceptors.response.use(
  (response) => {
    // Transform snake_case to camelCase
    if (response.data) {
      response.data = transformKeys(response.data)
    }
    return response
  },
  (error: AxiosError<ApiError>) => {
    // Handle 401 - Unauthorized
    if (error.response?.status === 401) {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('activeTenantId')
      window.location.href = '/auth/login'
      return Promise.reject(error)
    }

    // Handle 403 - Forbidden
    if (error.response?.status === 403) {
      console.error('Access denied:', error.response.data)
    }

    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message)
    }

    return Promise.reject(error)
  }
)

// Export typed API methods
export const api = {
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<ApiResponse<T>>(url, config).then((res) => res.data),

  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.post<ApiResponse<T>>(url, data, config).then((res) => res.data),

  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.put<ApiResponse<T>>(url, data, config).then((res) => res.data),

  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.patch<ApiResponse<T>>(url, data, config).then((res) => res.data),

  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.delete<ApiResponse<T>>(url, config).then((res) => res.data),
}

export default apiClient
