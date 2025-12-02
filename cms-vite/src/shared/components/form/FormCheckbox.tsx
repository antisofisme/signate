/**
 * FormCheckbox Component
 * Checkbox with React Hook Form integration
 * Uses pure Tailwind CSS styling (no shadcn)
 */
import { useFormContext, Controller } from 'react-hook-form';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FormCheckboxProps {
  name: string;
  label?: string;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export function FormCheckbox({
  name,
  label,
  description,
  disabled,
  className,
}: FormCheckboxProps) {
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
        <div className={cn('flex items-start space-x-3', className)}>
          <button
            type="button"
            role="checkbox"
            aria-checked={field.value}
            disabled={disabled}
            onClick={() => field.onChange(!field.value)}
            className={cn(
              'flex h-5 w-5 items-center justify-center rounded border transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
              'disabled:cursor-not-allowed disabled:opacity-50',
              field.value
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800',
              error && 'border-red-500 dark:border-red-400'
            )}
          >
            {field.value && <Check className="h-3.5 w-3.5" />}
          </button>
          <div className="flex flex-col">
            {label && (
              <label
                htmlFor={name}
                className={cn(
                  'text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer',
                  error && 'text-red-500 dark:text-red-400'
                )}
                onClick={() => !disabled && field.onChange(!field.value)}
              >
                {label}
              </label>
            )}
            {description && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{description}</p>
            )}
            {error && (
              <p className="text-xs text-red-500 dark:text-red-400 mt-1" role="alert">
                {error.message as string}
              </p>
            )}
          </div>
        </div>
      )}
    />
  );
}
