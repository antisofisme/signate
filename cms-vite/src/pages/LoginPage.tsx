/**
 * Login Page
 *
 * LAYER 1: PRESENTATION
 */

import { useState } from 'react';
import { Monitor } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useLogin } from '@/features/auth/hooks/useAuth';
import type { LoginRequest } from '@/features/auth/types/auth';
import { ThemeSwitcher, LanguageSwitcher } from '@/shared/components';

export default function LoginPage() {
  const { t } = useTranslation();
  const [credentials, setCredentials] = useState<LoginRequest>({
    username: '',
    password: '',
  });

  const loginMutation = useLogin();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    loginMutation.mutate(credentials);
  };

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

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Error Message */}
          {loginMutation.isError && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
              {loginMutation.error instanceof Error
                ? loginMutation.error.message
                : t('auth.loginError')}
            </div>
          )}

          {/* Username Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('auth.username')}
            </label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) =>
                setCredentials({ ...credentials, username: e.target.value })
              }
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              placeholder="Enter username"
              required
              disabled={loginMutation.isPending}
            />
          </div>

          {/* Password Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('auth.password')}
            </label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) =>
                setCredentials({ ...credentials, password: e.target.value })
              }
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              placeholder={t('auth.password')}
              required
              disabled={loginMutation.isPending}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loginMutation.isPending}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loginMutation.isPending ? t('common.loading') : t('auth.login')}
          </button>
        </form>

        {/* Default Credentials Hint */}
        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-6">
          Default: admin / admin123
        </p>
      </div>
    </div>
  );
}
