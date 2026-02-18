/**
 * Story 4.7: Commands API Client
 *
 * API functions for async job status tracking via surreal-commands.
 * Used to poll status of long-running tasks (podcast generation, quiz generation).
 */

import { apiClient } from './client'
import type { CommandJobStatusResponse } from '@/lib/types/api'

/**
 * Get status of a command job
 *
 * Polls the surreal-commands system to check job status.
 * Returns: pending, processing, completed, or error
 *
 * @param jobId - Command job ID (with or without "command:" prefix)
 */
export async function getJobStatus(jobId: string): Promise<CommandJobStatusResponse> {
  // Strip "command:" prefix if present (backend handles both formats)
  const cleanJobId = jobId.startsWith('command:') ? jobId.substring(8) : jobId

  const response = await apiClient.get<CommandJobStatusResponse>(
    `/commands/jobs/${cleanJobId}`
  )
  return response.data
}

/**
 * Cancel a running command job
 *
 * @param jobId - Command job ID
 */
export async function cancelJob(jobId: string): Promise<{ job_id: string; cancelled: boolean }> {
  const cleanJobId = jobId.startsWith('command:') ? jobId.substring(8) : jobId

  const response = await apiClient.delete<{ job_id: string; cancelled: boolean }>(
    `/commands/jobs/${cleanJobId}`
  )
  return response.data
}
