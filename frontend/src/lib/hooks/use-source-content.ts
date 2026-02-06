/**
 * Story 5.1: useSourceContent Hook
 *
 * TanStack Query hook for lazy-loading full document content.
 * Only fetches when sourceId is provided (enabled flag pattern).
 * Used by DocumentCard when user expands a document.
 *
 * Features:
 * - Lazy loading: content fetched only when sourceId provided
 * - 5-minute cache: avoids refetch on collapse/expand cycles
 * - Error handling: returns error state for UI display
 */

import { useQuery } from '@tanstack/react-query'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { sourcesApi } from '@/lib/api/sources'

export function useSourceContent(sourceId: string | null) {
  return useQuery({
    queryKey: QUERY_KEYS.sourceContent(sourceId ?? ''),
    queryFn: () => sourcesApi.getContent(sourceId!),
    enabled: !!sourceId, // Only fetch when sourceId provided (lazy load)
    staleTime: 5 * 60 * 1000, // 5 minutes cache
    gcTime: 10 * 60 * 1000, // 10 minutes garbage collection
    retry: 1, // Retry once on failure
  })
}
