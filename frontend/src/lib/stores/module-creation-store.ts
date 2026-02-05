/**
 * Module Creation Pipeline State Store (Story 3.1, Task 6)
 *
 * Zustand store for managing UI state during module creation pipeline.
 * Tracks active step: create → upload → generate → configure → publish
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
   * Set the active pipeline step
   */
  setActiveStep: (step: PipelineStep) => void;

  /**
   * Reset pipeline to initial state
   */
  reset: () => void;
}

const initialState = {
  activeStep: 'upload' as PipelineStep, // Start at upload since create is already done
};

export const useModuleCreationStore = create<ModuleCreationState>()(
  persist(
    (set) => ({
      ...initialState,

      setActiveStep: (step) => set({ activeStep: step }),

      reset: () => set(initialState),
    }),
    {
      name: 'module-creation-storage',
      // Only persist activeStep (UI state only)
      partialize: (state) => ({ activeStep: state.activeStep }),
    }
  )
);
