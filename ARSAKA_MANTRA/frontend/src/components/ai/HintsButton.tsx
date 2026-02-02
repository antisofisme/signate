/**
 * HintsButton - AI-powered hints for form fields
 *
 * Features:
 * - On-demand hints (user clicks button)
 * - Grammar correction
 * - Similar decision detection
 * - Improvement suggestions
 * - Classification recommendations
 */

import { useState } from 'react'
import { clsx } from 'clsx'
import { useAIHints } from '../../hooks/useAIChat'

interface HintsButtonProps {
  text: string
  fieldType?: string
  context?: Record<string, unknown>
  onApplyGrammar?: (corrected: string) => void
  className?: string
}

interface Hints {
  grammar: string
  similar: string
  suggestions: string[]
  classification?: string
}

export default function HintsButton({
  text,
  fieldType = 'statement',
  context,
  onApplyGrammar,
  className,
}: HintsButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [hints, setHints] = useState<Hints | null>(null)
  const hintsMutation = useAIHints()

  const handleGetHints = async () => {
    if (!text.trim()) {
      return
    }

    setIsOpen(true)
    setHints(null)

    try {
      const result = await hintsMutation.mutateAsync({
        text,
        field_type: fieldType,
        context,
      })

      if (result.success && result.hints) {
        setHints(result.hints)
      }
    } catch (error) {
      console.error('Failed to get hints:', error)
    }
  }

  const handleClose = () => {
    setIsOpen(false)
    setHints(null)
  }

  const handleApplyGrammar = () => {
    if (hints?.grammar && onApplyGrammar) {
      onApplyGrammar(hints.grammar)
      handleClose()
    }
  }

  return (
    <div className={clsx("relative inline-block", className)}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={handleGetHints}
        disabled={!text.trim() || hintsMutation.isPending}
        className={clsx(
          "flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors",
          text.trim()
            ? "bg-indigo-50 text-indigo-600 hover:bg-indigo-100"
            : "bg-gray-100 text-gray-400 cursor-not-allowed"
        )}
        title="Get AI hints for this text"
      >
        {hintsMutation.isPending ? (
          <>
            <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>Analyzing...</span>
          </>
        ) : (
          <>
            <span>🤖</span>
            <span>Get AI Hints</span>
          </>
        )}
      </button>

      {/* Hints Panel */}
      {isOpen && (
        <div className="absolute z-50 mt-2 right-0 w-80 bg-white rounded-lg shadow-xl border p-4 animate-in fade-in slide-in-from-top-2">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900 flex items-center gap-2">
              <span>🤖</span>
              AI Hints
            </h4>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Loading */}
          {hintsMutation.isPending && (
            <div className="text-center py-4">
              <div className="animate-pulse text-indigo-600">Analyzing text...</div>
            </div>
          )}

          {/* Error */}
          {hintsMutation.error && (
            <div className="bg-red-50 text-red-600 text-xs p-2 rounded">
              Failed to get hints. Please try again.
            </div>
          )}

          {/* Hints Content */}
          {hints && (
            <div className="space-y-3 text-sm">
              {/* Grammar */}
              <div className="bg-blue-50 rounded p-3">
                <div className="flex items-center gap-1 text-blue-700 font-medium mb-1">
                  <span>📝</span> Grammar
                </div>
                <p className="text-blue-800 text-xs">{hints.grammar}</p>
                {onApplyGrammar && hints.grammar !== text && (
                  <button
                    onClick={handleApplyGrammar}
                    className="mt-2 text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                  >
                    Apply Correction
                  </button>
                )}
              </div>

              {/* Similar */}
              <div className="bg-amber-50 rounded p-3">
                <div className="flex items-center gap-1 text-amber-700 font-medium mb-1">
                  <span>⚠️</span> Similar Decisions
                </div>
                <p className="text-amber-800 text-xs">{hints.similar}</p>
              </div>

              {/* Suggestions */}
              {hints.suggestions.length > 0 && (
                <div className="bg-green-50 rounded p-3">
                  <div className="flex items-center gap-1 text-green-700 font-medium mb-1">
                    <span>💡</span> Suggestions
                  </div>
                  <ul className="text-green-800 text-xs space-y-1">
                    {hints.suggestions.map((suggestion, i) => (
                      <li key={i} className="flex items-start gap-1">
                        <span className="text-green-500">•</span>
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Classification */}
              {hints.classification && (
                <div className="bg-purple-50 rounded p-3">
                  <div className="flex items-center gap-1 text-purple-700 font-medium mb-1">
                    <span>🏷️</span> Classification
                  </div>
                  <p className="text-purple-800 text-xs">{hints.classification}</p>
                </div>
              )}

              {/* Disclaimer */}
              <div className="text-xs text-gray-400 text-center pt-2 border-t">
                AI suggestions require human review
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
