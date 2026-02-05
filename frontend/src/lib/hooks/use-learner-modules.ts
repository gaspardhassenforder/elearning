import { useQuery } from '@tanstack/react-query'
import { learnerModulesApi } from '@/lib/api/learner-modules'
import { QUERY_KEYS } from '@/lib/api/query-client'

/**
 * Get all modules visible to the authenticated learner
 * (assigned to learner's company, unlocked only)
 */
export function useLearnerModules() {
  return useQuery({
    queryKey: QUERY_KEYS.learnerModules,
    queryFn: () => learnerModulesApi.list(),
  })
}

/**
 * Validate learner access to a specific module
 * (for direct URL navigation protection)
 */
export function useLearnerModule(notebookId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.learnerModule(notebookId),
    queryFn: () => learnerModulesApi.get(notebookId),
    enabled: !!notebookId,
    // Retry false for 403 errors (access denied should not retry)
    retry: false,
  })
}
