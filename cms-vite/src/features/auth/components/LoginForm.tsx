/**
 * Login Form Component
 * Form untuk login dengan React Hook Form + Zod validation
 */

import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { useLogin } from '../hooks/useAuth';
import { Button, FormInput } from '@/shared/components';

// Validation schema
const loginSchema = z.object({
  username: z
    .string()
    .min(1, 'Username harus diisi')
    .min(3, 'Username minimal 3 karakter')
    .max(50, 'Username maksimal 50 karakter'),
  password: z
    .string()
    .min(1, 'Password harus diisi')
    .min(3, 'Password minimal 3 karakter'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { t } = useTranslation();
  const { mutate: login, isPending } = useLogin();

  // Form setup with React Hook Form + Zod
  const methods = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  const handleSubmit = (data: LoginFormData) => {
    login({ username: data.username, password: data.password });
  };

  return (
    <FormProvider {...methods}>
      <form
        onSubmit={methods.handleSubmit(handleSubmit)}
        className="space-y-6"
        aria-label={t('auth.loginForm', 'Login form')}
      >
        {/* Username Field */}
        <FormInput
          name="username"
          label="Username"
          placeholder={t('auth.placeholders.username')}
          disabled={isPending}
          autoComplete="username"
          required
        />

        {/* Password Field */}
        <FormInput
          name="password"
          type="password"
          label="Password"
          placeholder={t('auth.placeholders.password')}
          disabled={isPending}
          autoComplete="current-password"
          required
        />

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          fullWidth
          disabled={isPending}
          loading={isPending}
          aria-busy={isPending}
          aria-label={isPending ? t('auth.loggingIn', 'Logging in...') : t('auth.login', 'Login')}
        >
          {isPending ? t('auth.loggingIn', 'Logging in...') : t('auth.login', 'Login')}
        </Button>
      </form>
    </FormProvider>
  );
}
