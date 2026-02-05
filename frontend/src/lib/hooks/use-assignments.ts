import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { assignmentsApi } from '@/lib/api/assignments'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { useToast } from '@/lib/hooks/use-toast'
import { useTranslation } from '@/lib/hooks/use-translation'
import { getApiErrorKey } from '@/lib/utils/error-handler'

export function useAssignments() {
  return useQuery({
    queryKey: QUERY_KEYS.assignments,
    queryFn: () => assignmentsApi.list(),
  })
}

export function useAssignmentMatrix() {
  return useQuery({
    queryKey: QUERY_KEYS.assignmentMatrix,
    queryFn: () => assignmentsApi.getMatrix(),
  })
}

export function useToggleAssignment() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({
      companyId,
      notebookId,
    }: {
      companyId: string
      notebookId: string
    }) => assignmentsApi.toggle(companyId, notebookId),
    onSuccess: (result) => {
      // Invalidate assignment queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.assignments })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.assignmentMatrix })
      // Invalidate companies query to update assignment_count
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.companies })

      if (result.action === 'assigned') {
        toast({
          title: t.common.success,
          description: t.assignments.assignmentCreated,
        })
        // Show warning if module is unpublished
        if (result.warning) {
          toast({
            title: t.common.warning,
            description: t.assignments.unpublishedWarning,
            variant: 'default',
          })
        }
      } else {
        toast({
          title: t.common.success,
          description: t.assignments.assignmentRemoved,
        })
      }
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.common.error)),
        variant: 'destructive',
      })
    },
  })
}

export function useAssignModule() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({
      companyId,
      notebookId,
    }: {
      companyId: string
      notebookId: string
    }) => assignmentsApi.assign(companyId, notebookId),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.assignments })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.assignmentMatrix })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.companies })

      toast({
        title: t.common.success,
        description: t.assignments.assignmentCreated,
      })

      if (result.warning) {
        toast({
          title: t.common.warning,
          description: t.assignments.unpublishedWarning,
          variant: 'default',
        })
      }
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.common.error)),
        variant: 'destructive',
      })
    },
  })
}

export function useUnassignModule() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({
      companyId,
      notebookId,
    }: {
      companyId: string
      notebookId: string
    }) => assignmentsApi.unassign(companyId, notebookId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.assignments })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.assignmentMatrix })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.companies })

      toast({
        title: t.common.success,
        description: t.assignments.assignmentRemoved,
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.common.error)),
        variant: 'destructive',
      })
    },
  })
}

/**
 * Toggle lock status on a module assignment (admin only)
 */
export function useToggleModuleLock() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({
      companyId,
      notebookId,
      isLocked,
    }: {
      companyId: string
      notebookId: string
      isLocked: boolean
    }) => assignmentsApi.toggleLock(companyId, notebookId, isLocked),
    onSuccess: (result) => {
      // Invalidate assignment queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.assignments })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.assignmentMatrix })
      // Also invalidate learner modules (affects learner visibility)
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.learnerModules })

      toast({
        title: t.common.success,
        description: result.is_locked
          ? t.assignments.moduleLocked
          : t.assignments.moduleUnlocked,
      })

      // Show warning if module is unpublished
      if (result.warning) {
        toast({
          title: t.common.warning,
          description: t.assignments.unpublishedWarning,
          variant: 'default',
        })
      }
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.common.error)),
        variant: 'destructive',
      })
    },
  })
}
