/**
 * Forgot Password Form Component
 * Form untuk request password reset dengan React Hook Form + Zod validation
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useForgotPassword } from '../hooks/useAuth';
import { Button, FormInput } from '@/shared/components';

// Validation schema
const forgotPasswordSchema = z.object({
  email: z
    .string()
    .min(1, 'Email harus diisi')
    .email('Format email tidak valid')
    .max(100, 'Email maksimal 100 karakter'),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export function ForgotPasswordForm() {
  const { t } = useTranslation();
  const [submitted, setSubmitted] = useState(false);

  const { mutate: forgotPassword, isPending } = useForgotPassword();

  // Form setup with React Hook Form + Zod
  const methods = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const handleSubmit = (data: ForgotPasswordFormData) => {
    forgotPassword(
      { email: data.email },
      {
        onSuccess: () => {
          setSubmitted(true);
        },
      }
    );
  };

  // Show success message after submission
  if (submitted) {
    return (
      <div className="space-y-6">
        <div className="rounded-md bg-green-50 dark:bg-green-900/20 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800 dark:text-green-200">
                {t('auth.messages.emailSent', 'Email terkirim!')}
              </h3>
              <div className="mt-2 text-sm text-green-700 dark:text-green-300">
                <p>
                  {t(
                    'auth.messages.resetEmailSentDescription',
                    'Jika akun dengan email tersebut ditemukan, kami telah mengirimkan link reset password ke email Anda. Silakan cek inbox dan folder spam Anda.'
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center">
          <Link
            to="/login"
            className="text-sm font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
          >
            {t('auth.backToLogin', 'Kembali ke Login')}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(handleSubmit)} className="space-y-6">
        {/* Info Message */}
        <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                {t(
                  'auth.messages.forgotPasswordInfo',
                  'Masukkan email Anda dan kami akan mengirimkan link untuk reset password.'
                )}
              </p>
            </div>
          </div>
        </div>

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

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          fullWidth
          disabled={isPending}
          loading={isPending}
        >
          {isPending
            ? t('auth.sending', 'Mengirim...')
            : t('auth.sendResetLink', 'Kirim Link Reset Password')}
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
