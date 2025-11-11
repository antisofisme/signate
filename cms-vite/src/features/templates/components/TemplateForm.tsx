/**
 * Template Form Component
 * Create/Edit template with integrated editor, variables, and preview
 */

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import TemplateEditor from './TemplateEditor'
import VariableBuilder from './VariableBuilder'
import TemplatePreview from './TemplatePreview'
import {
  TEMPLATE_TYPES,
  type Template,
  type TemplateType,
  type CreateTemplateRequest,
  type UpdateTemplateRequest,
} from '../types/template.types'
import {
  useExtractVariables,
  useRenderTemplate,
  useValidateTemplate
} from '../hooks/useTemplates'

// Validation schema
const templateFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name too long'),
  description: z.string().optional(),
  template_type: z.enum(['text', 'image', 'video', 'html', 'greeting']),
  content: z.string().min(1, 'Template content is required'),
  variables: z.record(z.string()),
  preview_data: z.record(z.any()).optional(),
})

type TemplateFormData = z.infer<typeof templateFormSchema>

interface TemplateFormProps {
  template?: Template
  onSubmit: (data: CreateTemplateRequest | UpdateTemplateRequest) => void
  onCancel: () => void
  isLoading?: boolean
}

export const TemplateForm = ({
  template,
  onSubmit,
  onCancel,
  isLoading = false,
}: TemplateFormProps) => {
  const isEdit = !!template

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TemplateFormData>({
    resolver: zodResolver(templateFormSchema),
    defaultValues: template
      ? {
          name: template.name,
          description: template.description || '',
          template_type: template.template_type,
          content: template.content,
          variables: template.variables || {},
          preview_data: template.preview_data || {},
        }
      : {
          name: '',
          description: '',
          template_type: 'text',
          content: TEMPLATE_TYPES.text.exampleContent,
          variables: TEMPLATE_TYPES.text.exampleVariables,
          preview_data: {},
        },
  })

  const templateType = watch('template_type')
  const content = watch('content')
  const variables = watch('variables')
  const previewData = watch('preview_data')

  const [extractedVars, setExtractedVars] = useState<string[]>([])
  const [renderedContent, setRenderedContent] = useState<string>('')

  // Mutations
  const extractMutation = useExtractVariables()
  const renderMutation = useRenderTemplate()
  const validateMutation = useValidateTemplate()

  // Update content when template type changes (only for create)
  useEffect(() => {
    if (!isEdit) {
      const typeInfo = TEMPLATE_TYPES[templateType]
      setValue('content', typeInfo.exampleContent)
      setValue('variables', typeInfo.exampleVariables)
    }
  }, [templateType, isEdit, setValue])

  // Handle extract variables
  const handleExtractVariables = async () => {
    try {
      const result = await extractMutation.mutateAsync({ content })
      setExtractedVars(result.variables)
    } catch (error) {
      console.error('Extract error:', error)
    }
  }

  // Handle render template
  const handleRender = async (data: Record<string, any>) => {
    if (!template?.id) {
      // For new templates, just do client-side preview
      return
    }

    try {
      const result = await renderMutation.mutateAsync({
        id: template.id,
        data: { data }
      })
      setRenderedContent(result.rendered_content)
    } catch (error) {
      console.error('Render error:', error)
    }
  }

  // Handle validate template
  const handleValidate = async () => {
    try {
      const result = await validateMutation.mutateAsync({ content })
      if (result.is_valid) {
        alert('✅ Template syntax is valid!')
      } else {
        alert('❌ Template has errors:\n' + result.errors.join('\n'))
      }
    } catch (error) {
      console.error('Validate error:', error)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Template Name *
            </label>
            <input
              {...register('name')}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="e.g., Welcome Message"
              disabled={isLoading}
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Template Type *
            </label>
            <select
              {...register('template_type')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              disabled={isLoading || isEdit}
            >
              {Object.values(TEMPLATE_TYPES).map((type) => (
                <option key={type.type} value={type.type}>
                  {type.icon} {type.label}
                </option>
              ))}
            </select>
            {isEdit && (
              <p className="mt-1 text-xs text-gray-500">
                Template type cannot be changed after creation
              </p>
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            {...register('description')}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="Optional description..."
            disabled={isLoading}
          />
        </div>

        {/* Template type info */}
        <div className="bg-blue-50 border border-blue-200 rounded p-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{TEMPLATE_TYPES[templateType].icon}</span>
            <div>
              <h4 className="text-sm font-semibold text-blue-900">
                {TEMPLATE_TYPES[templateType].label}
              </h4>
              <p className="text-xs text-blue-700">
                {TEMPLATE_TYPES[templateType].description}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Template Editor */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">Template Content</h3>
          <button
            type="button"
            onClick={handleValidate}
            disabled={isLoading || validateMutation.isPending}
            className="text-sm px-3 py-1.5 bg-purple-50 text-purple-700 rounded hover:bg-purple-100 disabled:opacity-50"
          >
            {validateMutation.isPending ? '⏳ Validating...' : '✓ Validate Syntax'}
          </button>
        </div>
        <TemplateEditor
          value={content}
          onChange={(value) => setValue('content', value)}
          disabled={isLoading}
          height="300px"
        />
        {errors.content && (
          <p className="mt-1 text-sm text-red-600">{errors.content.message}</p>
        )}
      </div>

      {/* Variable Builder */}
      <VariableBuilder
        variables={variables}
        onChange={(vars) => setValue('variables', vars)}
        onExtract={handleExtractVariables}
        disabled={isLoading}
        extractedVariables={extractedVars}
      />

      {/* Template Preview */}
      <TemplatePreview
        content={content}
        variables={variables}
        previewData={previewData}
        onPreviewDataChange={(data) => setValue('preview_data', data)}
        onRender={template?.id ? handleRender : undefined}
        renderedContent={renderedContent}
        isRendering={renderMutation.isPending}
      />

      {/* Action Buttons */}
      <div className="flex justify-between pt-6 border-t">
        <div className="text-sm text-gray-600">
          {Object.keys(variables).length} variable(s) defined
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading && (
              <svg
                className="animate-spin h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            )}
            {isEdit ? 'Update Template' : 'Create Template'}
          </button>
        </div>
      </div>
    </form>
  )
}

export default TemplateForm
