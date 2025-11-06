/**
 * Devices API Module
 * Device management, registration, content assignment, and monitoring endpoints
 */

import api from './index'

const devicesAPI = {
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
  // Content assignment endpoints (Phase 3) - Device-centric RESTful endpoints
  getContent: (id, params) => api.get(`/api/devices/${id}/content`, { params }),
  assignContent: (deviceId, contentId, priority = 0) => api.post(`/api/devices/${deviceId}/content`, { content_id: contentId, priority }),
  unassignContent: (deviceId, contentId) => api.delete(`/api/devices/${deviceId}/content/${contentId}`),
  // Preview endpoint (Phase 2)
  preview: (id, params) => api.get(`/api/devices/${id}/preview`, { params }),
  // Speed Test endpoints
  getSpeedTests: (id, limit = 20) => api.get(`/api/speedtest/devices/${id}/speedtest`, { params: { limit } }),
  getLatestSpeedTest: (id) => api.get(`/api/speedtest/devices/${id}/speedtest/latest`),
}

export default devicesAPI
