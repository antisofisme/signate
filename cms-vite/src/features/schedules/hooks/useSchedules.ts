/**
 * Schedule Hooks
 * React Query hooks for schedule management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { getApiErrorMessage } from '@/shared/utils/types'
import { useSelectedOrgId, scheduleKeys } from '@/shared/hooks'
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

// Export schedule keys for use in other components
export { scheduleKeys }

/**
 * Query: Get list of schedules
 *
 * Query key includes orgId for proper cache isolation between organizations.
 */
export const useSchedules = (filters?: ScheduleFilters) => {
  const orgId = useSelectedOrgId()

  return useQuery({
    queryKey: scheduleKeys.list(orgId, filters),
    queryFn: () => getSchedules(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    // Note: Backend handles org filtering via JWT or X-Organization-Id header
  })
}

/**
 * Query: Get single schedule
 */
export const useSchedule = (id: number, enabled = true) => {
  return useQuery({
    queryKey: scheduleKeys.detail(id),
    queryFn: () => getSchedule(id),
    enabled: enabled && id > 0,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Query: Get device schedules
 */
export const useDeviceSchedules = (deviceId: number, enabled = true) => {
  return useQuery({
    queryKey: scheduleKeys.deviceSchedules(deviceId),
    queryFn: () => getDeviceSchedules(deviceId),
    enabled: enabled && deviceId > 0,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Query: Get playlist schedules
 */
export const usePlaylistSchedules = (playlistId: number, enabled = true) => {
  return useQuery({
    queryKey: scheduleKeys.playlistSchedules(playlistId),
    queryFn: () => getPlaylistSchedules(playlistId),
    enabled: enabled && playlistId > 0,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Query: Get schedule occurrences
 *
 * Query key includes orgId for proper cache isolation between organizations.
 */
export const useOccurrences = (data: GetOccurrencesRequest, enabled = true) => {
  const orgId = useSelectedOrgId()

  return useQuery({
    queryKey: scheduleKeys.occurrences(orgId, data),
    queryFn: () => getOccurrences(data),
    enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
    // Note: Backend handles org filtering via JWT or X-Organization-Id header
  })
}

/**
 * Mutation: Create schedule
 */
export const useCreateSchedule = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateScheduleRequest) => createSchedule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.all })
      toast.success(t('schedules.messages.createSuccess'))
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('schedules.messages.createError')))
    },
  })
}

/**
 * Mutation: Update schedule
 */
export const useUpdateSchedule = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateScheduleRequest }) =>
      updateSchedule(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.all })
      queryClient.invalidateQueries({ queryKey: scheduleKeys.detail(variables.id) })
      toast.success(t('schedules.messages.updateSuccess'))
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('schedules.messages.updateError')))
    },
  })
}

/**
 * Mutation: Delete schedule
 */
export const useDeleteSchedule = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteSchedule(id),
    onSuccess: async () => {
      // Force refetch all schedule-related queries
      await queryClient.invalidateQueries({ queryKey: scheduleKeys.all, refetchType: 'all' })
      toast.success(t('schedules.messages.deleteSuccess'))
    },
    onError: (error: unknown) => {
      console.error('Delete schedule error:', error)
      toast.error(getApiErrorMessage(error, t('schedules.messages.deleteError')))
    },
  })
}

/**
 * Mutation: Activate schedule
 */
export const useActivateSchedule = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => activateSchedule(id),
    onSuccess: async (_, id) => {
      await queryClient.invalidateQueries({ queryKey: scheduleKeys.all, refetchType: 'all' })
      queryClient.invalidateQueries({ queryKey: scheduleKeys.detail(id) })
      toast.success(t('schedules.messages.activateSuccess'))
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('schedules.messages.activateError')))
    },
  })
}

/**
 * Mutation: Deactivate schedule
 */
export const useDeactivateSchedule = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deactivateSchedule(id),
    onSuccess: async (_, id) => {
      await queryClient.invalidateQueries({ queryKey: scheduleKeys.all, refetchType: 'all' })
      queryClient.invalidateQueries({ queryKey: scheduleKeys.detail(id) })
      toast.success(t('schedules.messages.deactivateSuccess'))
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('schedules.messages.deactivateError')))
    },
  })
}

/**
 * Mutation: Pause schedule
 */
export const usePauseSchedule = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => pauseSchedule(id),
    onSuccess: async (_, id) => {
      await queryClient.invalidateQueries({ queryKey: scheduleKeys.all, refetchType: 'all' })
      queryClient.invalidateQueries({ queryKey: scheduleKeys.detail(id) })
      toast.success(t('schedules.messages.pauseSuccess'))
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('schedules.messages.pauseError')))
    },
  })
}

/**
 * Mutation: Check conflicts
 */
export const useCheckConflicts = () => {
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (data: ConflictCheckRequest) => checkConflicts(data),
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('schedules.messages.conflictCheckError')))
    },
  })
}
