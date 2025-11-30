/**
 * Authentication Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for authentication
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/authApi';
import { useAuthStore } from '@/lib/stores/authStore';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from 'sonner';
import { logger } from '@/shared/utils/logger';
import { getDeviceInfo } from '@/shared/utils/networkUtils';
import type {
  LoginRequest,
  RegisterRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
} from '../types/auth';

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
 * Automatically includes device info (platform, user_agent, local_ip)
 */
export function useLogin() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      // Get device info including local IP
      const deviceInfo = await getDeviceInfo();

      // Merge with credentials
      const loginData: LoginRequest = {
        ...credentials,
        device_info: deviceInfo,
      };

      return authApi.login(loginData);
    },
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
 * Select organization (LEGACY - navigates to dashboard)
 * Use useSwitchOrganization for in-place switching
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
 * Switch organization (ENHANCED - no navigation)
 * Switches organization in-place with automatic cache invalidation
 * Use this for the OrganizationSwitcher component
 */
export function useSwitchOrganization() {
  const { switchOrganization } = useAuthStore();

  return (orgId: number) => {
    switchOrganization(orgId, true);
  };
}

/**
 * Get all user organizations
 */
export function useOrganizations() {
  const { organizations } = useAuthStore();
  return organizations;
}

/**
 * Get user preferences
 */
export function useUserPreferences() {
  const { preferences, updatePreferences } = useAuthStore();

  return {
    preferences,
    updatePreferences,
  };
}

/**
 * Check if user can auto-select organization
 */
export function useCanAutoSelectOrg() {
  const { canAutoSelectOrg } = useAuthStore();
  return canAutoSelectOrg();
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

      // In development, indicate token is available without logging it
      if (data.reset_token && import.meta.env.DEV) {
        logger.debug('Reset token received');
        toast.info('Reset token has been generated (dev mode)');
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
