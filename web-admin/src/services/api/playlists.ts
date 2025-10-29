/**
 * Playlists API Module
 * Playlist management, content scheduling, and device/tag assignment endpoints
 */

import api from './index'

const playlistsAPI = {
  list: () => api.get('/api/playlists'),
  create: (data) => api.post('/api/playlists', data),
  get: (id) => api.get(`/api/playlists/${id}`),
  update: (id, data) => api.patch(`/api/playlists/${id}`, data),
  delete: (id) => api.delete(`/api/playlists/${id}`),
  getContent: (id) => api.get(`/api/playlists/${id}/content`),
  assignContent: (id, data) => api.post(`/api/playlists/${id}/content`, data),
  removeContent: (id, contentId) => api.delete(`/api/playlists/${id}/content/${contentId}`),
  reorderContent: (id, data) => api.patch(`/api/playlists/${id}/reorder`, data),
  // Device & Tag Assignments
  getAssignments: (id) => api.get(`/api/playlists/${id}/assignments`),
  assignToDevices: (id, data) => api.post(`/api/playlists/${id}/assign/devices`, data),
  assignToTags: (id, data) => api.post(`/api/playlists/${id}/assign/tags`, data),
  unassignFromDevices: (id, data) => api.delete(`/api/playlists/${id}/assign/devices`, { data }),
  unassignFromTags: (id, data) => api.delete(`/api/playlists/${id}/assign/tags`, { data }),
}

export default playlistsAPI
