/**
 * ActivationCodeInput Component
 * Single input field for 6-digit activation codes with React Hook Form integration
 *
 * Features:
 * - Numeric only validation
 * - Monospace font with wide letter spacing
 * - Centered text, large display
 * - Auto-uppercase for alphanumeric codes (optional)
 */
import { useFormContext, Controller } from 'react-hook-form';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface ActivationCodeInputProps {
  /** Field name for React Hook Form */
  name: string;
  /** Label text */
  label?: string;
  /** Number of characters (default: 6) */
  length?: number;
  /** Whether the field is required */
  required?: boolean;
  /** Whether the input is disabled */
  disabled?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Description/hint text */
  description?: string;
  /** Allow alphanumeric (default: false - numeric only) */
  alphanumeric?: boolean;
}

export function ActivationCodeInput({
  name,
  label,
  length = 6,
  required = false,
  disabled = false,
  placeholder,
  description,
  alphanumeric = false,
}: ActivationCodeInputProps) {
  const {
    control,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => {
        const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
          let value = e.target.value;

          if (alphanumeric) {
            // Allow alphanumeric, convert to uppercase
            value = value.replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, length);
          } else {
            // Numeric only
            value = value.replace(/\D/g, '').slice(0, length);
          }

          field.onChange(value);
        };

        return (
          <div className="space-y-2">
            {label && (
              <Label
                htmlFor={name}
                className={cn(
                  'block text-sm font-medium text-gray-700 dark:text-gray-300',
                  error && 'text-red-500 dark:text-red-400'
                )}
              >
                {label}
                {required && <span className="text-red-500 ml-1">*</span>}
              </Label>
            )}

            <input
              {...field}
              id={name}
              type="text"
              inputMode={alphanumeric ? 'text' : 'numeric'}
              maxLength={length}
              value={field.value || ''}
              onChange={handleChange}
              placeholder={placeholder}
              disabled={disabled}
              className={cn(
                'w-full px-4 py-3',
                'text-center text-xl font-mono font-bold tracking-[0.5em]',
                'border rounded-lg',
                'bg-white dark:bg-gray-700',
                'text-gray-900 dark:text-white',
                'placeholder:text-gray-400 dark:placeholder:text-gray-500',
                'placeholder:tracking-normal placeholder:font-normal',
                'focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'transition-all duration-150',
                error
                  ? 'border-red-500 dark:border-red-400'
                  : 'border-gray-300 dark:border-gray-600'
              )}
              aria-invalid={!!error}
              aria-describedby={error ? `${name}-error` : description ? `${name}-desc` : undefined}
            />

            {description && !error && (
              <p id={`${name}-desc`} className="text-xs text-gray-500 dark:text-gray-400">
                {description}
              </p>
            )}

            {error && (
              <p
                id={`${name}-error`}
                className="text-xs text-red-500 dark:text-red-400"
                role="alert"
              >
                {error.message as string}
              </p>
            )}
          </div>
        );
      }}
    />
  );
}

ActivationCodeInput.displayName = 'ActivationCodeInput';
