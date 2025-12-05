/**
 * FormInput Component
 * Input field with React Hook Form integration and error handling
 * Uses pure Tailwind CSS styling (no shadcn)
 */
import { forwardRef } from 'react';
import { useFormContext, Controller } from 'react-hook-form';
import { cn } from '@/lib/utils';

interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  name: string;
  label?: string;
  description?: string;
}

export const FormInput = forwardRef<HTMLInputElement, FormInputProps>(
  ({ name, label, description, className, ...props }, ref) => {
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
                {props.required && <span className="text-red-500 ml-1">*</span>}
              </label>
            )}
            <input
              {...field}
              {...props}
              ref={ref}
              id={name}
              value={field.value ?? ''}
              className={cn(
                'w-full px-3 py-2',
                'border rounded-lg',
                'bg-white dark:bg-gray-700',
                'text-gray-900 dark:text-white',
                'placeholder:text-gray-400 dark:placeholder:text-gray-500',
                'focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'transition-colors duration-150',
                error
                  ? 'border-red-500 dark:border-red-400'
                  : 'border-gray-300 dark:border-gray-600',
                className
              )}
              aria-invalid={!!error}
              aria-required={props.required}
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
        )}
      />
    );
  }
);

FormInput.displayName = 'FormInput';
