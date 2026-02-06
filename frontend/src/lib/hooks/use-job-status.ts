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

import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getJobStatus } from '@/lib/api/commands'
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

  const query = useQuery<CommandJobStatusResponse>({
    queryKey: jobStatusKeys.job(jobId || ''),
    queryFn: async () => {
      if (!jobId) {
        throw new Error('Job ID is required')
      }
      return await getJobStatus(jobId)
    },
    enabled: !!jobId, // Only run if jobId exists
    refetchInterval: (data) => {
      // Stop polling if job is completed or errored
      if (!data || !data.status) return false
      const isTerminal = data.status === 'completed' || data.status === 'error'
      return isTerminal ? false : pollInterval
    },
    refetchIntervalInBackground: true, // Keep polling even when tab is backgrounded
    staleTime: 0, // Always refetch to get latest status
    gcTime: 300000, // Keep in cache for 5 minutes after unmount
  })

  // Handle completion and error callbacks
  const data = query.data
  const prevStatusRef = React.useRef<string | null>(null)

  React.useEffect(() => {
    if (!data || !data.status) return

    const currentStatus = data.status
    const prevStatus = prevStatusRef.current

    // Detect status transition to completed
    if (currentStatus === 'completed' && prevStatus !== 'completed') {
      // Invalidate artifacts query to refetch updated artifact list
      if (notebookId) {
        queryClient.invalidateQueries({
          queryKey: ['artifacts', notebookId],
        })
      }

      // Call onComplete callback
      if (onComplete) {
        onComplete(data.result)
      }
    }

    // Detect status transition to error
    if (currentStatus === 'error' && prevStatus !== 'error') {
      // Call onError callback
      if (onError) {
        onError(data.error_message || 'Unknown error')
      }
    }

    prevStatusRef.current = currentStatus
  }, [data, notebookId, onComplete, onError, queryClient])

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

// Re-export React for the useEffect and useRef hooks
import React from 'react'
