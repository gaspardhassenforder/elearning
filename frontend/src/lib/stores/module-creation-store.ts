/**
 * Module Creation Pipeline State Store (Story 3.1, Task 6)
 *
 * Zustand store for managing UI state during module creation pipeline.
 * Tracks active step: create → upload → generate → configure → publish
 *
 * Extended in Story 3.6, Task 7 to support edit mode.
 *
 * NOTE: This is UI-ONLY state. Server state (modules, documents) managed by TanStack Query.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type PipelineStep = 'create' | 'upload' | 'generate' | 'configure' | 'publish';

interface ModuleCreationState {
  /**
   * Current active step in the pipeline
   */
  activeStep: PipelineStep;

  /**
   * Whether the pipeline is in edit mode (editing published module)
   * Story 3.6, Task 7
   */
  isEditMode: boolean;

  /**
   * Module ID being edited (null if creating new module)
   * Story 3.6, Task 7
   */
  editingModuleId: string | null;

  /**
   * Set the active pipeline step
   */
  setActiveStep: (step: PipelineStep) => void;

  /**
   * Enter edit mode for a published module
   * Story 3.6, Task 7
   */
  enterEditMode: (moduleId: string) => void;

  /**
   * Exit edit mode (after publish or cancel)
   * Story 3.6, Task 7
   */
  exitEditMode: () => void;

  /**
   * Reset pipeline to initial state
   */
  reset: () => void;
}

const initialState = {
  activeStep: 'upload' as PipelineStep, // Start at upload since create is already done
  isEditMode: false,
  editingModuleId: null,
};

export const useModuleCreationStore = create<ModuleCreationState>()(
  persist(
    (set) => ({
      ...initialState,

      setActiveStep: (step) => set({ activeStep: step }),

      enterEditMode: (moduleId) =>
        set({
          isEditMode: true,
          editingModuleId: moduleId,
          activeStep: 'upload', // Start edit flow at Upload step
        }),

      exitEditMode: () =>
        set({
          isEditMode: false,
          editingModuleId: null,
          activeStep: 'upload',
        }),

      reset: () => set(initialState),
    }),
    {
      name: 'module-creation-storage',
      // Persist all UI state for edit mode continuity
      partialize: (state) => ({
        activeStep: state.activeStep,
        isEditMode: state.isEditMode,
        editingModuleId: state.editingModuleId,
      }),
    }
  )
);
