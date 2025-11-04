/**
 * Register Form Component
 * Form untuk registrasi user baru dengan validation
 */

import { useState, FormEvent } from 'react';
import { useRegister } from '@/features/auth/hooks/useAuth';
import { validators } from '@/lib/validation/schemas';

export function RegisterForm() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    confirmPassword: '',
  });

  const [errors, setErrors] = useState<{
    username?: string;
    email?: string;
    full_name?: string;
    password?: string;
    confirmPassword?: string;
  }>({});

  const { mutate: register, isPending } = useRegister();

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
   * Validate full name field
   */
  const validateFullName = (value: string) => {
    if (!validators.required(value)) {
      setErrors((prev) => ({ ...prev, full_name: 'Nama lengkap harus diisi' }));
      return false;
    }
    if (!validators.minLength(value, 3)) {
      setErrors((prev) => ({ ...prev, full_name: 'Nama lengkap minimal 3 karakter' }));
      return false;
    }
    setErrors((prev) => ({ ...prev, full_name: undefined }));
    return true;
  };

  /**
   * Validate password field
   */
  const validatePassword = (value: string) => {
    const result = validators.password(value);
    if (!result.valid) {
      setErrors((prev) => ({ ...prev, password: result.error }));
      return false;
    }
    setErrors((prev) => ({ ...prev, password: undefined }));
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
    if (value !== formData.password) {
      setErrors((prev) => ({ ...prev, confirmPassword: 'Password tidak cocok' }));
      return false;
    }
    setErrors((prev) => ({ ...prev, confirmPassword: undefined }));
    return true;
  };

  /**
   * Handle input change
   */
  const handleChange = (field: keyof typeof formData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));
  };

  /**
   * Handle form submit
   */
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    // Validate all fields
    const isUsernameValid = validateUsername(formData.username);
    const isEmailValid = validateEmail(formData.email);
    const isFullNameValid = validateFullName(formData.full_name);
    const isPasswordValid = validatePassword(formData.password);
    const isConfirmPasswordValid = validateConfirmPassword(formData.confirmPassword);

    if (
      !isUsernameValid ||
      !isEmailValid ||
      !isFullNameValid ||
      !isPasswordValid ||
      !isConfirmPasswordValid
    ) {
      return;
    }

    // Submit registration
    register({
      username: formData.username,
      email: formData.email,
      full_name: formData.full_name,
      password: formData.password,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Username Field */}
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-gray-700">
          Username
        </label>
        <input
          id="username"
          type="text"
          value={formData.username}
          onChange={handleChange('username')}
          onBlur={(e) => validateUsername(e.target.value)}
          disabled={isPending}
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.username
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`}
          placeholder="Masukkan username"
        />
        {errors.username && (
          <p className="mt-1 text-sm text-red-600">{errors.username}</p>
        )}
      </div>

      {/* Email Field */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={formData.email}
          onChange={handleChange('email')}
          onBlur={(e) => validateEmail(e.target.value)}
          disabled={isPending}
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.email
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`}
          placeholder="Masukkan email"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email}</p>
        )}
      </div>

      {/* Full Name Field */}
      <div>
        <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
          Nama Lengkap
        </label>
        <input
          id="full_name"
          type="text"
          value={formData.full_name}
          onChange={handleChange('full_name')}
          onBlur={(e) => validateFullName(e.target.value)}
          disabled={isPending}
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.full_name
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`}
          placeholder="Masukkan nama lengkap"
        />
        {errors.full_name && (
          <p className="mt-1 text-sm text-red-600">{errors.full_name}</p>
        )}
      </div>

      {/* Password Field */}
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={formData.password}
          onChange={handleChange('password')}
          onBlur={(e) => validatePassword(e.target.value)}
          disabled={isPending}
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.password
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`}
          placeholder="Masukkan password"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password}</p>
        )}
      </div>

      {/* Confirm Password Field */}
      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
          Konfirmasi Password
        </label>
        <input
          id="confirmPassword"
          type="password"
          value={formData.confirmPassword}
          onChange={handleChange('confirmPassword')}
          onBlur={(e) => validateConfirmPassword(e.target.value)}
          disabled={isPending}
          className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.confirmPassword
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
          } ${isPending ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`}
          placeholder="Konfirmasi password"
        />
        {errors.confirmPassword && (
          <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={
          isPending ||
          !formData.username ||
          !formData.email ||
          !formData.full_name ||
          !formData.password ||
          !formData.confirmPassword
        }
        className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
          isPending ||
          !formData.username ||
          !formData.email ||
          !formData.full_name ||
          !formData.password ||
          !formData.confirmPassword
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
            Loading...
          </span>
        ) : (
          'Daftar'
        )}
      </button>
    </form>
  );
}
