/**
 * Users API Module
 * User management and authentication endpoints
 */

import api from './index'

const usersAPI = {
  list: () => api.get('/api/users'),
  create: (data) => api.post('/api/users', data),
  get: (id) => api.get(`/api/users/${id}`),
  update: (id, data) => api.patch(`/api/users/${id}`, data),
  delete: (id) => api.delete(`/api/users/${id}`),
  resetPassword: (id, data) => api.post(`/api/users/${id}/reset-password`, data),
}

export default usersAPI
