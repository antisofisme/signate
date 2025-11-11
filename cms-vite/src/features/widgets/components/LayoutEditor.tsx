/**
 * Layout Editor Component
 * Visual editor for widget position and size
 */

import { useState, useRef, useEffect } from 'react'
import type { WidgetLayout } from '../types/widget.types'
import { CANVAS_WIDTH, CANVAS_HEIGHT } from '../types/widget.types'

interface LayoutEditorProps {
  value: WidgetLayout
  onChange: (layout: WidgetLayout) => void
  disabled?: boolean
}

export const LayoutEditor = ({ value, onChange, disabled = false }: LayoutEditorProps) => {
  const canvasRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isResizing, setIsResizing] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  // Scale for canvas (fit to container)
  const SCALE = 0.4 // 40% of actual size for preview

  const handleMouseDown = (e: React.MouseEvent, action: 'drag' | 'resize') => {
    if (disabled) return
    e.preventDefault()
    e.stopPropagation()

    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return

    const x = (e.clientX - rect.left) / SCALE
    const y = (e.clientY - rect.top) / SCALE

    setDragStart({ x, y })

    if (action === 'drag') {
      setIsDragging(true)
    } else {
      setIsResizing(true)
    }
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging && !isResizing) return

    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return

    const x = (e.clientX - rect.left) / SCALE
    const y = (e.clientY - rect.top) / SCALE

    if (isDragging) {
      const deltaX = x - dragStart.x
      const deltaY = y - dragStart.y

      onChange({
        ...value,
        x: Math.max(0, Math.min(CANVAS_WIDTH - value.width, value.x + deltaX)),
        y: Math.max(0, Math.min(CANVAS_HEIGHT - value.height, value.y + deltaY)),
      })

      setDragStart({ x, y })
    } else if (isResizing) {
      const newWidth = Math.max(50, Math.min(CANVAS_WIDTH - value.x, x - value.x))
      const newHeight = Math.max(50, Math.min(CANVAS_HEIGHT - value.y, y - value.y))

      onChange({
        ...value,
        width: newWidth,
        height: newHeight,
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
    setIsResizing(false)
  }

  useEffect(() => {
    if (isDragging || isResizing) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)

      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, isResizing, value])

  return (
    <div className="space-y-4">
      <label className="text-sm font-medium text-gray-700">Widget Position & Size</label>

      {/* Canvas */}
      <div className="border-2 border-gray-300 rounded-lg overflow-hidden bg-gray-900 relative">
        <div
          ref={canvasRef}
          className="relative bg-gray-800"
          style={{
            width: CANVAS_WIDTH * SCALE,
            height: CANVAS_HEIGHT * SCALE,
            backgroundImage:
              'linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px)',
            backgroundSize: `${40 * SCALE}px ${40 * SCALE}px`,
          }}
        >
          {/* Dimension labels */}
          <div className="absolute top-0 left-0 text-xs text-gray-400 p-2">
            {CANVAS_WIDTH} × {CANVAS_HEIGHT}
          </div>

          {/* Widget preview */}
          <div
            className={`absolute border-2 border-blue-500 bg-blue-500/20 ${
              disabled ? 'cursor-not-allowed' : 'cursor-move'
            }`}
            style={{
              left: value.x * SCALE,
              top: value.y * SCALE,
              width: value.width * SCALE,
              height: value.height * SCALE,
            }}
            onMouseDown={(e) => handleMouseDown(e, 'drag')}
          >
            {/* Widget info */}
            <div className="absolute top-1 left-1 text-xs text-white bg-blue-600 px-2 py-1 rounded">
              {Math.round(value.width)} × {Math.round(value.height)}
            </div>

            {/* Resize handle */}
            {!disabled && (
              <div
                className="absolute bottom-0 right-0 w-4 h-4 bg-blue-600 cursor-se-resize"
                onMouseDown={(e) => handleMouseDown(e, 'resize')}
              />
            )}
          </div>
        </div>
      </div>

      {/* Manual input fields */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">X Position</label>
          <input
            type="number"
            value={Math.round(value.x)}
            onChange={(e) =>
              onChange({
                ...value,
                x: Math.max(0, Math.min(CANVAS_WIDTH - value.width, Number(e.target.value))),
              })
            }
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            min={0}
            max={CANVAS_WIDTH - value.width}
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Y Position</label>
          <input
            type="number"
            value={Math.round(value.y)}
            onChange={(e) =>
              onChange({
                ...value,
                y: Math.max(0, Math.min(CANVAS_HEIGHT - value.height, Number(e.target.value))),
              })
            }
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            min={0}
            max={CANVAS_HEIGHT - value.height}
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Width</label>
          <input
            type="number"
            value={Math.round(value.width)}
            onChange={(e) =>
              onChange({
                ...value,
                width: Math.max(50, Math.min(CANVAS_WIDTH - value.x, Number(e.target.value))),
              })
            }
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            min={50}
            max={CANVAS_WIDTH - value.x}
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Height</label>
          <input
            type="number"
            value={Math.round(value.height)}
            onChange={(e) =>
              onChange({
                ...value,
                height: Math.max(50, Math.min(CANVAS_HEIGHT - value.y, Number(e.target.value))),
              })
            }
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            min={50}
            max={CANVAS_HEIGHT - value.y}
          />
        </div>
      </div>

      {/* Helper text */}
      <p className="text-xs text-gray-500">
        💡 Drag the blue rectangle to move, or drag the bottom-right corner to resize. Canvas represents 1920×1080 screen.
      </p>
    </div>
  )
}

export default LayoutEditor
