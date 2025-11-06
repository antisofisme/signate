/**
 * Tags API Module
 * Device tagging, tag management, and tag-based content assignment endpoints
 */

import api from './index'

const tagsAPI = {
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

export default tagsAPI
