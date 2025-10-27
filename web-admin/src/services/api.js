import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001'

const api = axios.create({
  baseURL: API_BASE_URL,
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

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
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

export default api
