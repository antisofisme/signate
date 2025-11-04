/**
 * UI Store - Zustand
 *
 * Manages UI state:
 * - Sidebar open/close
 * - Theme (light/dark)
 * - Language (id/en)
 * - Modal state
 *
 * Persisted to localStorage
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Language = 'id' | 'en';
type Theme = 'light' | 'dark';

interface UIStore {
  // State
  sidebarOpen: boolean;
  theme: Theme;
  language: Language;
  currentModal: string | null;
  modalData: any;

  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  setLanguage: (language: Language) => void;
  openModal: (modalId: string, data?: any) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set, get) => ({
      // Initial state
      sidebarOpen: true,
      theme: 'light',
      language: 'id',
      currentModal: null,
      modalData: null,

      // Toggle sidebar
      toggleSidebar: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }));
      },

      // Set sidebar state
      setSidebarOpen: (open) => {
        set({ sidebarOpen: open });
      },

      // Set theme with smooth transition
      setTheme: (theme) => {
        set({ theme });

        // Apply theme with View Transition API if available
        const applyTheme = () => {
          if (theme === 'dark') {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
        };

        // Use View Transition API for smooth animation (if supported)
        if (typeof window !== 'undefined' && 'startViewTransition' in document) {
          (document as any).startViewTransition(applyTheme);
        } else {
          applyTheme();
        }
      },

      // Toggle between light/dark
      toggleTheme: () => {
        const newTheme = get().theme === 'light' ? 'dark' : 'light';
        get().setTheme(newTheme);
      },

      // Set language
      setLanguage: (language) => {
        set({ language });
      },

      // Open modal with optional data
      openModal: (modalId, data = null) => {
        set({ currentModal: modalId, modalData: data });
      },

      // Close modal
      closeModal: () => {
        set({ currentModal: null, modalData: null });
      },
    }),
    {
      name: 'ui-preferences', // localStorage key
      partialize: (state) => ({
        // Only persist these fields
        sidebarOpen: state.sidebarOpen,
        theme: state.theme,
        language: state.language,
      }),
    }
  )
);

// Initialize theme on load
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('ui-preferences');
  if (stored) {
    const { theme } = JSON.parse(stored).state || {};
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    }
  }
}
