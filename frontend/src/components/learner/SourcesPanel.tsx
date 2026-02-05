'use client'

/**
 * Story 4.1: Learner Sources Panel
 *
 * Tabbed panel showing:
 * - Sources: Document cards (collapsible)
 * - Artifacts: Quizzes, podcasts (placeholder for Story 5.2)
 * - Progress: Learning objectives tracking (placeholder for Story 5.3)
 */

import { useCallback, useEffect, useRef } from 'react'
import { FileText, GraduationCap, TrendingUp, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { DocumentCard } from './DocumentCard'

interface SourcesPanelProps {
  notebookId: string
}

export function SourcesPanel({ notebookId }: SourcesPanelProps) {
  const { t } = useTranslation()
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  const {
    sources,
    isLoading,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useNotebookSources(notebookId)

  // Infinite scroll handler
  const handleScroll = useCallback(() => {
    const container = scrollContainerRef.current
    if (!container || !hasNextPage || isFetchingNextPage || !fetchNextPage) return

    const { scrollTop, scrollHeight, clientHeight } = container
    // Trigger when within 200px of bottom
    if (scrollHeight - scrollTop - clientHeight < 200) {
      fetchNextPage()
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return

    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [handleScroll])

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0">
        <CardTitle className="text-lg flex items-center gap-2">
          <FileText className="h-5 w-5" />
          {t.learner.sources.title}
        </CardTitle>
        <CardDescription>
          {t.learner.sources.description.replace('{count}', String(sources?.length || 0))}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        <Tabs defaultValue="sources" className="h-full flex flex-col">
          <div className="px-4 pt-2 border-b flex-shrink-0">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="sources" className="gap-2">
                <FileText className="h-4 w-4" />
                {t.learner.tabs.sources}
              </TabsTrigger>
              <TabsTrigger value="artifacts" className="gap-2">
                <GraduationCap className="h-4 w-4" />
                {t.learner.tabs.artifacts}
              </TabsTrigger>
              <TabsTrigger value="progress" className="gap-2">
                <TrendingUp className="h-4 w-4" />
                {t.learner.tabs.progress}
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-hidden">
            {/* Sources Tab */}
            <TabsContent value="sources" className="h-full m-0">
              <ScrollArea ref={scrollContainerRef} className="h-full px-4 py-3">
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner />
                  </div>
                ) : !sources || sources.length === 0 ? (
                  <EmptyState
                    icon={FileText}
                    title={t.learner.sources.noSources}
                    description={t.learner.sources.noSourcesDesc}
                  />
                ) : (
                  <div className="space-y-3">
                    {sources.map((source) => (
                      <DocumentCard
                        key={source.id}
                        source={source}
                      />
                    ))}
                    {isFetchingNextPage && (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                      </div>
                    )}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>

            {/* Artifacts Tab - Placeholder for Story 5.2 */}
            <TabsContent value="artifacts" className="h-full m-0">
              <div className="h-full flex items-center justify-center px-4">
                <EmptyState
                  icon={GraduationCap}
                  title={t.learner.artifacts.comingSoon}
                  description={t.learner.artifacts.comingSoonDesc}
                />
              </div>
            </TabsContent>

            {/* Progress Tab - Placeholder for Story 5.3 */}
            <TabsContent value="progress" className="h-full m-0">
              <div className="h-full flex items-center justify-center px-4">
                <EmptyState
                  icon={TrendingUp}
                  title={t.learner.progress.comingSoon}
                  description={t.learner.progress.comingSoonDesc}
                />
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  )
}
