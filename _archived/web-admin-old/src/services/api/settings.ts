/**
 * Settings API Module
 * System settings, configuration, and maintenance endpoints
 */

import api from './index'

const settingsAPI = {
  // System Settings
  getSystemInfo: () => api.get('/api/settings/system/info'),
  backupDatabase: () => api.get('/api/settings/system/backup', {
    responseType: 'blob',
  }),
  clearCache: () => api.post('/api/settings/system/clear-cache'),
}

export default settingsAPI
