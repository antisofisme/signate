/**
 * Template Editor Component
 * Code editor for template content with syntax highlighting hints
 */

import { useState, useRef, useEffect } from 'react'

interface TemplateEditorProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  language?: 'text' | 'html' | 'jinja2'
  height?: string
}

export const TemplateEditor = ({
  value,
  onChange,
  disabled = false,
  language = 'jinja2',
  height = '400px'
}: TemplateEditorProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [lineCount, setLineCount] = useState(1)

  // Update line count when value changes
  useEffect(() => {
    const lines = value.split('\n').length
    setLineCount(lines)
  }, [value])

  // Handle tab key for indentation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault()
      const start = e.currentTarget.selectionStart
      const end = e.currentTarget.selectionEnd
      const newValue = value.substring(0, start) + '  ' + value.substring(end)
      onChange(newValue)

      // Move cursor after inserted spaces
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = start + 2
          textareaRef.current.selectionEnd = start + 2
        }
      }, 0)
    }
  }

  // Highlight variables in preview
  const renderHighlightedPreview = () => {
    if (!value) return null

    // Simple regex to find {{variable}} patterns
    const parts = value.split(/({{[^}]+}})/)

    return (
      <div className="absolute inset-0 pointer-events-none overflow-hidden whitespace-pre-wrap break-words font-mono text-sm p-4 leading-6">
        {parts.map((part, index) => {
          if (part.startsWith('{{') && part.endsWith('}}')) {
            return (
              <span key={index} className="bg-blue-200/50 text-blue-700 px-1 rounded">
                {part}
              </span>
            )
          }
          return <span key={index} className="text-transparent">{part}</span>
        })}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">Template Content</label>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>{lineCount} lines</span>
          <span>•</span>
          <span>{value.length} characters</span>
        </div>
      </div>

      <div className="relative border-2 border-gray-300 rounded-lg overflow-hidden bg-white">
        {/* Line numbers */}
        <div
          className="absolute left-0 top-0 w-12 bg-gray-50 border-r border-gray-300 text-right pr-2 select-none"
          style={{ height }}
        >
          <div className="font-mono text-xs text-gray-500 p-4 leading-6">
            {Array.from({ length: lineCount }, (_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>
        </div>

        {/* Highlighted preview overlay */}
        <div className="absolute left-12 top-0 right-0 bottom-0">
          {renderHighlightedPreview()}
        </div>

        {/* Actual textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          className="relative w-full font-mono text-sm p-4 pl-14 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 leading-6 bg-transparent"
          style={{ height }}
          placeholder="Enter your template here...&#10;Use {{variable_name}} for variables"
          spellCheck={false}
        />
      </div>

      {/* Syntax hints */}
      <div className="bg-blue-50 border border-blue-200 rounded p-3">
        <h4 className="text-xs font-semibold text-blue-900 mb-2">💡 Syntax Tips:</h4>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• Use <code className="bg-blue-100 px-1 rounded">{'{{variable_name}}'}</code> for variable substitution</li>
          <li>• Variables are highlighted in <span className="bg-blue-200 px-1 rounded">blue</span></li>
          <li>• Press Tab to indent (2 spaces)</li>
          <li>• Supports Jinja2 template syntax</li>
        </ul>
      </div>
    </div>
  )
}

export default TemplateEditor
