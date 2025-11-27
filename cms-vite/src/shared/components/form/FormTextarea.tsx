/**
 * FormTextarea Component
 * Textarea with React Hook Form integration and error handling
 */
import { forwardRef } from 'react';
import { useFormContext, Controller } from 'react-hook-form';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface FormTextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  name: string;
  label?: string;
  description?: string;
}

export const FormTextarea = forwardRef<HTMLTextAreaElement, FormTextareaProps>(
  ({ name, label, description, className, rows = 4, ...props }, ref) => {
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
              <Label
                htmlFor={name}
                className={cn(
                  'text-sm font-medium text-gray-700 dark:text-gray-300',
                  error && 'text-destructive'
                )}
              >
                {label}
                {props.required && (
                  <span className="text-destructive ml-1">*</span>
                )}
              </Label>
            )}
            <textarea
              {...field}
              {...props}
              ref={ref}
              id={name}
              rows={rows}
              className={cn(
                'flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
                'placeholder:text-muted-foreground',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                'disabled:cursor-not-allowed disabled:opacity-50',
                'resize-y min-h-[80px]',
                error && 'border-destructive focus-visible:ring-destructive',
                className
              )}
              aria-invalid={!!error}
              aria-describedby={error ? `${name}-error` : undefined}
            />
            {description && !error && (
              <p className="text-sm text-muted-foreground">{description}</p>
            )}
            {error && (
              <p
                id={`${name}-error`}
                className="text-sm text-destructive"
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

FormTextarea.displayName = 'FormTextarea';
