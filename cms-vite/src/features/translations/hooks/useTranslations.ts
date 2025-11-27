/**
 * Translation Hooks
 * React Query hooks for translation management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { getApiErrorMessage } from '@/shared/utils/types'
import {
  getTranslations,
  getTranslation,
  createTranslation,
  updateTranslation,
  deleteTranslation,
  getEntityTranslations,
  bulkCreateTranslations,
  bulkImportTranslations,
  getTranslationStats,
  approveTranslation,
  rejectTranslation,
} from '../api/translationApi'
import type {
  TranslationFilters,
  CreateTranslationRequest,
  UpdateTranslationRequest,
  BulkTranslationRequest,
  BulkImportRequest,
} from '../types/translation.types'

/**
 * Query: Get list of translations
 */
export const useTranslations = (filters?: TranslationFilters) => {
  return useQuery({
    queryKey: ['translations', filters],
    queryFn: () => getTranslations(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Query: Get single translation
 */
export const useTranslation = (id: number, enabled = true) => {
  return useQuery({
    queryKey: ['translation', id],
    queryFn: () => getTranslation(id),
    enabled,
  })
}

/**
 * Query: Get entity translations
 */
export const useEntityTranslations = (
  entityType: string,
  entityId: number,
  enabled = true
) => {
  return useQuery({
    queryKey: ['entity-translations', entityType, entityId],
    queryFn: () => getEntityTranslations(entityType, entityId),
    enabled,
  })
}

/**
 * Query: Get translation statistics
 */
export const useTranslationStats = () => {
  return useQuery({
    queryKey: ['translation-stats'],
    queryFn: getTranslationStats,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Mutation: Create translation
 */
export const useCreateTranslation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateTranslationRequest) => createTranslation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translations'] })
      queryClient.invalidateQueries({ queryKey: ['entity-translations'] })
      queryClient.invalidateQueries({ queryKey: ['translation-stats'] })
      toast.success('Translation created successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to create translation'))
    },
  })
}

/**
 * Mutation: Update translation
 */
export const useUpdateTranslation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTranslationRequest }) =>
      updateTranslation(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['translations'] })
      queryClient.invalidateQueries({ queryKey: ['translation', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['entity-translations'] })
      queryClient.invalidateQueries({ queryKey: ['translation-stats'] })
      toast.success('Translation updated successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update translation'))
    },
  })
}

/**
 * Mutation: Delete translation
 */
export const useDeleteTranslation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteTranslation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translations'] })
      queryClient.invalidateQueries({ queryKey: ['entity-translations'] })
      queryClient.invalidateQueries({ queryKey: ['translation-stats'] })
      toast.success('Translation deleted successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete translation'))
    },
  })
}

/**
 * Mutation: Bulk create translations
 */
export const useBulkCreateTranslations = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: BulkTranslationRequest) => bulkCreateTranslations(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['translations'] })
      queryClient.invalidateQueries({ queryKey: ['entity-translations'] })
      queryClient.invalidateQueries({ queryKey: ['translation-stats'] })
      toast.success(`${data.created} translation(s) created successfully`)
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to create translations'))
    },
  })
}

/**
 * Mutation: Bulk import translations
 */
export const useBulkImportTranslations = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: BulkImportRequest) => bulkImportTranslations(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['translations'] })
      queryClient.invalidateQueries({ queryKey: ['entity-translations'] })
      queryClient.invalidateQueries({ queryKey: ['translation-stats'] })

      const message = `Imported: ${data.imported}, Skipped: ${data.skipped}`
      if (data.errors.length > 0) {
        toast.warning(`${message}. ${data.errors.length} error(s) occurred.`)
      } else {
        toast.success(message)
      }
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to import translations'))
    },
  })
}

/**
 * Mutation: Approve translation
 */
export const useApproveTranslation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => approveTranslation(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['translations'] })
      queryClient.invalidateQueries({ queryKey: ['translation', id] })
      queryClient.invalidateQueries({ queryKey: ['entity-translations'] })
      queryClient.invalidateQueries({ queryKey: ['translation-stats'] })
      toast.success('Translation approved')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to approve translation'))
    },
  })
}

/**
 * Mutation: Reject translation
 */
export const useRejectTranslation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => rejectTranslation(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['translations'] })
      queryClient.invalidateQueries({ queryKey: ['translation', id] })
      queryClient.invalidateQueries({ queryKey: ['entity-translations'] })
      queryClient.invalidateQueries({ queryKey: ['translation-stats'] })
      toast.success('Translation rejected')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to reject translation'))
    },
  })
}
