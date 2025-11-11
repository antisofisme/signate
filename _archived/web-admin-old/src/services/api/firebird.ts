/**
 * Firebird API Module
 * SystemPMS integration and Firebird database connection endpoints
 */

import api from './index'

const firebirdAPI = {
  listConfigs: () => api.get('/api/firebird/configs'),
  getConfig: (id) => api.get(`/api/firebird/configs/${id}`),
  createConfig: (data) => api.post('/api/firebird/configs', data),
  updateConfig: (id, data) => api.put(`/api/firebird/configs/${id}`, data),
  deleteConfig: (id) => api.delete(`/api/firebird/configs/${id}`),
  testConnection: (id) => api.post(`/api/firebird/configs/${id}/test`),
  getHealth: (id) => api.get(`/api/firebird/configs/${id}/health`),
  executeQuery: (id, query) => api.post(`/api/firebird/configs/${id}/query`, { query }),
}

export default firebirdAPI
