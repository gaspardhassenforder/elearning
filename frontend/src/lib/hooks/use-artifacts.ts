import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  artifactsApi,
  ArtifactResponse,
  BatchGenerationResponse,
  ArtifactPreview,
  LearnerArtifactListItem,
} from '@/lib/api/artifacts'
import { quizzesApi, QuizGenerateRequest } from '@/lib/api/quizzes'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { useToast } from './use-toast'
import { useTranslation } from './use-translation'
import { getApiErrorKey } from '@/lib/utils/error-handler'

export type { ArtifactResponse as Artifact }

export function useArtifacts(notebookId: string, type?: string) {
  return useQuery<ArtifactResponse[]>({
    queryKey: type 
      ? [...QUERY_KEYS.artifacts(notebookId), type]
      : QUERY_KEYS.artifacts(notebookId),
    queryFn: () => artifactsApi.list(notebookId, type),
    enabled: !!notebookId,
    staleTime: 30 * 1000, // 30 seconds - shorter to catch completed podcasts
    retry: 3,
    // Auto-refresh if there are generating podcasts (artifact_id starts with 'command:')
    refetchInterval: (query) => {
      const data = query.state.data as ArtifactResponse[] | undefined
      if (!data) return false
      const hasGenerating = data.some(
        (a) => a.artifact_type === 'podcast' && a.artifact_id.startsWith('command:')
      )
      return hasGenerating ? 10_000 : false // Poll every 10s if generating
    },
  })
}

export function useGenerateQuiz() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({ notebookId, request }: { notebookId: string; request: QuizGenerateRequest }) =>
      quizzesApi.generate(notebookId, request),
    onSuccess: (data, variables) => {
      // Invalidate artifacts and quizzes queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.artifacts(variables.notebookId) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.quizzes(variables.notebookId) })
      toast({
        title: t.common.success,
        description: t.artifacts?.quizGenerated || 'Quiz generated successfully',
      })
    },
    onError: (error: unknown) => {
      const errorKey = getApiErrorKey(error)
      toast({
        title: t.common.error,
        description: errorKey && t.errors?.[errorKey] ? t.errors[errorKey] : t.common.error,
        variant: 'destructive',
      })
    },
  })
}

export function useDeleteArtifact() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (artifactId: string) => artifactsApi.delete(artifactId),
    onSuccess: () => {
      // Invalidate all artifacts queries (admin and learner)
      queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      queryClient.invalidateQueries({ queryKey: ['learner-artifacts'] })
      toast({
        title: t.common.success,
        description: t.artifacts?.deleteSuccess || 'Artifact deleted successfully',
      })
    },
    onError: (error: unknown) => {
      const errorKey = getApiErrorKey(error)
      toast({
        title: t.common.error,
        description: errorKey && t.errors?.[errorKey] ? t.errors[errorKey] : t.common.error,
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook to generate all artifacts for a notebook (Story 3.2, Task 4)
 */
export function useGenerateAllArtifacts(notebookId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: () => artifactsApi.generateAll(notebookId),
    onSuccess: (data: BatchGenerationResponse) => {
      // Invalidate artifacts queries to pick up new artifacts (admin and learner)
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.artifacts(notebookId) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.learnerArtifacts(notebookId) })

      // Count successful/processing artifacts
      const results = [
        data.quiz.status === 'completed' || data.quiz.status === 'processing',
        data.summary.status === 'completed' || data.summary.status === 'processing',
        data.podcast.status === 'processing',
      ].filter(Boolean).length

      toast({
        title: t.common.success,
        description: t.artifacts?.generateAllSuccess || `Artifact generation started (${results} artifacts)`,
      })
    },
    onError: (error: unknown) => {
      const errorKey = getApiErrorKey(error)
      toast({
        title: t.common.error,
        description: errorKey && t.errors?.[errorKey] ? t.errors[errorKey] : t.common.error,
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook to get artifact preview with type-specific data (Story 3.2, Task 5)
 */
export function useArtifactPreview(artifactId: string | undefined) {
  return useQuery<ArtifactPreview>({
    queryKey: ['artifacts', 'preview', artifactId],
    queryFn: () => artifactsApi.getPreview(artifactId!),
    enabled: !!artifactId,
    staleTime: 60 * 1000, // 1 minute - previews don't change often
    retry: 2,
  })
}

/**
 * Hook to regenerate a single artifact (Story 3.2, Task 5)
 */
export function useRegenerateArtifact() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (artifactId: string) => artifactsApi.regenerate(artifactId),
    onSuccess: (data, artifactId) => {
      // Invalidate the specific artifact preview (admin and learner)
      queryClient.invalidateQueries({ queryKey: ['artifacts', 'preview', artifactId] })
      queryClient.invalidateQueries({ queryKey: ['learner-artifacts', 'preview', artifactId] })

      // Invalidate all artifact lists (admin and learner)
      queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      queryClient.invalidateQueries({ queryKey: ['learner-artifacts'] })

      if (data.status === 'completed') {
        toast({
          title: t.common.success,
          description: t.artifacts?.regenerateSuccess || 'Artifact regenerated successfully',
        })
      } else if (data.status === 'processing') {
        toast({
          title: t.common.success,
          description: t.artifacts?.regenerateStarted || 'Artifact regeneration started',
        })
      } else if (data.status === 'error') {
        toast({
          title: t.common.error,
          description: data.error || 'Regeneration failed',
          variant: 'destructive',
        })
      }
    },
    onError: (error: unknown) => {
      const errorKey = getApiErrorKey(error)
      toast({
        title: t.common.error,
        description: errorKey && t.errors?.[errorKey] ? t.errors[errorKey] : t.common.error,
        variant: 'destructive',
      })
    },
  })
}

// ============================================================================
// Story 5.2: Learner-Scoped Artifact Hooks
// ============================================================================

/**
 * Hook to fetch artifacts for a notebook (learner-scoped).
 *
 * Uses company-scoped validation on backend.
 * Caches results for 5 minutes (staleTime).
 *
 * @param notebookId - Notebook ID to fetch artifacts for
 * @returns TanStack Query result with artifact list
 */
export function useNotebookArtifacts(notebookId: string | null) {
  return useQuery<LearnerArtifactListItem[], Error>({
    queryKey: QUERY_KEYS.learnerArtifacts(notebookId || ''),
    queryFn: () => artifactsApi.listLearner(notebookId!),
    enabled: !!notebookId,
    staleTime: 5 * 60 * 1000, // 5 minutes cache
  })
}

/**
 * Hook to fetch artifact preview (learner-scoped).
 *
 * Lazy-loads preview only when artifactId is provided.
 * Used when user expands an artifact card.
 * Caches results for 10 minutes (artifacts rarely change).
 *
 * @param artifactId - Artifact ID to fetch preview for (null to disable)
 * @returns TanStack Query result with type-specific preview data
 */
export function useLearnerArtifactPreview(artifactId: string | null) {
  return useQuery<ArtifactPreview, Error>({
    queryKey: QUERY_KEYS.learnerArtifactPreview(artifactId || ''),
    queryFn: () => artifactsApi.getLearnerPreview(artifactId!),
    enabled: !!artifactId, // Only fetch when artifactId provided (lazy load)
    staleTime: 10 * 60 * 1000, // 10 minutes cache (artifacts rarely change)
  })
}
