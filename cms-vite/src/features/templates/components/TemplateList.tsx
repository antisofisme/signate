/**
 * Template List Component
 * Display templates in a card list with actions
 */

import { useState } from 'react'
import { FileText, Eye, Edit, Trash2 } from 'lucide-react'
import { TEMPLATE_TYPES, type Template, type TemplateType } from '../types/template.types'
import { formatDateTime } from '@/shared/utils/formatters'

interface TemplateListProps {
  templates: Template[]
  isLoading?: boolean
  onEdit: (template: Template) => void
  onDelete: (template: Template) => void
  onPreview: (template: Template) => void
}

export const TemplateList = ({
  templates,
  isLoading,
  onEdit,
  onDelete,
  onPreview,
}: TemplateListProps) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<TemplateType | 'all'>('all')

  // Filter templates
  const filteredTemplates = templates.filter((template) => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = filterType === 'all' || template.template_type === filterType

    return matchesSearch && matchesType
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 dark:bg-gray-700 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (templates.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
        <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400 dark:text-gray-500" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No templates yet</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Create your first template to get started
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        {/* Search */}
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        {/* Type filter */}
        <div className="w-full md:w-48">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as TemplateType | 'all')}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option value="all">All Types</option>
            {Object.values(TEMPLATE_TYPES).map((type) => (
              <option key={type.type} value={type.type}>
                {type.icon} {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results count */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Showing {filteredTemplates.length} of {templates.length} templates
      </div>

      {/* Template cards */}
      <div className="space-y-3">
        {filteredTemplates.map((template) => {
          const typeInfo = TEMPLATE_TYPES[template.template_type]
          const variableCount = Object.keys(template.variables || {}).length

          return (
            <div
              key={template.id}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                {/* Template info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{typeInfo.icon}</span>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{template.name}</h3>
                      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-xs font-medium">
                          {typeInfo.label}
                        </span>
                        <span>•</span>
                        <span>{variableCount} variable(s)</span>
                        <span>•</span>
                        <span>{template.content.length} chars</span>
                      </div>
                    </div>
                  </div>

                  {template.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{template.description}</p>
                  )}

                  {/* Variables preview */}
                  {variableCount > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {Object.keys(template.variables).slice(0, 5).map((varName) => (
                        <span
                          key={varName}
                          className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded font-mono"
                        >
                          {'{{'}{varName}{'}}'}
                        </span>
                      ))}
                      {variableCount > 5 && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          +{variableCount - 5} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Content preview */}
                  <div className="bg-gray-50 dark:bg-gray-700 rounded p-2 mb-2">
                    <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap line-clamp-2 font-mono">
                      {template.content}
                    </pre>
                  </div>

                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Created {formatDateTime(template.created_at)}
                    {template.updated_at !== template.created_at && (
                      <> • Updated {formatDateTime(template.updated_at)}</>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => onPreview(template)}
                    className="px-3 py-1.5 text-sm bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded hover:bg-purple-100 dark:hover:bg-purple-900/50 flex items-center gap-1"
                    title="Preview Template"
                  >
                    <Eye className="w-4 h-4" />
                    Preview
                  </button>
                  <button
                    onClick={() => onEdit(template)}
                    className="px-3 py-1.5 text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-100 dark:hover:bg-blue-900/50 flex items-center gap-1"
                    title="Edit Template"
                  >
                    <Edit className="w-4 h-4" />
                    Edit
                  </button>
                  <button
                    onClick={() => onDelete(template)}
                    className="px-3 py-1.5 text-sm bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded hover:bg-red-100 dark:hover:bg-red-900/50 flex items-center gap-1"
                    title="Delete Template"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* No results */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-8 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-gray-600 dark:text-gray-400">No templates match your filters</p>
          <button
            onClick={() => {
              setSearchQuery('')
              setFilterType('all')
            }}
            className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  )
}

export default TemplateList
