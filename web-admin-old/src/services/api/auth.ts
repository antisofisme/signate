/**
 * Auth API Module
 * Authentication and authorization endpoints
 */

import api from './index'

const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  logout: () => api.post('/api/auth/logout'),
  me: () => api.get('/api/auth/me'),
}

export default authAPI
