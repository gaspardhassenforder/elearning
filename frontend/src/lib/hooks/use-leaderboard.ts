import { useQuery } from '@tanstack/react-query'
import { leaderboardApi } from '@/lib/api/leaderboard'
import { QUERY_KEYS } from '@/lib/api/query-client'

export function useLeaderboard() {
  return useQuery({
    queryKey: QUERY_KEYS.leaderboard,
    queryFn: leaderboardApi.get,
    staleTime: 60_000,
  })
}
