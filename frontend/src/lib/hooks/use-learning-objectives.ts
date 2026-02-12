/**
 * Learning Objectives Hooks (Story 3.3, Task 5)
 *
 * TanStack Query hooks for managing learning objectives with optimistic updates
 * for drag-and-drop reordering.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import type {
  LearningObjectiveResponse,
  CreateLearningObjectiveRequest,
  UpdateLearningObjectiveRequest,
  ReorderLearningObjectivesRequest,
  LearnerObjectivesProgressResponse,
} from '@/lib/types/api'
import {
  listLearningObjectives,
  generateLearningObjectives,
  createLearningObjective,
  updateLearningObjective,
  deleteLearningObjective,
  reorderLearningObjectives,
  getLearnerObjectivesProgress,
} from '@/lib/api/learning-objectives'
import { QUERY_KEYS } from '@/lib/api/query-client'

/**
 * Query key factory for learning objectives
 * Follows hierarchical pattern: ['modules', id, 'objectives']
 */
export const learningObjectivesKeys = {
  all: ['learning-objectives'] as const,
  lists: () => [...learningObjectivesKeys.all, 'list'] as const,
  list: (notebookId: string) =>
    [...learningObjectivesKeys.lists(), notebookId] as const,
  // Story 4.4: Learner progress keys
  progress: () => [...learningObjectivesKeys.all, 'progress'] as const,
  progressByNotebook: (notebookId: string) =>
    [...learningObjectivesKeys.progress(), notebookId] as const,
}

/**
 * Query hook: List all learning objectives for a notebook
 */
export function useLearningObjectives(notebookId: string) {
  return useQuery({
    queryKey: learningObjectivesKeys.list(notebookId),
    queryFn: () => listLearningObjectives(notebookId),
    enabled: !!notebookId,
  })
}

/**
 * Mutation hook: Auto-generate learning objectives
 * Triggers LangGraph workflow (30-60s execution time)
 */
export function useGenerateLearningObjectives(notebookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => generateLearningObjectives(notebookId),
    onSuccess: (data) => {
      if (data.status === 'completed') {
        toast.success('Learning objectives generated successfully')
        queryClient.invalidateQueries({
          queryKey: learningObjectivesKeys.list(notebookId),
        })
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.notebook(notebookId),
        })
      } else if (data.status === 'error') {
        toast.error(data.error || 'Failed to generate objectives')
      }
    },
    onError: (error: Error) => {
      toast.error(`Generation failed: ${error.message}`)
    },
  })
}

/**
 * Mutation hook: Create manual learning objective
 */
export function useCreateLearningObjective(notebookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateLearningObjectiveRequest) =>
      createLearningObjective(notebookId, data),
    onSuccess: () => {
      toast.success('Objective added')
      queryClient.invalidateQueries({
        queryKey: learningObjectivesKeys.list(notebookId),
      })
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.notebook(notebookId),
      })
    },
    onError: (error: Error) => {
      toast.error(`Failed to add objective: ${error.message}`)
    },
  })
}

/**
 * Mutation hook: Update learning objective text
 */
export function useUpdateLearningObjective(notebookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      objectiveId,
      data,
    }: {
      objectiveId: string
      data: UpdateLearningObjectiveRequest
    }) => updateLearningObjective(notebookId, objectiveId, data),
    onSuccess: () => {
      toast.success('Objective updated')
      queryClient.invalidateQueries({
        queryKey: learningObjectivesKeys.list(notebookId),
      })
    },
    onError: (error: Error) => {
      toast.error(`Failed to update objective: ${error.message}`)
    },
  })
}

/**
 * Mutation hook: Delete learning objective
 */
export function useDeleteLearningObjective(notebookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (objectiveId: string) =>
      deleteLearningObjective(notebookId, objectiveId),
    onSuccess: () => {
      toast.success('Objective deleted')
      queryClient.invalidateQueries({
        queryKey: learningObjectivesKeys.list(notebookId),
      })
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.notebook(notebookId),
      })
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete objective: ${error.message}`)
    },
  })
}

/**
 * Mutation hook: Reorder learning objectives with optimistic updates
 * Provides instant feedback during drag-and-drop, with rollback on error
 */
export function useReorderLearningObjectives(notebookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ReorderLearningObjectivesRequest) =>
      reorderLearningObjectives(notebookId, data),
    // Optimistic update: Apply reordering immediately
    onMutate: async (variables) => {
      // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({
        queryKey: learningObjectivesKeys.list(notebookId),
      })

      // Snapshot the previous value
      const previousObjectives = queryClient.getQueryData<
        LearningObjectiveResponse[]
      >(learningObjectivesKeys.list(notebookId))

      // Optimistically update to the new value
      if (previousObjectives) {
        const orderMap = new Map(
          variables.objectives.map((obj) => [obj.id, obj.order])
        )
        const reordered = [...previousObjectives]
          .map((obj) => ({
            ...obj,
            order: orderMap.get(obj.id) ?? obj.order,
          }))
          .sort((a, b) => a.order - b.order)

        queryClient.setQueryData(
          learningObjectivesKeys.list(notebookId),
          reordered
        )
      }

      // Return a context object with the snapshotted value
      return { previousObjectives }
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (error: Error, _variables, context) => {
      if (context?.previousObjectives) {
        queryClient.setQueryData(
          learningObjectivesKeys.list(notebookId),
          context.previousObjectives
        )
      }
      toast.error(`Failed to reorder: ${error.message}`)
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: learningObjectivesKeys.list(notebookId),
      })
    },
  })
}

/**
 * Query hook: Get learner objectives with progress (Story 4.4)
 * Returns objectives with completion status for authenticated learner
 */
export function useLearnerObjectivesProgress(notebookId: string) {
  return useQuery({
    queryKey: learningObjectivesKeys.progressByNotebook(notebookId),
    queryFn: () => getLearnerObjectivesProgress(notebookId),
    enabled: !!notebookId,
    // Refetch when window regains focus to catch AI-triggered completions
    refetchOnWindowFocus: true,
    // Keep data fresh - objectives might be checked off during conversation
    staleTime: 30 * 1000, // 30 seconds
  })
}
