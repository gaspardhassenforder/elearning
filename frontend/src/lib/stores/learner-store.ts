/**
 * Story 4.1: Learner Store
 * Story 4.3: Document Snippet Scroll State
 * Story 4.7: Async Job Tracking
 * Story 5.1: Document Expansion and Badge Notifications
 *
 * Zustand store for learner UI state (NOT server data).
 * Handles:
 * - Panel sizes and collapsed state
 * - Scroll positions
 * - UI preferences
 * - Sources panel expansion and scroll targets (Story 4.3)
 * - Active async job tracking (Story 4.7)
 * - Document expansion (accordion behavior) and badge notifications (Story 5.1)
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

  // Story 5.1: Document expansion and badge notifications
  expandedSourceId: string | null // Currently expanded document (accordion behavior)
  pendingBadgeCount: number // Badge count when panel is collapsed

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

  // Story 5.1: Document expansion and badge actions
  setExpandedSourceId: (sourceId: string | null) => void
  incrementBadgeCount: () => void
  clearBadgeCount: () => void
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
      // Story 5.1: Document expansion and badge defaults
      expandedSourceId: null,
      pendingBadgeCount: 0,

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

        // If panel collapsed, expand it first and clear badge
        if (!state.sourcesPanelExpanded) {
          set({ sourcesPanelExpanded: true, pendingBadgeCount: 0 })
        }

        // Set scroll target
        set({ scrollToSourceId: sourceId })
      },

      // Story 4.7: Async job actions
      setActiveJob: (job) => set({ activeJob: job }),
      clearActiveJob: () => set({ activeJob: null }),

      // Story 5.1: Document expansion and badge actions
      setExpandedSourceId: (sourceId) => set({ expandedSourceId: sourceId }),
      incrementBadgeCount: () =>
        set((state) => ({ pendingBadgeCount: state.pendingBadgeCount + 1 })),
      clearBadgeCount: () => set({ pendingBadgeCount: 0 }),
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
