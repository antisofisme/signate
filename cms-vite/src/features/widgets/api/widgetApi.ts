/**
 * Widget API
 * API client for Widget System endpoints
 */

import api from '@/shared/utils/api'
import type {
  Widget,
  CreateWidgetRequest,
  UpdateWidgetRequest,
  WidgetFilters,
  WidgetListResponse,
  PlaylistWidget,
  AssignWidgetToPlaylistRequest,
  UpdatePlaylistWidgetRequest
} from '../types/widget.types'

// ============================================================================
// Widget CRUD
// ============================================================================

export const getWidgets = async (filters?: WidgetFilters): Promise<WidgetListResponse> => {
  const params = new URLSearchParams()

  if (filters?.widget_type) params.append('widget_type', filters.widget_type)
  if (filters?.search) params.append('search', filters.search)
  if (filters?.skip !== undefined) params.append('skip', filters.skip.toString())
  if (filters?.limit !== undefined) params.append('limit', filters.limit.toString())

  const response = await api.get<WidgetListResponse>('/widgets', { params })
  return response.data
}

export const getWidget = async (id: number): Promise<Widget> => {
  const response = await api.get<Widget>(`/widgets/${id}`)
  return response.data
}

export const createWidget = async (data: CreateWidgetRequest): Promise<Widget> => {
  const response = await api.post<Widget>('/widgets', data)
  return response.data
}

export const updateWidget = async (
  id: number,
  data: UpdateWidgetRequest
): Promise<Widget> => {
  const response = await api.put<Widget>(`/widgets/${id}`, data)
  return response.data
}

export const deleteWidget = async (id: number): Promise<void> => {
  await api.delete(`/widgets/${id}`)
}

// ============================================================================
// Playlist Widget Assignment
// ============================================================================

export const getPlaylistWidgets = async (playlistId: number): Promise<PlaylistWidget[]> => {
  const response = await api.get<PlaylistWidget[]>(`/widgets/playlists/${playlistId}/widgets`)
  return response.data
}

export const assignWidgetToPlaylist = async (
  playlistId: number,
  data: AssignWidgetToPlaylistRequest
): Promise<PlaylistWidget> => {
  const response = await api.post<PlaylistWidget>(
    `/widgets/playlists/${playlistId}/widgets`,
    data
  )
  return response.data
}

export const updatePlaylistWidget = async (
  id: number,
  data: UpdatePlaylistWidgetRequest
): Promise<PlaylistWidget> => {
  const response = await api.put<PlaylistWidget>(
    `/widgets/playlist-widgets/${id}`,
    data
  )
  return response.data
}

export const removeWidgetFromPlaylist = async (
  playlistId: number,
  widgetId: number
): Promise<void> => {
  await api.delete(`/widgets/playlists/${playlistId}/widgets/${widgetId}`)
}

// Export all as named exports
export default {
  getWidgets,
  getWidget,
  createWidget,
  updateWidget,
  deleteWidget,
  getPlaylistWidgets,
  assignWidgetToPlaylist,
  updatePlaylistWidget,
  removeWidgetFromPlaylist
}
