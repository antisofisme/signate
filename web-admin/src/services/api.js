import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001'
const IS_DEV = import.meta.env.DEV

/**
 * Development: Uses empty baseURL so /api/* endpoints are relative (proxied by Vite)
 * Production: Uses absolute URL http://192.168.5.12:8001
 */
const api = axios.create({
  baseURL: IS_DEV ? '' : API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add token
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

// Token refresh state management
let isRefreshing = false
let failedQueue = []

/**
 * Process queued requests after token refresh
 * @param {Error|null} error - Error if refresh failed
 * @param {string|null} token - New access token if refresh succeeded
 */
const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

/**
 * Refresh access token using refresh token
 * @returns {Promise<string>} New access token
 */
const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    throw new Error('No refresh token available')
  }

  const response = await axios.post(
    `${API_BASE_URL}/api/auth/refresh`,
    { refresh_token: refreshToken },
    { headers: { 'Content-Type': 'application/json' } }
  )

  // Extract tokens from standardized backend response
  const { access_token, refresh_token } = response.data.data
  localStorage.setItem('token', access_token)
  localStorage.setItem('refresh_token', refresh_token)

  return access_token
}

// Response interceptor to handle errors and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Handle 401 errors with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue concurrent requests during token refresh
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const newAccessToken = await refreshAccessToken()
        processQueue(null, newAccessToken)

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)

        // Refresh failed - clear tokens and redirect to login
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'

        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  logout: () => api.post('/api/auth/logout'),
  me: () => api.get('/api/auth/me'),
}

// Devices API
export const devicesAPI = {
  list: (params) => api.get('/api/devices', { params }),
  registerTV: (data) => api.post('/api/devices/tv', data),
  generateMonitorCode: (data) => api.post('/api/devices/monitor', data),
  activateMonitor: (data) => api.post('/api/devices/monitor/activate', data),
  update: (id, data) => api.put(`/api/devices/${id}`, data),
  delete: (id) => api.delete(`/api/devices/${id}`),
  release: (id) => api.post(`/api/devices/${id}/release`),
  replaceWithPending: (deviceId, pendingDeviceId) =>
    api.post(`/api/devices/${deviceId}/replace-with-pending/${pendingDeviceId}`),
  heartbeat: (id) => api.post(`/api/devices/${id}/heartbeat`),
  getLogs: (id, params) => api.get(`/api/devices/${id}/logs`, { params }),
  deleteLogs: (id, params) => api.delete(`/api/devices/${id}/logs`, { params }),
  queueCommand: (id, data) => api.post(`/api/devices/${id}/commands`, data),
  // Content assignment endpoints (Phase 3)
  getContent: (id, params) => api.get(`/api/devices/${id}/content`, { params }),
  assignContent: (deviceId, contentId, priority = 0) => api.post(`/api/content/${contentId}/assign`, { device_id: deviceId, priority }),
  unassignContent: (deviceId, contentId) => api.delete(`/api/devices/${deviceId}/content/${contentId}`),
  // Preview endpoint (Phase 2)
  preview: (id, params) => api.get(`/api/devices/${id}/preview`, { params }),
  // Speed Test endpoints
  getSpeedTests: (id, limit = 20) => api.get(`/api/speedtest/devices/${id}/speedtest`, { params: { limit } }),
  getLatestSpeedTest: (id) => api.get(`/api/speedtest/devices/${id}/speedtest/latest`),
}

