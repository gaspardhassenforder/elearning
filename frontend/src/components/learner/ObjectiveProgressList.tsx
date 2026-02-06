'use client'

/**
 * Story 4.4: Learning Objectives Progress Display
 *
 * Displays learning objectives as a checklist with progress status.
 * Used in the Progress tab of the learner SourcesPanel.
 *
 * Features:
 * - Checklist format with checkbox icons (checked/unchecked)
 * - Status-based styling (completed = green, not started = gray)
 * - Shows evidence summary on hover for completed objectives
 * - Auto-refreshes to catch AI-triggered completions
 */

import { CheckCircle2, Circle, Target, Loader2 } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { Progress } from '@/components/ui/progress'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useLearnerObjectivesProgress } from '@/lib/hooks/use-learning-objectives'
import type { ObjectiveWithProgress } from '@/lib/types/api'
import { cn } from '@/lib/utils'

interface ObjectiveProgressListProps {
  notebookId: string
}

interface ObjectiveItemProps {
  objective: ObjectiveWithProgress
  t: ReturnType<typeof useTranslation>['t']
}

function ObjectiveItem({ objective, t }: ObjectiveItemProps) {
  const isCompleted = objective.progress_status === 'completed'
  const hasEvidence = isCompleted && objective.progress_evidence

  const content = (
    <div
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg transition-colors',
        isCompleted
          ? 'bg-green-50 dark:bg-green-950/30'
          : 'bg-muted/50 hover:bg-muted'
      )}
    >
      {/* Checkbox icon */}
      <div className="flex-shrink-0 mt-0.5">
        {isCompleted ? (
          <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
        ) : (
          <Circle className="h-5 w-5 text-muted-foreground" />
        )}
      </div>

      {/* Objective text */}
      <div className="flex-1 min-w-0">
        <p
          className={cn(
            'text-sm leading-relaxed',
            isCompleted
              ? 'text-green-900 dark:text-green-100'
              : 'text-foreground'
          )}
        >
          {objective.text}
        </p>
        {isCompleted && objective.progress_completed_at && (
          <p className="text-xs text-green-600/80 dark:text-green-400/80 mt-1">
            {t.learner.progress.completedAt.replace(
              '{date}',
              new Date(objective.progress_completed_at).toLocaleDateString()
            )}
          </p>
        )}
      </div>
    </div>
  )

  // Wrap completed objectives with tooltip showing evidence
  if (hasEvidence) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="cursor-help">{content}</div>
        </TooltipTrigger>
        <TooltipContent side="left" className="max-w-xs">
          <p className="text-xs font-medium mb-1">{t.learner.progress.evidence}</p>
          <p className="text-xs text-muted-foreground">
            {objective.progress_evidence}
          </p>
        </TooltipContent>
      </Tooltip>
    )
  }

  return content
}

export function ObjectiveProgressList({ notebookId }: ObjectiveProgressListProps) {
  const { t } = useTranslation()
  const { data, isLoading, error } = useLearnerObjectivesProgress(notebookId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <EmptyState
        icon={Target}
        title={t.learner.progress.loadError}
        description={t.learner.progress.loadErrorDesc}
      />
    )
  }

  if (!data || data.objectives.length === 0) {
    return (
      <EmptyState
        icon={Target}
        title={t.learner.progress.noObjectives}
        description={t.learner.progress.noObjectivesDesc}
      />
    )
  }

  const progressPercentage = data.total_count > 0
    ? Math.round((data.completed_count / data.total_count) * 100)
    : 0

  return (
    <TooltipProvider>
      <div className="h-full flex flex-col">
        {/* Progress Summary Header */}
        <div className="px-4 py-3 border-b space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">{t.learner.progress.title}</h3>
            <span className="text-sm text-muted-foreground">
              {data.completed_count}/{data.total_count}
            </span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
          <p className="text-xs text-muted-foreground">
            {progressPercentage}% {t.learner.progress.complete}
          </p>
        </div>

        {/* Objectives List */}
        <ScrollArea className="flex-1 px-4 py-3">
          <div className="space-y-2">
            {data.objectives.map((objective) => (
              <ObjectiveItem
                key={objective.id}
                objective={objective}
                t={t}
              />
            ))}
          </div>
        </ScrollArea>

        {/* All Complete Message */}
        {data.completed_count === data.total_count && data.total_count > 0 && (
          <div className="px-4 py-3 border-t bg-green-50 dark:bg-green-950/30">
            <p className="text-sm text-green-700 dark:text-green-300 font-medium text-center">
              {t.learner.progress.allComplete}
            </p>
          </div>
        )}
      </div>
    </TooltipProvider>
  )
}
