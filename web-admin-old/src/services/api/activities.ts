/**
 * Activities API Module
 * Activity logging, audit trails, and system event tracking endpoints
 */

import api from './index'

const activitiesAPI = {
  list: (params) => api.get('/api/activities', { params }),
  stats: () => api.get('/api/activities/stats'),
  get: (id) => api.get(`/api/activities/${id}`),
  create: (data) => api.post('/api/activities', data),
  cleanup: (retentionDays = 90) => api.delete('/api/activities/cleanup', { params: { retention_days: retentionDays } }),
}

export default activitiesAPI
