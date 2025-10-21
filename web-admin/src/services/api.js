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
  list: () => api.get('/api/devices'),
  registerTV: (data) => api.post('/api/devices/tv', data),
  generateMonitorCode: (data) => api.post('/api/devices/monitor', data),
  activateMonitor: (data) => api.post('/api/devices/monitor/activate', data),
  update: (id, data) => api.put(`/api/devices/${id}`, data),
  delete: (id) => api.delete(`/api/devices/${id}`),
  heartbeat: (id) => api.post(`/api/devices/${id}/heartbeat`),
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
  getAssignments: (id) => api.get(`/api/content/${id}/assignments`),
}

// Client API (for testing)
export const clientAPI = {
  getPlaylist: (deviceId) => api.get(`/api/client/playlist?device_id=${deviceId}`),
  getStatus: (deviceId) => api.get(`/api/client/status?device_id=${deviceId}`),
}

export default api
