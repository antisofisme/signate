/**
 * Login Form Component
 * Form untuk login dengan validation
 */

import { useState, FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useLogin } from '../hooks/useAuth';
import { validators } from '@/lib/validation/schemas';
import { Button } from '@/shared/components';

export function LoginForm() {
  const { t } = useTranslation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({});

  const { mutate: login, isPending } = useLogin();

  /**
   * Validate username field
   */
  const validateUsername = (value: string) => {
    const result = validators.username(value);
    if (!result.valid) {
      setErrors((prev) => ({ ...prev, username: result.error }));
      return false;
    }
    setErrors((prev) => ({ ...prev, username: undefined }));
    return true;
  };

  /**
   * Validate password field
   */
  const validatePassword = (value: string) => {
    if (!validators.required(value)) {
      setErrors((prev) => ({ ...prev, password: 'Password harus diisi' }));
      return false;
    }
    if (!validators.minLength(value, 3)) {
      setErrors((prev) => ({ ...prev, password: 'Password minimal 3 karakter' }));
      return false;
    }
    setErrors((prev) => ({ ...prev, password: undefined }));
    return true;
  };

  /**
   * Handle form submit
   */
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    // Validate all fields
    const isUsernameValid = validateUsername(username);
    const isPasswordValid = validatePassword(password);

    if (!isUsernameValid || !isPasswordValid) {
      return;
    }

    // Submit login
    login({ username, password });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6" aria-label={t('auth.loginForm', 'Login form')}>
      {/* Username Field */}
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Username
          <span className="text-red-500 ml-1" aria-hidden="true">*</span>
        </label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onBlur={(e) => validateUsername(e.target.value)}
          disabled={isPending}
          aria-required="true"
          aria-invalid={!!errors.username}
          aria-describedby={errors.username ? 'username-error' : undefined}
          autoComplete="username"
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 ${
            errors.username
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 dark:bg-gray-700 cursor-not-allowed' : 'bg-white dark:bg-gray-800'}`}
          placeholder={t('auth.placeholders.username')}
        />
        {errors.username && (
          <p id="username-error" className="mt-1 text-sm text-red-600" role="alert">{errors.username}</p>
        )}
      </div>

      {/* Password Field */}
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Password
          <span className="text-red-500 ml-1" aria-hidden="true">*</span>
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onBlur={(e) => validatePassword(e.target.value)}
          disabled={isPending}
          aria-required="true"
          aria-invalid={!!errors.password}
          aria-describedby={errors.password ? 'password-error' : undefined}
          autoComplete="current-password"
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 ${
            errors.password
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 dark:bg-gray-700 cursor-not-allowed' : 'bg-white dark:bg-gray-800'}`}
          placeholder={t('auth.placeholders.password')}
        />
        {errors.password && (
          <p id="password-error" className="mt-1 text-sm text-red-600" role="alert">{errors.password}</p>
        )}
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        variant="primary"
        fullWidth
        disabled={isPending || !username || !password}
        loading={isPending}
        aria-busy={isPending}
        aria-label={isPending ? t('auth.loggingIn', 'Logging in...') : t('auth.login', 'Login')}
      >
        {isPending ? t('auth.loggingIn', 'Logging in...') : t('auth.login', 'Login')}
      </Button>
    </form>
  );
}
