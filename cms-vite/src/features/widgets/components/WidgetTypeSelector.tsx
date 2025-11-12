/**
 * Widget Type Selector Component
 * Select widget type with visual cards
 */

import { WIDGET_TYPES, type WidgetType } from '../types/widget.types'
import { renderIcon } from '@/shared/utils/iconHelper'

interface WidgetTypeSelectorProps {
  value: WidgetType
  onChange: (type: WidgetType) => void
  disabled?: boolean
}

export const WidgetTypeSelector = ({
  value,
  onChange,
  disabled = false,
}: WidgetTypeSelectorProps) => {
  return (
    <div className="space-y-3">
      <label className="text-sm font-medium text-gray-700">Widget Type</label>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {Object.values(WIDGET_TYPES).map((widgetType) => (
          <button
            key={widgetType.type}
            type="button"
            onClick={() => onChange(widgetType.type)}
            disabled={disabled}
            className={`
              relative p-4 rounded-lg border-2 transition-all text-left
              ${
                value === widgetType.type
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            {/* Selection indicator */}
            {value === widgetType.type && (
              <div className="absolute top-2 right-2">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                  <svg
                    className="w-3 h-3 text-white"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M5 13l4 4L19 7"></path>
                  </svg>
                </div>
              </div>
            )}

            {/* Icon */}
            <div className="mb-2">{renderIcon(widgetType.icon, { className: 'w-12 h-12 mx-auto' })}</div>

            {/* Label */}
            <h3 className="font-semibold text-gray-900 mb-1">
              {widgetType.label}
            </h3>

            {/* Description */}
            <p className="text-sm text-gray-600">{widgetType.description}</p>
          </button>
        ))}
      </div>
    </div>
  )
}

export default WidgetTypeSelector
