/**
 * Slider Component
 * Simple range slider for numeric input
 */

import * as React from 'react'

interface SliderProps {
  value: number[]
  onValueChange: (value: number[]) => void
  min?: number
  max?: number
  step?: number
  className?: string
  disabled?: boolean
}

export const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ value, onValueChange, min = 0, max = 100, step = 1, className = '', disabled = false }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onValueChange([Number(e.target.value)])
    }

    const percentage = ((value[0] - min) / (max - min)) * 100

    return (
      <div className={`relative w-full ${className}`}>
        <input
          ref={ref}
          type="range"
          min={min}
          max={max}
          step={step}
          value={value[0]}
          onChange={handleChange}
          disabled={disabled}
          className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed slider-thumb"
          style={{
            background: `linear-gradient(to right, rgb(147 51 234) 0%, rgb(147 51 234) ${percentage}%, rgb(229 231 235) ${percentage}%, rgb(229 231 235) 100%)`,
          }}
        />
        <style>{`
          .slider-thumb::-webkit-slider-thumb {
            appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: rgb(147 51 234);
            cursor: pointer;
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
          }
          .slider-thumb::-moz-range-thumb {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: rgb(147 51 234);
            cursor: pointer;
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
          }
          .slider-thumb:disabled::-webkit-slider-thumb {
            cursor: not-allowed;
            opacity: 0.5;
          }
          .slider-thumb:disabled::-moz-range-thumb {
            cursor: not-allowed;
            opacity: 0.5;
          }
        `}</style>
      </div>
    )
  }
)

Slider.displayName = 'Slider'
