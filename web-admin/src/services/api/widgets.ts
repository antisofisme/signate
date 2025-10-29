/**
 * Widgets API Module
 * Widget management and assignment endpoints for overlays and dynamic content
 */

import api from './index'

const widgetsAPI = {
  list: (type) => api.get('/api/widgets', { params: { type } }),
  create: (data) => api.post('/api/widgets', data),
  get: (id) => api.get(`/api/widgets/${id}`),
  update: (id, data) => api.patch(`/api/widgets/${id}`, data),
  delete: (id) => api.delete(`/api/widgets/${id}`),
  assign: (id, data) => api.post(`/api/widgets/${id}/assign`, data),
  unassign: (id, data) => api.delete(`/api/widgets/${id}/assign`, { data }),
}

export default widgetsAPI
