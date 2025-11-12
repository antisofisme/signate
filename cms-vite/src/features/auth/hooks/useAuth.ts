/**
 * Authentication Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for authentication
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi } from '@/features/auth/api/authApi';
import { useAuthStore } from '@/lib/stores/authStore';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/lib/notifications/toast';
import type {
  LoginRequest,
  RegisterRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
} from '@/features/auth/types/auth';

/**
 * Get current user
 */
export function useCurrentUser() {
  const { isAuthenticated } = useAuthStore();

  return useQuery({
    queryKey: ['user', 'me'],
    queryFn: authApi.me,
    enabled: isAuthenticated, // Only fetch if authenticated
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Login mutation
 */
export function useLogin() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: LoginRequest) => authApi.login(credentials),
    onSuccess: (data) => {
      // Save to Zustand store (persisted to localStorage)
      setAuth(data.user, data.token, data.organizations);

      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['user'] });

      // Show success toast
      toast.success(`Selamat datang, ${data.user.full_name || data.user.username}!`);

      // Navigate based on organization count
      if (data.organizations.length === 1) {
        // Single org - go to dashboard
        navigate('/dashboard');
      } else if (data.organizations.length > 1) {
        // Multiple orgs - show selector
        navigate('/select-organization');
      } else {
        // No org - error (shouldn't happen)
        toast.error('User tidak memiliki organisasi');
      }
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Register mutation
 */
export function useRegister() {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (userData: RegisterRequest) => authApi.register(userData),
    onSuccess: () => {
      // Show success toast
      toast.success('Registrasi berhasil! Silakan login.');

      // Redirect to login after successful registration
      navigate('/login');
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Logout mutation
 */
export function useLogout() {
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      // Clear Zustand store & localStorage
      logout();

      // Clear all queries
      queryClient.clear();

      // Show success toast
      toast.success('Anda telah logout');

      // Redirect to login
      navigate('/login');
    },
    onError: () => {
      // Even if API call fails, clear local state
      logout();
      queryClient.clear();
      toast.info('Anda telah logout');
      navigate('/login');
    },
  });
}

/**
 * Check if user is authenticated
 */
export function useIsAuthenticated() {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated;
}

/**
 * Get current organization
 */
export function useCurrentOrganization() {
  const { organizations, selectedOrgId } = useAuthStore();
  return organizations.find((org) => org.id === selectedOrgId);
}

/**
 * Select organization
 */
export function useSelectOrganization() {
  const navigate = useNavigate();
  const { selectOrganization } = useAuthStore();

  return (orgId: number) => {
    selectOrganization(orgId);
    navigate('/dashboard');
  };
}

/**
 * Forgot password mutation
 */
export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: ForgotPasswordRequest) => authApi.forgotPassword(email),
    onSuccess: (data) => {
      // Show success toast
      toast.success(data.message);

      // In development, also log the token for testing
      if (data.reset_token && import.meta.env.DEV) {
        console.log('Reset Token (DEV ONLY):', data.reset_token);
        toast.info('Check console for reset token (dev mode)');
      }
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Reset password mutation
 */
export function useResetPassword() {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (resetData: ResetPasswordRequest) =>
      authApi.resetPassword(resetData),
    onSuccess: (data) => {
      // Show success toast
      toast.success(data.message);

      // Redirect to login
      navigate('/login');
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}
