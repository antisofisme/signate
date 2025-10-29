/**
 * API Client Base Configuration
 *
 * Centralized axios instance with interceptors for:
 * - Automatic response unwrapping (standardized API format)
 * - Error handling and transformation
 * - Authentication token injection
 * - Debug logging
 */

import axios from 'axios'
import logger from '../../utils/logger'

// Require VITE_API_URL to be set in environment
// This prevents hardcoded IPs and ensures proper configuration
if (!import.meta.env.VITE_API_URL) {
  throw new Error(
    'VITE_API_URL environment variable is not set. ' +
    'Please create a .env file with VITE_API_URL=http://your-api-url:port'
  )
}

const API_BASE_URL = import.meta.env.VITE_API_URL

// Enable debug logging for API responses during transition
const DEBUG_API_RESPONSES = import.meta.env.VITE_DEBUG_API === 'true' || false

/**
 * Axios instance with base configuration
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Request Interceptor
 * Adds authentication token to all requests
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * Response Interceptor
 * Unwraps standardized API format and handles errors
 *
 * Standardized format: { success: true, data: {...}, meta: {...} }
 * This interceptor automatically unwraps to maintain backward compatibility
 */
api.interceptors.response.use(
  (response) => {
    // Skip unwrapping for blob responses (file downloads)
    if (response.config.responseType === 'blob') {
      if (DEBUG_API_RESPONSES) {
        logger.debug('[API] Blob response - skipping unwrap:', response.config.url)
      }
      return response
    }

    const data = response.data

    // Detect new standardized format: { success: true, data: {...}, meta: {...} }
    const isStandardizedFormat = (
      data !== null &&
      typeof data === 'object' &&
      'success' in data &&
      'data' in data &&
      'meta' in data
    )

    if (isStandardizedFormat) {
      if (DEBUG_API_RESPONSES) {
        logger.debug('[API] Unwrapping standardized response:', {
          url: response.config.url,
          success: data.success,
          hasData: !!data.data,
          meta: data.meta
        })
      }

      // Attach meta to response object for debugging/tracing
      response.meta = data.meta

      // Unwrap: response.data now contains the actual payload
      response.data = data.data

      // Attach success flag for explicit checking if needed
      response.apiSuccess = data.success

      return response
    }

    // Backward compatibility: Pass through non-standardized responses unchanged
    if (DEBUG_API_RESPONSES) {
      logger.debug('[API] Legacy response format - passing through:', response.config.url)
    }
    return response
  },
  (error) => {
    // Handle error responses
    if (error.response) {
      const errorData = error.response.data

      // Detect standardized error format
      const isStandardizedError = (
        errorData !== null &&
        typeof errorData === 'object' &&
        'success' in errorData &&
        errorData.success === false &&
        'error' in errorData
      )

      if (isStandardizedError) {
        if (DEBUG_API_RESPONSES) {
          logger.error('[API] Standardized error response:', {
            url: error.config.url,
            code: errorData.error.code,
            message: errorData.error.message,
            field: errorData.error.field,
            details: errorData.error.details
          })
        }

        // Attach meta for request tracing
        error.response.meta = errorData.meta

        // Transform standardized error to match existing error handling
        // Components expect: error.response.data.detail
        error.response.data = {
          detail: errorData.error.message,
          code: errorData.error.code,
          field: errorData.error.field,
          ...errorData.error.details
        }

        // Keep original error for advanced error handling
        error.response.standardizedError = errorData.error
      } else if (DEBUG_API_RESPONSES) {
        logger.error('[API] Legacy error format:', {
          url: error.config?.url,
          status: error.response.status,
          data: errorData
        })
      }

      // Handle 401 Unauthorized - redirect to login
      if (error.response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    } else if (DEBUG_API_RESPONSES) {
      // Network error or request setup error
      logger.error('[API] Network/Request error:', {
        message: error.message,
        config: error.config
      })
    }

    return Promise.reject(error)
  }
)

export default api

// Re-export all API modules for convenience
export { default as authAPI } from './auth'
export { default as devicesAPI } from './devices'
export { default as contentAPI } from './content'
export { default as tagsAPI } from './tags'
export { default as playlistsAPI } from './playlists'
export { default as widgetsAPI } from './widgets'
export { default as usersAPI } from './users'
export { default as settingsAPI } from './settings'
export { default as clientAPI } from './client'
export { default as activitiesAPI } from './activities'
export { default as firebirdAPI } from './firebird'
