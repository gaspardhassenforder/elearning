/**
 * Learner Store (Redesign)
 *
 * Simplified Zustand store for ChatGPT-like learner interface.
 * Handles:
 * - Sidebar visibility (mobile toggle)
 * - Resource viewer sheet state
 * - Active async job tracking
 * - Scroll-to-source (repurposed to open sheet)
 *
 * Note: Server data (modules, chat messages) uses TanStack Query, not Zustand.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Active async job state
interface ActiveJob {
  jobId: string
  artifactType: 'podcast' | 'quiz' | string
  notebookId: string
}

// Sheet viewer state for resource/artifact viewing
interface ViewerSheet {
  type: 'source' | 'artifact'
  id: string
  searchText?: string  // Excerpt text for PDF search / text highlight
  pageNumber?: number  // PDF page number for navigation (1-indexed)
}

// Current module context (for unified header)
interface CurrentModule {
  id: string
  name: string
}

interface LearnerState {
  // Sidebar state (for mobile toggle)
  sidebarOpen: boolean

  // Resource viewer sheet
  viewerSheet: ViewerSheet | null

  // Scroll-to-source: opens sheet for that source
  scrollToSourceId: string | null

  // Active async job tracking
  activeJob: ActiveJob | null

  // Current module (for header display)
  currentModule: CurrentModule | null

  // Actions
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  openViewerSheet: (sheet: ViewerSheet) => void
  closeViewerSheet: () => void
  setScrollToSourceId: (id: string | null) => void
  setActiveJob: (job: ActiveJob | null) => void
  clearActiveJob: () => void
  setCurrentModule: (module: CurrentModule | null) => void
}

export const useLearnerStore = create<LearnerState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      viewerSheet: null,
      scrollToSourceId: null,
      activeJob: null,
      currentModule: null,

      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      openViewerSheet: (sheet) => set({ viewerSheet: sheet }),
      closeViewerSheet: () => set({ viewerSheet: null }),

      setScrollToSourceId: (id) => {
        if (id) {
          // Opening a source via scroll target opens the sheet
          set({ viewerSheet: { type: 'source', id }, scrollToSourceId: null })
        } else {
          set({ scrollToSourceId: null })
        }
      },

      setActiveJob: (job) => set({ activeJob: job }),
      clearActiveJob: () => set({ activeJob: null }),
      setCurrentModule: (module) => set({ currentModule: module }),
    }),
    {
      name: 'learner-ui-storage',
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        // activeJob and viewerSheet NOT persisted (transient)
      }),
    }
  )
)
