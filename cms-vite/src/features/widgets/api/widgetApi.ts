/**
 * Widget API
 * API client for Widget System endpoints
 */

import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
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

  const response = await apiClient.get<WidgetListResponse>(API_ENDPOINTS.WIDGETS.LIST, { params })
  return response.data
}

export const getWidget = async (id: number): Promise<Widget> => {
  const response = await apiClient.get<Widget>(API_ENDPOINTS.WIDGETS.GET(id))
  return response.data
}

export const createWidget = async (data: CreateWidgetRequest): Promise<Widget> => {
  const response = await apiClient.post<Widget>(API_ENDPOINTS.WIDGETS.CREATE, data)
  return response.data
}

export const updateWidget = async (
  id: number,
  data: UpdateWidgetRequest
): Promise<Widget> => {
  const response = await apiClient.put<Widget>(API_ENDPOINTS.WIDGETS.UPDATE(id), data)
  return response.data
}

export const deleteWidget = async (id: number): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.WIDGETS.DELETE(id))
}

// ============================================================================
// Playlist Widget Assignment
// ============================================================================

export const getPlaylistWidgets = async (playlistId: number): Promise<PlaylistWidget[]> => {
  const response = await apiClient.get<PlaylistWidget[]>(API_ENDPOINTS.WIDGETS.GET_PLAYLIST_WIDGETS(playlistId))
  return response.data
}

export const assignWidgetToPlaylist = async (
  playlistId: number,
  data: AssignWidgetToPlaylistRequest
): Promise<PlaylistWidget> => {
  const response = await apiClient.post<PlaylistWidget>(
    API_ENDPOINTS.WIDGETS.ASSIGN_TO_PLAYLIST(playlistId),
    data
  )
  return response.data
}

export const updatePlaylistWidget = async (
  id: number,
  data: UpdatePlaylistWidgetRequest
): Promise<PlaylistWidget> => {
  const response = await apiClient.put<PlaylistWidget>(
    API_ENDPOINTS.WIDGETS.UPDATE_PLAYLIST_WIDGET(id),
    data
  )
  return response.data
}

export const removeWidgetFromPlaylist = async (
  playlistId: number,
  widgetId: number
): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.WIDGETS.REMOVE_FROM_PLAYLIST(playlistId, widgetId))
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
