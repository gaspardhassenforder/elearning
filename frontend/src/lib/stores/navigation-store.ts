/**
 * Navigation Assistant Store (Story 6.1)
 *
 * Manages state for the platform-wide navigation assistant overlay.
 * State includes overlay visibility, loading state.
 * Message history is loaded from backend via useNavigationHistory hook (not persisted in Zustand).
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface NavigationState {
  isOpen: boolean;
  isLoading: boolean;

  // Actions
  openNavigator: () => void;
  closeNavigator: () => void;
  setLoading: (loading: boolean) => void;
}

export const useNavigationStore = create<NavigationState>()(
  persist(
    (set) => ({
      // State
      isOpen: false,
      isLoading: false,

      // Actions
      openNavigator: () => {
        set({ isOpen: true });
      },

      closeNavigator: () => {
        set({ isOpen: false });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
    }),
    {
      name: 'navigation-storage',
      // Only persist isOpen state (not loading or messages)
      partialize: (state) => ({
        isOpen: state.isOpen,
      }),
    }
  )
);
