/**
 * Module Prompts Hooks (Story 3.4, Task 6)
 *
 * TanStack Query hooks for managing per-module AI teacher prompts.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { getModulePrompt, updateModulePrompt } from '@/lib/api/module-prompts'
import type { ModulePromptUpdate } from '@/lib/types/api'

/**
 * Hook to fetch module prompt for a notebook.
 * Returns null if no prompt configured.
 */
export function useModulePrompt(notebookId: string) {
  return useQuery({
    queryKey: ['modules', notebookId, 'prompt'],
    queryFn: () => getModulePrompt(notebookId),
    enabled: !!notebookId,
  })
}

/**
 * Hook to update module prompt for a notebook.
 * Invalidates query cache and shows toast notifications.
 */
export function useUpdateModulePrompt(notebookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ModulePromptUpdate) => updateModulePrompt(notebookId, data),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['modules', notebookId, 'prompt'] })
      toast.success('Module prompt saved successfully')
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error.message || 'Failed to save prompt'
      toast.error(`Error: ${message}`)
    },
  })
}
