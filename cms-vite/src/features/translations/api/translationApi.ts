/**
 * Translation API Client
 * API functions for translation management
 */

import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import type {
  Translation,
  TranslationFilters,
  TranslationListResponse,
  CreateTranslationRequest,
  UpdateTranslationRequest,
  BulkTranslationRequest,
  TranslationStatsResponse,
  EntityTranslationsResponse,
  BulkImportRequest,
  BulkImportResponse,
} from '../types/translation.types'

/**
 * Get list of translations with optional filters
 */
export const getTranslations = async (
  filters?: TranslationFilters
): Promise<TranslationListResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.TRANSLATIONS.LIST, {
    params: filters,
  })
  return response.data
}

/**
 * Get single translation by ID
 */
export const getTranslation = async (id: number): Promise<Translation> => {
  const response = await apiClient.get(API_ENDPOINTS.TRANSLATIONS.GET(id))
  return response.data
}

/**
 * Create new translation
 */
export const createTranslation = async (
  data: CreateTranslationRequest
): Promise<Translation> => {
  const response = await apiClient.post(API_ENDPOINTS.TRANSLATIONS.CREATE, data)
  return response.data
}

/**
 * Update existing translation
 */
export const updateTranslation = async (
  id: number,
  data: UpdateTranslationRequest
): Promise<Translation> => {
  const response = await apiClient.put(API_ENDPOINTS.TRANSLATIONS.UPDATE(id), data)
  return response.data
}

/**
 * Delete translation
 */
export const deleteTranslation = async (id: number): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.TRANSLATIONS.DELETE(id))
}

/**
 * Get translations for specific entity
 */
export const getEntityTranslations = async (
  entityType: string,
  entityId: number
): Promise<EntityTranslationsResponse> => {
  const response = await apiClient.get(
    API_ENDPOINTS.TRANSLATIONS.GET_ENTITY_TRANSLATIONS(entityType, entityId)
  )
  return response.data
}

/**
 * Bulk create translations for an entity
 */
export const bulkCreateTranslations = async (
  data: BulkTranslationRequest
): Promise<{ created: number }> => {
  const response = await apiClient.post(API_ENDPOINTS.TRANSLATIONS.BULK_CREATE, data)
  return response.data
}

/**
 * Bulk import translations from CSV/JSON
 */
export const bulkImportTranslations = async (
  data: BulkImportRequest
): Promise<BulkImportResponse> => {
  const response = await apiClient.post(API_ENDPOINTS.TRANSLATIONS.BULK_IMPORT, data)
  return response.data
}

/**
 * Get translation statistics
 */
export const getTranslationStats = async (): Promise<TranslationStatsResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.TRANSLATIONS.STATS)
  return response.data
}

/**
 * Approve translation
 */
export const approveTranslation = async (id: number): Promise<Translation> => {
  const response = await apiClient.post(API_ENDPOINTS.TRANSLATIONS.APPROVE(id))
  return response.data
}

/**
 * Reject translation
 */
export const rejectTranslation = async (id: number): Promise<Translation> => {
  const response = await apiClient.post(API_ENDPOINTS.TRANSLATIONS.REJECT(id))
  return response.data
}
