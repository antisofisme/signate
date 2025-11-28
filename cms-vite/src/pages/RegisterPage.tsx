/**
 * Register Page
 *
 * LAYER 1: PRESENTATION
 * Page untuk registrasi user baru
 */

import { Monitor } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { RegisterForm } from '@/features/auth/components/RegisterForm';
import { ThemeSwitcher, LanguageSwitcher } from '@/shared/components';

export default function RegisterPage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-700 dark:from-gray-900 dark:to-gray-800 py-8">
      {/* Theme & Language Switchers - Top Right */}
      <div className="absolute top-4 right-4 flex flex-col items-end gap-2 z-10">
        <LanguageSwitcher />
        <ThemeSwitcher />
      </div>

      <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-2xl w-full max-w-md">
        {/* Logo & Title */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Monitor className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
            {t('app.name')}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Daftar Akun Baru
          </p>
        </div>

        {/* Register Form Component */}
        <RegisterForm />

        {/* Login Link */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Sudah punya akun?{' '}
            <Link
              to="/login"
              className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
            >
              Login disini
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
