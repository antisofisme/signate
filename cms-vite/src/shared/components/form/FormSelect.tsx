/**
 * FormSelect Component
 * Select dropdown with React Hook Form integration and error handling
 */
import { useFormContext, Controller } from 'react-hook-form';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
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
  placeholder = 'Select...',
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
            <Label
              htmlFor={name}
              className={cn(
                'text-sm font-medium text-gray-700 dark:text-gray-300',
                error && 'text-destructive'
              )}
            >
              {label}
              {required && <span className="text-destructive ml-1">*</span>}
            </Label>
          )}
          <Select
            value={field.value || ''}
            onValueChange={field.onChange}
            disabled={disabled}
          >
            <SelectTrigger
              className={cn(
                className,
                error && 'border-destructive focus:ring-destructive'
              )}
            >
              <SelectValue placeholder={placeholder} />
            </SelectTrigger>
            <SelectContent>
              {options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
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
