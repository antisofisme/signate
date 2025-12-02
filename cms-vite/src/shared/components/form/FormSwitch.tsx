/**
 * FormSwitch Component
 * Toggle switch with React Hook Form integration
 * Uses pure Tailwind CSS styling (no shadcn)
 */
import { useFormContext, Controller } from 'react-hook-form';
import { cn } from '@/lib/utils';

interface FormSwitchProps {
  name: string;
  label?: string;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export function FormSwitch({
  name,
  label,
  description,
  disabled,
  className,
}: FormSwitchProps) {
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
            role="switch"
            aria-checked={field.value}
            disabled={disabled}
            onClick={() => field.onChange(!field.value)}
            className={cn(
              'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
              'disabled:cursor-not-allowed disabled:opacity-50',
              field.value
                ? 'bg-blue-600'
                : 'bg-gray-200 dark:bg-gray-700',
              error && 'ring-2 ring-red-500'
            )}
          >
            <span
              className={cn(
                'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                field.value ? 'translate-x-5' : 'translate-x-0'
              )}
            />
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
