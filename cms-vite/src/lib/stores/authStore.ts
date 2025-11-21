/**
 * Auth Store - Zustand
 *
 * Manages authentication state:
 * - User info
 * - JWT token
 * - Organizations
 * - Selected organization
 * - User preferences (organization switching, history)
 *
 * Persisted to localStorage
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Organization, AuthState } from '@/features/auth/types/auth';
import type {
  UserPreferences,
  OrgSwitchEvent,
} from '@/features/auth/types/userPreferences';
import {
  DEFAULT_USER_PREFERENCES,
  addToOrgHistory,
  isValidOrgId,
} from '@/features/auth/types/userPreferences';

interface AuthStore extends AuthState {
  // User preferences
  preferences: UserPreferences;

  // Hydration status
  _hasHydrated: boolean;
  setHasHydrated: (state: boolean) => void;

  // Actions
  setAuth: (user: User, token: string, organizations: Organization[]) => void;
  selectOrganization: (orgId: number) => void;
  switchOrganization: (orgId: number, isUserTriggered?: boolean) => void;
  updateUser: (user: Partial<User>) => void;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  logout: () => void;
  isOrgSelected: () => boolean;
  getOrganizationById: (orgId: number) => Organization | undefined;
  canAutoSelectOrg: () => boolean;
}

// Custom event for organization switch
const ORG_SWITCH_EVENT = 'org-switch';

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      organizations: [],
      selectedOrgId: null,
      isAuthenticated: false,
      isLoading: false,
      preferences: DEFAULT_USER_PREFERENCES,
      _hasHydrated: false,

      // Set hydration status
      setHasHydrated: (state) => {
        set({ _hasHydrated: state });
      },

      // Set auth after login
      setAuth: (user, token, organizations) => {
        const state = get();
        let selectedOrgId: number | null = null;

        // Priority 1: Single org - auto-select
        if (organizations.length === 1) {
          selectedOrgId = organizations[0].id;
        }
        // Priority 2: Remember preference enabled - restore last selected
        else if (
          state.preferences.rememberOrganization &&
          state.preferences.lastSelectedOrgId
        ) {
          const validOrgIds = organizations.map((org) => org.id);
          if (isValidOrgId(state.preferences.lastSelectedOrgId, validOrgIds)) {
            selectedOrgId = state.preferences.lastSelectedOrgId;
          }
        }

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

      // Select organization (for multi-org users) - LEGACY, use switchOrganization instead
      selectOrganization: (orgId) => {
        set({ selectedOrgId: orgId });
        localStorage.setItem('selected-org-id', orgId.toString());

        // Update preferences
        const state = get();
        set({
          preferences: {
            ...state.preferences,
            lastSelectedOrgId: orgId,
            orgSwitchHistory: addToOrgHistory(
              state.preferences.orgSwitchHistory,
              orgId
            ),
            lastSwitchTimestamp: Date.now(),
          },
        });
      },

      // Switch organization - ENHANCED version with events and preferences
      switchOrganization: (orgId, isUserTriggered = true) => {
        const state = get();
        const previousOrgId = state.selectedOrgId;
        const organization = state.organizations.find((org) => org.id === orgId);

        if (!organization) {
          console.error(`[AuthStore] Organization with ID ${orgId} not found`);
          return;
        }

        if (!organization.is_active) {
          console.error(
            `[AuthStore] Cannot switch to inactive organization: ${organization.name}`
          );
          return;
        }

        // Update state
        set({
          selectedOrgId: orgId,
          preferences: {
            ...state.preferences,
            lastSelectedOrgId: orgId,
            orgSwitchHistory: addToOrgHistory(
              state.preferences.orgSwitchHistory,
              orgId
            ),
            lastSwitchTimestamp: Date.now(),
          },
        });

        // Save to localStorage
        localStorage.setItem('selected-org-id', orgId.toString());

        // Emit custom event for cache invalidation
        const event: OrgSwitchEvent = {
          previousOrgId,
          newOrgId: orgId,
          organizationName: organization.name,
          timestamp: Date.now(),
          isUserTriggered,
        };

        window.dispatchEvent(
          new CustomEvent(ORG_SWITCH_EVENT, { detail: event })
        );

        console.log(`[AuthStore] Switched to organization: ${organization.name}`, {
          from: previousOrgId,
          to: orgId,
          isUserTriggered,
        });
      },

      // Update user info
      updateUser: (userData) => {
        const currentUser = get().user;
        if (currentUser) {
          set({ user: { ...currentUser, ...userData } });
        }
      },

      // Update user preferences
      updatePreferences: (newPreferences) => {
        const state = get();
        set({
          preferences: {
            ...state.preferences,
            ...newPreferences,
          },
        });
      },

      // Logout - clear all auth state
      logout: () => {
        set({
          user: null,
          token: null,
          organizations: [],
          selectedOrgId: null,
          isAuthenticated: false,
          preferences: DEFAULT_USER_PREFERENCES, // Reset preferences on logout
        });

        // Clear localStorage
        localStorage.removeItem('auth-token');
        localStorage.removeItem('selected-org-id');
      },

      // Check if organization is selected
      isOrgSelected: () => {
        return get().selectedOrgId !== null;
      },

      // Get organization by ID
      getOrganizationById: (orgId) => {
        return get().organizations.find((org) => org.id === orgId);
      },

      // Check if can auto-select organization
      canAutoSelectOrg: () => {
        const state = get();
        if (!state.preferences.rememberOrganization) return false;
        if (!state.preferences.lastSelectedOrgId) return false;

        const validOrgIds = state.organizations.map((org) => org.id);
        return isValidOrgId(state.preferences.lastSelectedOrgId, validOrgIds);
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
        preferences: state.preferences, // NEW: Persist user preferences
      }),
      onRehydrateStorage: () => (state) => {
        // Called when hydration is complete
        state?.setHasHydrated(true);
      },
    }
  )
);

/**
 * Export the organization switch event name for hooks to listen to
 */
export const ORG_SWITCH_EVENT_NAME = 'org-switch';

/**
 * Helper: Dispatch organization switch event manually (if needed)
 */
export function emitOrgSwitchEvent(event: OrgSwitchEvent): void {
  window.dispatchEvent(
    new CustomEvent(ORG_SWITCH_EVENT_NAME, { detail: event })
  );
}
