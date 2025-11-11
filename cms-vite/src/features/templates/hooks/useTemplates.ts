/**
 * Template Hooks
 * React Query hooks for Template data fetching
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  getTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  renderTemplate,
  validateTemplate,
  extractVariables
} from '../api/templateApi'
import type {
  TemplateFilters,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  RenderTemplateRequest,
  ValidateTemplateRequest,
  ExtractVariablesRequest
} from '../types/template.types'

// ============================================================================
// Query Hooks
// ============================================================================

export const useTemplates = (filters?: TemplateFilters) => {
  return useQuery({
    queryKey: ['templates', filters],
    queryFn: () => getTemplates(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useTemplate = (id: number, enabled = true) => {
  return useQuery({
    queryKey: ['template', id],
    queryFn: () => getTemplate(id),
    enabled: enabled && !!id,
  })
}

// ============================================================================
// Mutation Hooks
// ============================================================================

export const useCreateTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template created successfully')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to create template'
      toast.error(message)
    },
  })
}

export const useUpdateTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTemplateRequest }) =>
      updateTemplate(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      queryClient.invalidateQueries({ queryKey: ['template', variables.id] })
      toast.success('Template updated successfully')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to update template'
      toast.error(message)
    },
  })
}

export const useDeleteTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template deleted successfully')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to delete template'
      toast.error(message)
    },
  })
}

// ============================================================================
// Template Operation Hooks
// ============================================================================

export const useRenderTemplate = () => {
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: RenderTemplateRequest }) =>
      renderTemplate(id, data),
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to render template'
      toast.error(message)
    },
  })
}

export const useValidateTemplate = () => {
  return useMutation({
    mutationFn: (data: ValidateTemplateRequest) => validateTemplate(data),
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to validate template'
      toast.error(message)
    },
  })
}

export const useExtractVariables = () => {
  return useMutation({
    mutationFn: (data: ExtractVariablesRequest) => extractVariables(data),
    onSuccess: (data) => {
      if (data.variables.length > 0) {
        toast.success(`Found ${data.variables.length} variable(s)`)
      } else {
        toast.info('No variables found in template')
      }
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to extract variables'
      toast.error(message)
    },
  })
}
