/**
 * Schedule Hooks
 * React Query hooks for schedule management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  getSchedules,
  getSchedule,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  activateSchedule,
  deactivateSchedule,
  pauseSchedule,
  checkConflicts,
  getOccurrences,
  getDeviceSchedules,
  getPlaylistSchedules,
} from '../api/scheduleApi'
import type {
  ScheduleFilters,
  CreateScheduleRequest,
  UpdateScheduleRequest,
  ConflictCheckRequest,
  GetOccurrencesRequest,
} from '../types/schedule.types'

/**
 * Query: Get list of schedules
 */
export const useSchedules = (filters?: ScheduleFilters) => {
  return useQuery({
    queryKey: ['schedules', filters],
    queryFn: () => getSchedules(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Query: Get single schedule
 */
export const useSchedule = (id: number, enabled = true) => {
  return useQuery({
    queryKey: ['schedule', id],
    queryFn: () => getSchedule(id),
    enabled,
  })
}

/**
 * Query: Get device schedules
 */
export const useDeviceSchedules = (deviceId: number, enabled = true) => {
  return useQuery({
    queryKey: ['device-schedules', deviceId],
    queryFn: () => getDeviceSchedules(deviceId),
    enabled,
  })
}

/**
 * Query: Get playlist schedules
 */
export const usePlaylistSchedules = (playlistId: number, enabled = true) => {
  return useQuery({
    queryKey: ['playlist-schedules', playlistId],
    queryFn: () => getPlaylistSchedules(playlistId),
    enabled,
  })
}

/**
 * Query: Get schedule occurrences
 */
export const useOccurrences = (data: GetOccurrencesRequest, enabled = true) => {
  return useQuery({
    queryKey: ['schedule-occurrences', data],
    queryFn: () => getOccurrences(data),
    enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Mutation: Create schedule
 */
export const useCreateSchedule = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateScheduleRequest) => createSchedule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['schedule-occurrences'] })
      queryClient.invalidateQueries({ queryKey: ['device-schedules'] })
      queryClient.invalidateQueries({ queryKey: ['playlist-schedules'] })
      toast.success('Schedule created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create schedule')
    },
  })
}

/**
 * Mutation: Update schedule
 */
export const useUpdateSchedule = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateScheduleRequest }) =>
      updateSchedule(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['schedule', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['schedule-occurrences'] })
      queryClient.invalidateQueries({ queryKey: ['device-schedules'] })
      queryClient.invalidateQueries({ queryKey: ['playlist-schedules'] })
      toast.success('Schedule updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update schedule')
    },
  })
}

/**
 * Mutation: Delete schedule
 */
export const useDeleteSchedule = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteSchedule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['schedule-occurrences'] })
      queryClient.invalidateQueries({ queryKey: ['device-schedules'] })
      queryClient.invalidateQueries({ queryKey: ['playlist-schedules'] })
      toast.success('Schedule deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete schedule')
    },
  })
}

/**
 * Mutation: Activate schedule
 */
export const useActivateSchedule = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => activateSchedule(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['schedule', id] })
      queryClient.invalidateQueries({ queryKey: ['schedule-occurrences'] })
      toast.success('Schedule activated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to activate schedule')
    },
  })
}

/**
 * Mutation: Deactivate schedule
 */
export const useDeactivateSchedule = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deactivateSchedule(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['schedule', id] })
      queryClient.invalidateQueries({ queryKey: ['schedule-occurrences'] })
      toast.success('Schedule deactivated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to deactivate schedule')
    },
  })
}

/**
 * Mutation: Pause schedule
 */
export const usePauseSchedule = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => pauseSchedule(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['schedule', id] })
      queryClient.invalidateQueries({ queryKey: ['schedule-occurrences'] })
      toast.success('Schedule paused')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to pause schedule')
    },
  })
}

/**
 * Mutation: Check conflicts
 */
export const useCheckConflicts = () => {
  return useMutation({
    mutationFn: (data: ConflictCheckRequest) => checkConflicts(data),
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to check conflicts')
    },
  })
}
