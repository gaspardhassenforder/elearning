'use client'

/**
 * Story 4.4: Ambient Progress Bar
 *
 * Thin 3px progress bar displayed below the header showing learner's
 * progress through learning objectives. Uses smooth CSS transitions
 * for a calm, professional appearance.
 *
 * Features:
 * - 3px height (thin, unobtrusive)
 * - Full width, fixed below header
 * - Warm primary color fill
 * - 150ms ease transition for smooth animations
 * - Hidden when no objectives exist
 */

import { Progress } from '@/components/ui/progress'
import { useLearnerObjectivesProgress } from '@/lib/hooks/use-learning-objectives'
import { cn } from '@/lib/utils'

interface AmbientProgressBarProps {
  notebookId: string
  className?: string
}

export function AmbientProgressBar({ notebookId, className }: AmbientProgressBarProps) {
  const { data, isLoading } = useLearnerObjectivesProgress(notebookId)

  // Don't show if loading or no objectives
  if (isLoading || !data || data.total_count === 0) {
    return null
  }

  const progressPercentage = Math.round((data.completed_count / data.total_count) * 100)
  const isComplete = data.completed_count === data.total_count

  return (
    <div className={cn('w-full', className)}>
      <Progress
        value={progressPercentage}
        className={cn(
          'h-[3px] rounded-none',
          // Use success color when complete
          isComplete && '[&>div]:bg-green-500 dark:[&>div]:bg-green-400'
        )}
        style={{
          // Smooth transition for progress changes
          transition: 'width 150ms ease',
        }}
      />
    </div>
  )
}
