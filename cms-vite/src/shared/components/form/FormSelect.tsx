/**
 * FormSelect Component
 * Select dropdown with React Hook Form integration and error handling
 * Uses pure Tailwind CSS styling (no shadcn)
 */
import { useFormContext, Controller } from 'react-hook-form';
import { cn } from '@/lib/utils';

export interface SelectOption {
  value: string;
  label: string;
}

interface FormSelectProps {
  name: string;
  label?: string;
  placeholder?: string;
  options: SelectOption[];
  description?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
}

export function FormSelect({
  name,
  label,
  placeholder = 'Pilih...',
  options,
  description,
  required,
  disabled,
  className,
}: FormSelectProps) {
  const {
    control,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <div className="space-y-2">
          {label && (
            <label
              htmlFor={name}
              className={cn(
                'block text-sm font-medium text-gray-700 dark:text-gray-300',
                error && 'text-red-500 dark:text-red-400'
              )}
            >
              {label}
              {required && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          <select
            {...field}
            id={name}
            disabled={disabled}
            className={cn(
              'w-full px-3 py-2',
              'border rounded-lg',
              'bg-white dark:bg-gray-700',
              'text-gray-900 dark:text-white',
              'focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-colors duration-150',
              error
                ? 'border-red-500 dark:border-red-400'
                : 'border-gray-300 dark:border-gray-600',
              className
            )}
            aria-invalid={!!error}
            aria-required={required}
            aria-describedby={error ? `${name}-error` : description ? `${name}-desc` : undefined}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
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
      )}
    />
  );
}
