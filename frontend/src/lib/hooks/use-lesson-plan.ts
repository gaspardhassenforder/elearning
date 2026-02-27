/**
 * Lesson Plan Hooks
 *
 * TanStack Query hooks for managing lesson steps with optimistic reorder updates.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  listLessonSteps,
  generateLessonPlan,
  updateLessonStep,
  deleteLessonStep,
  reorderLessonSteps,
  getLessonStepsProgress,
  type LessonStepResponse,
  type LessonStepUpdate,
} from '@/lib/api/lesson-plan'
import { QUERY_KEYS } from '@/lib/api/query-client'

/**
 * Query hook: List all lesson steps for a notebook (admin)
 */
export function useLessonSteps(notebookId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.lessonSteps(notebookId),
    queryFn: () => listLessonSteps(notebookId),
    enabled: !!notebookId,
  })
}

/**
 * Mutation hook: Generate lesson plan via AI
 */
export function useGenerateLessonPlan(notebookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => generateLessonPlan(notebookId),
    onSuccess: (data) => {
      if (data.status === 'completed') {
        toast.success('Lesson plan generated successfully')
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.lessonSteps(notebookId),
        })
      } else {
        toast.error(data.error || 'Failed to generate lesson plan')
      }
    },
    onError: (error: Error) => {
      toast.error(`Generation failed: ${error.message}`)
    },
  })
}

/**
 * Mutation hook: Update a lesson step
 */
export function useUpdateLessonStep(notebookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ stepId, data }: { stepId: string; data: LessonStepUpdate }) =>
      updateLessonStep(stepId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.lessonSteps(notebookId),
      })
    },
    onError: (error: Error) => {
      toast.error(`Failed to update step: ${error.message}`)
    },
  })
}

/**
 * Mutation hook: Delete a lesson step
 */
export function useDeleteLessonStep(notebookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (stepId: string) => deleteLessonStep(stepId),
    onSuccess: () => {
      toast.success('Step deleted')
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.lessonSteps(notebookId),
      })
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete step: ${error.message}`)
    },
  })
}

/**
 * Mutation hook: Reorder lesson steps with optimistic updates
 */
export function useReorderLessonSteps(notebookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (steps: { id: string; order: number }[]) =>
      reorderLessonSteps(notebookId, steps),
    onMutate: async (variables) => {
      await queryClient.cancelQueries({
        queryKey: QUERY_KEYS.lessonSteps(notebookId),
      })

      const previousSteps = queryClient.getQueryData<LessonStepResponse[]>(
        QUERY_KEYS.lessonSteps(notebookId)
      )

      if (previousSteps) {
        const orderMap = new Map(variables.map((s) => [s.id, s.order]))
        const reordered = [...previousSteps]
          .map((step) => ({
            ...step,
            order: orderMap.get(step.id) ?? step.order,
          }))
          .sort((a, b) => a.order - b.order)

        queryClient.setQueryData(QUERY_KEYS.lessonSteps(notebookId), reordered)
      }

      return { previousSteps }
    },
    onError: (error: Error, _variables, context) => {
      if (context?.previousSteps) {
        queryClient.setQueryData(
          QUERY_KEYS.lessonSteps(notebookId),
          context.previousSteps
        )
      }
      toast.error(`Failed to reorder: ${error.message}`)
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.lessonSteps(notebookId),
      })
    },
  })
}

/**
 * Query hook: Get learner step progress for a notebook
 */
export function useLessonStepsProgress(notebookId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.lessonStepsProgress(notebookId),
    queryFn: () => getLessonStepsProgress(notebookId),
    enabled: !!notebookId,
    staleTime: 30 * 1000, // 30 seconds — refresh after step completion
    refetchOnWindowFocus: true,
  })
}
