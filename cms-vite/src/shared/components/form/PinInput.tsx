/**
 * PinInput Component
 * 6-digit PIN input with separate boxes and React Hook Form integration
 *
 * Features:
 * - Separate input boxes for each digit
 * - Auto-focus next on input
 * - Backspace moves to previous
 * - Paste support (splits string across boxes)
 * - Numeric only validation
 */
import { useRef, useEffect, KeyboardEvent, ClipboardEvent } from 'react';
import { useFormContext, Controller } from 'react-hook-form';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface PinInputProps {
  /** Field name for React Hook Form */
  name: string;
  /** Label text */
  label?: string;
  /** Number of digits (default: 6) */
  length?: number;
  /** Whether the field is required */
  required?: boolean;
  /** Whether the input is disabled */
  disabled?: boolean;
  /** Auto focus on mount */
  autoFocus?: boolean;
  /** Description/hint text */
  description?: string;
}

export function PinInput({
  name,
  label,
  length = 6,
  required = false,
  disabled = false,
  autoFocus = false,
  description,
}: PinInputProps) {
  const {
    control,
    formState: { errors },
  } = useFormContext();

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const error = errors[name];

  // Auto focus first input on mount
  useEffect(() => {
    if (autoFocus && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [autoFocus]);

  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => {
        // Convert value to array of digits
        const digits = (field.value || '').split('').slice(0, length);
        while (digits.length < length) digits.push('');

        const handleChange = (index: number, value: string) => {
          // Only allow numeric input
          const digit = value.replace(/\D/g, '').slice(-1);

          const newDigits = [...digits];
          newDigits[index] = digit;

          // Update form value
          field.onChange(newDigits.join(''));

          // Auto-focus next input
          if (digit && index < length - 1) {
            inputRefs.current[index + 1]?.focus();
          }
        };

        const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
          // Backspace: clear current and move to previous
          if (e.key === 'Backspace') {
            if (!digits[index] && index > 0) {
              e.preventDefault();
              const newDigits = [...digits];
              newDigits[index - 1] = '';
              field.onChange(newDigits.join(''));
              inputRefs.current[index - 1]?.focus();
            }
          }

          // Arrow keys navigation
          if (e.key === 'ArrowLeft' && index > 0) {
            e.preventDefault();
            inputRefs.current[index - 1]?.focus();
          }
          if (e.key === 'ArrowRight' && index < length - 1) {
            e.preventDefault();
            inputRefs.current[index + 1]?.focus();
          }
        };

        const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
          e.preventDefault();
          const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length);
          field.onChange(pastedData);

          // Focus the input after last pasted digit
          const focusIndex = Math.min(pastedData.length, length - 1);
          inputRefs.current[focusIndex]?.focus();
        };

        const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
          e.target.select();
        };

        return (
          <div className="space-y-2">
            {label && (
              <Label
                className={cn(
                  'text-sm font-medium text-gray-700 dark:text-gray-300',
                  error && 'text-red-500 dark:text-red-400'
                )}
              >
                {label}
                {required && <span className="text-red-500 ml-1">*</span>}
              </Label>
            )}

            <div className="flex gap-2 justify-center">
              {Array.from({ length }).map((_, index) => (
                <input
                  key={index}
                  ref={(el) => (inputRefs.current[index] = el)}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digits[index]}
                  onChange={(e) => handleChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  onPaste={handlePaste}
                  onFocus={handleFocus}
                  disabled={disabled}
                  className={cn(
                    'w-12 h-14 text-center text-2xl font-mono font-bold',
                    'border rounded-lg bg-white dark:bg-gray-700',
                    'text-gray-900 dark:text-white',
                    'focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    'disabled:opacity-50 disabled:cursor-not-allowed',
                    'transition-all duration-150',
                    error
                      ? 'border-red-500 dark:border-red-400'
                      : 'border-gray-300 dark:border-gray-600'
                  )}
                  aria-label={`Digit ${index + 1}`}
                />
              ))}
            </div>

            {description && !error && (
              <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                {description}
              </p>
            )}

            {error && (
              <p className="text-xs text-red-500 dark:text-red-400 text-center" role="alert">
                {error.message as string}
              </p>
            )}
          </div>
        );
      }}
    />
  );
}

PinInput.displayName = 'PinInput';
