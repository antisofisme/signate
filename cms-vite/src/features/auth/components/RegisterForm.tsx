/**
 * Register Form Component
 * Form untuk registrasi user baru dengan React Hook Form + Zod validation
 */

import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { useRegister } from '../hooks/useAuth';
import { PasswordStrengthIndicator } from './PasswordStrengthIndicator';
import { Button, FormInput } from '@/shared/components';

// Validation schema
const registerSchema = z
  .object({
    username: z
      .string()
      .min(1, 'Username harus diisi')
      .min(3, 'Username minimal 3 karakter')
      .max(50, 'Username maksimal 50 karakter')
      .regex(/^[a-zA-Z0-9_-]+$/, 'Username hanya boleh huruf, angka, underscore, dan dash'),
    email: z
      .string()
      .min(1, 'Email harus diisi')
      .email('Format email tidak valid')
      .max(100, 'Email maksimal 100 karakter'),
    full_name: z
      .string()
      .min(1, 'Nama lengkap harus diisi')
      .min(3, 'Nama lengkap minimal 3 karakter')
      .max(100, 'Nama lengkap maksimal 100 karakter'),
    password: z
      .string()
      .min(1, 'Password harus diisi')
      .min(8, 'Password minimal 8 karakter')
      .regex(/[A-Z]/, 'Password harus mengandung minimal 1 huruf besar')
      .regex(/[a-z]/, 'Password harus mengandung minimal 1 huruf kecil')
      .regex(/[0-9]/, 'Password harus mengandung minimal 1 angka'),
    confirmPassword: z.string().min(1, 'Konfirmasi password harus diisi'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Password tidak cocok',
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const { t } = useTranslation();
  const { mutate: register, isPending } = useRegister();

  // Form setup with React Hook Form + Zod
  const methods = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: '',
      email: '',
      full_name: '',
      password: '',
      confirmPassword: '',
    },
  });

  // Watch password for strength indicator
  const password = methods.watch('password');

  const handleSubmit = (data: RegisterFormData) => {
    register({
      username: data.username,
      email: data.email,
      full_name: data.full_name,
      password: data.password,
    });
  };

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(handleSubmit)} className="space-y-6">
        {/* Username Field */}
        <FormInput
          name="username"
          label="Username"
          placeholder={t('auth.placeholders.username')}
          disabled={isPending}
          autoComplete="username"
          required
        />

        {/* Email Field */}
        <FormInput
          name="email"
          type="email"
          label="Email"
          placeholder={t('auth.placeholders.email')}
          disabled={isPending}
          autoComplete="email"
          required
        />

        {/* Full Name Field */}
        <FormInput
          name="full_name"
          label={t('auth.labels.fullName', 'Nama Lengkap')}
          placeholder={t('auth.placeholders.fullName')}
          disabled={isPending}
          autoComplete="name"
          required
        />

        {/* Password Field */}
        <div className="space-y-2">
          <FormInput
            name="password"
            type="password"
            label="Password"
            placeholder={t('auth.placeholders.password')}
            disabled={isPending}
            autoComplete="new-password"
            required
          />
          {/* Password Strength Indicator */}
          <PasswordStrengthIndicator password={password} showRequirements={true} />
        </div>

        {/* Confirm Password Field */}
        <FormInput
          name="confirmPassword"
          type="password"
          label={t('auth.labels.confirmPassword', 'Konfirmasi Password')}
          placeholder={t('auth.placeholders.confirmPassword')}
          disabled={isPending}
          autoComplete="new-password"
          required
        />

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          fullWidth
          disabled={isPending}
          loading={isPending}
        >
          {isPending ? t('auth.registering', 'Loading...') : t('auth.register', 'Daftar')}
        </Button>
      </form>
    </FormProvider>
  );
}
