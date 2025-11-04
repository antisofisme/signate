/**
 * Login Page
 *
 * LAYER 1: PRESENTATION
 * Updated to use LoginForm component with centralized validation
 */

import { Monitor } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { ThemeSwitcher, LanguageSwitcher } from '@/shared/components';

export default function LoginPage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-700 dark:from-gray-900 dark:to-gray-800">
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
            {t('app.welcome')}
          </p>
        </div>

        {/* Login Form Component */}
        <LoginForm />

        {/* Register Link */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Belum punya akun?{' '}
            <Link
              to="/register"
              className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
            >
              Daftar disini
            </Link>
          </p>
        </div>

        {/* Default Credentials Hint */}
        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4">
          Default: admin / admin123
        </p>
      </div>
    </div>
  );
}
