/**
 * Widget Hooks
 * React Query hooks for Widget data fetching
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from '@/shared/utils/toast'
import {
  getWidgets,
  getWidget,
  createWidget,
  updateWidget,
  deleteWidget,
  getPlaylistWidgets,
  assignWidgetToPlaylist,
  updatePlaylistWidget,
  removeWidgetFromPlaylist
} from '../api/widgetApi'
import { getApiErrorMessage } from '@/shared/utils/types'
import type {
  WidgetFilters,
  CreateWidgetRequest,
  UpdateWidgetRequest,
  AssignWidgetToPlaylistRequest,
  UpdatePlaylistWidgetRequest
} from '../types/widget.types'

// ============================================================================
// Query Hooks
// ============================================================================

export const useWidgets = (filters?: WidgetFilters) => {
  return useQuery({
    queryKey: ['widgets', filters],
    queryFn: () => getWidgets(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useWidget = (id: number, enabled = true) => {
  return useQuery({
    queryKey: ['widget', id],
    queryFn: () => getWidget(id),
    enabled: enabled && !!id,
  })
}

export const usePlaylistWidgets = (playlistId: number, enabled = true) => {
  return useQuery({
    queryKey: ['playlist-widgets', playlistId],
    queryFn: () => getPlaylistWidgets(playlistId),
    enabled: enabled && !!playlistId,
  })
}

// ============================================================================
// Mutation Hooks
// ============================================================================

export const useCreateWidget = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createWidget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['widgets'] })
      toast.success('Widget created successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to create widget'))
    },
  })
}

export const useUpdateWidget = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateWidgetRequest }) =>
      updateWidget(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['widgets'] })
      queryClient.invalidateQueries({ queryKey: ['widget', variables.id] })
      toast.success('Widget updated successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update widget'))
    },
  })
}

export const useDeleteWidget = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteWidget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['widgets'] })
      toast.success('Widget deleted successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete widget'))
    },
  })
}

// ============================================================================
// Playlist Assignment Mutation Hooks
// ============================================================================

export const useAssignWidgetToPlaylist = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      playlistId,
      data,
    }: {
      playlistId: number
      data: AssignWidgetToPlaylistRequest
    }) => assignWidgetToPlaylist(playlistId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['playlist-widgets', variables.playlistId],
      })

      // Invalidate playlist queries (playlist now has widget)
      queryClient.invalidateQueries({ queryKey: ['playlists'] })
      queryClient.invalidateQueries({ queryKey: ['playlist', variables.playlistId] })

      toast.success('Widget assigned to playlist')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to assign widget to playlist'))
    },
  })
}

export const useUpdatePlaylistWidget = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdatePlaylistWidgetRequest }) =>
      updatePlaylistWidget(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playlist-widgets'] })
      toast.success('Widget settings updated')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update widget settings'))
    },
  })
}

export const useRemoveWidgetFromPlaylist = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ playlistId, widgetId }: { playlistId: number; widgetId: number }) =>
      removeWidgetFromPlaylist(playlistId, widgetId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['playlist-widgets', variables.playlistId],
      })

      // Invalidate playlist queries (playlist no longer has widget)
      queryClient.invalidateQueries({ queryKey: ['playlists'] })
      queryClient.invalidateQueries({ queryKey: ['playlist', variables.playlistId] })

      toast.success('Widget removed from playlist')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to remove widget from playlist'))
    },
  })
}
