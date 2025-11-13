/**
 * Auth Store - Zustand
 *
 * Manages authentication state:
 * - User info
 * - JWT token
 * - Organizations
 * - Selected organization
 *
 * Persisted to localStorage
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Organization, AuthState } from '@/features/auth/types/auth';

interface AuthStore extends AuthState {
  // Hydration status
  _hasHydrated: boolean;
  setHasHydrated: (state: boolean) => void;

  // Actions
  setAuth: (user: User, token: string, organizations: Organization[]) => void;
  selectOrganization: (orgId: number) => void;
  updateUser: (user: Partial<User>) => void;
  logout: () => void;
  isOrgSelected: () => boolean;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      organizations: [],
      selectedOrgId: null,
      isAuthenticated: false,
      _hasHydrated: false,

      // Set hydration status
      setHasHydrated: (state) => {
        set({ _hasHydrated: state });
      },

      // Set auth after login
      setAuth: (user, token, organizations) => {
        // Auto-select org if only one
        const selectedOrgId =
          organizations.length === 1 ? organizations[0].id : null;

        set({
          user,
          token,
          organizations,
          selectedOrgId,
          isAuthenticated: true,
        });

        // Save token to localStorage for API client
        localStorage.setItem('auth-token', token);
        if (selectedOrgId) {
          localStorage.setItem('selected-org-id', selectedOrgId.toString());
        }
      },

      // Select organization (for multi-org users)
      selectOrganization: (orgId) => {
        set({ selectedOrgId: orgId });
        localStorage.setItem('selected-org-id', orgId.toString());
      },

      // Update user info
      updateUser: (userData) => {
        const currentUser = get().user;
        if (currentUser) {
          set({ user: { ...currentUser, ...userData } });
        }
      },

      // Logout - clear all auth state
      logout: () => {
        set({
          user: null,
          token: null,
          organizations: [],
          selectedOrgId: null,
          isAuthenticated: false,
        });

        // Clear localStorage
        localStorage.removeItem('auth-token');
        localStorage.removeItem('selected-org-id');
      },

      // Check if organization is selected
      isOrgSelected: () => {
        return get().selectedOrgId !== null;
      },
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({
        // Only persist these fields
        user: state.user,
        token: state.token,
        organizations: state.organizations,
        selectedOrgId: state.selectedOrgId,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        // Called when hydration is complete
        state?.setHasHydrated(true);
      },
    }
  )
);
