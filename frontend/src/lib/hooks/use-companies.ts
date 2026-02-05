import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { companiesApi } from '@/lib/api/companies'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { useToast } from '@/lib/hooks/use-toast'
import { useTranslation } from '@/lib/hooks/use-translation'
import { getApiErrorKey } from '@/lib/utils/error-handler'
import { CreateCompanyRequest, UpdateCompanyRequest } from '@/lib/types/api'

export function useCompanies() {
  return useQuery({
    queryKey: QUERY_KEYS.companies,
    queryFn: () => companiesApi.list(),
  })
}

export function useCompany(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.company(id),
    queryFn: () => companiesApi.get(id),
    enabled: !!id,
  })
}

export function useCreateCompany() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (data: CreateCompanyRequest) => companiesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.companies })
      toast({
        title: t.common.success,
        description: t.companies.companyCreated,
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

export function useUpdateCompany() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateCompanyRequest }) =>
      companiesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.companies })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.company(id) })
      toast({
        title: t.common.success,
        description: t.companies.companyUpdated,
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

export function useDeleteCompany() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { t } = useTranslation()

  return useMutation({
    mutationFn: (id: string) => companiesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.companies })
      toast({
        title: t.common.success,
        description: t.companies.companyDeleted,
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
