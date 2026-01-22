import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { artifactsApi, ArtifactResponse } from '@/lib/api/artifacts'
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
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
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
      // Invalidate all artifacts queries
      queryClient.invalidateQueries({ queryKey: ['artifacts'] })
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
