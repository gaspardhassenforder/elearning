/**
 * Story 4.1: Learner Store
 * Story 4.3: Document Snippet Scroll State
 * Story 4.7: Async Job Tracking
 *
 * Zustand store for learner UI state (NOT server data).
 * Handles:
 * - Panel sizes and collapsed state
 * - Scroll positions
 * - UI preferences
 * - Sources panel expansion and scroll targets (Story 4.3)
 * - Active async job tracking (Story 4.7)
 *
 * Note: Server data (modules, chat messages) uses TanStack Query, not Zustand.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface PanelSizes {
  [notebookId: string]: number[] // Panel sizes for each notebook
}

// Story 4.7: Active async job state
interface ActiveJob {
  jobId: string
  artifactType: 'podcast' | 'quiz' | string
  notebookId: string
}

interface LearnerState {
  // Panel sizes per notebook
  panelSizes: PanelSizes

  // Story 4.3: Sources panel expansion and scroll state
  sourcesPanelExpanded: boolean
  scrollToSourceId: string | null
  panelManuallyCollapsed: boolean // Track if user manually collapsed panel

  // Story 4.7: Active async job tracking
  activeJob: ActiveJob | null

  // Actions
  setPanelSizes: (notebookId: string, sizes: number[]) => void
  getPanelSizes: (notebookId: string) => number[] | undefined
  resetPanelSizes: (notebookId: string) => void

  // Story 4.3: Sources panel actions
  setSourcesPanelExpanded: (expanded: boolean) => void
  setScrollToSourceId: (id: string | null) => void
  setPanelManuallyCollapsed: (manual: boolean) => void
  expandAndScrollToSource: (sourceId: string) => void

  // Story 4.7: Async job actions
  setActiveJob: (job: ActiveJob | null) => void
  clearActiveJob: () => void
}

export const useLearnerStore = create<LearnerState>()(
  persist(
    (set, get) => ({
      panelSizes: {},
      // Story 4.3: Default panel state
      sourcesPanelExpanded: true,
      scrollToSourceId: null,
      panelManuallyCollapsed: false,
      // Story 4.7: No active job by default
      activeJob: null,

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

      // Story 4.3: Sources panel actions
      setSourcesPanelExpanded: (expanded) =>
        set({ sourcesPanelExpanded: expanded }),

      setScrollToSourceId: (id) =>
        set({ scrollToSourceId: id }),

      setPanelManuallyCollapsed: (manual) =>
        set({ panelManuallyCollapsed: manual }),

      expandAndScrollToSource: (sourceId) => {
        const state = get()

        // If panel collapsed, expand it first
        if (!state.sourcesPanelExpanded) {
          set({ sourcesPanelExpanded: true })
        }

        // Set scroll target
        set({ scrollToSourceId: sourceId })
      },

      // Story 4.7: Async job actions
      setActiveJob: (job) => set({ activeJob: job }),
      clearActiveJob: () => set({ activeJob: null }),
    }),
    {
      name: 'learner-ui-storage',
      // Only persist UI preferences, not server data
      // Story 4.3: Persist panel state
      // Story 4.7: Don't persist activeJob (transient state)
      partialize: (state) => ({
        panelSizes: state.panelSizes,
        sourcesPanelExpanded: state.sourcesPanelExpanded,
        panelManuallyCollapsed: state.panelManuallyCollapsed,
        // activeJob NOT persisted (transient)
      }),
    }
  )
)
