/**
 * Client API Module
 * Client-side testing and monitoring endpoints
 */

import api from './index'

const clientAPI = {
  getPlaylist: (deviceId) => api.get(`/api/client/playlist?device_id=${deviceId}`),
  getStatus: (deviceId) => api.get(`/api/client/status?device_id=${deviceId}`),
}

export default clientAPI
