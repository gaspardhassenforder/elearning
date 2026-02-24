'use client'

/**
 * Story 4.1: Learner Sources Panel
 * Story 4.3: Scroll-to-document and highlight animation
 * Story 5.1: Document expand/collapse accordion behavior
 *
 * Tabbed panel showing:
 * - Sources: Document cards (collapsible)
 * - Artifacts: Quizzes, podcasts (placeholder for Story 5.2)
 * - Progress: Learning objectives tracking (placeholder for Story 5.3)
 *
 * Story 4.3 additions:
 * - Scroll to document when scrollToSourceId changes in store
 * - Highlight animation on target document (3s glow)
 * - Smooth scroll behavior
 *
 * Story 5.1 additions:
 * - Accordion behavior: only one document expanded at a time
 * - Track expandedSourceId in learner-store
 * - Pass isExpanded and onToggleExpand to DocumentCard
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { FileText, GraduationCap, TrendingUp, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useLearnerStore } from '@/lib/stores/learner-store'
import { DocumentCard } from './DocumentCard'
import { ObjectiveProgressList } from './ObjectiveProgressList'
import { ArtifactsPanel } from './ArtifactsPanel'

interface SourcesPanelProps {
  notebookId: string
}

export function SourcesPanel({ notebookId }: SourcesPanelProps) {
  const { t } = useTranslation()
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Story 4.3: Track document card refs for scroll-to functionality
  const documentRefs = useRef<Map<string, HTMLDivElement>>(new Map())
  const [highlightedSourceId, setHighlightedSourceId] = useState<string | null>(null)

  // Story 4.3: Track timeouts for cleanup on unmount
  const scrollTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined)
  const highlightTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined)

  // Story 4.3: Listen to scroll target from store
  const scrollToSourceId = useLearnerStore((state) => state.scrollToSourceId)
  const setScrollToSourceId = useLearnerStore((state) => state.setScrollToSourceId)

  // Story 5.1: Track expanded document (accordion behavior) - local state (store properties removed)
  const [expandedSourceId, setExpandedSourceId] = useState<string | null>(null)

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

  // Story 4.3: Cleanup timeouts on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current)
      if (highlightTimeoutRef.current) clearTimeout(highlightTimeoutRef.current)
    }
  }, [])

  // Story 4.3: Scroll to document when scrollToSourceId changes
  useEffect(() => {
    if (!scrollToSourceId) return

    // Clear any pending scroll timeout
    if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current)

    // Wait for panel expansion animation if needed (200ms)
    scrollTimeoutRef.current = setTimeout(() => {
      const targetElement = documentRefs.current.get(scrollToSourceId)

      if (targetElement && scrollContainerRef.current) {
        // Scroll to element with smooth behavior, centered in view
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        })

        // Add highlight animation
        setHighlightedSourceId(scrollToSourceId)

        // Clear any pending highlight timeout
        if (highlightTimeoutRef.current) clearTimeout(highlightTimeoutRef.current)

        // Remove highlight after 3 seconds
        highlightTimeoutRef.current = setTimeout(() => {
          setHighlightedSourceId(null)
        }, 3000)
      }

      // Clear scroll target from store
      setScrollToSourceId(null)
    }, 200)
  }, [scrollToSourceId, setScrollToSourceId])

  // Story 4.3: Callback to register document refs
  const setDocumentRef = useCallback((sourceId: string, element: HTMLDivElement | null) => {
    if (element) {
      documentRefs.current.set(sourceId, element)
    } else {
      documentRefs.current.delete(sourceId)
    }
  }, [])

  // Story 5.1: Toggle expand handler (accordion behavior)
  const handleToggleExpand = useCallback((sourceId: string) => {
    // Accordion pattern: only one document expanded at a time
    // If clicking the already expanded card, collapse it (set to null)
    // Otherwise, expand this card (automatically collapses any other expanded card)
    setExpandedSourceId(expandedSourceId === sourceId ? null : sourceId)
  }, [expandedSourceId, setExpandedSourceId])

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
                        ref={(el) => setDocumentRef(source.id, el)}
                        isHighlighted={highlightedSourceId === source.id}
                        isExpanded={expandedSourceId === source.id}
                        onToggleExpand={() => handleToggleExpand(source.id)}
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

            {/* Artifacts Tab - Story 5.2: Artifacts Browsing */}
            <TabsContent value="artifacts" className="h-full m-0">
              <ArtifactsPanel notebookId={notebookId} />
            </TabsContent>

            {/* Progress Tab - Story 4.4: Learning Objectives Progress */}
            <TabsContent value="progress" className="h-full m-0">
              <ObjectiveProgressList notebookId={notebookId} />
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  )
}
