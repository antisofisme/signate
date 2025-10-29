/**
 * Content API Module
 * Media content management, upload, and assignment endpoints
 */

import api from './index'

const contentAPI = {
  list: () => api.get('/api/content/').then((res: any) => ({
    items: res.data,  // unwrapped array from interceptor
    total: res.meta?.total || res.data.length  // get total from meta
  })),  // trailing slash required for FastAPI
  upload: (formData) => api.post('/api/content/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  get: (id) => api.get(`/api/content/${id}`),
  update: (id, data) => api.patch(`/api/content/${id}`, data),
  delete: (id) => api.delete(`/api/content/${id}`),
  // Content-centric assignment endpoints (for viewing which devices have this content)
  // Note: For device-centric operations, use devicesAPI.assignContent() instead
  assign: (id, data) => api.post(`/api/content/${id}/assign`, data),
  unassign: (id, data) => api.delete(`/api/content/${id}/assign`, { data }),
  getAssignments: (id) => api.get(`/api/content/${id}/assignments`),
}

export default contentAPI
