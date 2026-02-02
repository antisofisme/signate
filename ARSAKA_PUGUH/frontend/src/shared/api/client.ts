/**
 * ARSAKA_PUGUH - Centralized API Client
 * Following ARSAKA_PANDAWA standards
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

// Get CSRF token from cookie
function getCsrfToken(): string | null {
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrf_token') {
      return value
    }
  }
  return null
}

// Methods that don't require CSRF token (safe methods)
const SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']

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
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  // Enable cookies for httpOnly token authentication
  withCredentials: true,
})

// Request interceptor - Add tenant context, request ID & CSRF token
// Note: Auth token is now sent via httpOnly cookie (withCredentials: true)
apiClient.interceptors.request.use(
  (config) => {
    // Tenant context (stored in localStorage, not sensitive)
    const tenantId = localStorage.getItem('activeTenantId')
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId
    }

    // Add request ID for tracing
    config.headers['X-Request-ID'] = generateRequestId()

    // Add CSRF token for state-changing requests
    const method = (config.method || 'GET').toUpperCase()
    if (!SAFE_METHODS.includes(method)) {
      const csrfToken = getCsrfToken()
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken
      }
    }

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
  async (error: AxiosError<ApiError>) => {
    // Handle 401 - Unauthorized (token expired or invalid)
    if (error.response?.status === 401) {
      const errorCode = (error.response.data as ApiError)?.error?.code

      // Don't redirect if already on auth pages (prevents redirect loop)
      const isAuthPage = window.location.pathname.startsWith('/login') ||
                         window.location.pathname.startsWith('/register') ||
                         window.location.pathname.startsWith('/forgot-password') ||
                         window.location.pathname.startsWith('/reset-password')

      if (isAuthPage) {
        return Promise.reject(error)
      }

      // If token expired, try to refresh
      if (errorCode === 'TOKEN_EXPIRED') {
        try {
          // Attempt to refresh token (uses httpOnly cookie)
          await apiClient.post('/auth/refresh')
          // Retry the original request
          return apiClient.request(error.config!)
        } catch {
          // Refresh failed, clear auth state and redirect to login
          localStorage.removeItem('activeTenantId')
          localStorage.removeItem('arsaka-puguh-auth')
          window.location.href = '/login'
        }
      } else {
        // Other auth errors - clear auth state and redirect to login
        localStorage.removeItem('activeTenantId')
        localStorage.removeItem('arsaka-puguh-auth')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    // Handle 403 - Forbidden
    if (error.response?.status === 403) {
      const errorCode = (error.response.data as ApiError)?.error?.code

      // CSRF token invalid - refresh page to get new token (with guard against infinite loop)
      if (errorCode === 'CSRF_VALIDATION_FAILED') {
        const lastReload = sessionStorage.getItem('csrf_reload_time')
        const now = Date.now()
        // Only reload if we haven't reloaded in the last 5 seconds
        if (!lastReload || now - parseInt(lastReload) > 5000) {
          sessionStorage.setItem('csrf_reload_time', now.toString())
          window.location.reload()
        } else {
          console.error('CSRF validation failed - please refresh the page manually')
        }
        return Promise.reject(error)
      }

      // Security: Don't log detailed errors in production
      if (import.meta.env.DEV) {
        console.error('Access denied:', error.response.data)
      }
    }

    // Handle network errors
    if (!error.response) {
      if (import.meta.env.DEV) {
        console.error('Network error:', error.message)
      }
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
