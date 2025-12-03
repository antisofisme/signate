/**
 * Template Preview Component
 * Live preview of rendered template with test data
 */

import { useState, useEffect } from 'react'
import { Eye, Edit, Rocket, Lightbulb } from 'lucide-react'
import { Button } from '@/shared/components'
import { DEFAULT_PREVIEW_DATA } from '../types/template.types'

interface TemplatePreviewProps {
  content: string
  variables: Record<string, string>
  previewData?: Record<string, any>
  onPreviewDataChange?: (data: Record<string, any>) => void
  onRender?: (data: Record<string, any>) => void
  renderedContent?: string
  isRendering?: boolean
}

export const TemplatePreview = ({
  content,
  variables,
  previewData,
  onPreviewDataChange,
  onRender,
  renderedContent,
  isRendering = false
}: TemplatePreviewProps) => {
  const [testData, setTestData] = useState<Record<string, any>>(previewData || {})
  const [showDataEditor, setShowDataEditor] = useState(false)

  // Initialize test data with defaults
  useEffect(() => {
    if (Object.keys(testData).length === 0 && Object.keys(variables).length > 0) {
      const initialData: Record<string, any> = {}
      Object.keys(variables).forEach(varName => {
        initialData[varName] = DEFAULT_PREVIEW_DATA[varName] || ''
      })
      setTestData(initialData)
    }
  }, [variables])

  const handleDataChange = (varName: string, value: any) => {
    const newData = { ...testData, [varName]: value }
    setTestData(newData)
    onPreviewDataChange?.(newData)
  }

  const handleRenderClick = () => {
    onRender?.(testData)
  }

  // Client-side preview (simple replacement)
  const getClientPreview = () => {
    let preview = content
    Object.entries(testData).forEach(([key, value]) => {
      const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g')
      preview = preview.replace(regex, String(value || ''))
    })
    return preview
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Template Preview</label>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => setShowDataEditor(!showDataEditor)}
            leftIcon={showDataEditor ? <Eye className="w-3 h-3" /> : <Edit className="w-3 h-3" />}
          >
            {showDataEditor ? 'Show Preview' : 'Edit Data'}
          </Button>
          {onRender && (
            <Button
              type="button"
              size="sm"
              onClick={handleRenderClick}
              disabled={isRendering}
              loading={isRendering}
              leftIcon={<Rocket className="w-3 h-3" />}
            >
              {isRendering ? 'Rendering...' : 'Render'}
            </Button>
          )}
        </div>
      </div>

      {showDataEditor ? (
        /* Test Data Editor */
        <div className="space-y-3">
          <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 rounded p-3">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-4 h-4 text-yellow-800 dark:text-yellow-200 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-yellow-800 dark:text-yellow-200">
                Enter test data for variables to preview the rendered template
              </p>
            </div>
          </div>

          {Object.keys(variables).length > 0 ? (
            <div className="space-y-3">
              {Object.keys(variables).map(varName => {
                const varType = variables[varName]
                return (
                  <div key={varName}>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      <code className="bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded text-gray-900 dark:text-gray-100">
                        {'{{'}{varName}{'}}'}
                      </code>
                      <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">({varType})</span>
                    </label>
                    {varType === 'boolean' ? (
                      <input
                        type="checkbox"
                        checked={testData[varName] || false}
                        onChange={(e) => handleDataChange(varName, e.target.checked)}
                        className="w-4 h-4"
                      />
                    ) : (
                      <input
                        type={varType === 'number' ? 'number' : varType === 'date' ? 'date' : 'text'}
                        value={testData[varName] || ''}
                        onChange={(e) => handleDataChange(varName, e.target.value)}
                        placeholder={`Enter ${varName}...`}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    )}
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded bg-gray-50 dark:bg-gray-800">
              <p className="text-sm text-gray-600 dark:text-gray-400">No variables defined</p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Add variables to enable test data</p>
            </div>
          )}
        </div>
      ) : (
        /* Preview Panel */
        <div className="border-2 border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
          {/* Preview Tabs */}
          <div className="bg-gray-50 dark:bg-gray-700 border-b border-gray-300 dark:border-gray-600 px-4 py-2 flex gap-2">
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Preview:</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {renderedContent ? 'Server Rendered' : 'Client Preview'}
            </span>
          </div>

          {/* Preview Content */}
          <div className="p-4 bg-white dark:bg-gray-800 min-h-[200px] max-h-[400px] overflow-auto">
            {renderedContent ? (
              <div className="prose prose-sm max-w-none">
                <pre className="whitespace-pre-wrap break-words bg-gray-50 dark:bg-gray-700 p-4 rounded border border-gray-200 dark:border-gray-600 text-gray-900 dark:text-gray-100">
                  {renderedContent}
                </pre>
              </div>
            ) : (
              <div className="prose prose-sm max-w-none text-gray-900 dark:text-gray-100">
                <pre className="whitespace-pre-wrap break-words">
                  {getClientPreview() || 'Enter template content to see preview...'}
                </pre>
              </div>
            )}
          </div>

          {/* Preview Footer */}
          <div className="bg-gray-50 dark:bg-gray-700 border-t border-gray-300 dark:border-gray-600 px-4 py-2">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-3 h-3 text-gray-600 dark:text-gray-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-gray-600 dark:text-gray-400">
                This is a preview. Click "Render" to see server-rendered output with Jinja2.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TemplatePreview
