/**
 * FormInput Component
 * Input field with React Hook Form integration and error handling
 */
import { forwardRef } from 'react';
import { useFormContext, Controller } from 'react-hook-form';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
              <Label
                htmlFor={name}
                className={cn(
                  'text-sm font-medium text-gray-700 dark:text-gray-300',
                  error && 'text-destructive'
                )}
              >
                {label}
                {props.required && <span className="text-destructive ml-1">*</span>}
              </Label>
            )}
            <Input
              {...field}
              {...props}
              ref={ref}
              id={name}
              className={cn(
                className,
                error && 'border-destructive focus-visible:ring-destructive'
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

FormInput.displayName = 'FormInput';
