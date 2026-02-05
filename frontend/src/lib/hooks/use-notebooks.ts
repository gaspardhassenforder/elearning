import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '@/lib/api/notebooks'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { useToast } from '@/lib/hooks/use-toast'
import { useTranslation } from '@/lib/hooks/use-translation'
import { getApiErrorKey } from '@/lib/utils/error-handler'
import { CreateNotebookRequest, UpdateNotebookRequest } from '@/lib/types/api'

export function useNotebooks(archived?: boolean) {
  return useQuery({
    queryKey: [...QUERY_KEYS.notebooks, { archived }],
    queryFn: () => notebooksApi.list({ archived, order_by: 'updated desc' }),
  })
}

export function useNotebook(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.notebook(id),
    queryFn: () => notebooksApi.get(id),
    enabled: !!id,
  })
}

export function useCreateNotebook() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (data: CreateNotebookRequest) => notebooksApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebooks })
      toast({
        title: t.common.success,
        description: t.notebooks.createSuccess,
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

export function useUpdateNotebook() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateNotebookRequest }) =>
      notebooksApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebooks })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebook(id) })
      toast({
        title: t.common.success,
        description: t.notebooks.updateSuccess,
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

export function useDeleteNotebook() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (id: string) => notebooksApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebooks })
      toast({
        title: t.common.success,
        description: t.notebooks.deleteSuccess,
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

export function usePublishModule(notebookId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: () => notebooksApi.publish(notebookId),
    onSuccess: (data) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebooks })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebook(notebookId) })

      // Optimistically update cached data
      queryClient.setQueryData(QUERY_KEYS.notebook(notebookId), data)

      toast({
        title: t.common.success,
        description: t.modules.publish.success,
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.modules.publish.error)),
        variant: 'destructive',
      })
    },
  })
}

export function useUnpublishModule(notebookId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: () => notebooksApi.unpublish(notebookId),
    onSuccess: (data) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebooks })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebook(notebookId) })

      // Optimistically update cached data
      queryClient.setQueryData(QUERY_KEYS.notebook(notebookId), data)

      toast({
        title: t.common.success,
        description: t.modules.publish.unpublishSuccess,
      })
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: t(getApiErrorKey(error, t.modules.publish.unpublishError)),
        variant: 'destructive',
      })
    },
  })
}