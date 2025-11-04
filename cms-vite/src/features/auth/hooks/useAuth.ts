/**
 * Authentication Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for authentication
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi } from '@/features/auth/services/authApi';
import { useAuthStore } from '@/lib/stores/authStore';
import type { LoginRequest, RegisterRequest } from '@/features/auth/types/auth';

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

      // Navigate based on organization count
      if (data.organizations.length === 1) {
        // Single org - go to dashboard
        navigate('/dashboard');
      } else if (data.organizations.length > 1) {
        // Multiple orgs - show selector
        navigate('/select-organization');
      } else {
        // No org - error (shouldn't happen)
        console.error('User has no organizations');
      }
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
      // Redirect to login after successful registration
      navigate('/login');
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

      // Redirect to login
      navigate('/login');
    },
    onError: () => {
      // Even if API call fails, clear local state
      logout();
      queryClient.clear();
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
