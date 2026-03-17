'use client'

import { useAuthStore } from '@/lib/stores/auth-store'
import { useLeaderboard } from '@/lib/hooks/use-leaderboard'
import { useTranslation } from '@/lib/hooks/use-translation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Trophy } from 'lucide-react'

const RANK_EMOJIS: Record<number, string> = { 1: '🥇', 2: '🥈', 3: '🥉' }

export function Leaderboard() {
  const { user } = useAuthStore()
  const { t } = useTranslation()
  const { data: entries, isLoading } = useLeaderboard()

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Trophy className="h-5 w-5 text-amber-500" />
          {t.gamification.leaderboard}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}
        {!isLoading && (!entries || entries.length === 0) && (
          <p className="text-sm text-muted-foreground text-center py-4">
            {t.gamification.noEntries}
          </p>
        )}
        {!isLoading && entries && entries.length > 0 && (
          <div className="space-y-1">
            {entries.map(entry => {
              const isCurrentUser = entry.username === user?.username
              return (
                <div
                  key={entry.username}
                  className={`flex items-center justify-between rounded-md px-3 py-2 text-sm ${
                    isCurrentUser
                      ? 'bg-primary/10 ring-1 ring-primary/30'
                      : 'hover:bg-muted/50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="w-6 text-center font-medium">
                      {RANK_EMOJIS[entry.rank] ?? entry.rank}
                    </span>
                    <span className={isCurrentUser ? 'font-semibold' : ''}>
                      {entry.username}
                    </span>
                    {isCurrentUser && (
                      <Badge variant="secondary" className="text-xs px-1 py-0">
                        {t.gamification.you}
                      </Badge>
                    )}
                  </div>
                  <span className="font-mono text-xs text-muted-foreground">
                    {entry.points} {t.gamification.points}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
