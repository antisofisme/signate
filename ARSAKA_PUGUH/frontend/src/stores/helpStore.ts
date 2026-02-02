/**
 * Help Store - Zustand store for in-app help system
 * Manages help sidebar, guided tours, and contextual help state
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface HelpState {
  // Sidebar state
  isOpen: boolean
  currentPage: string
  searchQuery: string

  // Guided tours
  activeTour: string | null
  completedTours: string[]

  // First-time user detection
  hasSeenWelcome: boolean

  // Actions
  setOpen: (open: boolean) => void
  toggleOpen: () => void
  setCurrentPage: (page: string) => void
  setSearchQuery: (query: string) => void
  setActiveTour: (tour: string | null) => void
  markTourComplete: (tour: string) => void
  resetTours: () => void
  markWelcomeSeen: () => void
}

export const useHelpStore = create<HelpState>()(
  persist(
    (set) => ({
      // Initial state
      isOpen: false,
      currentPage: '',
      searchQuery: '',
      activeTour: null,
      completedTours: [],
      hasSeenWelcome: false,

      // Actions
      setOpen: (isOpen) => set({ isOpen }),

      toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),

      setCurrentPage: (currentPage) => set({ currentPage, searchQuery: '' }),

      setSearchQuery: (searchQuery) => set({ searchQuery }),

      setActiveTour: (activeTour) => set({ activeTour }),

      markTourComplete: (tour) =>
        set((state) => ({
          completedTours: state.completedTours.includes(tour)
            ? state.completedTours
            : [...state.completedTours, tour],
          activeTour: null,
        })),

      resetTours: () => set({ completedTours: [], hasSeenWelcome: false }),

      markWelcomeSeen: () => set({ hasSeenWelcome: true }),
    }),
    {
      name: 'puguh-help',
      // Only persist completed tours and welcome flag
      partialize: (state) => ({
        completedTours: state.completedTours,
        hasSeenWelcome: state.hasSeenWelcome,
      }),
    }
  )
)

// Selectors for convenience
export const useIsHelpOpen = () => useHelpStore((state) => state.isOpen)
export const useCurrentHelpPage = () => useHelpStore((state) => state.currentPage)
export const useActiveTour = () => useHelpStore((state) => state.activeTour)
export const useHasCompletedTour = (tourId: string) =>
  useHelpStore((state) => state.completedTours.includes(tourId))
