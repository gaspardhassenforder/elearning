import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface NotebookColumnsState {
  sourcesCollapsed: boolean
  notesCollapsed: boolean
  artifactsCollapsed: boolean
  chatCollapsed: boolean
  toggleSources: () => void
  toggleNotes: () => void
  toggleArtifacts: () => void
  toggleChat: () => void
  setSources: (collapsed: boolean) => void
  setNotes: (collapsed: boolean) => void
  setArtifacts: (collapsed: boolean) => void
  setChat: (collapsed: boolean) => void
}

export const useNotebookColumnsStore = create<NotebookColumnsState>()(
  persist(
    (set) => ({
      sourcesCollapsed: false,
      notesCollapsed: false,
      artifactsCollapsed: false,
      chatCollapsed: false,
      toggleSources: () => set((state) => ({ sourcesCollapsed: !state.sourcesCollapsed })),
      toggleNotes: () => set((state) => ({ notesCollapsed: !state.notesCollapsed })),
      toggleArtifacts: () => set((state) => ({ artifactsCollapsed: !state.artifactsCollapsed })),
      toggleChat: () => set((state) => ({ chatCollapsed: !state.chatCollapsed })),
      setSources: (collapsed) => set({ sourcesCollapsed: collapsed }),
      setNotes: (collapsed) => set({ notesCollapsed: collapsed }),
      setArtifacts: (collapsed) => set({ artifactsCollapsed: collapsed }),
      setChat: (collapsed) => set({ chatCollapsed: collapsed }),
    }),
    {
      name: 'notebook-columns-storage',
    }
  )
)
