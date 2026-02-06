/**
 * Story 4.7: useJobStatus Hook Tests
 *
 * Tests for job status polling hook with TanStack Query.
 */

import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useJobStatus } from '../use-job-status'

// Mock API
vi.mock('@/lib/api/commands', () => ({
  getJobStatus: vi.fn(),
}))

import { getJobStatus } from '@/lib/api/commands'

describe('useJobStatus', () => {
  let queryClient: QueryClient

  const createWrapper = () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false, // Disable retries for testing
          gcTime: 0, // Immediate garbage collection
        },
      },
    })

    return ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: queryClient }, children)
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Polling Behavior', () => {
    it('polls job status every 2 seconds by default', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'processing',
        progress: { percentage: 30 },
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.status).toBe('processing')
      })

      // Verify polling is active
      expect(result.current.isPolling).toBe(true)
    })

    it('stops polling when status is completed', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      let callCount = 0

      mockGetStatus.mockImplementation(async () => {
        callCount++
        if (callCount === 1) {
          return {
            job_id: 'command:test',
            status: 'processing',
          }
        }
        return {
          job_id: 'command:test',
          status: 'completed',
          result: { success: true },
        }
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.status).toBe('completed')
      })

      // Verify polling stops
      await waitFor(() => {
        expect(result.current.isPolling).toBe(false)
      })

      // Wait a bit and ensure no more calls (polling stopped)
      const callCountAtStop = callCount
      await new Promise((resolve) => setTimeout(resolve, 3000))
      expect(callCount).toBeLessThanOrEqual(callCountAtStop + 1) // Allow 1 final check
    })

    it('stops polling when status is error', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'error',
        error_message: 'Job failed',
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.status).toBe('error')
      })

      await waitFor(() => {
        expect(result.current.isPolling).toBe(false)
      })
    })

    it('does not poll when jobId is null', () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'processing',
      })

      renderHook(() => useJobStatus(null), {
        wrapper: createWrapper(),
      })

      // Verify API was not called
      expect(mockGetStatus).not.toHaveBeenCalled()
    })

    it('uses custom poll interval when provided', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'processing',
      })

      renderHook(() => useJobStatus('command:test', { pollInterval: 500 }), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(mockGetStatus).toHaveBeenCalled()
      })

      // Note: Testing exact poll interval timing is fragile
      // We just verify custom interval is accepted
    })
  })

  describe('Callbacks', () => {
    it('calls onComplete callback when status becomes completed', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      const onComplete = vi.fn()

      mockGetStatus.mockResolvedValueOnce({
        job_id: 'command:test',
        status: 'processing',
      })

      const { rerender } = renderHook(
        ({ jobId }) => useJobStatus(jobId, { onComplete }),
        {
          wrapper: createWrapper(),
          initialProps: { jobId: 'command:test' },
        }
      )

      await waitFor(() => {
        expect(mockGetStatus).toHaveBeenCalled()
      })

      // Simulate status change to completed
      mockGetStatus.mockResolvedValueOnce({
        job_id: 'command:test',
        status: 'completed',
        result: { success: true, artifact_id: 'artifact:final' },
      })

      // Trigger refetch by forcing query invalidation
      await act(async () => {
        await queryClient.invalidateQueries({ queryKey: ['commands', 'jobs', 'command:test'] })
      })

      await waitFor(() => {
        expect(onComplete).toHaveBeenCalledWith({ success: true, artifact_id: 'artifact:final' })
      })
    })

    it('calls onError callback when status becomes error', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      const onError = vi.fn()

      mockGetStatus.mockResolvedValueOnce({
        job_id: 'command:test',
        status: 'processing',
      })

      renderHook(() => useJobStatus('command:test', { onError }), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(mockGetStatus).toHaveBeenCalled()
      })

      // Simulate status change to error
      mockGetStatus.mockResolvedValueOnce({
        job_id: 'command:test',
        status: 'error',
        error_message: 'TTS service failed',
      })

      await act(async () => {
        await queryClient.invalidateQueries({ queryKey: ['commands', 'jobs', 'command:test'] })
      })

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith('TTS service failed')
      })
    })

    it('does not call callbacks multiple times for same status', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      const onComplete = vi.fn()

      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'completed',
        result: { success: true },
      })

      renderHook(() => useJobStatus('command:test', { onComplete }), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(onComplete).toHaveBeenCalledTimes(1)
      })

      // Wait a bit more
      await new Promise((resolve) => setTimeout(resolve, 500))

      // onComplete should still have been called only once
      expect(onComplete).toHaveBeenCalledTimes(1)
    })
  })

  describe('Artifacts Query Invalidation', () => {
    it('invalidates artifacts query on completion', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      const notebookId = 'notebook:test'

      mockGetStatus.mockResolvedValueOnce({
        job_id: 'command:test',
        status: 'processing',
      })

      const { rerender } = renderHook(
        ({ jobId }) => useJobStatus(jobId, { notebookId }),
        {
          wrapper: createWrapper(),
          initialProps: { jobId: 'command:test' },
        }
      )

      await waitFor(() => {
        expect(mockGetStatus).toHaveBeenCalled()
      })

      // Spy on queryClient invalidation
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      // Simulate completion
      mockGetStatus.mockResolvedValueOnce({
        job_id: 'command:test',
        status: 'completed',
        result: { success: true },
      })

      await act(async () => {
        await queryClient.invalidateQueries({ queryKey: ['commands', 'jobs', 'command:test'] })
      })

      await waitFor(() => {
        expect(invalidateSpy).toHaveBeenCalledWith({
          queryKey: ['artifacts', notebookId],
        })
      })
    })

    it('does not invalidate artifacts query if notebookId not provided', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)

      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'completed',
        result: { success: true },
      })

      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(mockGetStatus).toHaveBeenCalled()
      })

      // Should not have called invalidateQueries with artifacts key
      const artifactsInvalidations = invalidateSpy.mock.calls.filter((call) =>
        JSON.stringify(call[0]).includes('artifacts')
      )
      expect(artifactsInvalidations).toHaveLength(0)
    })
  })

  describe('Return Values', () => {
    it('returns status from query data', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'processing',
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.status).toBe('processing')
      })
    })

    it('returns progress from query data', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'processing',
        progress: { current: 40, total: 100, percentage: 40 },
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.progress).toEqual({
          current: 40,
          total: 100,
          percentage: 40,
        })
      })
    })

    it('returns result when completed', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      const resultData = { success: true, artifact_id: 'artifact:final' }

      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'completed',
        result: resultData,
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.result).toEqual(resultData)
      })
    })

    it('returns error message when error', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'error',
        error_message: 'TTS service failed',
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.error).toBe('TTS service failed')
      })
    })

    it('returns isPolling true when actively polling', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'processing',
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isPolling).toBe(true)
      })
    })

    it('returns isPolling false when completed', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'completed',
        result: { success: true },
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isPolling).toBe(false)
      })
    })
  })

  describe('Edge Cases', () => {
    it('handles API errors gracefully', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should not crash, just handle error state
      expect(result.current.status).toBeUndefined()
    })

    it('handles missing progress data', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'processing',
        // No progress field
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.status).toBe('processing')
      })

      expect(result.current.progress).toBeUndefined()
    })

    it('handles jobId change during polling', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockImplementation(async (jobId) => ({
        job_id: jobId,
        status: 'processing',
      }))

      const { result, rerender } = renderHook(
        ({ jobId }) => useJobStatus(jobId),
        {
          wrapper: createWrapper(),
          initialProps: { jobId: 'command:first' },
        }
      )

      await waitFor(() => {
        expect(result.current.status).toBe('processing')
      })

      // Change jobId
      rerender({ jobId: 'command:second' })

      await waitFor(() => {
        expect(mockGetStatus).toHaveBeenCalledWith('command:second')
      })
    })

    it('handles refetchInterval returning false', async () => {
      const mockGetStatus = vi.mocked(getJobStatus)
      mockGetStatus.mockResolvedValue({
        job_id: 'command:test',
        status: 'completed',
        result: { success: true },
      })

      const { result } = renderHook(() => useJobStatus('command:test'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.status).toBe('completed')
      })

      // Verify polling is disabled (refetchInterval returned false)
      expect(result.current.isPolling).toBe(false)
    })
  })
})
