'use client'

import { useMemo } from 'react'
import {
  CheckCircle2,
  Circle,
  Lock,
  BookOpen,
  MonitorPlay,
  MessageSquare,
  ClipboardList,
  Mic,
} from 'lucide-react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { Progress } from '@/components/ui/progress'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useLessonSteps, useLessonStepsProgress } from '@/lib/hooks/use-lesson-plan'
import { useLearnerStore } from '@/lib/stores/learner-store'
import { cn } from '@/lib/utils'
import type { LessonStepResponse } from '@/lib/api/lesson-plan'

interface LessonPlanProgressProps {
  notebookId: string
}

const STEP_TYPE_ICONS: Record<string, typeof BookOpen> = {
  read: BookOpen,
  watch: MonitorPlay,
  quiz: ClipboardList,
  discuss: MessageSquare,
  podcast: Mic,
}

function getStepIcon(stepType: string) {
  return STEP_TYPE_ICONS[stepType] || BookOpen
}

export function LessonPlanProgress({ notebookId }: LessonPlanProgressProps) {
  const { t } = useTranslation()
  const openViewerSheet = useLearnerStore((state) => state.openViewerSheet)

  const { data: steps, isLoading: stepsLoading } = useLessonSteps(notebookId)
  const { data: progress, isLoading: progressLoading } = useLessonStepsProgress(notebookId)

  const isLoading = stepsLoading || progressLoading

  const completedSet = useMemo(
    () => new Set(progress?.completed_step_ids ?? []),
    [progress?.completed_step_ids]
  )

  // Find the first non-completed step
  const currentStepIndex = useMemo(() => {
    if (!steps) return -1
    return steps.findIndex((step) => !completedSet.has(step.id))
  }, [steps, completedSet])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner />
      </div>
    )
  }

  if (!steps || steps.length === 0) {
    return (
      <EmptyState
        icon={BookOpen}
        title={t.learner?.progress?.noObjectives || 'No Lesson Plan'}
        description={t.learner?.progress?.noObjectivesDesc || 'A lesson plan will appear here once configured by your instructor.'}
      />
    )
  }

  const completedCount = progress?.completed_count ?? 0
  const totalSteps = steps.length
  const progressPercentage = totalSteps > 0
    ? Math.round((completedCount / totalSteps) * 100)
    : 0

  return (
    <div>
      {/* Progress Summary */}
      <div className="px-1 py-2 space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium">
            {t.learner?.progress?.title || 'Progress'}
          </span>
          <span className="text-[10px] text-muted-foreground tabular-nums">
            {completedCount}/{totalSteps}
          </span>
        </div>
        <Progress value={progressPercentage} className="h-1.5" />
        <p className="text-[10px] text-muted-foreground">
          {progressPercentage}% {t.learner?.progress?.complete || 'complete'}
        </p>
      </div>

      {/* Steps List */}
      <div className="space-y-0.5 px-1 pb-2">
        {steps.map((step, index) => {
          const isPast = completedSet.has(step.id)
          const isCurrent = index === currentStepIndex
          const isFuture = !isPast && !isCurrent

          return (
            <StepItem
              key={step.id}
              step={step}
              isPast={isPast}
              isCurrent={isCurrent}
              isFuture={isFuture}
              onSourceClick={
                step.source_id && !isFuture
                  ? () => openViewerSheet({ type: 'source', id: step.source_id! })
                  : undefined
              }
            />
          )
        })}
      </div>

      {/* All Complete */}
      {completedCount === totalSteps && totalSteps > 0 && (
        <div className="px-1 py-2 bg-green-50 dark:bg-green-950/30 rounded-md">
          <p className="text-xs text-green-700 dark:text-green-300 font-medium text-center">
            {t.learner?.progress?.allComplete || 'All steps completed!'}
          </p>
        </div>
      )}
    </div>
  )
}

interface StepItemProps {
  step: LessonStepResponse
  isPast: boolean
  isCurrent: boolean
  isFuture: boolean
  onSourceClick?: () => void
}

function StepItem({ step, isPast, isCurrent, isFuture, onSourceClick }: StepItemProps) {
  const Icon = getStepIcon(step.step_type)

  return (
    <div
      className={cn(
        'flex items-start gap-2 py-1.5 px-2 rounded-md transition-all duration-150',
        isPast && 'bg-green-50 dark:bg-green-950/30 opacity-70',
        isCurrent && 'bg-accent border-l-2 border-primary',
        isFuture && 'opacity-40 pointer-events-none',
      )}
    >
      {/* Status icon */}
      <div className="flex-shrink-0 mt-0.5">
        {isPast ? (
          <CheckCircle2 className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
        ) : isFuture ? (
          <Lock className="h-3 w-3 text-muted-foreground" />
        ) : (
          <Circle className="h-3.5 w-3.5 text-primary" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <Icon className="h-3 w-3 flex-shrink-0 text-muted-foreground" />
          <p className={cn(
            'text-xs leading-normal truncate',
            isPast && 'text-green-900 dark:text-green-100',
            isCurrent && 'text-foreground font-medium',
            isFuture && 'text-muted-foreground',
          )}>
            {step.title}
          </p>
        </div>

        {/* Source link (visible for past and current steps only) */}
        {!isFuture && step.source_title && onSourceClick && (
          <button
            onClick={onSourceClick}
            className="text-[10px] text-muted-foreground hover:text-primary truncate block mt-0.5 text-left"
          >
            {step.source_title}
          </button>
        )}
      </div>
    </div>
  )
}
