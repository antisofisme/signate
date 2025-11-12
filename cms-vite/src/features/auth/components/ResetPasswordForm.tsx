/**
 * Reset Password Form Component
 * Form untuk reset password dengan token
 */

import { useState, FormEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useResetPassword } from '@/features/auth/hooks/useAuth';
import { validators } from '@/lib/validation/schemas';

export function ResetPasswordForm() {
  const [searchParams] = useSearchParams();
  const tokenFromUrl = searchParams.get('token') || '';

  const [token, setToken] = useState(tokenFromUrl);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{
    token?: string;
    newPassword?: string;
    confirmPassword?: string;
  }>({});

  const { mutate: resetPassword, isPending } = useResetPassword();

  /**
   * Validate token field
   */
  const validateToken = (value: string) => {
    if (!validators.required(value)) {
      setErrors((prev) => ({ ...prev, token: 'Token harus diisi' }));
      return false;
    }
    setErrors((prev) => ({ ...prev, token: undefined }));
    return true;
  };

  /**
   * Validate new password field
   */
  const validateNewPassword = (value: string) => {
    if (!validators.required(value)) {
      setErrors((prev) => ({ ...prev, newPassword: 'Password baru harus diisi' }));
      return false;
    }
    if (!validators.minLength(value, 6)) {
      setErrors((prev) => ({
        ...prev,
        newPassword: 'Password minimal 6 karakter',
      }));
      return false;
    }
    setErrors((prev) => ({ ...prev, newPassword: undefined }));
    return true;
  };

  /**
   * Validate confirm password field
   */
  const validateConfirmPassword = (value: string) => {
    if (!validators.required(value)) {
      setErrors((prev) => ({ ...prev, confirmPassword: 'Konfirmasi password harus diisi' }));
      return false;
    }
    if (value !== newPassword) {
      setErrors((prev) => ({ ...prev, confirmPassword: 'Password tidak cocok' }));
      return false;
    }
    setErrors((prev) => ({ ...prev, confirmPassword: undefined }));
    return true;
  };

  /**
   * Handle form submit
   */
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    // Validate all fields
    const isTokenValid = validateToken(token);
    const isNewPasswordValid = validateNewPassword(newPassword);
    const isConfirmPasswordValid = validateConfirmPassword(confirmPassword);

    if (!isTokenValid || !isNewPasswordValid || !isConfirmPasswordValid) {
      return;
    }

    // Submit reset password
    resetPassword({
      token,
      new_password: newPassword,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Info Message */}
      <div className="rounded-md bg-blue-50 p-4">
        <div className="flex">
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              Masukkan token reset password dan password baru Anda.
            </p>
          </div>
        </div>
      </div>

      {/* Token Field */}
      <div>
        <label htmlFor="token" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Token Reset
        </label>
        <input
          id="token"
          type="text"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          onBlur={(e) => validateToken(e.target.value)}
          disabled={isPending}
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.token
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 dark:bg-gray-700 cursor-not-allowed' : 'bg-white dark:bg-gray-800'}`}
          placeholder="Masukkan token dari email"
        />
        {errors.token && <p className="mt-1 text-sm text-red-600">{errors.token}</p>}
      </div>

      {/* New Password Field */}
      <div>
        <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Password Baru
        </label>
        <input
          id="newPassword"
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          onBlur={(e) => validateNewPassword(e.target.value)}
          disabled={isPending}
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.newPassword
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 dark:bg-gray-700 cursor-not-allowed' : 'bg-white dark:bg-gray-800'}`}
          placeholder="Minimal 6 karakter"
        />
        {errors.newPassword && (
          <p className="mt-1 text-sm text-red-600">{errors.newPassword}</p>
        )}
      </div>

      {/* Confirm Password Field */}
      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Konfirmasi Password Baru
        </label>
        <input
          id="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          onBlur={(e) => validateConfirmPassword(e.target.value)}
          disabled={isPending}
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.confirmPassword
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 dark:bg-gray-700 cursor-not-allowed' : 'bg-white dark:bg-gray-800'}`}
          placeholder="Ulangi password baru"
        />
        {errors.confirmPassword && (
          <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isPending || !token || !newPassword || !confirmPassword}
        className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
          isPending || !token || !newPassword || !confirmPassword
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
        }`}
      >
        {isPending ? (
          <span className="flex items-center">
            <svg
              className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Mereset Password...
          </span>
        ) : (
          'Reset Password'
        )}
      </button>

      {/* Back to Login Link */}
      <div className="text-center">
        <Link
          to="/login"
          className="text-sm font-medium text-blue-600 hover:text-blue-500"
        >
          Kembali ke Login
        </Link>
      </div>
    </form>
  );
}
