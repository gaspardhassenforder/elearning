import { apiClient } from './client'

export interface LeaderboardEntry {
  rank: number
  username: string
  points: number
}

export const leaderboardApi = {
  get: () => apiClient.get<LeaderboardEntry[]>('/leaderboard').then(r => r.data),
}
