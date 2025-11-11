/**
 * Template API
 * API client for Template System endpoints
 */

import api from '@/shared/utils/api'
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

  const response = await api.get<TemplateListResponse>('/templates', { params })
  return response.data
}

export const getTemplate = async (id: number): Promise<Template> => {
  const response = await api.get<Template>(`/templates/${id}`)
  return response.data
}

export const createTemplate = async (data: CreateTemplateRequest): Promise<Template> => {
  const response = await api.post<Template>('/templates', data)
  return response.data
}

export const updateTemplate = async (
  id: number,
  data: UpdateTemplateRequest
): Promise<Template> => {
  const response = await api.put<Template>(`/templates/${id}`, data)
  return response.data
}

export const deleteTemplate = async (id: number): Promise<void> => {
  await api.delete(`/templates/${id}`)
}

// ============================================================================
// Template Operations
// ============================================================================

export const renderTemplate = async (
  id: number,
  data: RenderTemplateRequest
): Promise<RenderTemplateResponse> => {
  const response = await api.post<RenderTemplateResponse>(`/templates/${id}/render`, data)
  return response.data
}

export const validateTemplate = async (
  data: ValidateTemplateRequest
): Promise<ValidateTemplateResponse> => {
  const response = await api.post<ValidateTemplateResponse>('/templates/validate', data)
  return response.data
}

export const extractVariables = async (
  data: ExtractVariablesRequest
): Promise<ExtractVariablesResponse> => {
  const response = await api.post<ExtractVariablesResponse>('/templates/extract-variables', data)
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
