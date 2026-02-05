/**
 * Story 4.1: Learner Store
 *
 * Zustand store for learner UI state (NOT server data).
 * Handles:
 * - Panel sizes and collapsed state
 * - Scroll positions
 * - UI preferences
 *
 * Note: Server data (modules, chat messages) uses TanStack Query, not Zustand.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface PanelSizes {
  [notebookId: string]: number[] // Panel sizes for each notebook
}

interface LearnerState {
  // Panel sizes per notebook
  panelSizes: PanelSizes

  // Actions
  setPanelSizes: (notebookId: string, sizes: number[]) => void
  getPanelSizes: (notebookId: string) => number[] | undefined
  resetPanelSizes: (notebookId: string) => void
}

export const useLearnerStore = create<LearnerState>()(
  persist(
    (set, get) => ({
      panelSizes: {},

      setPanelSizes: (notebookId, sizes) =>
        set((state) => ({
          panelSizes: {
            ...state.panelSizes,
            [notebookId]: sizes,
          },
        })),

      getPanelSizes: (notebookId) => {
        return get().panelSizes[notebookId]
      },

      resetPanelSizes: (notebookId) =>
        set((state) => {
          const { [notebookId]: _, ...rest } = state.panelSizes
          return { panelSizes: rest }
        }),
    }),
    {
      name: 'learner-ui-storage',
      // Only persist UI preferences, not server data
      partialize: (state) => ({ panelSizes: state.panelSizes }),
    }
  )
)
