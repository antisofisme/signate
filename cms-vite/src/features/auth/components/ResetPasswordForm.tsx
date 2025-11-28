/**
 * Reset Password Form Component
 * Form untuk reset password dengan token menggunakan React Hook Form + Zod validation
 */

import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useResetPassword } from '../hooks/useAuth';
import { Button, FormInput } from '@/shared/components';

// Validation schema
const resetPasswordSchema = z
  .object({
    token: z.string().min(1, 'Token harus diisi'),
    newPassword: z
      .string()
      .min(1, 'Password baru harus diisi')
      .min(6, 'Password minimal 6 karakter'),
    confirmPassword: z.string().min(1, 'Konfirmasi password harus diisi'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Password tidak cocok',
    path: ['confirmPassword'],
  });

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export function ResetPasswordForm() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const tokenFromUrl = searchParams.get('token') || '';

  const { mutate: resetPassword, isPending } = useResetPassword();

  // Form setup with React Hook Form + Zod
  const methods = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      token: tokenFromUrl,
      newPassword: '',
      confirmPassword: '',
    },
  });

  const handleSubmit = (data: ResetPasswordFormData) => {
    resetPassword({
      token: data.token,
      new_password: data.newPassword,
    });
  };

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(handleSubmit)} className="space-y-6">
        {/* Info Message */}
        <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                {t(
                  'auth.messages.resetPasswordInfo',
                  'Masukkan token reset password dan password baru Anda.'
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Token Field */}
        <FormInput
          name="token"
          label={t('auth.labels.resetToken', 'Token Reset')}
          placeholder={t('auth.placeholders.token')}
          disabled={isPending}
          required
        />

        {/* New Password Field */}
        <FormInput
          name="newPassword"
          type="password"
          label={t('auth.labels.newPassword', 'Password Baru')}
          placeholder={t('auth.placeholders.newPassword')}
          disabled={isPending}
          autoComplete="new-password"
          required
        />

        {/* Confirm Password Field */}
        <FormInput
          name="confirmPassword"
          type="password"
          label={t('auth.labels.confirmNewPassword', 'Konfirmasi Password Baru')}
          placeholder={t('auth.placeholders.repeatPassword')}
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
          {isPending
            ? t('auth.resettingPassword', 'Mereset Password...')
            : t('auth.resetPassword', 'Reset Password')}
        </Button>

        {/* Back to Login Link */}
        <div className="text-center">
          <Link
            to="/login"
            className="text-sm font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
          >
            {t('auth.backToLogin', 'Kembali ke Login')}
          </Link>
        </div>
      </form>
    </FormProvider>
  );
}
