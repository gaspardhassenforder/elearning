/**
 * Story 4.7: Job Status Hook
 *
 * TanStack Query hook for polling async job status (e.g., podcast/quiz generation).
 * Automatically polls every 2 seconds until job completes or errors.
 * Invalidates artifacts query on completion to trigger UI refresh.
 *
 * Usage:
 * ```tsx
 * const { status, progress, error, isPolling } = useJobStatus(jobId, {
 *   onComplete: () => toast.success('Artifact ready!'),
 *   onError: (error) => toast.error(`Failed: ${error}`),
 * })
 * ```
 */

import { useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getJobStatus } from '@/lib/api/commands'
import { QUERY_KEYS } from '@/lib/api/query-client'
import type { CommandJobStatusResponse } from '@/lib/types/api'

interface UseJobStatusOptions {
  /** Notebook ID to invalidate artifacts query on completion */
  notebookId?: string
  /** Callback when job completes successfully */
  onComplete?: (result: any) => void
  /** Callback when job fails */
  onError?: (error: string) => void
  /** Poll interval in milliseconds (default: 2000) */
  pollInterval?: number
}

/**
 * Query key factory for job status
 */
export const jobStatusKeys = {
  all: ['commands', 'jobs'] as const,
  job: (jobId: string) => [...jobStatusKeys.all, jobId] as const,
}

/**
 * Hook: Poll job status until completion or error
 *
 * Features:
 * - Auto-polls every 2 seconds (configurable)
 * - Stops polling when status is "completed" or "error"
 * - Invalidates artifacts query on completion
 * - Calls onComplete/onError callbacks
 * - Retries failed network requests up to 3 times with exponential backoff
 */
export function useJobStatus(
  jobId: string | null,
  options: UseJobStatusOptions = {}
) {
  const {
    notebookId,
    onComplete,
    onError,
    pollInterval = 2000, // 2 seconds default
  } = options

  const queryClient = useQueryClient()

  // Store callbacks in refs to decouple effect deps from callback identity.
  // This prevents the effect from re-running every render when callers pass
  // inline arrow functions (standard "latest callback ref" pattern).
  const onCompleteRef = useRef(onComplete)
  const onErrorRef = useRef(onError)
  useEffect(() => { onCompleteRef.current = onComplete }, [onComplete])
  useEffect(() => { onErrorRef.current = onError }, [onError])

  const query = useQuery<CommandJobStatusResponse>({
    queryKey: jobStatusKeys.job(jobId || ''),
    queryFn: async () => {
      if (!jobId) {
        throw new Error('Job ID is required')
      }
      return await getJobStatus(jobId)
    },
    enabled: !!jobId, // Only run if jobId exists
    refetchInterval: (query) => {
      // TanStack Query v5: callback receives the Query object, not data directly
      const data = query.state.data
      if (!data?.status) return pollInterval // Keep polling until data arrives
      // Accept both normalized (completed/error) and raw surreal-commands values (failed/canceled)
      const terminalStatuses = ['completed', 'error', 'failed', 'canceled']
      const isTerminal = terminalStatuses.includes(data.status)
      return isTerminal ? false : pollInterval
    },
    refetchIntervalInBackground: true, // Keep polling even when tab is backgrounded
    staleTime: 0, // Always refetch to get latest status
    gcTime: 300000, // Keep in cache for 5 minutes after unmount
    retry: 3, // Stop after 3 failed network requests instead of polling forever
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10000),
  })

  // Handle completion and error callbacks
  const data = query.data
  const prevStatusRef = useRef<string | null>(null)

  useEffect(() => {
    if (!data || !data.status) return

    const currentStatus = data.status
    const prevStatus = prevStatusRef.current

    // Detect status transition to completed
    if (currentStatus === 'completed' && prevStatus !== 'completed') {
      // Invalidate artifacts queries so admin and learner lists refetch (e.g. podcast ready)
      if (notebookId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.artifacts(notebookId) })
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.learnerArtifacts(notebookId) })
      }

      // Call onComplete callback via ref
      onCompleteRef.current?.(data.result)
    }

    // Detect status transition to error (accept both normalized and raw values)
    const errorStatuses = ['error', 'failed', 'canceled']
    if (errorStatuses.includes(currentStatus) && !errorStatuses.includes(prevStatus || '')) {
      // Call onError callback via ref
      onErrorRef.current?.(data.error_message || 'Unknown error')
    }

    prevStatusRef.current = currentStatus
  }, [data, notebookId, queryClient])

  return {
    /** Job status: "pending" | "processing" | "completed" | "error" */
    status: data?.status,
    /** Progress data (if job reports progress) */
    progress: data?.progress,
    /** Job result (only available when completed) */
    result: data?.result,
    /** Error message (only available when error) */
    error: data?.error_message,
    /** Whether hook is actively polling */
    isPolling:
      query.isRefetching && data?.status !== 'completed' && data?.status !== 'error',
    /** Whether initial query is loading */
    isLoading: query.isLoading,
    /** Raw query data */
    data,
    /** Refetch function (manual refresh) */
    refetch: query.refetch,
  }
}
