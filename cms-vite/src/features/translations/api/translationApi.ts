/**
 * Translation API Client
 * API functions for translation management
 */

import axios from 'axios'
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

const API_BASE = '/api/v1'

/**
 * Get list of translations with optional filters
 */
export const getTranslations = async (
  filters?: TranslationFilters
): Promise<TranslationListResponse> => {
  const response = await axios.get(`${API_BASE}/translations`, {
    params: filters,
  })
  return response.data
}

/**
 * Get single translation by ID
 */
export const getTranslation = async (id: number): Promise<Translation> => {
  const response = await axios.get(`${API_BASE}/translations/${id}`)
  return response.data
}

/**
 * Create new translation
 */
export const createTranslation = async (
  data: CreateTranslationRequest
): Promise<Translation> => {
  const response = await axios.post(`${API_BASE}/translations`, data)
  return response.data
}

/**
 * Update existing translation
 */
export const updateTranslation = async (
  id: number,
  data: UpdateTranslationRequest
): Promise<Translation> => {
  const response = await axios.put(`${API_BASE}/translations/${id}`, data)
  return response.data
}

/**
 * Delete translation
 */
export const deleteTranslation = async (id: number): Promise<void> => {
  await axios.delete(`${API_BASE}/translations/${id}`)
}

/**
 * Get translations for specific entity
 */
export const getEntityTranslations = async (
  entityType: string,
  entityId: number
): Promise<EntityTranslationsResponse> => {
  const response = await axios.get(
    `${API_BASE}/translations/${entityType}/${entityId}`
  )
  return response.data
}

/**
 * Bulk create translations for an entity
 */
export const bulkCreateTranslations = async (
  data: BulkTranslationRequest
): Promise<{ created: number }> => {
  const response = await axios.post(`${API_BASE}/translations/bulk`, data)
  return response.data
}

/**
 * Bulk import translations from CSV/JSON
 */
export const bulkImportTranslations = async (
  data: BulkImportRequest
): Promise<BulkImportResponse> => {
  const response = await axios.post(`${API_BASE}/translations/import`, data)
  return response.data
}

/**
 * Get translation statistics
 */
export const getTranslationStats = async (): Promise<TranslationStatsResponse> => {
  const response = await axios.get(`${API_BASE}/translations/stats`)
  return response.data
}

/**
 * Approve translation
 */
export const approveTranslation = async (id: number): Promise<Translation> => {
  const response = await axios.post(`${API_BASE}/translations/${id}/approve`)
  return response.data
}

/**
 * Reject translation
 */
export const rejectTranslation = async (id: number): Promise<Translation> => {
  const response = await axios.post(`${API_BASE}/translations/${id}/reject`)
  return response.data
}
