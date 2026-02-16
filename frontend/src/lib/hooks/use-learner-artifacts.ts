import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  learnerArtifactsApi,
  LearnerPodcastRequest,
  LearnerQuizRequest,
  LearnerTransformationRequest,
} from '@/lib/api/learner-artifacts'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { useToast } from './use-toast'
import { useTranslation } from './use-translation'
import { useLearnerStore } from '@/lib/stores/learner-store'
import { getApiErrorKey } from '@/lib/utils/error-handler'

export function useLearnerGeneratePodcast(notebookId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()
  const setActiveJob = useLearnerStore((state) => state.setActiveJob)

  return useMutation({
    mutationFn: (request: LearnerPodcastRequest) =>
      learnerArtifactsApi.generatePodcast(notebookId, request),
    onSuccess: (data) => {
      // Set active job for AsyncStatusBar tracking
      if (data.job_id) {
        setActiveJob({
          jobId: data.job_id,
          artifactType: 'podcast',
          notebookId,
        })
      }
      // Invalidate artifact lists
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.learnerArtifacts(notebookId) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.artifacts(notebookId) })
      toast({
        title: t.common.success,
        description: t.learner?.createArtifact?.podcastStarted || 'Podcast generation started',
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

export function useLearnerGenerateQuiz(notebookId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (request: LearnerQuizRequest) =>
      learnerArtifactsApi.generateQuiz(notebookId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.learnerArtifacts(notebookId) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.artifacts(notebookId) })
      toast({
        title: t.common.success,
        description: t.learner?.createArtifact?.quizGenerated || 'Quiz generated successfully',
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

export function useLearnerExecuteTransformation(notebookId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (request: LearnerTransformationRequest) =>
      learnerArtifactsApi.executeTransformation(notebookId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.learnerArtifacts(notebookId) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.artifacts(notebookId) })
      toast({
        title: t.common.success,
        description: t.learner?.createArtifact?.transformationComplete || 'Transformation complete',
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
