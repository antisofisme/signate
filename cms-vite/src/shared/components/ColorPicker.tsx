/**
 * ColorPicker Component
 *
 * Reusable color picker with:
 * - Native color input
 * - Hex value display
 * - Label and error state support
 */

import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface ColorPickerProps {
  value?: string;
  onChange?: (color: string) => void;
  label?: string;
  error?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
  name?: string;
}

export const ColorPicker = forwardRef<HTMLInputElement, ColorPickerProps>(
  ({ value = '#3B82F6', onChange, label, error, disabled, className, id, name }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange?.(e.target.value);
    };

    return (
      <div className={cn('space-y-1', className)}>
        {label && (
          <label
            htmlFor={id || name}
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {label}
          </label>
        )}

        <div className="flex items-center gap-3">
          {/* Color Preview Box */}
          <div
            className="w-10 h-10 rounded-lg border-2 border-gray-200 dark:border-gray-600 shadow-sm overflow-hidden"
            style={{ backgroundColor: value }}
          >
            <input
              ref={ref}
              type="color"
              id={id || name}
              name={name}
              value={value}
              onChange={handleChange}
              disabled={disabled}
              className="w-full h-full cursor-pointer opacity-0"
              title="Pick a color"
            />
          </div>

          {/* Hex Value Display */}
          <input
            type="text"
            value={value?.toUpperCase()}
            onChange={(e) => {
              const hex = e.target.value;
              if (/^#[0-9A-Fa-f]{0,6}$/.test(hex)) {
                onChange?.(hex);
              }
            }}
            onBlur={(e) => {
              // Validate and fix hex on blur
              let hex = e.target.value;
              if (!/^#[0-9A-Fa-f]{6}$/.test(hex)) {
                onChange?.('#3B82F6'); // Reset to default if invalid
              }
            }}
            disabled={disabled}
            placeholder="#3B82F6"
            className={cn(
              'w-24 px-3 py-2 text-sm font-mono uppercase',
              'border border-gray-300 dark:border-gray-600 rounded-lg',
              'bg-white dark:bg-gray-800',
              'text-gray-900 dark:text-gray-100',
              'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              'disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed',
              error && 'border-red-500 focus:ring-red-500'
            )}
          />
        </div>

        {error && (
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

ColorPicker.displayName = 'ColorPicker';

export default ColorPicker;