// Content API
export const contentAPI = {
  list: () => api.get('/api/content'),
  upload: (formData) => api.post('/api/content/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  get: (id) => api.get(`/api/content/${id}`),
  update: (id, data) => api.patch(`/api/content/${id}`, data),
  delete: (id) => api.delete(`/api/content/${id}`),
  assign: (id, data) => api.post(`/api/content/${id}/assign`, data),
  unassign: (id, data) => api.delete(`/api/content/${id}/assign`, { data }),
  getAssignments: (id) => api.get(`/api/content/${id}/assignments`),
}

// Tags API
export const tagsAPI = {
  list: (params) => api.get('/api/tags', { params }),
  create: (data) => api.post('/api/tags', data),
  get: (id) => api.get(`/api/tags/${id}`),
  update: (id, data) => api.patch(`/api/tags/${id}`, data),
  delete: (id) => api.delete(`/api/tags/${id}`),
  assign: (data) => api.post('/api/tags/assign', data),
  unassign: (data) => api({
    method: 'delete',
    url: '/api/tags/assign',
    data: data
  }),
  getDevices: (id) => api.get(`/api/tags/${id}/devices`),
  // Content assignment endpoints (Phase 3)
  getContent: (id, params) => api.get(`/api/tags/${id}/content`, { params }),
  assignContent: (id, data) => api.post(`/api/tags/${id}/content`, data),
  unassignContent: (id, contentId) => api.delete(`/api/tags/${id}/content/${contentId}`),
}

// Playlists API
export const playlistsAPI = {
  list: () => api.get('/api/playlists'),
  create: (data) => api.post('/api/playlists', data),
  get: (id) => api.get(`/api/playlists/${id}`),
  update: (id, data) => api.patch(`/api/playlists/${id}`, data),
  delete: (id) => api.delete(`/api/playlists/${id}`),
  getContent: (id) => api.get(`/api/playlists/${id}/content`),
  assignContent: (id, data) => api.post(`/api/playlists/${id}/content`, data),
  removeContent: (id, contentId) => api.delete(`/api/playlists/${id}/content/${contentId}`),
  reorderContent: (id, data) => api.patch(`/api/playlists/${id}/reorder`, data),
  // Device & Tag Assignments
  getAssignments: (id) => api.get(`/api/playlists/${id}/assignments`),
  assignToDevices: (id, data) => api.post(`/api/playlists/${id}/assign/devices`, data),
  assignToTags: (id, data) => api.post(`/api/playlists/${id}/assign/tags`, data),
  unassignFromDevices: (id, data) => api.delete(`/api/playlists/${id}/assign/devices`, { data }),
  unassignFromTags: (id, data) => api.delete(`/api/playlists/${id}/assign/tags`, { data }),
}

// Widgets API
export const widgetsAPI = {
  list: (type) => api.get('/api/widgets', { params: { type } }),
  create: (data) => api.post('/api/widgets', data),
  get: (id) => api.get(`/api/widgets/${id}`),
  update: (id, data) => api.patch(`/api/widgets/${id}`, data),
  delete: (id) => api.delete(`/api/widgets/${id}`),
  assign: (id, data) => api.post(`/api/widgets/${id}/assign`, data),
  unassign: (id, data) => api.delete(`/api/widgets/${id}/assign`, { data }),
}

// Users API
export const usersAPI = {
  list: () => api.get('/api/users'),
  create: (data) => api.post('/api/users', data),
  get: (id) => api.get(`/api/users/${id}`),
  update: (id, data) => api.patch(`/api/users/${id}`, data),
  delete: (id) => api.delete(`/api/users/${id}`),
  resetPassword: (id, data) => api.post(`/api/users/${id}/reset-password`, data),
}

// Settings API
export const settingsAPI = {
  // System Settings
  getSystemInfo: () => api.get('/api/settings/system/info'),
  backupDatabase: () => api.get('/api/settings/system/backup', {
    responseType: 'blob',
  }),
  clearCache: () => api.post('/api/settings/system/clear-cache'),
}

// Client API (for testing)
export const clientAPI = {
  getPlaylist: (deviceId) => api.get(`/api/client/playlist?device_id=${deviceId}`),
  getStatus: (deviceId) => api.get(`/api/client/status?device_id=${deviceId}`),
}

// Activities API (FASE 3: Activity Logs)
export const activitiesAPI = {
  list: (params) => api.get('/api/activities', { params }),
  stats: () => api.get('/api/activities/stats'),
  get: (id) => api.get(`/api/activities/${id}`),
  create: (data) => api.post('/api/activities', data),
  cleanup: (retentionDays = 90) => api.delete('/api/activities/cleanup', { params: { retention_days: retentionDays } }),
}

// Firebird API (SystemPMS Integration)
export const firebirdAPI = {
  listConfigs: () => api.get('/api/firebird/configs'),
  getConfig: (id) => api.get(`/api/firebird/configs/${id}`),
  createConfig: (data) => api.post('/api/firebird/configs', data),
  updateConfig: (id, data) => api.put(`/api/firebird/configs/${id}`, data),
  deleteConfig: (id) => api.delete(`/api/firebird/configs/${id}`),
  testConnection: (id) => api.post(`/api/firebird/configs/${id}/test`),
  getHealth: (id) => api.get(`/api/firebird/configs/${id}/health`),
  executeQuery: (id, query) => api.post(`/api/firebird/configs/${id}/query`, { query }),
}

export default api
