/**
 * Widget Form Component
 * Create/Edit widget with dynamic configuration based on widget type
 */

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2 } from 'lucide-react'
import WidgetTypeSelector from './WidgetTypeSelector'
import LayoutEditor from './LayoutEditor'
import {
  WIDGET_TYPES,
  DEFAULT_LAYOUT,
  type Widget,
  type WidgetType,
  type WidgetLayout,
  type CreateWidgetRequest,
  type UpdateWidgetRequest,
} from '../types/widget.types'

// Validation schema
const widgetFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name too long'),
  description: z.string().optional(),
  widget_type: z.enum(['clock', 'weather', 'news', 'hotel_info', 'custom']),
  config: z.record(z.any()),
  layout: z.object({
    x: z.number().min(0),
    y: z.number().min(0),
    width: z.number().min(50),
    height: z.number().min(50),
  }),
})

type WidgetFormData = z.infer<typeof widgetFormSchema>

interface WidgetFormProps {
  widget?: Widget
  onSubmit: (data: CreateWidgetRequest | UpdateWidgetRequest) => void
  onCancel: () => void
  isLoading?: boolean
}

export const WidgetForm = ({
  widget,
  onSubmit,
  onCancel,
  isLoading = false,
}: WidgetFormProps) => {
  const isEdit = !!widget

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<WidgetFormData>({
    resolver: zodResolver(widgetFormSchema),
    defaultValues: widget
      ? {
          name: widget.name,
          description: widget.description || '',
          widget_type: widget.widget_type,
          config: widget.config,
          layout: widget.layout,
        }
      : {
          name: '',
          description: '',
          widget_type: 'clock',
          config: WIDGET_TYPES.clock.defaultConfig,
          layout: DEFAULT_LAYOUT,
        },
  })

  const widgetType = watch('widget_type')
  const config = watch('config')
  const layout = watch('layout')

  // Update config when widget type changes
  useEffect(() => {
    if (!isEdit) {
      setValue('config', WIDGET_TYPES[widgetType].defaultConfig)
    }
  }, [widgetType, isEdit, setValue])

  // Render dynamic config fields based on widget type
  const renderConfigFields = () => {
    const typeInfo = WIDGET_TYPES[widgetType]
    const schema = typeInfo.configSchema

    return (
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-gray-700">Widget Configuration</h3>
        <div className="space-y-3">
          {Object.entries(schema).map(([fieldName, fieldSchema]: [string, any]) => {
            const value = config[fieldName]

            switch (fieldSchema.type) {
              case 'text':
              case 'url':
                return (
                  <div key={fieldName}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {fieldSchema.label}
                    </label>
                    <input
                      type={fieldSchema.type === 'url' ? 'url' : 'text'}
                      value={value || ''}
                      onChange={(e) =>
                        setValue('config', { ...config, [fieldName]: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      disabled={isLoading}
                    />
                  </div>
                )

              case 'password':
                return (
                  <div key={fieldName}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {fieldSchema.label}
                    </label>
                    <input
                      type="password"
                      value={value || ''}
                      onChange={(e) =>
                        setValue('config', { ...config, [fieldName]: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      disabled={isLoading}
                    />
                  </div>
                )

              case 'number':
                return (
                  <div key={fieldName}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {fieldSchema.label}
                    </label>
                    <input
                      type="number"
                      value={value || 0}
                      onChange={(e) =>
                        setValue('config', {
                          ...config,
                          [fieldName]: Number(e.target.value),
                        })
                      }
                      min={fieldSchema.min}
                      max={fieldSchema.max}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      disabled={isLoading}
                    />
                  </div>
                )

              case 'boolean':
                return (
                  <div key={fieldName} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={value || false}
                      onChange={(e) =>
                        setValue('config', { ...config, [fieldName]: e.target.checked })
                      }
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded"
                      disabled={isLoading}
                    />
                    <label className="ml-2 text-sm font-medium text-gray-700">
                      {fieldSchema.label}
                    </label>
                  </div>
                )

              case 'select':
                return (
                  <div key={fieldName}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {fieldSchema.label}
                    </label>
                    <select
                      value={value || ''}
                      onChange={(e) =>
                        setValue('config', { ...config, [fieldName]: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      disabled={isLoading}
                    >
                      {fieldSchema.options.map((option: string) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </div>
                )

              case 'multiselect':
                return (
                  <div key={fieldName}>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {fieldSchema.label}
                    </label>
                    <div className="space-y-2 max-h-40 overflow-y-auto border border-gray-300 rounded-md p-2">
                      {fieldSchema.options.map((option: string) => (
                        <div key={option} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={(value || []).includes(option)}
                            onChange={(e) => {
                              const currentValues = value || []
                              const newValues = e.target.checked
                                ? [...currentValues, option]
                                : currentValues.filter((v: string) => v !== option)
                              setValue('config', { ...config, [fieldName]: newValues })
                            }}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded"
                            disabled={isLoading}
                          />
                          <label className="ml-2 text-sm text-gray-700">{option}</label>
                        </div>
                      ))}
                    </div>
                  </div>
                )

              case 'textarea':
                return (
                  <div key={fieldName}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {fieldSchema.label}
                    </label>
                    <textarea
                      value={value || ''}
                      onChange={(e) =>
                        setValue('config', { ...config, [fieldName]: e.target.value })
                      }
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      disabled={isLoading}
                    />
                  </div>
                )

              case 'color':
                return (
                  <div key={fieldName}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {fieldSchema.label}
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={value || '#ffffff'}
                        onChange={(e) =>
                          setValue('config', { ...config, [fieldName]: e.target.value })
                        }
                        className="w-12 h-10 border border-gray-300 rounded-md cursor-pointer"
                        disabled={isLoading}
                      />
                      <input
                        type="text"
                        value={value || '#ffffff'}
                        onChange={(e) =>
                          setValue('config', { ...config, [fieldName]: e.target.value })
                        }
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
                        disabled={isLoading}
                      />
                    </div>
                  </div>
                )

              case 'code':
                return (
                  <div key={fieldName}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {fieldSchema.label}
                    </label>
                    <textarea
                      value={value || ''}
                      onChange={(e) =>
                        setValue('config', { ...config, [fieldName]: e.target.value })
                      }
                      rows={8}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
                      disabled={isLoading}
                      placeholder={`Enter ${fieldSchema.language} code...`}
                    />
                  </div>
                )

              default:
                return null
            }
          })}
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Widget Name *
          </label>
          <input
            {...register('name')}
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="e.g., Lobby Clock"
            disabled={isLoading}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            {...register('description')}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="Optional description..."
            disabled={isLoading}
          />
        </div>
      </div>

      {/* Widget Type Selection */}
      {!isEdit && (
        <WidgetTypeSelector
          value={widgetType}
          onChange={(type) => setValue('widget_type', type)}
          disabled={isLoading}
        />
      )}

      {/* Dynamic Configuration */}
      {renderConfigFields()}

      {/* Layout Editor */}
      <LayoutEditor
        value={(layout || { x: 10, y: 10, width: 200, height: 100 }) as WidgetLayout}
        onChange={(newLayout) => setValue('layout', newLayout)}
        disabled={isLoading}
      />

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-6 border-t">
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
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {isLoading && <Loader2 className="animate-spin h-4 w-4" />}
          {isEdit ? 'Update Widget' : 'Create Widget'}
        </button>
      </div>
    </form>
  )
}

export default WidgetForm
