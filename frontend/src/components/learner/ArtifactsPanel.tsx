'use client'

/**
 * Story 5.2: Artifacts Panel Component
 *
 * Panel displaying list of artifacts (quizzes, podcasts, summaries, transformations)
 * for a module in the learner view.
 *
 * Features:
 * - Fetches artifacts using useNotebookArtifacts hook
 * - Renders list of ArtifactCard components
 * - Accordion behavior: only one artifact expanded at a time (local state)
 * - Loading state while fetching
 * - Error state with retry button (distinct from empty state)
 * - Empty state when no artifacts exist
 */

import { useState } from 'react'
import { GraduationCap, AlertCircle } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useNotebookArtifacts } from '@/lib/hooks/use-artifacts'
import { ArtifactCard } from './ArtifactCard'

interface ArtifactsPanelProps {
  notebookId: string
}

export function ArtifactsPanel({ notebookId }: ArtifactsPanelProps) {
  const { t } = useTranslation()

  // Local state for accordion behavior (only one expanded at a time)
  const [expandedArtifactId, setExpandedArtifactId] = useState<string | null>(null)

  // Fetch artifacts for the notebook
  const { data: artifacts, isLoading, error, refetch } = useNotebookArtifacts(notebookId)

  // Toggle expand handler (accordion behavior)
  const handleToggleExpand = (artifactId: string) => {
    // If clicking the already expanded card, collapse it
    // Otherwise, expand this card (collapses any other expanded card)
    setExpandedArtifactId(expandedArtifactId === artifactId ? null : artifactId)
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  // Error state with retry button (distinct from empty state)
  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center px-4 text-center">
        <AlertCircle className="h-10 w-10 text-destructive mb-3" />
        <h3 className="text-sm font-medium text-foreground mb-1">
          {t.learner?.artifacts?.loadError || "Failed to load artifacts"}
        </h3>
        <p className="text-xs text-muted-foreground mb-4">
          {t.learner?.artifacts?.loadErrorDesc || "There was a problem loading the artifacts. Please try again."}
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
        >
          {t.learner?.artifacts?.retry || "Try Again"}
        </Button>
      </div>
    )
  }

  // Empty state when no artifacts
  if (!artifacts || artifacts.length === 0) {
    return (
      <div className="h-full flex items-center justify-center px-4">
        <EmptyState
          icon={GraduationCap}
          title={t.learner?.artifacts?.noArtifacts || "No artifacts yet"}
          description={t.learner?.artifacts?.noArtifactsDesc || "Your AI teacher may generate quizzes and summaries as you learn."}
        />
      </div>
    )
  }

  // Artifacts list
  return (
    <ScrollArea className="h-full px-4 py-3">
      <div className="space-y-3">
        {artifacts.map((artifact) => (
          <ArtifactCard
            key={artifact.id}
            artifact={artifact}
            isExpanded={expandedArtifactId === artifact.id}
            onToggleExpand={() => handleToggleExpand(artifact.id)}
          />
        ))}
      </div>
    </ScrollArea>
  )
}
