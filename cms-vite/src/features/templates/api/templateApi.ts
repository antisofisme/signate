/**
 * Template API
 * API client for Template System endpoints
 */

import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import type {
  Template,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  TemplateFilters,
  TemplateListResponse,
  RenderTemplateRequest,
  RenderTemplateResponse,
  ValidateTemplateRequest,
  ValidateTemplateResponse,
  ExtractVariablesRequest,
  ExtractVariablesResponse
} from '../types/template.types'

// ============================================================================
// Template CRUD
// ============================================================================

export const getTemplates = async (filters?: TemplateFilters): Promise<TemplateListResponse> => {
  const params = new URLSearchParams()

  if (filters?.template_type) params.append('template_type', filters.template_type)
  if (filters?.search) params.append('search', filters.search)
  if (filters?.skip !== undefined) params.append('skip', filters.skip.toString())
  if (filters?.limit !== undefined) params.append('limit', filters.limit.toString())

  const response = await apiClient.get<TemplateListResponse>(API_ENDPOINTS.TEMPLATES.LIST, { params })
  return response.data
}

export const getTemplate = async (id: number): Promise<Template> => {
  const response = await apiClient.get<Template>(API_ENDPOINTS.TEMPLATES.GET(id))
  return response.data
}

export const createTemplate = async (data: CreateTemplateRequest): Promise<Template> => {
  const response = await apiClient.post<Template>(API_ENDPOINTS.TEMPLATES.CREATE, data)
  return response.data
}

export const updateTemplate = async (
  id: number,
  data: UpdateTemplateRequest
): Promise<Template> => {
  const response = await apiClient.put<Template>(API_ENDPOINTS.TEMPLATES.UPDATE(id), data)
  return response.data
}

export const deleteTemplate = async (id: number): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.TEMPLATES.DELETE(id))
}

// ============================================================================
// Template Operations
// ============================================================================

export const renderTemplate = async (
  id: number,
  data: RenderTemplateRequest
): Promise<RenderTemplateResponse> => {
  const response = await apiClient.post<RenderTemplateResponse>(API_ENDPOINTS.TEMPLATES.RENDER(id), data)
  return response.data
}

export const validateTemplate = async (
  data: ValidateTemplateRequest
): Promise<ValidateTemplateResponse> => {
  const response = await apiClient.post<ValidateTemplateResponse>(API_ENDPOINTS.TEMPLATES.VALIDATE, data)
  return response.data
}

export const extractVariables = async (
  data: ExtractVariablesRequest
): Promise<ExtractVariablesResponse> => {
  const response = await apiClient.post<ExtractVariablesResponse>(API_ENDPOINTS.TEMPLATES.EXTRACT_VARIABLES, data)
  return response.data
}

// Export all as named exports
export default {
  getTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  renderTemplate,
  validateTemplate,
  extractVariables
}
