/**
 * Forgot Password Form Component
 * Form untuk request password reset
 */

import { useState, FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { useForgotPassword } from '../hooks/useAuth';
import { validators } from '@/lib/validation/schemas';

export function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState<{ email?: string }>({});
  const [submitted, setSubmitted] = useState(false);

  const { mutate: forgotPassword, isPending } = useForgotPassword();

  /**
   * Validate email field
   */
  const validateEmail = (value: string) => {
    const result = validators.email(value);
    if (!result.valid) {
      setErrors((prev) => ({ ...prev, email: result.error }));
      return false;
    }
    setErrors((prev) => ({ ...prev, email: undefined }));
    return true;
  };

  /**
   * Handle form submit
   */
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    // Validate email
    const isEmailValid = validateEmail(email);

    if (!isEmailValid) {
      return;
    }

    // Submit forgot password request
    forgotPassword(
      { email },
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
        <div className="rounded-md bg-green-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Email terkirim!</h3>
              <div className="mt-2 text-sm text-green-700">
                <p>
                  Jika akun dengan email tersebut ditemukan, kami telah mengirimkan link
                  reset password ke email Anda. Silakan cek inbox dan folder spam Anda.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center">
          <Link
            to="/login"
            className="text-sm font-medium text-blue-600 hover:text-blue-500"
          >
            Kembali ke Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Info Message */}
      <div className="rounded-md bg-blue-50 p-4">
        <div className="flex">
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              Masukkan email Anda dan kami akan mengirimkan link untuk reset password.
            </p>
          </div>
        </div>
      </div>

      {/* Email Field */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onBlur={(e) => validateEmail(e.target.value)}
          disabled={isPending}
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.email
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 dark:bg-gray-700 cursor-not-allowed' : 'bg-white dark:bg-gray-800'}`}
          placeholder="nama@contoh.com"
        />
        {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isPending || !email}
        className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
          isPending || !email
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
            Mengirim...
          </span>
        ) : (
          'Kirim Link Reset Password'
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
