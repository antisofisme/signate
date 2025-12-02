/**
 * PasswordInput Component
 * Password input with visibility toggle and React Hook Form integration
 *
 * Features:
 * - Toggle visibility (eye icon)
 * - Optional strength meter
 * - Requirements checklist (uppercase, lowercase, number, special char)
 * - Minimum length indicator
 */
import { useState } from 'react';
import { useFormContext, Controller } from 'react-hook-form';
import { Label } from '@/components/ui/label';
import { Eye, EyeOff, Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PasswordRequirement {
  label: string;
  test: (value: string) => boolean;
}

const defaultRequirements: PasswordRequirement[] = [
  { label: 'Minimal 8 karakter', test: (v) => v.length >= 8 },
  { label: 'Huruf besar (A-Z)', test: (v) => /[A-Z]/.test(v) },
  { label: 'Huruf kecil (a-z)', test: (v) => /[a-z]/.test(v) },
  { label: 'Angka (0-9)', test: (v) => /[0-9]/.test(v) },
  { label: 'Karakter khusus (!@#$%)', test: (v) => /[!@#$%^&*(),.?":{}|<>]/.test(v) },
];

interface PasswordInputProps {
  /** Field name for React Hook Form */
  name: string;
  /** Label text */
  label?: string;
  /** Whether the field is required */
  required?: boolean;
  /** Whether the input is disabled */
  disabled?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Show strength meter */
  showStrengthMeter?: boolean;
  /** Show requirements checklist */
  showRequirements?: boolean;
  /** Custom requirements (overrides default) */
  requirements?: PasswordRequirement[];
  /** Description/hint text */
  description?: string;
  /** Auto focus on mount */
  autoFocus?: boolean;
}

function calculateStrength(value: string, requirements: PasswordRequirement[]): number {
  if (!value) return 0;
  const passed = requirements.filter((req) => req.test(value)).length;
  return Math.round((passed / requirements.length) * 100);
}

function getStrengthLabel(strength: number): { label: string; color: string } {
  if (strength < 25) return { label: 'Sangat Lemah', color: 'bg-red-500' };
  if (strength < 50) return { label: 'Lemah', color: 'bg-orange-500' };
  if (strength < 75) return { label: 'Sedang', color: 'bg-yellow-500' };
  if (strength < 100) return { label: 'Kuat', color: 'bg-green-500' };
  return { label: 'Sangat Kuat', color: 'bg-green-600' };
}

export function PasswordInput({
  name,
  label,
  required = false,
  disabled = false,
  placeholder = 'Masukkan password',
  showStrengthMeter = false,
  showRequirements = false,
  requirements = defaultRequirements,
  description,
  autoFocus = false,
}: PasswordInputProps) {
  const {
    control,
    formState: { errors },
  } = useFormContext();

  const [showPassword, setShowPassword] = useState(false);
  const error = errors[name];

  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => {
        const value = field.value || '';
        const strength = calculateStrength(value, requirements);
        const { label: strengthLabel, color: strengthColor } = getStrengthLabel(strength);

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

            <div className="relative">
              <input
                {...field}
                id={name}
                type={showPassword ? 'text' : 'password'}
                value={value}
                placeholder={placeholder}
                disabled={disabled}
                autoFocus={autoFocus}
                className={cn(
                  'w-full px-3 py-2 pr-10',
                  'border rounded-lg',
                  'bg-white dark:bg-gray-700',
                  'text-gray-900 dark:text-white',
                  'placeholder:text-gray-400 dark:placeholder:text-gray-500',
                  'focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'transition-all duration-150',
                  error
                    ? 'border-red-500 dark:border-red-400'
                    : 'border-gray-300 dark:border-gray-600'
                )}
                aria-invalid={!!error}
                aria-describedby={
                  error ? `${name}-error` : description ? `${name}-desc` : undefined
                }
              />

              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                disabled={disabled}
                className={cn(
                  'absolute right-2 top-1/2 -translate-y-1/2',
                  'p-1 rounded',
                  'text-gray-500 dark:text-gray-400',
                  'hover:text-gray-700 dark:hover:text-gray-200',
                  'hover:bg-gray-100 dark:hover:bg-gray-600',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'transition-colors duration-150'
                )}
                aria-label={showPassword ? 'Sembunyikan password' : 'Tampilkan password'}
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>

            {/* Strength Meter */}
            {showStrengthMeter && value && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500 dark:text-gray-400">Kekuatan Password</span>
                  <span
                    className={cn(
                      'font-medium',
                      strength < 50
                        ? 'text-red-500'
                        : strength < 75
                          ? 'text-yellow-500'
                          : 'text-green-500'
                    )}
                  >
                    {strengthLabel}
                  </span>
                </div>
                <div className="h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                  <div
                    className={cn('h-full transition-all duration-300', strengthColor)}
                    style={{ width: `${strength}%` }}
                  />
                </div>
              </div>
            )}

            {/* Requirements Checklist */}
            {showRequirements && value && (
              <div className="space-y-1 pt-1">
                {requirements.map((req, index) => {
                  const passed = req.test(value);
                  return (
                    <div
                      key={index}
                      className={cn(
                        'flex items-center gap-2 text-xs',
                        passed
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-gray-500 dark:text-gray-400'
                      )}
                    >
                      {passed ? (
                        <Check className="w-3.5 h-3.5" />
                      ) : (
                        <X className="w-3.5 h-3.5" />
                      )}
                      <span>{req.label}</span>
                    </div>
                  );
                })}
              </div>
            )}

            {description && !error && !showRequirements && (
              <p id={`${name}-desc`} className="text-xs text-gray-500 dark:text-gray-400">
                {description}
              </p>
            )}

            {error && (
              <p id={`${name}-error`} className="text-xs text-red-500 dark:text-red-400" role="alert">
                {error.message as string}
              </p>
            )}
          </div>
        );
      }}
    />
  );
}

PasswordInput.displayName = 'PasswordInput';
